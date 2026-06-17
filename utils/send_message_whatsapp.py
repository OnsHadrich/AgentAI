from fastapi import Request
import requests
from core.config import Configs

configs= Configs()
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

