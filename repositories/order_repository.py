from dataclasses import asdict
import json
from json import JSONDecodeError

from core.config import Configs
from model.order_model import Order
from utils.hash import get_rand_hash



class OrderRepository:
    def __init__(self, filepath: str | None = None, configs: Configs = Configs()):
        self._filepath = filepath or str(configs.ORDERS_FILE)
        try:
            with open(self._filepath) as f:
                raw = json.load(f)
        except JSONDecodeError:
            raw = []
        self._orders: list[Order] = [Order(**order) for order in raw]
        
    # ── persistence ───────────────────────────────────────
    def _save(self):
        with open(self._filepath, "w") as f:
            json.dump([asdict(o) for o in self._orders], f, indent=2)
    

    def find_by_id(self, order_id: str) -> Order | None:
        return next((o for o in self._orders if o.order_id == order_id), None)
    
    def find_by_user(self, user_id: str) -> list[Order]:
        return [order for order in self._orders if order.user_id == user_id]
    
    def find_by_status(self, status: str) -> list[Order]:
        return [order for order in self._orders if order.status == status]
    
    def find_by_product(self, product_id: str) -> list[Order]:
        return [order for order in self._orders if order.product_id == product_id]
    
    def get_all_orders(self) -> list[Order]:
        return self._orders

    def create_order(self, data_order: Order) -> Order:
        new_order = Order(
            order_id=data_order.order_id or str(get_rand_hash()),
            user_id=data_order.user_id,
            product_id=data_order.product_id,
            quantity=data_order.quantity,
            status=data_order.status,
            date=data_order.date
        )
        self._orders.append(new_order)
        with open(self._filepath, "w") as f:
            json.dump([asdict(order) for order in self._orders], f, indent=2)
        return new_order
    
    
    def update_order_status(self, order_id: str, status: str) -> Order | None:
        order = self.find_by_id(order_id)
        if not order:
            return None
        
        if status not in ["processing", "shipped", "delivered", "cancelled"]:
            raise ValueError(f"Invalid status: {status}. Must be one of processing, shipped, delivered, cancelled.")
        
        order.status = status
        with open(self._filepath, "w") as f:
            json.dump([asdict(order) for order in self._orders], f, indent=2)
        return order
    
    def update_quantity(self, order_id: str, quantity: int) -> Order | None:
        order = self.find_by_id(order_id)
        if not order:
            return None
        order.quantity = quantity
        self._save()
        return order
    
    def delete_order(self, order_id: str) -> bool:
        order = self.find_by_id(order_id)
        if not order:
            return False
       
        self._orders.remove(order)
        with open(self._filepath, "w") as f:
            json.dump([asdict(order) for order in self._orders], f, indent=2)
        return True
