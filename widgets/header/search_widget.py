from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QSize
from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QHBoxLayout, QCompleter,
    QToolButton, QMenu, QAction
)
from PyQt5.QtGui import QIcon, QFont
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
        layout.setSpacing(5)  # More compact spacing

        # Search input with placeholder and better styling
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.translator.t('search_placeholder'))
        self.search_input.setMinimumWidth(220)  # Slightly smaller
        self.search_input.returnPressed.connect(self._on_search_submitted)

        # Add search icon with proper sizing
        search_icon_path = Path(
            __file__).resolve().parent.parent.parent / "resources/search_icon.png"
        if search_icon_path.exists():
            search_icon = QIcon(str(search_icon_path))
            self.search_input.addAction(search_icon, QLineEdit.LeadingPosition)

        # Add dropdown button with proper functionality
        self.dropdown_btn = QToolButton()
        self.dropdown_btn.setCursor(Qt.PointingHandCursor)
        self.dropdown_btn.setText("▼")
        self.dropdown_btn.setFixedSize(24, 24)
        self.dropdown_btn.setToolTip(self.translator.t('search_options'))

        # Create dropdown menu with search filtering options
        self.dropdown_menu = QMenu(self)

        # Define the search filter options
        search_options = [
            {"text": "Search Products", "slot": self.search_products},
            {"text": "Search Categories", "slot": self.search_categories},
            {"text": "Search Cars", "slot": self.search_cars},
            {"text": "Advanced Search", "slot": self.advanced_search}
        ]

        # Add separator between categories
        self.dropdown_menu.addSection("Search Filters")

        # Add options to menu
        for option in search_options:
            action = QAction(option["text"], self)
            action.triggered.connect(option["slot"])
            self.dropdown_menu.addAction(action)

        # Connect menu to button
        self.dropdown_btn.setMenu(self.dropdown_menu)
        self.dropdown_btn.setPopupMode(QToolButton.InstantPopup)

        # Set up autocomplete for search
        self.setup_autocomplete()

        # Expand button for wider search with better styling
        self.expand_btn = QToolButton()
        self.expand_btn.setCursor(Qt.PointingHandCursor)
        self.expand_btn.setText("⟷")
        self.expand_btn.setToolTip(self.translator.t('expand_search'))
        self.expand_btn.clicked.connect(self.toggle_expand)
        self.expand_btn.setFixedSize(24, 24)

        # Add to layout with proper spacing
        layout.addWidget(self.search_input)
        layout.addWidget(self.dropdown_btn)
        layout.addWidget(self.expand_btn)

        # Animation for expansion
        self.animation = QPropertyAnimation(self.search_input, b"minimumWidth")
        self.animation.setDuration(200)  # Slightly faster animation
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)

    def setup_autocomplete(self):
        """Set up autocomplete for the search input"""
        try:
            # Get product names for autocomplete
            # If the database method isn't available, use sample data
            try:
                if hasattr(self.database, 'get_product_names'):
                    product_names = self.database.get_product_names()
                else:
                    product_names = []
            except:
                # Fallback to sample data
                product_names = [
                    "Oil Filter", "Air Filter", "Brake Pad", "Brake Disc",
                    "Spark Plug", "Fuel Filter", "Cabin Filter", "Engine Oil",
                    "Transmission Fluid", "Coolant", "Wiper Blade", "Battery",
                    "Alternator", "Starter Motor", "Water Pump", "Radiator",
                    "Timing Belt", "Serpentine Belt", "Shock Absorber", "Strut"
                ]

            # Create and configure the completer
            completer = QCompleter(product_names)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)  # Match anywhere in the string
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
            self.animation.setStartValue(220)
            self.animation.setEndValue(350)
            self.expand_btn.setText("⟵")
            self.expand_btn.setToolTip(self.translator.t('collapse_search'))
        else:
            self.animation.setStartValue(350)
            self.animation.setEndValue(220)
            self.expand_btn.setText("⟷")
            self.expand_btn.setToolTip(self.translator.t('expand_search'))

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

    def advanced_search(self):
        """Open advanced search dialog"""
        # In a real implementation, this would open a more complex search dialog
        self.search_input.setPlaceholderText(self.translator.t('advanced_search'))
        self.search_input.setFocus()

    def clear_search(self):
        """Clear the search input"""
        self.search_input.clear()

    def update_translations(self):
        """Update translations for this widget"""
        self.search_input.setPlaceholderText(self.translator.t('search_placeholder'))
        self.expand_btn.setToolTip(self.translator.t('expand_search'))
        self.dropdown_btn.setToolTip(self.translator.t('search_options'))

    def apply_theme(self):
        """Apply current theme to this widget"""
        from themes import get_color

        # Apply elegant search styling
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {get_color('input_bg')};
                color: {get_color('text')};
                border: 1px solid {get_color('border')};
                border-radius: 12px;
                padding: 5px 12px;
                font-size: 12px;
                min-height: 18px;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {get_color('highlight')};
            }}
        """)

        button_style = f"""
            QToolButton {{
                background-color: transparent;
                color: {get_color('text')};
                border: none;
                padding: 3px;
            }}
            QToolButton:hover {{
                background-color: {get_color('button_hover')};
                border-radius: 10px;
            }}
        """

        self.dropdown_btn.setStyleSheet(button_style)
        self.expand_btn.setStyleSheet(button_style)

        # Style for dropdown menu
        self.dropdown_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {get_color('card_bg')};
                color: {get_color('text')};
                border: 1px solid {get_color('border')};
                border-radius: 6px;
                padding: 4px;
            }}

            QMenu::item {{
                padding: 5px 25px 5px 20px;
                border-radius: 4px;
            }}

            QMenu::item:selected {{
                background-color: {get_color('button_hover')};
            }}

            QMenu::separator {{
                height: 1px;
                background-color: {get_color('border')};
                margin: 4px 10px;
            }}
        """)