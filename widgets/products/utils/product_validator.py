class ProductValidator:
    """Validates product data before database operations"""

    def __init__(self, translator):
        self.translator = translator

    def validate_product(self, data):
        """Validate product data

        Returns:
            tuple: (is_valid, error_message)
        """
        errors = []

        # Required fields check
        if 'product_name' not in data or not data['product_name']:
            errors.append(self.translator.t('product_name_required'))

        # Numeric validation
        if 'quantity' in data:
            try:
                qty = int(data['quantity'])
                if qty < 0:
                    errors.append(self.translator.t('quantity_positive'))
            except ValueError:
                errors.append(self.translator.t('quantity_invalid'))

        if 'price' in data:
            try:
                price = float(data['price'])
                if price < 0:
                    errors.append(self.translator.t('price_positive'))
            except ValueError:
                errors.append(self.translator.t('price_invalid'))

        # Return validation result
        return (len(errors) == 0, "\n".join(errors))

    def sanitize_product_data(self, data):
        """Sanitize product data to ensure valid types and defaults

        Returns:
            dict: Sanitized data
        """
        sanitized = {}

        # Set default values for missing fields
        if 'category' not in data or not data['category']:
            sanitized['category'] = "3"  # Default category
        else:
            sanitized['category'] = data['category']

        if 'car_name' not in data or not data['car_name']:
            sanitized['car_name'] = "-"
        else:
            sanitized['car_name'] = data['car_name']

        if 'model' not in data or not data['model']:
            sanitized['model'] = "-"
        else:
            sanitized['model'] = data['model']

        # Product name is required
        sanitized['product_name'] = data.get('product_name', '')

        # Convert numeric values
        try:
            sanitized['quantity'] = int(data.get('quantity', 0))
        except ValueError:
            sanitized['quantity'] = 0

        try:
            sanitized['price'] = float(data.get('price', 0.0))
        except ValueError:
            sanitized['price'] = 0.0

        return sanitized