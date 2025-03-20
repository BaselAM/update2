from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QPushButton, QDialogButtonBox, QLabel, QFrame,
                             QHBoxLayout, QDoubleSpinBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from themes import get_color


class FilterDialog(QDialog):
    """Dialog for filtering products by various criteria"""

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.setWindowTitle(self.translator.t('filter_title'))
        self.setWindowIcon(QIcon("resources/filter_icon.png"))
        self.setMinimumWidth(350)

        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QFrame()
        header_layout = QHBoxLayout(header)
        icon = QLabel()
        icon.setPixmap(QIcon("resources/filter_icon.png").pixmap(32, 32))
        header_layout.addWidget(icon)
        title = QLabel(f"<h3>{self.translator.t('filter_title')}</h3>")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addWidget(header)

        # Form layout for filter inputs
        form = QFormLayout()
        form.setSpacing(15)
        form.setContentsMargins(10, 10, 10, 10)

        # Category filter
        self.category_input = QLineEdit()
        form.addRow(self.translator.t('category'), self.category_input)

        # Name filter
        self.name_input = QLineEdit()
        form.addRow(self.translator.t('product_name'), self.name_input)

        # Price range
        price_layout = QHBoxLayout()
        self.min_price = QDoubleSpinBox()
        self.min_price.setRange(0, 99999)
        self.min_price.setPrefix(self.translator.t('min') + ": ")

        self.max_price = QDoubleSpinBox()
        self.max_price.setRange(0, 99999)
        self.max_price.setPrefix(self.translator.t('max') + ": ")
        self.max_price.setValue(99999)

        price_layout.addWidget(self.min_price)
        price_layout.addWidget(self.max_price)
        form.addRow(self.translator.t('price_range'), price_layout)

        layout.addLayout(form)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        reset_btn = QPushButton(self.translator.t('reset_filters'))
        reset_btn.clicked.connect(self.reset_filters)
        button_box.addButton(reset_btn, QDialogButtonBox.ResetRole)

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
            QLineEdit, QDoubleSpinBox {{
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

    def reset_filters(self):
        """Clear all filter inputs"""
        self.category_input.clear()
        self.name_input.clear()
        self.min_price.setValue(0)
        self.max_price.setValue(99999)

    def get_filters(self):
        """Get the current filter values

        Returns:
            dict: Filter parameters
        """
        filters = {
            "category": self.category_input.text().strip(),
            "name": self.name_input.text().strip(),
            "min_price": self.min_price.value() if self.min_price.value() > 0 else None,
            "max_price": self.max_price.value() if self.max_price.value() < 99999 else None
        }
        return filters