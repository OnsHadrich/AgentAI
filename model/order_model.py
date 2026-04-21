from pydantic import BaseModel, Field
from typing import Literal

class OrderInput(BaseModel):
    id: str = Field(..., description="The unique identifier for the order.")
    status: Literal['pending', 'shipped', 'delivered', 'cancelled'] = Field(..., description="The current status of the order.")