from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QSize
from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QHBoxLayout, QCompleter,
    QToolButton, QMenu, QAction, QVBoxLayout
)
from PyQt5.QtGui import QIcon
from pathlib import Path


class SearchWidget(QWidget):
    """Widget for handling search functionality in the top bar"""
    search_submitted = pyqtSignal(str)

    def __init__(self, translator, database, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.database = database
        self.expanded = False
        self.setup_ui()

    def setup_ui(self):
        """Create the search input with autocomplete and dropdown options"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Search input with placeholder
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.translator.t('search_placeholder'))
        self.search_input.setMinimumWidth(250)
        self.search_input.returnPressed.connect(self._on_search_submitted)

        # Add search icon if available
        search_icon_path = Path(
            __file__).resolve().parent.parent.parent / "resources/search_icon.png"
        if search_icon_path.exists():
            self.search_input.addAction(QIcon(str(search_icon_path)),
                                        QLineEdit.LeadingPosition)

        # Add dropdown button for advanced search options
        self.dropdown_btn = QToolButton()
        self.dropdown_btn.setCursor(Qt.PointingHandCursor)
        self.dropdown_btn.setText("▼")
        self.dropdown_btn.setFixedSize(24, 24)

        # Create dropdown menu
        self.dropdown_menu = QMenu(self)
        actions = [
            {"text": "Products", "icon": "product_icon.png",
             "slot": self.search_products},
            {"text": "Categories", "icon": "category_icon.png",
             "slot": self.search_categories},
            {"text": "Cars", "icon": "car_icon.png", "slot": self.search_cars}
        ]

        for action_info in actions:
            action = QAction(action_info["text"], self)
            icon_path = Path(
                __file__).resolve().parent.parent.parent / f"resources/{action_info['icon']}"
            if icon_path.exists():
                action.setIcon(QIcon(str(icon_path)))
            action.triggered.connect(action_info["slot"])
            self.dropdown_menu.addAction(action)

        self.dropdown_btn.setMenu(self.dropdown_menu)
        self.dropdown_btn.setPopupMode(QToolButton.InstantPopup)

        # Set up autocomplete for search
        self.setup_autocomplete()

        # Expand button for wider search
        self.expand_btn = QToolButton()
        self.expand_btn.setCursor(Qt.PointingHandCursor)
        self.expand_btn.setText("⟷")
        self.expand_btn.setToolTip(self.translator.t('expand_search'))
        self.expand_btn.clicked.connect(self.toggle_expand)
        self.expand_btn.setFixedSize(24, 24)

        # Add to layout
        layout.addWidget(self.search_input)
        layout.addWidget(self.dropdown_btn)
        layout.addWidget(self.expand_btn)

        # Animation for expansion
        self.animation = QPropertyAnimation(self.search_input, b"minimumWidth")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)

    def setup_autocomplete(self):
        """Set up autocomplete for the search input"""
        try:
            # Get product names for autocomplete
            product_names = self.database.get_product_names() if hasattr(self.database,
                                                                         'get_product_names') else []
            completer = QCompleter(product_names)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.search_input.setCompleter(completer)
        except Exception as e:
            print(f"Error setting up search autocomplete: {str(e)}")

    def _on_search_submitted(self):
        """Handle search submission"""
        search_text = self.search_input.text().strip()
        if search_text:
            self.search_submitted.emit(search_text)

    def toggle_expand(self):
        """Toggle between normal and expanded search width"""
        self.expanded = not self.expanded

        if self.expanded:
            self.animation.setStartValue(250)
            self.animation.setEndValue(400)
            self.expand_btn.setText("⟵")
        else:
            self.animation.setStartValue(400)
            self.animation.setEndValue(250)
            self.expand_btn.setText("⟷")

        self.animation.start()

    def search_products(self):
        """Focus search on products"""
        self.search_input.setPlaceholderText(self.translator.t('search_products'))
        self.search_input.setFocus()

    def search_categories(self):
        """Focus search on categories"""
        self.search_input.setPlaceholderText(self.translator.t('search_categories'))
        self.search_input.setFocus()

    def search_cars(self):
        """Focus search on cars"""
        self.search_input.setPlaceholderText(self.translator.t('search_cars'))
        self.search_input.setFocus()

    def clear_search(self):
        """Clear the search input"""
        self.search_input.clear()

    def update_translations(self):
        """Update translations for this widget"""
        self.search_input.setPlaceholderText(self.translator.t('search_placeholder'))
        self.expand_btn.setToolTip(self.translator.t('expand_search'))

    def apply_theme(self):
        """Apply current theme to this widget"""
        from themes import get_color

        # Apply elegant search styling
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {get_color('input_bg')};
                color: {get_color('text')};
                border: 1px solid {get_color('border')};
                border-radius: 15px;
                padding: 8px 12px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {get_color('highlight')};
            }}
        """)

        button_style = f"""
            QToolButton {{
                background-color: transparent;
                color: {get_color('text')};
                border: none;
            }}
            QToolButton:hover {{
                background-color: {get_color('button_hover')};
                border-radius: 12px;
            }}
        """

        self.dropdown_btn.setStyleSheet(button_style)
        self.expand_btn.setStyleSheet(button_style)