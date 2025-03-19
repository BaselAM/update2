from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFormLayout, QComboBox, QLineEdit, QPushButton)
from PyQt5.QtCore import Qt, pyqtSignal
from themes import get_color


class DetailsWidget(QWidget):
    """
    Third step in the parts navigation - selecting additional details/specifications
    for the chosen product
    """
    details_selected = pyqtSignal(dict)

    def __init__(self, translator, parts_db):
        super().__init__()
        self.translator = translator
        self.parts_db = parts_db
        self.product_data = None
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        """Initialize and arrange UI elements"""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(15)

        # Product info at top
        self.product_info = QLabel("")
        self.product_info.setAlignment(Qt.AlignCenter)
        self.product_info.setObjectName("productInfoLabel")
        self.main_layout.addWidget(self.product_info)

        # Title
        self.title = QLabel(self.translator.t('select_details'))
        self.title.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.title)

        # Form for selecting details
        self.form_container = QWidget()
        self.form_layout = QFormLayout(self.form_container)
        self.form_layout.setContentsMargins(20, 10, 20, 10)
        self.form_layout.setSpacing(15)

        # Manufacturer selection
        self.manufacturer_label = QLabel(self.translator.t('manufacturer'))
        self.manufacturer_combo = QComboBox()
        self.form_layout.addRow(self.manufacturer_label, self.manufacturer_combo)

        # Material selection
        self.material_label = QLabel(self.translator.t('material'))
        self.material_combo = QComboBox()
        self.form_layout.addRow(self.material_label, self.material_combo)

        # Quality selection
        self.quality_label = QLabel(self.translator.t('quality'))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems([
            self.translator.t('quality_standard'),
            self.translator.t('quality_premium'),
            self.translator.t('quality_oem')
        ])
        self.form_layout.addRow(self.quality_label, self.quality_combo)

        # Special comments
        self.comments_label = QLabel(self.translator.t('comments'))
        self.comments_input = QLineEdit()
        self.comments_input.setPlaceholderText(self.translator.t('comments_placeholder'))
        self.form_layout.addRow(self.comments_label, self.comments_input)

        self.main_layout.addWidget(self.form_container)

        # Continue button
        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch(1)

        self.continue_button = QPushButton(self.translator.t('continue_button'))
        self.continue_button.setMinimumWidth(150)
        self.continue_button.clicked.connect(self.on_continue_clicked)

        self.button_layout.addWidget(self.continue_button)
        self.button_layout.addStretch(1)

        self.main_layout.addLayout(self.button_layout)

        # Help text at bottom
        self.help_text = QLabel(self.translator.t('select_details_help'))
        self.help_text.setAlignment(Qt.AlignCenter)
        self.help_text.setWordWrap(True)
        self.main_layout.addWidget(self.help_text)

    def set_product(self, product_data):
        """Set the product and load appropriate details options"""
        self.product_data = product_data
        self.product_info.setText(f"{product_data['name']} - {product_data['category']}")

        # Load manufacturers for this product
        self.load_manufacturers()

        # Load materials for this product
        self.load_materials()

    def load_manufacturers(self):
        """Load manufacturers for the selected product"""
        try:
            self.manufacturer_combo.clear()

            # Get manufacturers from database
            manufacturers = self.parts_db.get_manufacturers(
                self.product_data['category']
            )

            self.manufacturer_combo.addItems(manufacturers)

        except Exception as e:
            print(f"Error loading manufacturers: {str(e)}")
            # Add default items if database call fails
            self.manufacturer_combo.addItems(["OEM", "Aftermarket", "Generic"])

    def load_materials(self):
        """Load materials for the selected product"""
        try:
            self.material_combo.clear()

            # Get materials from database
            materials = self.parts_db.get_materials(
                self.product_data['category']
            )

            self.material_combo.addItems(materials)

        except Exception as e:
            print(f"Error loading materials: {str(e)}")
            # Add default items if database call fails
            self.material_combo.addItems(["Metal", "Plastic", "Rubber", "Composite"])

    def on_continue_clicked(self):
        """Handle click on continue button"""
        # Gather selected details
        details = {
            'manufacturer': self.manufacturer_combo.currentText(),
            'material': self.material_combo.currentText(),
            'quality': self.quality_combo.currentText(),
            'comments': self.comments_input.text()
        }

        # Emit signal with selected details
        self.details_selected.emit(details)

    def update_translations(self):
        """Update all translatable text"""
        self.title.setText(self.translator.t('select_details'))
        self.manufacturer_label.setText(self.translator.t('manufacturer'))
        self.material_label.setText(self.translator.t('material'))
        self.quality_label.setText(self.translator.t('quality'))
        self.comments_label.setText(self.translator.t('comments'))
        self.comments_input.setPlaceholderText(self.translator.t('comments_placeholder'))
        self.continue_button.setText(self.translator.t('continue_button'))
        self.help_text.setText(self.translator.t('select_details_help'))

        # Update quality combo items
        self.quality_combo.clear()
        self.quality_combo.addItems([
            self.translator.t('quality_standard'),
            self.translator.t('quality_premium'),
            self.translator.t('quality_oem')
        ])

        # Refresh product info if a product is selected
        if self.product_data:
            self.product_info.setText(
                f"{self.product_data['name']} - {self.product_data['category']}")

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

            QComboBox {{
                background-color: {card_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 5px;
                padding: 8px;
                min-width: 200px;
                font-size: 14px;
            }}

            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}

            QComboBox:hover {{
                border: 1px solid {highlight};
            }}

            QPushButton {{
                background-color: {highlight};
                color: {get_color('highlight_text')};
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 15px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: {get_color('button_hover')};
            }}

            #productInfoLabel {{
                font-size: 16px;
                font-weight: bold;
                color: {highlight};
                margin-bottom: 5px;
            }}
        """)

        # Title style
        self.title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            color: {text_color};
        """)

        # Form container style
        self.form_container.setStyleSheet(f"""
            background-color: {card_bg};
            border-radius: 10px;
            border: 1px solid {border_color};
        """)

        # Help text style
        self.help_text.setStyleSheet(f"""
            color: {get_color('secondary_text')};
            font-size: 13px;
            font-style: italic;
            margin-top: 5px;
        """)