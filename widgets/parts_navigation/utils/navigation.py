class NavigationState:
    """
    Manages the navigation state for the parts selection process.
    Keeps track of what's selected at each step.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset all navigation state"""
        self.car = {}
        self.product = {}
        self.details = {}

    @property
    def has_car(self):
        """Check if a car has been selected"""
        return bool(self.car)

    @property
    def has_product(self):
        """Check if a product has been selected"""
        return bool(self.product)

    @property
    def has_details(self):
        """Check if details have been selected"""
        return bool(self.details)

    @property
    def is_complete(self):
        """Check if all steps are complete"""
        return self.has_car and self.has_product and self.has_details