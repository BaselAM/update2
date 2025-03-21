class FilterHandler:
    """Handles product filtering functionality"""

    def __init__(self, translator):
        self.translator = translator
        self.last_filter_settings = {
            "category": "",
            "name": "",
            "car_name": "",
            "model": "",
            "min_price": None,
            "max_price": None,
            "stock_status": None
        }

    def get_last_filter_settings(self):
        """Get the last filter settings used"""
        return self.last_filter_settings.copy()

    def save_filter_settings(self, settings):
        """Save the current filter settings"""
        self.last_filter_settings = settings.copy()

    def reset_filters(self):
        """Reset filters to default values"""
        self.last_filter_settings = {
            "category": "",
            "name": "",
            "car_name": "",
            "model": "",
            "min_price": None,
            "max_price": None,
            "stock_status": None
        }

    def filter_products(self, all_products, filters):
        """
        Filter products based on criteria

        Args:
            all_products: List of all products
            filters: Dictionary of filter settings

        Returns:
            tuple: (filtered_products, message)
        """
        try:
            filtered = []
            for prod in all_products:
                category = prod[1] if prod[1] else ""
                name = prod[4] if prod[4] else ""
                car_name = prod[2] if prod[2] else ""
                model = prod[3] if prod[3] else ""
                price = float(prod[6]) if prod[6] else 0
                quantity = int(prod[5]) if prod[5] else 0

                # Check category
                if filters["category"] and filters[
                    "category"].lower() not in category.lower():
                    continue

                # Check name
                if filters["name"] and filters["name"].lower() not in name.lower():
                    continue

                # Check car name
                if filters["car_name"] and filters[
                    "car_name"].lower() not in car_name.lower():
                    continue

                # Check model
                if filters["model"] and filters["model"].lower() not in model.lower():
                    continue

                # Check price range
                if filters["min_price"] is not None and price < filters["min_price"]:
                    continue
                if filters["max_price"] is not None and price > filters["max_price"]:
                    continue

                # Check stock status
                if filters["stock_status"] == "in_stock" and quantity <= 0:
                    continue
                if filters["stock_status"] == "out_of_stock" and quantity > 0:
                    continue

                filtered.append(prod)

            message = self.translator.t('filter_results').format(
                count=len(filtered),
                total=len(all_products)
            )
            return filtered, message

        except Exception as e:
            print("Error filtering products:", e)
            import traceback
            print(traceback.format_exc())
            return all_products, self.translator.t('filter_error')