from fastapi import Request
import requests
from core.config import Configs

configs= Configs()


# ── Send Message ──────────────────────────────────────────
def send_whatsapp_message(phone_number: str, text: str, phone_number_id: str) -> None:
    """Send a message back to the user via WhatsApp."""
    if not configs.WHATSAPP_ACCESS_TOKEN:
        print(f"[WhatsApp] No access token configured")
        return
    number_id = phone_number_id or configs.WHATSAPP_PHONE_NUMBER_ID

    url = f"{configs.WHATSAPP_API_URL}/{number_id}/messages"

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

        print(f"[WhatsApp] Sent to {phone_number}: {response.status_code} ✓")

        if response.raise_for_status() !=200:
            print(f"[WhatsApp] Failed to send: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"[WhatsApp] Failed to send: {e}")

