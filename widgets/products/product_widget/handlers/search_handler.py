class SearchHandler:
    """Handles product search functionality"""

    def __init__(self, translator):
        self.translator = translator

    def search_products(self, all_products, search_text):
        """
        Search products based on search text

        Args:
            all_products: List of all products
            search_text: Text to search for

        Returns:
            tuple: (filtered_products, message)
        """
        search_text = search_text.lower().strip()
        if not search_text:
            return all_products, None

        filtered_products = []
        for product in all_products:
            searchable_fields = [
                str(product[1] or ""),  # category
                str(product[2] or ""),  # car_name
                str(product[3] or ""),  # model
                str(product[4] or "")  # product_name
            ]
            searchable_text = " ".join(searchable_fields).lower()
            if search_text in searchable_text:
                filtered_products.append(product)

        if len(filtered_products) < len(all_products):
            message = self.translator.t('search_results').format(
                count=len(filtered_products),
                total=len(all_products)
            )
            return filtered_products, message

        return filtered_products, None