from dataclasses import dataclass

@dataclass
class Order:
    order_id: str
    user_id: str
    product_id: str
    quantity: int
    status: str
    date: str