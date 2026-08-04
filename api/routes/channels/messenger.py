from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
import requests
import json
from core.config import Configs
from services.agent_service import AgentService
from schema.channel_schema import Channel
from utils.helpers import _get_conversation_id

router = APIRouter(prefix="/messenger", tags=["Messenger"])
configs = Configs()
agent_service = AgentService()




def send_message(recipient_id: str, text: str) -> None:
    """Send Messenger message via Meta Graph API."""
    url     = f"https://graph.facebook.com/v18.0/me/messages"
    params  = {"access_token": configs.MESSENGER_ACCESS_TOKEN}
    payload = {
        "recipient": {"id": recipient_id},
        "message"  : {"text": text}
    }
    try:
        res = requests.post(url, json=payload, params=params)
        print(f"[Messenger] Sent to {recipient_id}: {res.status_code} ✓")
    except Exception as e:
        print(f"[Messenger] Failed: {e}")


@router.get("/webhook")
def verify(request: Request):
    mode      = request.query_params.get("hub.mode")
    token     = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == configs.MESSENGER_VERIFY_TOKEN:
        print("[Messenger] Webhook verified ✓")
        return PlainTextResponse(content=challenge, status_code=200)

    return PlainTextResponse(content="Forbidden", status_code=403)


@router.post("/webhook")
async def receive(request: Request):
    try:
        data = await request.json()
        print(f"[Messenger] Payload: {json.dumps(data, indent=2)}")

        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging.get("sender", {}).get("id", "")
                message   = messaging.get("message", {})
                text      = message.get("text", "").strip()

                if not text or not sender_id:
                    continue

                print(f"[Messenger] ({sender_id}): {text}")

                try:
                    conversation_id =await  _get_conversation_id(sender_id)

                    reply = await agent_service.reply(
                        user_id        =sender_id,
                        conversation_id=conversation_id,
                        user_message   =text,
                        channel        =Channel.MESSENGER,
                        sender_name    ="Messenger User"
                    )

                    send_message(sender_id, reply)

                except Exception as e:
                    print(f"[Messenger] Error: {e}")
                    send_message(sender_id, "Sorry, please try again.")

        return {"status": 200}

    except Exception as e:
        print(f"[Messenger] Fatal: {e}")
        return {"status": 500}