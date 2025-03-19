from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QListWidget, QListWidgetItem, QLineEdit, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from themes import get_color


class ProductsWidget(QWidget):
    """
    Second step in the parts navigation - selecting a product for the chosen car
    """
    product_selected = pyqtSignal(dict)

    def __init__(self, translator, parts_db):
        super().__init__()
        self.translator = translator
        self.parts_db = parts_db
        self.car_filter = None
        self.all_products = []
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        """Initialize and arrange UI elements"""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(15)

        # Car info at top
        self.car_info = QLabel("")
        self.car_info.setAlignment(Qt.AlignCenter)
        self.car_info.setObjectName("carInfoLabel")
        self.main_layout.addWidget(self.car_info)

        # Title
        self.title = QLabel(self.translator.t('select_product'))
        self.title.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.title)

        # Search box
        self.search_layout = QHBoxLayout()
        self.search_label = QLabel(self.translator.t('search_products'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            self.translator.t('search_products_placeholder'))
        self.search_input.textChanged.connect(self.filter_products)

        self.search_layout.addWidget(self.search_label)
        self.search_layout.addWidget(self.search_input, 1)
        self.main_layout.addLayout(self.search_layout)

        # Products grid for a more visual representation
        self.products_container = QWidget()
        self.products_layout = QGridLayout(self.products_container)
        self.products_layout.setContentsMargins(0, 0, 0, 0)
        self.products_layout.setSpacing(10)
        self.main_layout.addWidget(self.products_container, 1)

        # Help text at bottom
        self.help_text = QLabel(self.translator.t('select_product_help'))
        self.help_text.setAlignment(Qt.AlignCenter)
        self.help_text.setWordWrap(True)
        self.main_layout.addWidget(self.help_text)

    def set_car_filter(self, car_data):
        """Set the car filter and load products for this car"""
        self.car_filter = car_data
        self.car_info.setText(
            f"{car_data['make']} {car_data['model']} ({car_data['year']})"
        )
        self.load_products()

    def load_products(self):
        """Load products from database based on selected car"""
        try:
            if not self.car_filter:
                return

            # Clear existing products
            self.clear_products_grid()

            # Get products for this car from database
            products = self.parts_db.get_products_for_car(
                self.car_filter['make'],
                self.car_filter['model'],
                self.car_filter['year']
            )

            self.all_products = products

            # Populate the grid with product cards
            self.populate_products_grid(products)

        except Exception as e:
            print(f"Error loading products: {str(e)}")

    def clear_products_grid(self):
        """Clear all items from the products grid"""
        # Remove all widgets from grid
        for i in reversed(range(self.products_layout.count())):
            item = self.products_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

    def populate_products_grid(self, products):
        """Populate the grid with product cards"""
        # Calculate grid dimensions
        cols = 3  # Number of columns

        for i, product in enumerate(products):
            # Create product card
            card = self.create_product_card(product)

            # Add to grid
            row = i // cols
            col = i % cols
            self.products_layout.addWidget(card, row, col)

    def create_product_card(self, product):
        """Create a product card widget"""
        card = QWidget()
        card.setObjectName("productCard")
        card.setCursor(Qt.PointingHandCursor)

        # Store product data
        card.setProperty("product_data", product)

        # Card layout
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)

        # Product name
        name_label = QLabel(product['name'])
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setObjectName("productName")

        # Product category
        category_label = QLabel(product['category'])
        category_label.setAlignment(Qt.AlignCenter)
        category_label.setObjectName("productCategory")

        # Add to layout
        layout.addWidget(name_label)
        layout.addWidget(category_label)

        # Connect click event
        card.mousePressEvent = lambda event, p=product: self.on_product_clicked(p)

        return card

    def on_product_clicked(self, product):
        """Handle click on a product card"""
        self.product_selected.emit(product)

    def filter_products(self, search_text):
        """Filter products based on search text"""
        search_text = search_text.lower()

        # Clear existing products
        self.clear_products_grid()

        # Filter products
        filtered_products = []
        for product in self.all_products:
            name = product['name'].lower()
            category = product['category'].lower()

            if search_text in name or search_text in category:
                filtered_products.append(product)

        # Populate grid with filtered products
        self.populate_products_grid(filtered_products)

    def update_translations(self):
        """Update all translatable text"""
        self.title.setText(self.translator.t('select_product'))
        self.search_label.setText(self.translator.t('search_products'))
        self.search_input.setPlaceholderText(
            self.translator.t('search_products_placeholder'))
        self.help_text.setText(self.translator.t('select_product_help'))

        # Refresh products to update any text in the cards
        if self.car_filter:
            self.load_products()

    def apply_theme(self):
        """Apply current theme"""
        bg_color = get_color('background')
        card_bg = get_color('card_bg')
        text_color = get_color('text')
        border_color = get_color('border')
        highlight = get_color('highlight')

        # Set styles
        self.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-size: 14px;
            }}

            QLineEdit {{
                background-color: {card_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }}

            #carInfoLabel {{
                font-size: 16px;
                font-weight: bold;
                color: {highlight};
                margin-bottom: 5px;
            }}

            #productCard {{
                background-color: {card_bg};
                border: 1px solid {border_color};
                border-radius: 8px;
                min-height: 120px;
                min-width: 150px;
            }}

            #productCard:hover {{
                border: 2px solid {highlight};
                background-color: {get_color('button_hover')};
            }}

            #productName {{
                font-size: 15px;
                font-weight: bold;
                color: {text_color};
            }}

            #productCategory {{
                font-size: 13px;
                color: {get_color('secondary_text')};
                font-style: italic;
            }}
        """)

        # Title style
        self.title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            color: {text_color};
        """)

        # Help text style
        self.help_text.setStyleSheet(f"""
            color: {get_color('secondary_text')};
            font-size: 13px;
            font-style: italic;
            margin-top: 5px;
        """)