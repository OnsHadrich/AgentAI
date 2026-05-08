from model.order_model import Order
from repositories.order_repository import OrderRepository
from repositories.product_repository import ProductRepository



class OrderTool:
    def __init__(
        self,
        order_repo: OrderRepository| None = None,
        product_repo: ProductRepository| None = None
    ):
        self.order_repo = order_repo or OrderRepository()
        self.product_repo = product_repo or ProductRepository()



    # ── private methods mirror your existing functions ─────

    def _get_order_status(self, order_id: str) -> str:
        order = self.order_repo.find_by_id(order_id)
        if not order:
            return f"No order found with ID: {order_id}."
        product = self.product_repo.find_by_id(order.product_id)
        return (
            f"Order #{order.order_id}\n"
            f"  Product   : {order.product_id}\n"
            f"  Quantity  : {order.quantity}\n"
            f"  Status    : {order.status}\n"
            f"  Date      : {order.date}\n"
            f"  Price     : ${product.price if product else 'N/A'}\n"
            f"  Warranty  : {product.warranty_years if product else 'N/A'} year(s)"
        )

    def _create_order(self, order_id: str, user_id: str, product_id: str,
                      quantity: int, status: str, date: str) -> str:
        product = self.product_repo.find_by_id(product_id)
        if not product:
            available = ", ".join(self.product_repo.get_all_product_ids())
            return f"Product '{product_id}' not found. Available: {available}"

        if self.order_repo.find_by_id(order_id):
            return f"Order ID '{order_id}' already exists."

        if quantity < 1:
            return "Quantity must be at least 1."

        if product.stock == 0:
            return f"Cannot create order — '{product.name}' is out of stock."

        if quantity > product.stock:
            return (
                f"Not enough stock for '{product.name}'.\n"
                f"  Requested : {quantity}\n"
                f"  Available : {product.stock}"
            )

        # update stock
        new_stock = product.stock - quantity
        self.product_repo.update_stock(product_id, new_stock)

        # create order
        total = product.price * quantity
        self.order_repo.create_order(Order(
            order_id=order_id,
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            status=status,
            date=date
        ))
        return (
            f"Order created successfully!\n"
            f"  Order ID : {order_id}\n"
            f"  Product  : {product.name}\n"
            f"  Quantity : {quantity}\n"
            f"  Total    : ${total:.2f}\n"
            f"  Stock    : {product.stock} → {new_stock} remaining"
        )

    def _cancel_order(self, order_id: str) -> str:
        order = self.order_repo.find_by_id(order_id)
        if not order:
            return f"No order found with ID: {order_id}."
        if order.status == "delivered":
            return f"Cannot cancel — order {order_id} already delivered."
        if order.status == "cancelled":
            return f"Order {order_id} is already cancelled."

        # restore stock
        product = self.product_repo.find_by_id(order.product_id)
        stock_msg = ""
        if product:
            new_stock = product.stock + order.quantity
            self.product_repo.update_stock(order.product_id, new_stock)
            stock_msg = f"\n  Stock restored: +{order.quantity} → {new_stock} total"

        self.order_repo.update_order_status(order_id, "cancelled")
        return f"Order {order_id} cancelled.{stock_msg}"

    def _delete_order(self, order_id: str) -> str:
        order = self.order_repo.find_by_id(order_id)
        if not order:
            return f"No order found with ID: {order_id}."

        if order.status != "cancelled":
            product = self.product_repo.find_by_id(order.product_id)
            if product:
                self.product_repo.update_stock(
                    order.product_id,
                    product.stock + order.quantity
                )

        self.order_repo.delete_order(order_id)
        return f"Order {order_id} deleted successfully."

    def _confirm_delivery(self, order_id: str) -> str:
        order = self.order_repo.find_by_id(order_id)
        if not order:
            return f"No order found with ID: {order_id}."
        if order.status == "delivered":
            return f"Order {order_id} is already delivered."
        if order.status == "cancelled":
            return f"Order {order_id} is cancelled — cannot confirm delivery."
        self.order_repo.update_order_status(order_id, "delivered")
        return f"Order {order_id} marked as delivered."

    def _list_orders(self, user_id: str) -> str:
        orders = self.order_repo.find_by_user(user_id)
        if not orders:
            return f"No orders found for user {user_id}."
        result = f"Orders for user {user_id}:\n"
        for order in orders:
            product = self.product_repo.find_by_id(order.product_id)
            result += (
                f"\n  Order #{order.order_id}\n"
                f"    Product  : {order.product_id}\n"
                f"    Quantity : {order.quantity}\n"
                f"    Status   : {order.status}\n"
                f"    Date     : {order.date}\n"
                f"    Price    : ${product.price if product else 'N/A'}\n"
            )
        return result

    def _update_order_quantity(self, order_id: str, quantity: int) -> str:
        order = self.order_repo.find_by_id(order_id)
        if not order:
            return f"No order found with ID: {order_id}."
        if order.status in ["delivered", "cancelled", "shipped"]:
            return f"Cannot update — order {order_id} is {order.status}."

        old_qty = order.quantity
        product = self.product_repo.find_by_id(order.product_id)
        stock_msg = ""
        if product:
            stock_change = old_qty - quantity
            self.product_repo.update_stock(
                order.product_id,
                product.stock + stock_change
            )
            stock_msg = f"\n  Stock adjusted: {stock_change:+d} → {product.stock + stock_change} total"

        self.order_repo.update_quantity(order_id, quantity)
        return f"Order {order_id} updated: {old_qty} → {quantity} units.{stock_msg}"