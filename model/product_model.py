from pydantic import BaseModel, Field
from typing import Literal

class ProductInput(BaseModel):
    product_id: str = Field(..., description="The unique identifier for the product.")
    name: str = Field(..., description="The name of the product.")
    price: float = Field(..., description="The price of the product.")
    availability: Literal['in stock', 'out of stock'] = Field(..., description="The availability status of the product.")