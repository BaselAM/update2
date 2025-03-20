from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QFormLayout, QDoubleSpinBox, QSpinBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QColor, QFont

from themes import get_color
from widgets.products.dialogs.base_dialog import ElegantDialog


class AddProductDialog(ElegantDialog):
    """An elegant dialog for adding new products with improved validation and animation."""

    def __init__(self, translator, parent=None):
        super().__init__(translator, parent, title='product_details')
        self.setWindowTitle(self.translator.t('product_details'))
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self.product_data = {}
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Add a title label with larger font
        title_label = QLabel(self.translator.t('product_details'))
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Create a form layout for product inputs
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # Category
        category_label = QLabel(self.translator.t('category') + ":")
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText(self.translator.t('category_placeholder'))
        form_layout.addRow(category_label, self.category_input)

        # Car Name
        car_label = QLabel(self.translator.t('car') + ":")
        self.car_input = QLineEdit()
        self.car_input.setPlaceholderText(self.translator.t('car_placeholder'))
        form_layout.addRow(car_label, self.car_input)

        # Model
        model_label = QLabel(self.translator.t('model') + ":")
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText(self.translator.t('model_placeholder'))
        form_layout.addRow(model_label, self.model_input)

        # Product Name (Required)
        product_name_label = QLabel(self.translator.t('product_name') + " *:")
        product_name_label.setStyleSheet("font-weight: bold;")
        self.product_name_input = QLineEdit()
        self.product_name_input.setPlaceholderText(
            self.translator.t('product_name_placeholder'))
        form_layout.addRow(product_name_label, self.product_name_input)

        # Quantity
        quantity_label = QLabel(self.translator.t('quantity') + ":")
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(0, 9999)
        self.quantity_input.setValue(1)
        self.quantity_input.setButtonSymbols(QSpinBox.UpDownArrows)
        form_layout.addRow(quantity_label, self.quantity_input)

        # Price
        price_label = QLabel(self.translator.t('price') + ":")
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 9999.99)
        self.price_input.setPrefix("$ ")
        self.price_input.setDecimals(2)
        self.price_input.setButtonSymbols(QDoubleSpinBox.UpDownArrows)
        form_layout.addRow(price_label, self.price_input)

        # Required field note
        required_note = QLabel("* " + self.translator.t('required_field'))
        required_note.setStyleSheet("color: #888; font-style: italic; font-size: 12px;")
        required_note.setAlignment(Qt.AlignRight)
        form_layout.addRow("", required_note)

        main_layout.addLayout(form_layout)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Clear button
        self.clear_btn = QPushButton(self.translator.t('clear_all'))
        self.clear_btn.setIcon(QIcon("resources/clear_icon.png"))
        self.clear_btn.clicked.connect(self.clear_fields)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        button_layout.addWidget(self.clear_btn)

        # Spacer
        button_layout.addStretch()

        # Cancel button
        self.cancel_btn = QPushButton(self.translator.t('cancel'))
        self.cancel_btn.setIcon(QIcon("resources/cancel_icon.png"))
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        button_layout.addWidget(self.cancel_btn)

        # Save button
        self.save_btn = QPushButton(self.translator.t('save'))
        self.save_btn.setIcon(QIcon("resources/save_icon.png"))
        self.save_btn.clicked.connect(self.save_product)
        self.save_btn.setCursor(Qt.PointingHandCursor)

        # Make Save button stand out
        highlight_color = get_color('highlight')
        bg_color = get_color('background')
        button_style = f"""
            QPushButton {{
                background-color: {highlight_color};
                color: {bg_color};
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {QColor(highlight_color).lighter(110).name()};
            }}
            QPushButton:pressed {{
                background-color: {QColor(highlight_color).darker(110).name()};
            }}
        """
        self.save_btn.setStyleSheet(button_style)

        button_layout.addWidget(self.save_btn)

        main_layout.addLayout(button_layout)

    def clear_fields(self):
        """Clear all input fields."""
        self.category_input.clear()
        self.car_input.clear()
        self.model_input.clear()
        self.product_name_input.clear()
        self.quantity_input.setValue(1)
        self.price_input.setValue(0.00)

    def save_product(self):
        """Validate and save product data."""
        # Check required fields
        product_name = self.product_name_input.text().strip()
        if not product_name:
            # Highlight the required field in red
            self.product_name_input.setStyleSheet("border: 2px solid red;")
            # Show error message
            error_color = get_color('status_error_text') or "#C62828"
            error_label = QLabel(self.translator.t('name_required'))
            error_label.setStyleSheet(f"color: {error_color}; font-weight: bold;")
            layout = self.layout()
            layout.insertWidget(1, error_label)  # Insert after title
            # Remove the error after 3 seconds
            QTimer.singleShot(3000, lambda: error_label.setParent(None))
            return

        # Collect all data
        self.product_data = {
            "category": self.category_input.text().strip(),
            "car_name": self.car_input.text().strip(),
            "model": self.model_input.text().strip(),
            "product_name": product_name,
            "quantity": self.quantity_input.value(),
            "price": self.price_input.value()
        }

        self.accept()

    def get_data(self):
        """Return the product data."""
        return self.product_data