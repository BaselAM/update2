
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QFormLayout, QDoubleSpinBox, QGroupBox,
                             QComboBox, QCheckBox, QRadioButton, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor

from themes import get_color
from widgets.products.dialogs.base_dialog import ElegantDialog


class BetterDoubleSpinBox(QDoubleSpinBox):
    """A better double spin box that clears special text on focus"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        # When the widget gets focus, clear any special text
        if obj == self and event.type() == QEvent.FocusIn:
            # If the value is the minimum (0), temporarily remove special text to allow editing
            if self.value() == self.minimum():
                self.setSpecialValueText("")
                # Force redisplay
                self.setValue(self.value())

        # When focus is lost, restore special text if value is minimum
        if obj == self and event.type() == QEvent.FocusOut:
            if self.value() == self.minimum() and hasattr(self, '_special_text'):
                self.setSpecialValueText(self._special_text)
                # Force redisplay
                self.setValue(self.value())

        return super().eventFilter(obj, event)

    def setSpecialValueText(self, text):
        self._special_text = text
        super().setSpecialValueText(text)



class FilterDialog(ElegantDialog):
    """Enhanced filter dialog with fixed stock status filtering."""

    def __init__(self, translator, parent=None, currency_symbol="₪"):
        super().__init__(translator, parent, title='filter_title')
        self.setWindowTitle(self.translator.t('filter_title'))

        # Make the dialog smaller
        self.setMinimumWidth(420)
        self.setMinimumHeight(400)

        # Use the provided currency symbol or default to ILS
        self.currency_symbol = currency_symbol

        # Initialize empty filters dictionary
        self.filters = {
            "category": "",
            "name": "",
            "car_name": "",
            "model": "",
            "min_price": None,
            "max_price": None,
            "stock_status": None  # This is the key we'll use for stock filtering
        }

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)  # Reduced spacing
        main_layout.setContentsMargins(15, 15, 15, 15)  # Reduced margins

        # Add a title label with medium font
        title_label = QLabel(self.translator.t('filter_criteria'))
        title_font = title_label.font()
        title_font.setPointSize(14)  # Smaller font
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Create a form layout for filter inputs
        form_layout = QFormLayout()
        form_layout.setSpacing(10)  # Reduced spacing
        form_layout.setContentsMargins(5, 5, 5, 5)  # Reduced margins
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # Product Details Group
        product_group = QGroupBox(self.translator.t('product_details'))
        product_grid = QGridLayout(product_group)
        product_grid.setSpacing(8)  # Reduced spacing
        product_grid.setContentsMargins(8, 12, 8, 8)  # Adjusted to fit title

        # Product Name
        name_label = QLabel(self.translator.t('product_name') + ":")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(self.translator.t('name_placeholder'))
        product_grid.addWidget(name_label, 0, 0)
        product_grid.addWidget(self.name_input, 0, 1)

        # Category
        category_label = QLabel(self.translator.t('category') + ":")
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText(self.translator.t('category_placeholder'))
        product_grid.addWidget(category_label, 1, 0)
        product_grid.addWidget(self.category_input, 1, 1)

        form_layout.addRow("", product_group)

        # Car Details Group
        car_group = QGroupBox(self.translator.t('car_details'))
        car_grid = QGridLayout(car_group)
        car_grid.setSpacing(8)  # Reduced spacing
        car_grid.setContentsMargins(8, 12, 8, 8)  # Adjusted to fit title

        # Car Name
        car_label = QLabel(self.translator.t('car') + ":")
        self.car_input = QLineEdit()
        self.car_input.setPlaceholderText(self.translator.t('car_placeholder'))
        car_grid.addWidget(car_label, 0, 0)
        car_grid.addWidget(self.car_input, 0, 1)

        # Model
        model_label = QLabel(self.translator.t('model') + ":")
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText(self.translator.t('model_placeholder'))
        car_grid.addWidget(model_label, 1, 0)
        car_grid.addWidget(self.model_input, 1, 1)

        form_layout.addRow("", car_group)

        # Price range and Stock Status in the same row
        dual_layout = QHBoxLayout()

        # Price range group - make it smaller
        price_group = QGroupBox(self.translator.t('price_range'))
        price_layout = QHBoxLayout(price_group)
        price_layout.setSpacing(5)  # Reduced spacing
        price_layout.setContentsMargins(8, 12, 8, 8)  # Adjusted to fit title

        # Min price - using standard QDoubleSpinBox instead of our custom one
        min_layout = QVBoxLayout()
        min_layout.setSpacing(2)  # Very small spacing
        min_label = QLabel(self.translator.t('min'))
        self.min_price = QDoubleSpinBox()
        self.min_price.setRange(0, 9999.99)
        self.min_price.setPrefix(f"{self.currency_symbol} ")
        # Don't use special value text to avoid input issues
        self.min_price.setFixedWidth(100)  # Smaller width
        min_layout.addWidget(min_label)
        min_layout.addWidget(self.min_price)

        # Max price - using standard QDoubleSpinBox
        max_layout = QVBoxLayout()
        max_layout.setSpacing(2)  # Very small spacing
        max_label = QLabel(self.translator.t('max'))
        self.max_price = QDoubleSpinBox()
        self.max_price.setRange(0, 9999.99)
        self.max_price.setPrefix(f"{self.currency_symbol} ")
        # Don't use special value text
        self.max_price.setFixedWidth(100)  # Smaller width
        max_layout.addWidget(max_label)
        max_layout.addWidget(self.max_price)

        price_layout.addLayout(min_layout)
        price_layout.addLayout(max_layout)

        # Stock status group - make it smaller
        stock_group = QGroupBox(self.translator.t('stock_status'))
        stock_layout = QVBoxLayout(stock_group)
        stock_layout.setSpacing(3)  # Reduced spacing
        stock_layout.setContentsMargins(8, 12, 8, 8)  # Adjusted to fit title

        self.in_stock_all = QRadioButton(self.translator.t('all_products'))
        self.in_stock_yes = QRadioButton(self.translator.t('in_stock_only'))
        self.in_stock_no = QRadioButton(self.translator.t('out_of_stock_only'))

        self.in_stock_all.setChecked(True)  # Default to all products

        stock_layout.addWidget(self.in_stock_all)
        stock_layout.addWidget(self.in_stock_yes)
        stock_layout.addWidget(self.in_stock_no)

        # Add both groups side by side
        dual_layout.addWidget(price_group, 1)
        dual_layout.addWidget(stock_group, 1)
        form_layout.addRow("", dual_layout)

        # Add form to main layout
        main_layout.addLayout(form_layout)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)  # Reduced spacing

        # Reset button
        self.reset_btn = QPushButton(self.translator.t('reset'))
        self.reset_btn.setIcon(QIcon("resources/reset_icon.png"))
        self.reset_btn.clicked.connect(self.reset_filters)
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        button_layout.addWidget(self.reset_btn)

        # Spacer
        button_layout.addStretch()

        # Cancel button
        self.cancel_btn = QPushButton(self.translator.t('cancel'))
        self.cancel_btn.setIcon(QIcon("resources/cancel_icon.png"))
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        button_layout.addWidget(self.cancel_btn)

        # Apply button
        self.apply_btn = QPushButton(self.translator.t('apply_filter'))
        self.apply_btn.setIcon(QIcon("resources/filter_icon.png"))
        self.apply_btn.clicked.connect(self.apply_filters)
        self.apply_btn.setCursor(Qt.PointingHandCursor)

        # Make Apply button stand out
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
        self.apply_btn.setStyleSheet(button_style)

        button_layout.addWidget(self.apply_btn)

        main_layout.addLayout(button_layout)

    def reset_filters(self):
        """Reset all filter fields to default values."""
        self.category_input.clear()
        self.name_input.clear()
        self.car_input.clear()
        self.model_input.clear()
        self.min_price.setValue(0)
        self.max_price.setValue(0)
        self.in_stock_all.setChecked(True)

    # Update the apply_filters method in the FilterDialog class:

    def apply_filters(self):
        """Apply filters and store values with simplified stock status handling."""
        self.filters["category"] = self.category_input.text().strip()
        self.filters["name"] = self.name_input.text().strip()
        self.filters["car_name"] = self.car_input.text().strip()
        self.filters["model"] = self.model_input.text().strip()

        # Only set min/max price if they're not at default values
        if self.min_price.value() > 0:
            self.filters["min_price"] = self.min_price.value()
        else:
            self.filters["min_price"] = None

        if self.max_price.value() > 0:
            self.filters["max_price"] = self.max_price.value()
        else:
            self.filters["max_price"] = None

        # Simplified stock status handling - use a simple string identifier
        if self.in_stock_yes.isChecked():
            self.filters["stock_status"] = "in_stock"
        elif self.in_stock_no.isChecked():
            self.filters["stock_status"] = "out_of_stock"
        else:
            self.filters["stock_status"] = None

        self.accept()
    def get_filters(self):
        """Return the current filter settings."""
        return self.filters