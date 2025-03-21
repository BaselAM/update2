class ProductManager:
    """Manages the product data and operations"""

    def __init__(self, db):
        self.db = db
        self.all_products = []

    def set_products(self, products):
        """Set the current product list"""
        self.all_products = products

    def get_products(self):
        """Get the current product list"""
        return self.all_products

    def update_product_in_memory(self, product_id, field, value, column_index=None):
        """Update a product in the in-memory list"""
        for i, prod in enumerate(self.all_products):
            if prod[0] == product_id:
                prod_list = list(prod)

                # Handle special data types
                if field == 'quantity' or column_index == 5:
                    prod_list[5] = int(value)
                elif field == 'price' or column_index == 6:
                    prod_list[6] = float(value)
                elif column_index is not None:
                    prod_list[column_index] = value
                else:
                    # Map field name to index if column_index not provided
                    field_map = {
                        'category': 1,
                        'car_name': 2,
                        'model': 3,
                        'product_name': 4,
                        'quantity': 5,
                        'price': 6
                    }
                    if field in field_map:
                        prod_list[field_map[field]] = value

                self.all_products[i] = tuple(prod_list)
                return True

        return False

    def remove_products_by_ids(self, product_ids):
        """Remove products with the given IDs from the in-memory list"""
        if not product_ids:
            return 0

        original_count = len(self.all_products)
        self.all_products = [p for p in self.all_products if p[0] not in product_ids]
        return original_count - len(self.all_products)

    def clear(self):
        """Clear all products"""
        self.all_products = []