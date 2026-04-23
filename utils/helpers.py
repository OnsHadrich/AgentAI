import json

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
