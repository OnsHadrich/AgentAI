from fastapi import APIRouter, Request, HTTPException
import requests
import json
from core.config import Configs
from services.agent_service import AgentService

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])
configs = Configs()
agent_service = AgentService()


# ── Webhook Verification ──────────────────────────────────
@router.get("/webhook")
def verify_webhook(request: Request):
    """
    Verify webhook with Meta.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    print(f"[WhatsApp] Verify webhook called")
    print(f"  mode: {mode}")
    print(f"  token: {token}")
    print(f"  challenge: {challenge}")
    print(f"  expected token: {configs.WHATSAPP_VERIFY_TOKEN}")

    if mode != "subscribe":
        raise HTTPException(status_code=403, detail="Invalid mode")

    if token != configs.WHATSAPP_VERIFY_TOKEN:
        print(f"[WhatsApp] Token mismatch! Got: {token}, Expected: {configs.WHATSAPP_VERIFY_TOKEN}")
        raise HTTPException(status_code=403, detail="Invalid verification token")

    print(f"[WhatsApp] Webhook verified ✓")
    return {"status": 200, "body": challenge}


# ── Receive Messages ──────────────────────────────────────
@router.post("/webhook")
async def receive_whatsapp_message(request: Request):
    """
    Receive messages from WhatsApp.
    """
    try:
        body = await request.json()
        print(f"[WhatsApp] Received: {json.dumps(body, indent=2)}")

        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": 200}

        message = messages[0]
        phone_number = message.get("from")
        text = message.get("text", {}).get("body", "")

        if not text:
            return {"status": 200}

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

        return {"status": 200}

    except Exception as e:
        print(f"[WhatsApp] Error: {e}")
        import traceback
        print(traceback.format_exc())
        return {"status": 500, "error": str(e)}


# ── Send Message ──────────────────────────────────────────
def send_whatsapp_message(phone_number: str, text: str) -> None:
    """Send a message back to the user via WhatsApp."""
    if not configs.WHATSAPP_ACCESS_TOKEN:
        print(f"[WhatsApp] No access token configured")
        return

    url = f"{configs.WHATSAPP_API_URL}/{configs.WHATSAPP_PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {configs.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"[WhatsApp] Sent to {phone_number} ✓")
    except requests.exceptions.RequestException as e:
        print(f"[WhatsApp] Failed to send: {e}")


# ── Conversation tracking ─────────────────────────────────
_conversations = {}


def _get_conversation_id(phone_number: str) -> str:
    """Get or create a conversation for this phone number."""
    if phone_number not in _conversations:
        conversation_id = agent_service.start_conversation(phone_number)
        _conversations[phone_number] = conversation_id
        print(f"[WhatsApp] Created conversation {conversation_id} for {phone_number}")
    return _conversations[phone_number]