from langchain_core.tools import StructuredTool
from schema.order_schema import OrderInput,UpdateQuantityInput
from modular_agentic_ai.tools.order_tool import OrderTool


def create_order_tools(tool: OrderTool) -> list[StructuredTool]:
    return [
        StructuredTool.from_function(
            func=tool._get_order_status,
            name="get_order_status",
            description="Look up the status of a customer order by order ID e.g. 1001."
        ),
        StructuredTool.from_function(
            func=tool._create_order,
            name="create_order",
            description="Create a new order. Verifies stock and reduces it after order.",
            args_schema=OrderInput
        ),
        StructuredTool.from_function(
            func=tool._cancel_order,
            name="cancel_order",
            description="Cancel an order and restore product stock."
        ),
        StructuredTool.from_function(
            func=tool._delete_order,
            name="delete_order",
            description="Delete an order permanently by order ID."
        ),
        StructuredTool.from_function(
            func=tool._confirm_delivery,
            name="confirm_delivery",
            description="Mark an order as delivered."
        ),
        StructuredTool.from_function(
            func=tool._list_orders,
            name="list_orders",
            description="List all orders for a specific user by user ID e.g. u1, u2."
        ),
        StructuredTool.from_function(
            func=tool._update_order_quantity,
            name="update_order_quantity",
            description="Change the quantity of an existing order.",
            args_schema=UpdateQuantityInput
        ),
    ]