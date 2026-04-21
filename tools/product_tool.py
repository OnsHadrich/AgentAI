import json
from langchain.tools import tool

with open('products.json', 'r') as f:
    products = json.load(f)

@tool("list_products", return_direct=True, description="List all products with their details.")
def list_products() -> str:
    """List all products with their details."""
    if not products:
        return "No products available."
    return "\n".join([f"{prod['product_id']}: {prod['name']} - ${prod['price']} ({prod['availability']})" for prod in products])

@tool ("list_available_products", return_direct=True, description="List all available products.")
def list_available_products() -> str:
    """List all available products."""
    available_products = [prod for prod in products if prod['availability'] == 'in stock']
    if not available_products:
        return "No products available."
    return "\n".join([f"{prod['product_id']}: {prod['name']} - ${prod['price']}" for prod in available_products])