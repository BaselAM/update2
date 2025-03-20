from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QPushButton, QDialogButtonBox, QLabel, QFrame,
                             QHBoxLayout, QDoubleSpinBox, QSpinBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from themes import get_color


class AddProductDialog(QDialog):
    """Dialog for adding new products"""

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.setWindowTitle(self.translator.t('add_product'))
        self.setWindowIcon(QIcon("resources/add_icon.png"))
        self.setMinimumWidth(350)

        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QFrame()
        header_layout = QHBoxLayout(header)
        icon = QLabel()
        icon.setPixmap(QIcon("resources/add_icon.png").pixmap(32, 32))
        header_layout.addWidget(icon)
        title = QLabel(f"<h3>{self.translator.t('add_product')}</h3>")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addWidget(header)

        # Form layout for product inputs
        form = QFormLayout()
        form.setSpacing(15)
        form.setContentsMargins(10, 10, 10, 10)

        # Category input
        self.category_input = QLineEdit()
        form.addRow(self.translator.t('category') + ":", self.category_input)

        # Car name input
        self.car_input = QLineEdit()
        form.addRow(self.translator.t('car') + ":", self.car_input)

        # Model input
        self.model_input = QLineEdit()
        form.addRow(self.translator.t('model') + ":", self.model_input)

        # Product name input (required)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(self.translator.t('required'))
        form.addRow(self.translator.t('product_name') + ":", self.name_input)

        # Quantity input
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(0, 9999)
        self.quantity_input.setValue(0)
        form.addRow(self.translator.t('quantity') + ":", self.quantity_input)

        # Price input
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 99999.99)
        self.price_input.setValue(0)
        self.price_input.setDecimals(2)
        self.price_input.setSingleStep(0.01)
        form.addRow(self.translator.t('price') + ":", self.price_input)

        layout.addLayout(form)

        # Required fields note
        note = QLabel(f"<i>{self.translator.t('required_fields_note')}</i>")
        note.setAlignment(Qt.AlignRight)
        layout.addWidget(note)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def apply_theme(self):
        """Apply current theme colors"""
        bg_color = get_color('background')
        text_color = get_color('text')
        border_color = get_color('border')
        input_bg = get_color('input_bg')
        button_color = get_color('button')

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
            }}
            QLabel {{
                color: {text_color};
            }}
            QLineEdit, QDoubleSpinBox, QSpinBox {{
                background-color: {input_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 5px;
                min-height: 25px;
            }}
            QPushButton {{
                background-color: {button_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {get_color('button_hover')};
                border: 1px solid {get_color('highlight')};
            }}
        """)

    def validate_and_accept(self):
        """Validate inputs before accepting"""
        # Ensure product name is provided
        if not self.name_input.text().strip():
            self.name_input.setStyleSheet(f"""
                background-color: {get_color('error')};
                color: white;
            """)
            return

        # Validation passed
        self.accept()

    def get_data(self):
        """Get the product data

        Returns:
            dict: Product data
        """
        return {
            "category": self.category_input.text().strip(),
            "car_name": self.car_input.text().strip(),
            "model": self.model_input.text().strip(),
            "product_name": self.name_input.text().strip(),
            "quantity": self.quantity_input.value(),
            "price": self.price_input.value()
        }