import json
from datetime import datetime
from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Literal

# ── Load data ─────────────────────────────────────────────
with open("data/orders.json", "r") as f:
    ORDERS: list[dict] = json.load(f)

with open("data/products.json", "r") as f:
    PRODUCTS: dict = {p["product_id"]: p for p in json.load(f)}


# ── Input schema — matches your JSON fields exactly ───────
class OrderInput(BaseModel):
    order_id: str = Field(
        description="Order ID as a number string e.g. 1001, 1002, 1003"
    )
    user_id: str = Field(
        description="User ID e.g. u1, u2"
    )
    product_id: str = Field(
        description="Product ID e.g. p1, p2, p3, p4, p5"
    )
    status: Literal["processing", "shipped", "delivered", "cancelled"] = Field(
        default="processing",
        description="Order status"
    )
    date: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d"),
        description="Order date in YYYY-MM-DD format e.g. 2026-04-10"
    )


def save_orders():
    """Persist current ORDERS list back to the JSON file."""
    with open("data/orders.json", "w") as f:
        json.dump(ORDERS, f, indent=2)


# ── Tools ─────────────────────────────────────────────────
@tool
def get_order_status(order_id: str) -> str:
    """Look up the status of a customer order by order ID e.g. 1001."""
    for order in ORDERS:
        if order["order_id"] == order_id:
            product = PRODUCTS.get(order["product_id"], {})
            return (
                f"Order #{order['order_id']}\n"
                f"  Product   : {order['product']} (ID: {order['product_id']})\n"
                f"  Status    : {order['status']}\n"
                f"  Date      : {order['date']}\n"
                f"  Price     : ${product.get('price', 'N/A')}\n"
                f"  Warranty  : {product.get('warranty_years', 'N/A')} year(s)"
            )
    return f"No order found with ID: {order_id}."


@tool("create_order", args_schema=OrderInput)
def create_order(order_id: str, user_id: str, product_id: str, status: str, date: str) -> str:
    """Create a new order. Requires order_id, user_id, product_id. Status defaults to processing."""

    # validate product exists
    if product_id not in PRODUCTS:
        available = ", ".join(PRODUCTS.keys())
        return f"Product '{product_id}' not found. Available product IDs: {available}"

    # validate order_id not already taken
    existing_ids = [o["order_id"] for o in ORDERS]
    if order_id in existing_ids:
        return f"Order ID '{order_id}' already exists. Existing IDs: {', '.join(existing_ids)}"

    new_order = {
        "order_id": order_id,
        "user_id": user_id,
        "product_id": product_id,
        "product": PRODUCTS[product_id]["name"],   # auto-fill product name from products.json
        "status": status,
        "date": date
    }

    ORDERS.append(new_order)
    save_orders()

    return (
        f"Order created successfully!\n"
        f"  Order ID : {order_id}\n"
        f"  User     : {user_id}\n"
        f"  Product  : {PRODUCTS[product_id]['name']} ({product_id})\n"
        f"  Status   : {status}\n"
        f"  Date     : {date}"
    )


@tool
def delete_order(order_id: str) -> str:
    """Delete an order permanently by order ID e.g. 1001."""
    global ORDERS
    for order in ORDERS:
        if order["order_id"] == order_id:
            ORDERS = [o for o in ORDERS if o["order_id"] != order_id]
            save_orders()
            return (
                f"Order {order_id} ({order['product']}) has been deleted successfully."
            )
    return f"No order found with ID: {order_id}."


@tool
def confirm_delivery(order_id: str) -> str:
    """Mark an order as delivered by order ID e.g. 1001."""
    for order in ORDERS:
        if order["order_id"] == order_id:
            if order["status"] == "delivered":
                return f"Order {order_id} is already marked as delivered."
            if order["status"] == "cancelled":
                return f"Order {order_id} is cancelled and cannot be confirmed as delivered."
            old_status = order["status"]
            order["status"] = "delivered"
            save_orders()
            return (
                f"Order {order_id} ({order['product']}) updated:\n"
                f"  {old_status} → delivered"
            )
    return f"No order found with ID: {order_id}."


@tool
def cancel_order(order_id: str) -> str:
    """Cancel an order by order ID. Cannot cancel already delivered orders."""
    for order in ORDERS:
        if order["order_id"] == order_id:
            if order["status"] == "delivered":
                return (
                    f"Order {order_id} cannot be cancelled — "
                    f"it has already been delivered on {order['date']}."
                )
            if order["status"] == "cancelled":
                return f"Order {order_id} is already cancelled."
            old_status = order["status"]
            order["status"] = "cancelled"
            save_orders()
            return (
                f"Order {order_id} ({order['product']}) has been cancelled.\n"
                f"  {old_status} → cancelled"
            )
    return f"No order found with ID: {order_id}."

@tool
def list_orders(user_id: str) -> str:
    """List all orders for a specific user by user ID e.g. u1, u2."""
    user_orders = [o for o in ORDERS if o["user_id"] == user_id]
    if not user_orders:
        return f"No orders found for user {user_id}."
    result = f"Orders for user {user_id}:\n"
    for order in user_orders:
        product = PRODUCTS.get(order["product_id"], {})
        result += (
            f"\n  Order #{order['order_id']}\n"
            f"    Product : {order['product']} ({order['product_id']})\n"
            f"    Status  : {order['status']}\n"
            f"    Date    : {order['date']}\n"
            f"    Price   : ${product.get('price', 'N/A')}\n"
        )
    return result