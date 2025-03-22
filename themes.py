from PyQt5.QtGui import QColor
from shared_imports import *
import traceback
THEMES = {
    "classic": {
        # Sophisticated blue theme with depth and elegance
        "primary": "#1A365D",  # Rich navy primary
        "secondary": "#2A4365",  # Slightly lighter navy secondary
        "background": "#0F2942",  # Deep blue background
        "text": "#E2E8F0",  # Soft white text with slight blue tint
        "button": "#3182CE",  # Vibrant blue button
        "button_hover": "#4299E1",  # Lighter vibrant blue on hover
        "button_pressed": "#2B6CB0",  # Deeper blue when pressed
        "border": "#2C5282",  # Refined border color
        "input_bg": "#1E3A5F",  # Slightly elevated input fields
        "header": "#0F2942",  # Match with background
        "footer": "#0F2942",  # Match with background
        "sidebar_bg": "#0F2942",  # Match with background
        "sidebar_button": "#1E3A5F",  # Slightly raised button
        "stats_card": "#2A4D6A",  # Rich blue for cards with slight green tint
        "warning": "#ECC94B",  # Gold warning
        "success": "#38B2AC",  # Teal success
        "error": "#E53E3E",  # Clean red error
        "card_bg": "#1E3A5F",  # Card background
        "shadow": "#00000066",  # Subtle shadow
        "highlight": "#4299E1",  # Selection highlight
        "divider": "#2C5282",  # Subtle divider
        "accent": "#805AD5",  # Purple accent for special elements
        "overlay": "#0F2942DD",  # Semi-transparent overlay
        "title": "#E2E8F0"  # Title text color matching text color
    },

    "dark": {
        # Refined dark theme with subtle depth
        "primary": "#121212",  # Near black primary with hint of warmth
        "secondary": "#1E1E1E",  # Dark gray secondary with warmth
        "background": "#000000",  # Pure black background
        "text": "#F7FAFC",  # Crisp white text
        "button": "#2D3748",  # Deep slate button
        "button_hover": "#4A5568",  # Medium slate hover
        "button_pressed": "#1A202C",  # Very deep slate when pressed
        "border": "#2D3748",  # Matching border with buttons
        "input_bg": "#1E1E1E",  # Slightly elevated input fields
        "header": "#000000",  # Match with background
        "footer": "#000000",  # Match with background
        "sidebar_bg": "#121212",  # Slightly lighter than background
        "sidebar_button": "#1E1E1E",  # Raised button
        "stats_card": "#1A202C",  # Card background
        "success": "#38A169",  # Forest green success
        "warning": "#DD6B20",  # Burnt orange warning
        "error": "#E53E3E",  # Clean red error
        "card_bg": "#1E1E1E",  # Card background
        "shadow": "#00000080",  # Pronounced shadow
        "highlight": "#5A67D8",  # Royal blue highlight
        "divider": "#2D3748",  # Subtle divider
        "accent": "#9F7AEA",  # Rich purple accent
        "overlay": "#000000E6",  # Near-opaque overlay
        "title": "#F7FAFC"  # Title text color matching text color
    },

    "light": {
        # Elevated modern light theme
        "primary": "#FFFFFF",  # Pure white primary
        "secondary": "#F7FAFC",  # Very light blue-gray secondary
        "background": "#EDF2F7",  # Light blue-gray background
        "text": "#1A202C",  # Deep gray-blue text for contrast
        "button": "#4299E1",  # Sky blue button
        "button_hover": "#63B3ED",  # Lighter sky blue hover
        "button_pressed": "#3182CE",  # Darker blue when pressed
        "border": "#CBD5E0",  # Soft gray border
        "input_bg": "#FFFFFF",  # White input background
        "header": "#FFFFFF",  # White header
        "footer": "#FFFFFF",  # White footer
        "sidebar_bg": "#FFFFFF",  # White sidebar
        "sidebar_button": "#F7FAFC",  # Very light sidebar buttons
        "stats_card": "#F7FAFC",  # Very light card
        "success": "#38A169",  # Forest green success
        "warning": "#DD6B20",  # Burnt orange warning
        "error": "#E53E3E",  # Clean red error
        "card_bg": "#FFFFFF",  # White card background
        "shadow": "#00000015",  # Very subtle shadow
        "highlight": "#90CDF4",  # Light blue highlight
        "divider": "#E2E8F0",  # Very light divider
        "accent": "#9F7AEA",  # Rich purple accent
        "overlay": "#EDF2F7E6",  # Light translucent overlay
        "title": "#1A202C"  # Title text color matching text color
    }
}

# Function implementations remain the same
from contextlib import contextmanager

_current_theme = "classic"


def set_theme(theme_name):
    global _current_theme
    _current_theme = theme_name if theme_name in THEMES else "classic"


# Add this to your themes.py file

def apply_enhanced_borders():
    """Apply enhanced borders to all widgets"""
    from PyQt5.QtWidgets import QApplication

    # Define the style with stronger borders
    enhanced_border_style = """
        /* Enhanced borders for QFrame */
        QFrame {
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        /* Enhanced borders for card-like containers */
        QFrame#appGridContainer, QWidget#settingsContainer, QWidget#partsContainer, 
        QWidget#productsContainer, QWidget#statsContainer, QWidget#searchContainer {
            border: 2px solid rgba(200, 200, 200, 0.3);
            border-radius: 8px;
            padding: 5px;
        }

        /* Enhanced tab widgets */
        QTabWidget::pane {
            border: 2px solid rgba(200, 200, 200, 0.3);
            border-radius: 5px;
        }

        /* Settings widget specific enhancements */
        QWidget#settingsContainer {
            border: 3px solid rgba(64, 158, 255, 0.5);
            border-radius: 10px;
        }

        /* Group boxes with better defined borders */
        QGroupBox {
            border: 2px solid rgba(200, 200, 200, 0.25);
            border-radius: 6px;
            margin-top: 20px;
            font-weight: bold;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 10px;
        }
    """

    # Apply the enhanced border style to the application
    app = QApplication.instance()
    if app:
        app.setStyleSheet(app.styleSheet() + enhanced_border_style)

@contextmanager
def temp_theme(theme_name):
    """Temporary theme context manager"""
    original = _current_theme
    set_theme(theme_name)
    try:
        yield
    finally:
        set_theme(original)


# Modify the get_color function to trace where it's called incorrectly:
def get_color(color_key):
    if isinstance(color_key, tuple) or len(color_key) > 30:
        print("Invalid get_color call:")
        traceback.print_stack()
    return THEMES[_current_theme].get(color_key, QColor(0, 0, 0))


def apply_dialog_theme(dialog, title="", icon_path=None, min_width=400):
    """Apply consistent theme styling to any dialog"""
    # Set basic properties
    if title:
        dialog.setWindowTitle(title)
    if icon_path:
        dialog.setWindowIcon(QIcon(icon_path))
    dialog.setMinimumWidth(min_width)

    # Apply elegant styling with theme colors
    dialog.setStyleSheet(f"""
        QDialog {{
            background-color: {get_color('background')};
            border: 2px solid {get_color('border')};
            border-radius: 8px;
        }}
        QLabel {{
            color: {get_color('text')};
            font-size: 14px;
        }}
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
            background-color: {get_color('input_bg')};
            color: {get_color('text')};
            border: 1px solid {get_color('border')};
            border-radius: 4px;
            padding: 8px;
            font-size: 14px;
        }}
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 2px solid {get_color('highlight')};
        }}
        QPushButton {{
            background-color: {get_color('button')};
            color: {get_color('text')};
            border: 1px solid {get_color('border')};
            border-radius: 5px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: bold;
            min-width: 100px;
        }}
        QPushButton:hover {{
            background-color: {get_color('button_hover')};
            border: 1px solid {get_color('highlight')};
        }}
        QPushButton:pressed {{
            background-color: {get_color('button_pressed')};
            border: 2px solid {get_color('highlight')};
        }}
        QPushButton#primaryButton {{
            background-color: {get_color('highlight')};
            color: white;
            border: none;
        }}
        QPushButton#primaryButton:hover {{
            background-color: {QColor(get_color('highlight')).darker(115).name()};
        }}
        QScrollArea {{
            border: 1px solid {get_color('border')};
            background-color: {get_color('card_bg')};
            border-radius: 4px;
        }}
        QGroupBox {{
            background-color: {get_color('card_bg')};
            border: 1px solid {get_color('border')};
            border-radius: 6px;
            margin-top: 16px;
            font-weight: bold;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 5px;
        }}
    """)

    return dialog