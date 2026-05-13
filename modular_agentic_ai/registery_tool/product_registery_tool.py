from langchain_core.tools import StructuredTool
from modular_agentic_ai.tools.product_tool import ProductTool


def create_product_tools(tool: ProductTool) -> list[StructuredTool]:
    return [
        StructuredTool.from_function(
            func=tool._list_products,
            name="list_products",
            description="List all products with their details, price, and availability."
        ),
        StructuredTool.from_function(
            func=tool._list_available_products,
            name="list_available_products",
            description="List all products that are currently in stock."
        ),
        StructuredTool.from_function(
            func=tool._get_product_details,
            name="get_product_details",
            description="Get full details of a product by its product ID e.g. p1, p2."
        ),
        StructuredTool.from_function(
            func=tool._check_product_availability,
            name="check_product_availability",
            description="Check if a specific product is available by its product ID."
        ),
        StructuredTool.from_function(
            func=tool._get_product_price,
            name="get_product_price",
            description="Get the price of a product by its product ID."
        ),
        StructuredTool.from_function(
            func=tool._search_products,
            name="search_products",
            description="Search for products by a name keyword e.g. laptop, keyboard."
        ),
    ]