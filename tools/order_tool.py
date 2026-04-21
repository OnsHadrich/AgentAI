import json
from langchain.tools import tool

from model.order_model import OrderInput

with open('orders.json', 'r') as f:
    orders = json.load(f)

with open('products.json', 'r') as file_products:
    products = json.load(file_products)
    
@tool("get_order_status", args_schema =OrderInput ,return_direct=True, description="Get the status of an order by its ID.")
def get_order_status(order_id: str) -> str:
    """Get the status of an order by its ID."""
    for order in orders:
        if order['id'] == order_id:
            return f"Order {order_id} is currently {order['status']}."
    return f"Order {order_id} not found."

@tool("update_order_status", args_schema =OrderInput ,return_direct=True, description="Update the status of an order by its ID.")
def update_order_status(order_id: str, status: str) -> str:
    """Update the status of an order by its ID."""
    for order in orders:
        if order['id'] == order_id:
            order['status'] = status
            with open('orders.json', 'w') as f:
                json.dump(orders, f, indent=4)
            return f"Order {order_id} status updated to {status}."
    return f"Order {order_id} not found."

@tool("list_orders", return_direct=True, description="List all orders with their statuses.")
def list_orders_by_user(user_id: str) -> str:
    """List all orders for a specific user with their statuses."""
    user_orders = [order for order in orders if order['user_id'] == user_id]
    if not user_orders:
        return f"No orders found for user {user_id}."
    return "\n".join([f"Order {order['id']}: {order['status']}" for order in user_orders])

@tool("cancel_order", args_schema =OrderInput ,return_direct=True, description="Cancel an order by its ID.")
def cancel_order(order_id: str) -> str:
    """Cancel an order by its ID."""
    for order in orders:
        if order['id'] == order_id:
            order['status'] = 'cancelled'
            with open('orders.json', 'w') as f:
                json.dump(orders, f, indent=4)
            return f"Order {order_id} has been cancelled."
    return f"Order {order_id} not found."

@tool("delete_order", args_schema =OrderInput ,return_direct=True, description="Delete an order by its ID.")
def delete_order(order_id: str) -> str:
    """Delete an order by its ID."""
    global orders
    orders = [order for order in orders if order['id'] != order_id]
    with open('orders.json', 'w') as f:
        json.dump(orders, f, indent=4)
    return f"Order {order_id} has been deleted."

@tool("create_order", args_schema =OrderInput ,return_direct=True, description="Create a new order with a given ID and status.")
def create_order(order_id: str, status: str, user_id: str, product_id: str) -> str:
    """Create a new order with a given ID and status."""
    new_order = {
        "id": order_id,
        "status": status,
        "user_id": user_id,
        "product_id": product_id
        
    }
    # Verify product exists
    product = next((prod for prod in products if prod['product_id'] == product_id), None)
    if not product:
        return f"Product {product_id} not found. Order cannot be created."
    
    #Verify the stock of the product
    if product['stock'] <= 0:
        return f"Product {product_id} is out of stock. Order cannot be created."
    
    orders.append(new_order)
    
    with open('orders.json', 'w') as f:
        json.dump(orders, f, indent=4)
    return f"Order {order_id} has been created with status {status} for user {user_id}."

@tool("confirm_delivery", args_schema =OrderInput ,return_direct=True, description="Confirm the delivery of an order by its ID. This will update the order status to 'delivered'.")
def confirm_delivery(order_id: str) -> str:
    """Confirm the delivery of an order by its ID. This will update the order status to 'delivered'."""
    for order in orders:
        if order['id'] == order_id:
            order['status'] = 'delivered'
            with open('orders.json', 'w') as f:
                json.dump(orders, f, indent=4)
            return f"Order {order_id} has been marked as delivered."
    return f"Order {order_id} not found."
