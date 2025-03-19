from shared_imports import *
from themes import *
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QScrollArea, QDialogButtonBox,
    QWidget, QGraphicsDropShadowEffect  # Move the effect here
)
from PyQt5.QtGui import QColor, QPixmap

from themes import get_color
from shared import SCRIPT_DIR

class ItemDetailsDialog(QDialog):
    def __init__(self, item_data, translator, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.translator = translator
        self.setWindowTitle("Item Details")  # You can translate this too
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        # Assuming item_data is a dict with your fields
        for key, value in self.item_data.items():
            layout.addWidget(QLabel(f"{key}: {value}"))
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
        btn_box.accepted.connect(self.accept)
        layout.addWidget(btn_box)


class AddProductDialog(QDialog):
    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator

        # Apply dialog theme
        apply_dialog_theme(
            self,
            title=self.translator.t('add_product'),
            icon_path="resources/add_icon.png",
            min_width=500
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Create header with icon
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 10)

        icon = QLabel()
        icon.setPixmap(QIcon("resources/add_icon.png").pixmap(32, 32))
        header_layout.addWidget(icon)

        title = QLabel(f"<h2>{self.translator.t('add_product')}</h2>")
        title.setStyleSheet(f"color: {get_color('text')}; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addWidget(header)

        # Create form for product details
        form_container = QGroupBox(self.translator.t('product_details'))
        form_layout = QFormLayout(form_container)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(15, 20, 15, 15)

        # Product name (required)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(self.translator.t('product_name_placeholder'))
        name_label = QLabel(f"{self.translator.t('product_name')}* :")
        name_label.setStyleSheet("font-weight: bold;")
        form_layout.addRow(name_label, self.name_edit)

        # Category
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText(self.translator.t('category_placeholder'))
        form_layout.addRow(QLabel(f"{self.translator.t('category')}:"),
                           self.category_edit)

        # Car name
        self.car_edit = QLineEdit()
        self.car_edit.setPlaceholderText(self.translator.t('car_placeholder'))
        form_layout.addRow(QLabel(f"{self.translator.t('car')}:"), self.car_edit)

        # Model
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText(self.translator.t('model_placeholder'))
        form_layout.addRow(QLabel(f"{self.translator.t('model')}:"), self.model_edit)

        # Quantity
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(0, 9999)
        self.quantity_spin.setValue(1)
        form_layout.addRow(QLabel(f"{self.translator.t('quantity')}:"),
                           self.quantity_spin)

        # Price
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 999999.99)
        self.price_spin.setDecimals(2)
        self.price_spin.setSuffix(" ₪")  # Change to your currency
        self.price_spin.setValue(0.00)
        form_layout.addRow(QLabel(f"{self.translator.t('price')}:"), self.price_spin)

        layout.addWidget(form_container)

        # Add note about required fields
        note = QLabel(f"* {self.translator.t('required_field')}")
        note.setStyleSheet(
            f"color: {get_color('highlight')}; font-style: italic; font-size: 12px;")
        layout.addWidget(note)

        # Buttons
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)

        clear_btn = QPushButton(self.translator.t('clear_all'))
        clear_btn.setIcon(QIcon("resources/clear_icon.png"))
        clear_btn.clicked.connect(self.clear_fields)

        save_btn = QPushButton(self.translator.t('save'))
        save_btn.setObjectName("primaryButton")  # For special styling
        save_btn.setIcon(QIcon("resources/save_icon.png"))
        save_btn.clicked.connect(self.validate_and_accept)

        cancel_btn = QPushButton(self.translator.t('cancel'))
        cancel_btn.setIcon(QIcon("resources/cancel_icon.png"))
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(clear_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)

        layout.addWidget(button_container)

        # Set focus to name field
        self.name_edit.setFocus()

    def clear_fields(self):
        """Clear all input fields"""
        self.name_edit.clear()
        self.category_edit.clear()
        self.car_edit.clear()
        self.model_edit.clear()
        self.quantity_spin.setValue(1)
        self.price_spin.setValue(0.00)
        self.name_edit.setFocus()

    def validate_and_accept(self):
        """Validate inputs before accepting"""
        if not self.name_edit.text().strip():
            self.show_error(self.translator.t('name_required'))
            self.name_edit.setFocus()
            return

        self.accept()

    def show_error(self, message):
        """Show styled error message"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(self.translator.t('validation_error'))
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)

        # Apply theme to message box
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {get_color('background')};
                color: {get_color('text')};
            }}
            QLabel {{
                color: {get_color('text')};
                min-width: 250px;
            }}
            QPushButton {{
                background-color: {get_color('button')};
                color: {get_color('text')};
                border: 1px solid {get_color('border')};
                border-radius: 4px;
                padding: 6px 12px;
            }}
        """)

        msg.exec_()

    def get_data(self):
        """Return the product data"""
        return {
            'product_name': self.name_edit.text().strip(),
            'category': self.category_edit.text().strip() or None,
            'car_name': self.car_edit.text().strip() or None,
            'model': self.model_edit.text().strip() or None,
            'quantity': self.quantity_spin.value(),
            'price': self.price_spin.value()
        }


    def closeEvent(self, event):
        """Cleanup resources"""
        self.deleteLater()
        super().closeEvent(event)


class FilterDialog(QDialog):
    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator

        # Set up the dialog with theme
        apply_dialog_theme(
            self,
            title=self.translator.t('filter_title'),
            icon_path="resources/filter_icon.png"
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Create header with icon
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 10)

        icon = QLabel()
        icon.setPixmap(QIcon("resources/filter_icon.png").pixmap(32, 32))
        header_layout.addWidget(icon)

        title = QLabel(f"<h2>{self.translator.t('filter_title')}</h2>")
        title.setStyleSheet(f"color: {get_color('text')}; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addWidget(header)

        # Create form layout for filter fields
        form_container = QGroupBox(self.translator.t('filter_criteria'))
        form_layout = QFormLayout(form_container)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(15, 20, 15, 15)

        # Category filter
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText(self.translator.t('category_placeholder'))
        form_layout.addRow(QLabel(f"{self.translator.t('category')}:"),
                           self.category_edit)

        # Name filter
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(self.translator.t('name_placeholder'))
        form_layout.addRow(QLabel(f"{self.translator.t('product_name')}:"),
                           self.name_edit)

        # Price range
        price_widget = QWidget()
        price_layout = QHBoxLayout(price_widget)
        price_layout.setContentsMargins(0, 0, 0, 0)

        self.min_price = QDoubleSpinBox()
        self.min_price.setRange(0, 999999)
        self.min_price.setDecimals(2)
        self.min_price.setSuffix(" ₪")  # You can change to your currency
        self.min_price.setSpecialValueText(self.translator.t('no_min_price'))

        self.max_price = QDoubleSpinBox()
        self.max_price.setRange(0, 999999)
        self.max_price.setDecimals(2)
        self.max_price.setSuffix(" ₪")  # You can change to your currency
        self.max_price.setSpecialValueText(self.translator.t('no_max_price'))
        self.max_price.setValue(0)

        price_layout.addWidget(self.min_price)
        price_layout.addWidget(QLabel("-"))
        price_layout.addWidget(self.max_price)

        form_layout.addRow(QLabel(f"{self.translator.t('price_range')}:"), price_widget)

        layout.addWidget(form_container)

        # Buttons with unified styling
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)

        reset_btn = QPushButton(self.translator.t('reset'))
        reset_btn.setIcon(QIcon("resources/reset_icon.png"))
        reset_btn.clicked.connect(self.reset_filters)

        apply_btn = QPushButton(self.translator.t('apply_filter'))
        apply_btn.setIcon(QIcon("resources/check_icon.png"))
        apply_btn.clicked.connect(self.accept)
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {get_color('highlight')};
                color: white;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {QColor(get_color('highlight')).darker(115).name()};
            }}
        """)

        cancel_btn = QPushButton(self.translator.t('cancel'))
        cancel_btn.setIcon(QIcon("resources/cancel_icon.png"))
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(apply_btn)

        layout.addWidget(button_container)

    def reset_filters(self):
        """Clear all filter fields"""
        self.category_edit.clear()
        self.name_edit.clear()
        self.min_price.setValue(0)
        self.max_price.setValue(0)

    def get_filters(self):
        """Return the current filter values"""
        return {
            "category": self.category_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "min_price": self.min_price.value() if self.min_price.value() > 0 else None,
            "max_price": self.max_price.value() if self.max_price.value() > 0 else None
        }

