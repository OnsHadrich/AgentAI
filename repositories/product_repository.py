import json
from dataclasses import asdict
from pathlib import Path

from core.config import Configs
from model.product_model import Product


class ProductRepository:
    def __init__(self, filepath: str | Path | None = None, configs: Configs = Configs()):
        self._filepath = Path(filepath or configs.PRODUCTS_FILE)
        with open(self._filepath) as f:
            raw_products = json.load(f)
        self._products: list[Product] = [Product(**product) for product in raw_products]

    def _save(self) -> None:
        with open(self._filepath, "w") as f:
            json.dump([asdict(product) for product in self._products], f, indent=2)

    def get_all(self) -> list[Product]:
        return self._products

    def get_all_product_ids(self) -> list[str]:
        return [product.product_id for product in self._products]

    def get_available(self) -> list[Product]:
        return [p for p in self._products if p.availability == "in stock"]

    def find_by_id(self, product_id: str) -> Product | None:
        return next((p for p in self._products if p.product_id == product_id), None)

    def search_by_name(self, keyword: str) -> list[Product]:
        return [p for p in self._products if keyword.lower() in p.name.lower()]

    def update_stock(self, product_id: str, stock: int) -> Product | None:
        product = self.find_by_id(product_id)
        if not product:
            return None
        product.stock = stock
        product.availability = "in stock" if stock > 0 else "out of stock"
        self._save()
        return product


