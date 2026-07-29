import json
from services.agent_service import AgentService

agent_service = AgentService()

# ── Load data ─────────────────────────────────────────────
with open("data/orders.json", "r") as f:
    ORDERS: list[dict] = json.load(f)

with open("data/products.json", "r") as f:
    PRODUCTS: dict = {p["product_id"]: p for p in json.load(f)}
    
def save_orders():
    """Persist current ORDERS list back to the JSON file."""
    with open("data/orders.json", "w") as f:
        json.dump(ORDERS, f, indent=2)
        
def save_products():
    with open("data/products.json", "w") as f:
        json.dump(list(PRODUCTS.values()), f, indent=2)

# ── Conversation tracking ─────────────────────────────────
_conversations = {}

async def _get_conversation_id(phone_number: str) -> str:
    """Get or create a conversation for this phone number."""
    if phone_number not in _conversations:
        conversation_id = await agent_service.start_conversation(phone_number)
        _conversations[phone_number] = conversation_id
        print(f"[WhatsApp] Created conversation {conversation_id} for {phone_number}")
    return _conversations[phone_number]



