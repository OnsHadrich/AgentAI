from datetime import datetime 
from pydantic import BaseModel, Field
from typing import Literal

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