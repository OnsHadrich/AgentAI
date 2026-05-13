from repositories.product_repository import ProductRepository
from model.product_model import Product



class ProductTool:
    def __init__(self, product_repository: ProductRepository | None = None):
        self.product_repository = product_repository or ProductRepository()
        self.products: list[Product] = self.product_repository.get_all()

    def _reload(self):
        """Reload products from the repository after any stock update."""
        self.products = self.product_repository.get_all()

    def _availability(self, product: Product) -> str:
        return "in stock" if product.stock > 0 else "out of stock"

    def _list_products(self) -> str:
        """List all products with their details."""
        if not self.products:
            return "No products available."
        return "\n".join([
            f"{p.product_id}: {p.name} - ${p.price} ({self._availability(p)})"
            for p in self.products
        ])

    def _list_available_products(self) -> str:
        """List all products that are currently in stock."""
        available = [p for p in self.products if p.stock > 0]
        if not available:
            return "No products are currently in stock."
        return "\n".join([
            f"{p.product_id}: {p.name} - ${p.price}"
            for p in available
        ])

    def _get_product_details(self, product_id: str) -> str:
        """Get full details of a product by its product ID e.g. p1, p2."""
        for p in self.products:
            if p.product_id == product_id:
                return (
                    f"Product ID  : {p.product_id}\n"
                    f"Name        : {p.name}\n"
                    f"Category    : {p.category}\n"
                    f"Price       : ${p.price}\n"
                    f"Stock       : {p.stock} units\n"
                    f"Availability: {self._availability(p)}\n"
                    f"Description : {p.description}\n"
                    f"Warranty    : {p.warranty_years} year(s)"
                )
        return f"No product found with ID: {product_id}"

    def _check_product_availability(self, product_id: str) -> str:
        """Check if a specific product is available by its product ID."""
        for p in self.products:
            if p.product_id == product_id:
                return f"'{p.name}' is currently {self._availability(p)} ({p.stock} units)."
        return f"No product found with ID: {product_id}"

    def _get_product_price(self, product_id: str) -> str:
        """Get the price of a product by its product ID."""
        for p in self.products:
            if p.product_id == product_id:
                return f"The price of '{p.name}' is ${p.price}."
        return f"No product found with ID: {product_id}"

    def _search_products(self, keyword: str) -> str:
        """Search for products by a name keyword e.g. laptop, keyboard."""
        found = [p for p in self.products if keyword.lower() in p.name.lower()]
        if not found:
            return f"No products found matching '{keyword}'."
        return "\n".join([
            f"{p.product_id}: {p.name} - ${p.price} ({self._availability(p)})"
            for p in found
        ])
