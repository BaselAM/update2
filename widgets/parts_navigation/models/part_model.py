class PartModel:
    """
    Data model for parts in the navigation system.
    Handles data validation and formatting.
    """

    def __init__(self, part_data=None):
        self.data = part_data or {}

    @property
    def car_make(self):
        """Get the car make"""
        return self.data.get('car_make', '')

    @property
    def car_model(self):
        """Get the car model"""
        return self.data.get('car_model', '')

    @property
    def year(self):
        """Get the car year"""
        return self.data.get('year', '')

    @property
    def part_name(self):
        """Get the part name"""
        return self.data.get('part_name', '')

    @property
    def manufacturer(self):
        """Get the part manufacturer"""
        return self.data.get('manufacturer', '')

    @property
    def price(self):
        """Get the part price"""
        return self.data.get('price', 0.0)

    @property
    def quantity(self):
        """Get the part quantity"""
        return self.data.get('quantity', 0)

    @property
    def image_path(self):
        """Get the part image path"""
        return self.data.get('image_path', '')

    def to_dict(self):
        """Convert model to dictionary"""
        return self.data.copy()

    @classmethod
    def from_dict(cls, data):
        """Create model from dictionary"""
        return cls(data)