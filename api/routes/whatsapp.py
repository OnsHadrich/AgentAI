from fastapi import APIRouter, Query, Request, HTTPException
import json
from core.config import Configs
from services.agent_service import AgentService
from utils.helpers import _get_conversation_id
from utils.send_message_whatsapp import send_whatsapp_message

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])
configs = Configs()
agent_service = AgentService()

# ── Health check ──────────────────────────────────
@router.get("/")
async def home():
    return {"message": "API is up"}
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

    if hub_mode != "subscribe":
        raise HTTPException(status_code=403, detail="Invalid mode")

    if hub_verify_token != configs.WHATSAPP_VERIFY_TOKEN:
        print(f"[WhatsApp] Token mismatch! Got: {hub_verify_token}, Expected: {configs.WHATSAPP_VERIFY_TOKEN}")
        raise HTTPException(status_code=403, detail="Invalid verification token")

    print(f"[WhatsApp] Webhook verified ✓")
    return {"status": 200, "body": hub_challenge}


# ── Handling incoming messages ──────────────────────────────────────
@router.post("/webhook")
async def receive_whatsapp_message(request: Request):
    """
    Receive messages from WhatsApp.
    """
    try:
        data = await request.json()
        print(f"[WhatsApp] Received: {json.dumps(data, indent=2)}")
        if data:
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    phone_number_id = value.get("metadata", {}).get("phone_number_id")
                    messages_data = value.get("messages", [])
                    if messages_data:
                        for message in messages_data:
                            phone_number = message.get("from")
                            text = message.get("text", {}).get("body", "")
                            if text:
                                print(f"[WhatsApp] Message from {phone_number}: {text}")
                                # Get or create conversation
                                conversation_id = _get_conversation_id(phone_number)

                                # Call your chat API
                                reply = await agent_service.reply(
                                    user_id=phone_number,
                                    conversation_id=conversation_id,
                                    user_message=text
                                )

                                # Send reply back
                                send_whatsapp_message(phone_number, reply)
        return {"status": 200, "message": "Message processed"}
    except Exception as e:
        print(f"[WhatsApp] Error: {e}")
        import traceback
        print(traceback.format_exc())
        return {"status": 500, "error": str(e)}



