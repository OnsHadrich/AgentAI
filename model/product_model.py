from dataclasses import dataclass

@dataclass
class Product:
    product_id: str
    name: str
    price: float
    stock: int
    description: str
    warranty_years: int
    availability: str
    category: str = ""
