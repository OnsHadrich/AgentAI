from langchain.tools import tool
from model.order_model import OrderInput, UpdateQuantityInput
from utils.helpers import PRODUCTS,ORDERS, save_orders, save_products

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
                f"  Quantity  : {order['quantity']}\n"
                f"  Status    : {order['status']}\n"
                f"  Date      : {order['date']}\n"
                f"  Price     : ${product.get('price', 'N/A')}\n"
                f"  Warranty  : {product.get('warranty_years', 'N/A')} year(s)"
            )
    return f"No order found with ID: {order_id}."


@tool("create_order", args_schema=OrderInput)
def create_order(order_id: str, user_id: str, product_id: str, quantity: int, status: str, date: str) -> str:
    """
    Create a new order for a user.
    Automatically verifies stock availability and reduces stock after successful order.
    """

    # ── Step 1: validate product exists ──────────────────
    if product_id not in PRODUCTS:
        available = ", ".join(PRODUCTS.keys())
        return f"Product '{product_id}' not found. Available product IDs: {available}"

    # ── Step 2: validate order ID is unique ──────────────
    existing_ids = [o["order_id"] for o in ORDERS]
    if order_id in existing_ids:
        return f"Order ID '{order_id}' already exists. Please use a different order ID."

    # ── Step 3: validate quantity ─────────────────────────
    if quantity < 1:
        return "Quantity must be at least 1."

    # ── Step 4: check stock availability ─────────────────
    product = PRODUCTS[product_id]
    current_stock = product.get("stock", 0)

    if current_stock == 0:
        return (
            f"Cannot create order — '{product['name']}' is out of stock.\n"
            f"  Current stock : 0 units available"
        )

    if quantity > current_stock:
        return (
            f"Cannot create order — not enough stock for '{product['name']}'.\n"
            f"  Requested : {quantity} units\n"
            f"  Available : {current_stock} units\n"
            f"  Please reduce quantity to {current_stock} or less."
        )

    # ── Step 5: reduce stock ──────────────────────────────
    new_stock = current_stock - quantity
    PRODUCTS[product_id]["stock"] = new_stock

    # update availability flag if stock hits zero
    if new_stock == 0:
        PRODUCTS[product_id]["availability"] = "out of stock"

    save_products()

    # ── Step 6: create the order ──────────────────────────
    total = product["price"] * quantity

    new_order = {
        "order_id": order_id,
        "user_id": user_id,
        "product_id": product_id,
        "product": product["name"],
        "quantity": quantity,
        "status": status,
        "date": date
    }

    ORDERS.append(new_order)
    save_orders()

    return (
        f"Order created successfully!\n"
        f"  Order ID  : {order_id}\n"
        f"  User      : {user_id}\n"
        f"  Product   : {product['name']} ({product_id})\n"
        f"  Quantity  : {quantity} units\n"
        f"  Total     : ${product['price']} x {quantity} = ${total:.2f}\n"
        f"  Status    : {status}\n"
        f"  Date      : {date}\n"
        f"  Stock     : {current_stock} → {new_stock} units remaining"
    )
@tool
def delete_order(order_id: str) -> str:
    """Delete an order permanently by order ID e.g. 1001."""
    global ORDERS
    for order in ORDERS:
        if order["order_id"] == order_id:
            product_id = order["product_id"]
            quantity = order["quantity"]
            # ── Step 1: restore stock if order was not cancelled ──
            if product_id in PRODUCTS and order["status"] != "cancelled":
                PRODUCTS[product_id]["stock"] += quantity
                # update availability if stock was previously zero
                if PRODUCTS[product_id]["stock"] == 0 and PRODUCTS[product_id]["availability"] == "out of stock":
                    PRODUCTS[product_id]["availability"] = "in stock"
                save_products()
                stock_info = f"Restored {quantity} units to stock for product '{PRODUCTS[product_id]['name']}' (ID: {product_id})."
            else:
                stock_info = "No stock adjustment needed (order was cancelled or product not found)."   
            ORDERS = [o for o in ORDERS if o["order_id"] != order_id]
            save_orders()
            return (
                f"Order {order_id} ({order['product']}) has been deleted successfully.\n"
                f"{stock_info}"
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
    """
    Cancel an order by order ID.
    Automatically restores product stock when a processing or shipped order is cancelled.
    """
    for order in ORDERS:
        if order["order_id"] == order_id:
            if order["status"] == "delivered":
                return f"Order {order_id} cannot be cancelled — it has already been delivered."
            if order["status"] == "cancelled":
                return f"Order {order_id} is already cancelled."

            old_status = order["status"]
            qty = order.get("quantity", 1)
            product_id = order["product_id"]

            # ── restore stock on cancel ───────────────────
            if product_id in PRODUCTS:
                PRODUCTS[product_id]["stock"] += qty
                if PRODUCTS[product_id]["availability"] == "out of stock":
                    PRODUCTS[product_id]["availability"] = "in stock"
                save_products()
                stock_msg = f"  Stock restored : +{qty} units → {PRODUCTS[product_id]['stock']} total"
            else:
                stock_msg = "  Stock : product not found, no stock restored"

            order["status"] = "cancelled"
            save_orders()
            return (
                f"Order {order_id} ({order['product']} x{qty}) cancelled.\n"
                f"  {old_status} → cancelled\n"
                f"{stock_msg}"
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
            f"    Quantity: {order['quantity']}\n"
            f"    Status  : {order['status']}\n"
            f"    Date    : {order['date']}\n"
            f"    Price   : ${product.get('price', 'N/A')}\n"
        )
    return result


@tool(args_schema=UpdateQuantityInput)
def update_order_quantity(order_id: str, quantity: int) -> str:
    """
    Use this when a customer wants to CHANGE THE QUANTITY of an existing order.
    Automatically adjusts product stock if order is still pending or processing.
    """

    # find order (your create_order uses "id", not "order_id")
    order = next((o for o in ORDERS if o.get("id") == order_id), None)
    if not order:
        return f"No order found with ID: {order_id}."

    if order["status"] in ["delivered", "cancelled", "shipped"]:
        return f"Cannot change quantity - order {order_id} is already {order['status']}."

    old_qty = int(order.get("quantity", 1))
    order["quantity"] = quantity

    # adjust stock
    product = next((p for p in PRODUCTS if p["product_id"] == order["product_id"]), None)
    stock_msg = ""
    if product:
        stock_change = old_qty - quantity  # positive = return to stock
        product["stock"] += stock_change
        stock_msg = f"\nStock adjusted by {stock_change:+d} → {product['stock']} units now."

    save_orders()
    save_products()

    return f"Order {order_id} updated: quantity {old_qty} → {quantity}.{stock_msg}"