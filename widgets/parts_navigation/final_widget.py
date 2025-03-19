from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QGridLayout, QPushButton, QFrame, QSpacerItem,
                             QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from themes import get_color
from pathlib import Path


class FinalWidget(QWidget):
    """
    Final step in the parts navigation - showing complete part details
    and allowing purchase or further actions
    """
    back_requested = pyqtSignal()

    def __init__(self, translator, parts_db):
        super().__init__()
        self.translator = translator
        self.parts_db = parts_db
        self.part_data = None
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        """Initialize and arrange UI elements"""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(15)

        # Title
        self.title = QLabel(self.translator.t('part_details'))
        self.title.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.title)

        # Part details container
        self.details_container = QFrame()
        self.details_container.setObjectName("detailsContainer")

        details_layout = QHBoxLayout(self.details_container)
        details_layout.setContentsMargins(20, 20, 20, 20)
        details_layout.setSpacing(20)

        # Left side - Image
        self.image_container = QFrame()
        self.image_container.setObjectName("imageContainer")
        self.image_container.setMinimumSize(300, 300)
        self.image_container.setMaximumSize(300, 300)

        image_layout = QVBoxLayout(self.image_container)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setObjectName("partImage")
        self.image_label.setScaledContents(True)
        self.image_label.setMinimumSize(250, 250)
        self.image_label.setMaximumSize(250, 250)

        # Default image
        default_img = QPixmap("resources/default_part.png")
        if not default_img.isNull():
            self.image_label.setPixmap(default_img)
        else:
            self.image_label.setText(self.translator.t('no_image'))

        image_layout.addWidget(self.image_label, 0, Qt.AlignCenter)
        details_layout.addWidget(self.image_container)

        # Right side - Details grid
        self.info_container = QFrame()
        self.info_container.setObjectName("infoContainer")

        info_layout = QGridLayout(self.info_container)
        info_layout.setVerticalSpacing(15)
        info_layout.setHorizontalSpacing(10)

        # Row 0 - Part name
        self.part_name_label = QLabel(self.translator.t('part_name'))
        self.part_name_label.setObjectName("detailLabel")
        self.part_name_value = QLabel("-")
        self.part_name_value.setObjectName("detailValue")

        info_layout.addWidget(self.part_name_label, 0, 0)
        info_layout.addWidget(self.part_name_value, 0, 1)

        # Row 1 - Car info
        self.car_label = QLabel(self.translator.t('car_info'))
        self.car_label.setObjectName("detailLabel")
        self.car_value = QLabel("-")
        self.car_value.setObjectName("detailValue")

        info_layout.addWidget(self.car_label, 1, 0)
        info_layout.addWidget(self.car_value, 1, 1)

        # Row 2 - Manufacturer
        self.manufacturer_label = QLabel(self.translator.t('manufacturer'))
        self.manufacturer_label.setObjectName("detailLabel")
        self.manufacturer_value = QLabel("-")
        self.manufacturer_value.setObjectName("detailValue")

        info_layout.addWidget(self.manufacturer_label, 2, 0)
        info_layout.addWidget(self.manufacturer_value, 2, 1)

        # Row 3 - Material
        self.material_label = QLabel(self.translator.t('material'))
        self.material_label.setObjectName("detailLabel")
        self.material_value = QLabel("-")
        self.material_value.setObjectName("detailValue")

        info_layout.addWidget(self.material_label, 3, 0)
        info_layout.addWidget(self.material_value, 3, 1)

        # Row 4 - Quality
        self.quality_label = QLabel(self.translator.t('quality'))
        self.quality_label.setObjectName("detailLabel")
        self.quality_value = QLabel("-")
        self.quality_value.setObjectName("detailValue")

        info_layout.addWidget(self.quality_label, 4, 0)
        info_layout.addWidget(self.quality_value, 4, 1)

        # Row 5 - Price
        self.price_label = QLabel(self.translator.t('price'))
        self.price_label.setObjectName("detailLabel")
        self.price_value = QLabel("-")
        self.price_value.setObjectName("priceValue")

        info_layout.addWidget(self.price_label, 5, 0)
        info_layout.addWidget(self.price_value, 5, 1)

        # Row 6 - Quantity
        self.quantity_label = QLabel(self.translator.t('quantity'))
        self.quantity_label.setObjectName("detailLabel")
        self.quantity_value = QLabel("-")
        self.quantity_value.setObjectName("detailValue")

        info_layout.addWidget(self.quantity_label, 6, 0)
        info_layout.addWidget(self.quantity_value, 6, 1)

        # Row 7 - Comments
        self.comments_label = QLabel(self.translator.t('comments'))
        self.comments_label.setObjectName("detailLabel")
        self.comments_value = QLabel("-")
        self.comments_value.setObjectName("detailValue")
        self.comments_value.setWordWrap(True)

        info_layout.addWidget(self.comments_label, 7, 0, Qt.AlignTop)
        info_layout.addWidget(self.comments_value, 7, 1)

        # Set column stretch
        info_layout.setColumnStretch(0, 1)
        info_layout.setColumnStretch(1, 3)

        details_layout.addWidget(self.info_container, 1)  # Give more space to info

        self.main_layout.addWidget(self.details_container, 1)  # Takes most space

        # Action buttons
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setContentsMargins(0, 10, 0, 0)

        self.back_button = QPushButton(self.translator.t('back_button'))
        self.back_button.setObjectName("secondaryButton")
        self.back_button.clicked.connect(self.back_requested)

        self.add_to_cart_button = QPushButton(self.translator.t('add_to_cart'))
        self.add_to_cart_button.setObjectName("primaryButton")
        self.add_to_cart_button.clicked.connect(self.on_add_to_cart)

        self.print_button = QPushButton(self.translator.t('print_details'))
        self.print_button.setObjectName("secondaryButton")
        self.print_button.clicked.connect(self.on_print)

        # Add buttons with spacers
        self.buttons_layout.addWidget(self.back_button)
        self.buttons_layout.addStretch(1)
        self.buttons_layout.addWidget(self.print_button)
        self.buttons_layout.addWidget(self.add_to_cart_button)

        self.main_layout.addLayout(self.buttons_layout)

    def set_complete_data(self, part_data):
        """Set all the part data and update the display"""
        self.part_data = part_data

        # Update part details
        self.part_name_value.setText(part_data.get('name', '-'))
        self.car_value.setText(
            f"{part_data.get('make', '-')} {part_data.get('model', '-')} ({part_data.get('year', '-')})")
        self.manufacturer_value.setText(part_data.get('manufacturer', '-'))
        self.material_value.setText(part_data.get('material', '-'))
        self.quality_value.setText(part_data.get('quality', '-'))

        # Format price
        price = part_data.get('price', 0)
        currency = self.translator.t('currency_symbol')
        self.price_value.setText(f"{currency} {price:.2f}")

        # Set quantity
        self.quantity_value.setText(str(part_data.get('quantity', 0)))

        # Set comments
        self.comments_value.setText(part_data.get('comments', '-'))

        # Try to load part image
        self.load_part_image(part_data)

    def load_part_image(self, part_data):
        """Load the part image from the given data"""
        try:
            # First, try to load from a direct image path if available
            image_path = part_data.get('image_path', '')

            if image_path and Path(image_path).exists():
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    self.image_label.setPixmap(pixmap)
                    return

            # If no direct path or it failed, try to load from product ID
            product_id = part_data.get('id')
            if product_id:
                # Try to get image from database
                image_data = self.parts_db.get_product_image(product_id)
                if image_data:
                    pixmap = QPixmap()
                    pixmap.loadFromData(image_data)
                    if not pixmap.isNull():
                        self.image_label.setPixmap(pixmap)
                        return

            # If all attempts failed, load default image
            default_img = QPixmap("resources/default_part.png")
            if not default_img.isNull():
                self.image_label.setPixmap(default_img)
            else:
                self.image_label.setText(self.translator.t('no_image'))

        except Exception as e:
            print(f"Error loading part image: {str(e)}")
            self.image_label.setText(self.translator.t('image_error'))

    def on_add_to_cart(self):
        """Handle add to cart button click"""
        if self.part_data:
            print(f"Adding part to cart: {self.part_data.get('name')}")
            # In a real implementation, this would call a method to add to cart
            # For now, just show a message
            try:
                QMessageBox.information(
                    self,
                    self.translator.t('success'),
                    self.translator.t('added_to_cart')
                )
            except NameError:
                # QMessageBox not imported, so just print
                print(f"Success: {self.translator.t('added_to_cart')}")

    def on_print(self):
        """Handle print button click"""
        if self.part_data:
            print(f"Printing details for part: {self.part_data.get('name')}")
            # In a real implementation, this would open a print dialog
            # For now, just show a message
            try:
                QMessageBox.information(
                    self,
                    self.translator.t('print'),
                    self.translator.t('print_started')
                )
            except NameError:
                # QMessageBox not imported, so just print
                print(f"Print: {self.translator.t('print_started')}")

    def update_translations(self):
        """Update all translatable text"""
        self.title.setText(self.translator.t('part_details'))
        self.part_name_label.setText(self.translator.t('part_name'))
        self.car_label.setText(self.translator.t('car_info'))
        self.manufacturer_label.setText(self.translator.t('manufacturer'))
        self.material_label.setText(self.translator.t('material'))
        self.quality_label.setText(self.translator.t('quality'))
        self.price_label.setText(self.translator.t('price'))
        self.quantity_label.setText(self.translator.t('quantity'))
        self.comments_label.setText(self.translator.t('comments'))

        self.back_button.setText(self.translator.t('back_button'))
        self.add_to_cart_button.setText(self.translator.t('add_to_cart'))
        self.print_button.setText(self.translator.t('print_details'))

        # Refresh part data if available
        if self.part_data:
            self.set_complete_data(self.part_data)

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

            #detailsContainer {{
                background-color: {card_bg};
                border-radius: 10px;
                border: 1px solid {border_color};
            }}

            #imageContainer {{
                background-color: {bg_color};
                border-radius: 10px;
                border: 1px solid {border_color};
            }}

            #partImage {{
                background-color: white;
                border-radius: 5px;
                border: 1px solid {border_color};
            }}

            #detailLabel {{
                font-weight: bold;
                color: {text_color};
            }}

            #detailValue {{
                color: {text_color};
            }}

            #priceValue {{
                color: {highlight};
                font-size: 16px;
                font-weight: bold;
            }}

            #primaryButton {{
                background-color: {highlight};
                color: {get_color('highlight_text')};
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 15px;
                font-weight: bold;
                min-width: 150px;
            }}

            #primaryButton:hover {{
                background-color: {get_color('button_hover')};
            }}

            #secondaryButton {{
                background-color: {get_color('button')};
                color: {text_color};
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 15px;
                min-width: 120px;
            }}

            #secondaryButton:hover {{
                background-color: {get_color('button_hover')};
            }}
        """)

        # Title style
        self.title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 10px;
            color: {text_color};
        """)