from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.responses import PlainTextResponse
import json
import requests
from core.config import Configs
from services.agent_service import AgentService
from utils.helpers import _get_conversation_id
from utils.send_message_whatsapp import send_whatsapp_message
router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])
configs = Configs()
agent_service = AgentService()

GRAPH_API_URL = f"{configs.WHATSAPP_API_URL}/{configs.WHATSAPP_PHONE_NUMBER_ID}/messages"

# ── Health check ──────────────────────────────────────────
@router.get("/health")
def whatsapp_health():
    try:
        url = f"{configs.WHATSAPP_API_URL}/{configs.WHATSAPP_PHONE_NUMBER_ID}"
        headers = {"Authorization": f"Bearer {configs.WHATSAPP_ACCESS_TOKEN}"}
        response = requests.get(url, headers=headers)
        data = response.json()
        return {
            "status"      : "connected",
            "phone_number": data.get("display_phone_number", "unknown"),
            "verified"    : data.get("verified_name", "unknown")
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
# ── Webhook Verification ──────────────────────────────────
@router.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """
    Verify webhook with Meta.
    """

    print(f"[WhatsApp] Verify webhook called")
    print(f"  mode: {hub_mode}")
    print(f"  token: {hub_verify_token}")
    print(f"  challenge: {hub_challenge}")
    print(f"  expected token: {configs.WHATSAPP_VERIFY_TOKEN}")

    if hub_mode != "subscribe" :
        raise HTTPException(status_code=403, detail="Invalid mode")

    if hub_verify_token != configs.WHATSAPP_VERIFY_TOKEN:
        print(f"[WhatsApp] Token mismatch! Got: {hub_verify_token}, Expected: {configs.WHATSAPP_VERIFY_TOKEN}")
        raise HTTPException(status_code=403, detail="Invalid verification token")

    print(f"[WhatsApp] Webhook verified ✓")
    return PlainTextResponse(content=hub_challenge, status_code=200)


# ── Handling incoming messages ──────────────────────────────────────
@router.post("/webhook")
async def receive_whatsapp_message(request: Request):
    """
    Receive messages from WhatsApp.
    Loops through ALL entries and messages — handles bulk payloads.
    """
    try:
        data = await request.json()
        print(f"[WhatsApp] Payload received: {json.dumps(data, indent=2)}")

        if not data:
            return {"status": 200, "message": "Empty payload"}

        processed = 0
        skipped   = 0

        for entry in data.get("entry", []):
            for change in entry.get("changes", []):

                value = change.get("value", {})

                # ── skip status updates ────────────────────
                # Meta sends status updates (delivered, read)
                # we don't want to process those as messages
                if "statuses" in value:
                    skipped += 1
                    continue

                # ── get metadata ───────────────────────────
                metadata        = value.get("metadata", {})
                phone_number_id = metadata.get("phone_number_id", "")


                # ── process each message ───────────────────
                for message in value.get("messages", []):

                    msg_type    = message.get("type", "")
                    from_number = message.get("from", "")
                    
                    # ── get sender name in one line ────────────────────
                    sender_name = next(
                        (
                            contact.get("profile", {}).get("name", "Customer")
                            for contact in value.get("contacts", [])
                            if contact.get("wa_id") == from_number
                        ),
                        "Customer"
                    )

                    print(f"[WhatsApp] {sender_name} ({from_number}): {msg_type}")

                    # ── only handle text messages ──────────
                    if msg_type != "text":
                        print(f"[WhatsApp] Skipping {msg_type} from {from_number}")
                        skipped += 1
                        continue

                    text = message.get("text", {}).get("body", "").strip()

                    if not text or not from_number:
                        skipped += 1
                        continue

                    print(f"[WhatsApp] {sender_name} ({from_number}): {text}")

                    try:
                        # ── get or create conversation ─────
                        conversation_id = await _get_conversation_id(from_number)

                        # ── call your agent ────────────────
                        reply = await agent_service.reply(
                            user_id=from_number,
                            conversation_id=conversation_id,
                            user_message=text,
                            channel="whatsapp"
                        )

                        # ── send reply ─────────────────────
                        send_whatsapp_message(from_number, reply,phone_number_id)

                        processed += 1

                    except Exception as msg_error:
                        print(f"[WhatsApp] Error processing message from {from_number}: {msg_error}")
                        import traceback
                        print(traceback.format_exc())

                        # notify user of error
                        send_whatsapp_message(
                            from_number,
                            "Sorry, I encountered an error. Please try again.",
                            phone_number_id
                        )
                        skipped += 1

        print(f"[WhatsApp] Done — processed: {processed}, skipped: {skipped}")
        return {
            "status"   : 200,
            "processed": processed,
            "skipped"  : skipped
        }

    except Exception as e:
        print(f"[WhatsApp] Fatal error: {e}")
        import traceback
        print(traceback.format_exc())
        return {"status": 500, "error": str(e)}
