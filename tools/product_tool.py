import json
from langchain.tools import tool

with open('data/products.json', 'r') as f:
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

@tool("get_product_details", return_direct=True, description="Get details of a product by its ID.")
def get_product_details(product_id: str) -> str:
    """Get details of a product by its ID."""
    for prod in products:
        if prod['product_id'] == product_id:
            return (
                f"Product ID: {prod['product_id']}\n"
                f"Name      : {prod['name']}\n"
                f"Price     : ${prod['price']}\n"
                f"Stock     : {prod['stock']}\n"
                f"Description: {prod['description']}\n"
                f"Warranty   : {prod['warranty_years']} year(s)\n"
                f"Availability: {prod['availability']}"
            )
    return f"No product found with ID: {product_id}"

@tool("check_product_availability", return_direct=True, description="Check if a product is available by its ID.")
def check_product_availability(product_id: str) -> str:
    """Check if a product is available by its ID."""
    for prod in products:
        if prod['product_id'] == product_id:
            return f"Product '{prod['name']}' is {prod['availability']}."
    return f"No product found with ID: {product_id}"

@tool("get_product_price", return_direct=True, description="Get the price of a product by its ID.")
def get_product_price(product_id: str) -> str:
    """Get the price of a product by its ID."""
    for prod in products:
        if prod['product_id'] == product_id:
            return f"The price of '{prod['name']}' is ${prod['price']}."
    return f"No product found with ID: {product_id}"

@tool("search_products", return_direct=True, description="Search for products by name keyword.")
def search_products(keyword: str) -> str:
    """Search for products by name keyword."""
    found_products = [prod for prod in products if keyword.lower() in prod['name'].lower()]
    if not found_products:
        return f"No products found with keyword: {keyword}"
    return "\n".join([f"{prod['product_id']}: {prod['name']} - ${prod['price']}" for prod in found_products])
