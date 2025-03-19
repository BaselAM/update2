#!/usr/bin/env python3

from pathlib import Path
import os


def find_all_homepage_files():
    """Find all home_page.py files in the current directory and subdirectories"""
    home_pages = []
    for root, dirs, files in os.walk("."):
        if "home_page.py" in files:
            home_pages.append(os.path.join(root, "home_page.py"))
    return home_pages


def fix_home_page_text(file_path):
    """Fix the verbose text in a specific home_page.py file"""
    print(f"Checking {file_path}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if this file has the verbose date/time text
    if "Current Date and Time (UTC" in content:
        print(f"Found verbose text in {file_path}, fixing...")

        # Replace the actual date/time and user login components
        # This is a more direct approach focusing on the exact setup_ui method

        # Look for the specific patterns that display the verbose text
        if "self.date_time = QLabel(\"Current Date and Time" in content:
            # Replace with commented out code
            content = content.replace(
                'self.date_time = QLabel("Current Date and Time',
                '# Removed verbose date time\n        # self.date_time = QLabel("'
            )

        if "self.user_info = QLabel(\"Current User's Login:" in content:
            # Replace with clean welcome message
            content = content.replace(
                'self.user_info = QLabel("Current User\'s Login: BaselAM")',
                'self.user_info = QLabel(f"Welcome, {self.username}")'
            )

        # Also check for any update method that sets this text
        if "def update_user" in content and "Current User's Login" in content:
            content = content.replace(
                'self.user_info.setText(f"Current User\'s Login: {username}")',
                'self.user_info.setText(f"Welcome, {username}")'
            )

        # Write changes back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✓ Fixed verbose text in {file_path}")
        return True
    else:
        print(f"× No verbose text found in {file_path} (might be a different version)")
        return False


def create_clean_home_page():
    """Create a new clean home_page.py file in the current directory"""
    print("Creating a new clean home_page.py with proper formatting...")

    # This is a simplified version with the clean welcome message
    clean_code = """
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import (
    QWidget, QGridLayout, QVBoxLayout, QLabel,
    QHBoxLayout, QFrame, QSizePolicy, QToolButton
)
from PyQt5.QtGui import QIcon, QFont
from themes import get_color
from pathlib import Path

class ResponsiveAppButton(QToolButton):
    \"\"\"Modern, responsive app button that stretches with the window\"\"\"
    def __init__(self, text, icon_path=None, parent=None):
        super().__init__(parent)
        # Make the button expand in both directions
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Set minimum size but allow expansion
        self.setMinimumSize(140, 120)
        self.setText(text)

        if icon_path and Path(icon_path).exists():
            self.setIcon(QIcon(str(icon_path)))
            self.setIconSize(QSize(48, 48))

        # Set text to appear below icon
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

class HomePageWidget(QWidget):
    def __init__(self, translator, navigation_functions):
        super().__init__()
        self.setObjectName("appGridContainer")  # Added for styling
        self.translator = translator
        self.navigation_functions = navigation_functions
        self.username = "BaselAM"  # Default username
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        \"\"\"Create a modern app-like layout with responsive buttons\"\"\"
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Header section
        header = QFrame()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 5)

        # Title
        self.title = QLabel(self.translator.t('home_page_title'))
        self.title.setAlignment(Qt.AlignCenter)
        title_font = QFont("Segoe UI", 24)
        title_font.setBold(True)
        self.title.setFont(title_font)

        # Add to header layout
        header_layout.addWidget(self.title)

        # App grid container with responsive design
        app_grid_container = QFrame()
        app_grid_container.setObjectName("appGridContainer")
        app_grid_layout = QVBoxLayout(app_grid_container)
        app_grid_layout.setContentsMargins(15, 15, 15, 15)

        # App buttons grid - with reduced spacing
        grid_widget = QWidget()
        grid_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.grid_layout = QGridLayout(grid_widget)
        self.grid_layout.setSpacing(10)  # Closer spacing

        # Define buttons in a more app-like arrangement - 3x2 grid
        buttons = [
            {"id": "products_button", "icon": "resources/product_icon.png", "position": (0, 0)},
            {"id": "parts_button", "icon": "resources/parts_icon.png", "position": (0, 1)}, 
            {"id": "web_search_button", "icon": "resources/search_web_icon.png", "position": (0, 2)},
            {"id": "statistics_button", "icon": "resources/stats_icon.png", "position": (1, 0)},
            {"id": "settings_button", "icon": "resources/settings_icon.png", "position": (1, 1)},
            {"id": "help_button", "icon": "resources/help_icon.png", "position": (1, 2)}
        ]

        # Create app-style buttons that stretch
        self.nav_buttons = {}

        for btn in buttons:
            button = ResponsiveAppButton(
                self.translator.t(btn["id"]),
                btn["icon"]
            )

            if btn["id"] in self.navigation_functions:
                button.clicked.connect(self.navigation_functions[btn["id"]])

            self.nav_buttons[btn["id"]] = button
            self.grid_layout.addWidget(button, *btn["position"])

        # Set equal stretch for all columns and rows
        for i in range(3):  # 3 columns
            self.grid_layout.setColumnStretch(i, 1)
        for i in range(2):  # 2 rows
            self.grid_layout.setRowStretch(i, 1)

        # Add grid to container
        app_grid_layout.addWidget(grid_widget)

        # CLEAN WELCOME MESSAGE
        self.user_info = QLabel(f"Welcome, {self.username}")
        self.user_info.setAlignment(Qt.AlignCenter)
        user_font = QFont("Segoe UI", 13)
        user_font.setBold(True)
        self.user_info.setFont(user_font)
        app_grid_layout.addWidget(self.user_info)

        # Exit button at bottom with a different style
        exit_container = QFrame()
        exit_layout = QHBoxLayout(exit_container)
        exit_layout.setContentsMargins(0, 15, 0, 0)

        # Modern, floating action button style for exit
        self.exit_button = QToolButton()
        self.exit_button.setText(self.translator.t("exit_button"))
        self.exit_button.setMinimumSize(180, 50)

        if "exit_button" in self.navigation_functions:
            self.exit_button.clicked.connect(self.navigation_functions["exit_button"])

        # Center the exit button
        exit_layout.addStretch(1)
        exit_layout.addWidget(self.exit_button)
        exit_layout.addStretch(1)

        # Add everything to main layout with proper proportions
        self.main_layout.addWidget(header)
        self.main_layout.addSpacing(5)
        self.main_layout.addWidget(app_grid_container, 1)  # Give more space to buttons
        self.main_layout.addWidget(exit_container)

    def update_user(self, username):
        \"\"\"Update the displayed username\"\"\"
        self.username = username
        if hasattr(self, 'user_info'):
            self.user_info.setText(f"Welcome, {username}")

    def apply_theme(self):
        \"\"\"Apply elegant theme styling with modern app aesthetics\"\"\"
        bg_color = get_color('background')
        card_bg = get_color('card_bg')
        text_color = get_color('text')
        button_bg = get_color('button')
        button_hover = get_color('button_hover')
        highlight_color = get_color('highlight')

        # App container style with subtle shadow and rounded corners
        container_style = f\"\"\"
            #appGridContainer {{
                background-color: {card_bg};
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
        \"\"\"

        # Modern app button style - larger with better spacing
        app_button_style = f\"\"\"
            QToolButton {{
                background-color: {button_bg};
                color: {text_color};
                border: none;
                border-radius: 18px;
                padding: 10px;
                font-size: 15px;
                font-weight: bold;
            }}
            QToolButton:hover {{
                background-color: {button_hover};
                border: 2px solid {get_color('highlight')};
            }}
        \"\"\"

        # Exit button with a distinct style
        exit_button_style = f\"\"\"
            QToolButton {{
                background-color: {get_color('error')};
                color: white;
                border: none;
                border-radius: 25px;
                padding: 10px 20px;
                font-size: 15px;
                font-weight: bold;
            }}
            QToolButton:hover {{
                background-color: #FF5252;
            }}
        \"\"\"

        # Apply styles
        for button in self.nav_buttons.values():
            button.setStyleSheet(app_button_style)

        self.exit_button.setStyleSheet(exit_button_style)

        # Title and user info styles
        self.title.setStyleSheet(f"color: {text_color};")
        self.user_info.setStyleSheet(f"color: {highlight_color}; margin-top: 10px;")

        # Main widget style
        self.setStyleSheet(f\"\"\"
            HomePageWidget {{
                background-color: {bg_color};
            }}
            QLabel {{
                color: {text_color};
            }}
            {container_style}
        \"\"\")

    def update_translations(self):
        \"\"\"Update all text when language changes\"\"\"
        self.title.setText(self.translator.t('home_page_title'))

        # Update button texts
        for btn_id, button in self.nav_buttons.items():
            button.setText(self.translator.t(btn_id))

        # Update user info - maintain username
        self.user_info.setText(f"Welcome, {self.username}")

        self.exit_button.setText(self.translator.t('exit_button'))
"""

    # Write the clean home page to the current directory
    with open('home_page.py', 'w', encoding='utf-8') as f:
        f.write(clean_code.strip())

    print("✓ Created a new clean home_page.py file")
    return True


if __name__ == "__main__":
    print("=== Home Page Text Fixer ===")
    print("This script will fix the verbose text in home_page.py")

    # First try to find and fix all existing home_page.py files
    files = find_all_homepage_files()
    if files:
        fixed_any = False
        for file_path in files:
            if fix_home_page_text(file_path):
                fixed_any = True

        if not fixed_any:
            print("\nCouldn't fix any existing home_page.py files.")
            create_clean_home_page()
    else:
        print("No home_page.py files found. Creating a new one...")
        create_clean_home_page()

    print("\nDone! Run your application to check if the text is fixed.")