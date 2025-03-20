from PyQt5.QtWidgets import QDialog, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from themes import get_color


class ElegantDialog(QDialog):
    """Base class for all elegant dialogs with consistent styling and animations."""

    def __init__(self, translator, parent=None, title="Dialog"):
        super().__init__(parent)
        self.translator = translator
        self.setWindowTitle(self.translator.t(title) if title else "Dialog")
        self.setMinimumWidth(450)
        self.setMinimumHeight(300)

        # Set window flags for modern look
        self.setWindowFlags(self.windowFlags() | Qt.WindowCloseButtonHint)

        self.apply_theme()

    def apply_theme(self):
        """Apply theme colors to dialog"""
        bg_color = get_color('background')
        text_color = get_color('text')
        card_bg = get_color('card_bg')
        border_color = get_color('border')
        button_color = get_color('button')
        button_hover = get_color('button_hover')
        button_pressed = get_color('button_pressed')
        highlight_color = get_color('highlight')

        # Create elegant shadow effect for buttons
        is_dark_theme = QColor(bg_color).lightness() < 128
        shadow_opacity = "0.4" if is_dark_theme else "0.15"
        shadow_color = f"rgba(0, 0, 0, {shadow_opacity})"

        # Main dialog style
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 10px;
                font-family: 'Segoe UI', sans-serif;
            }}

            QLabel {{
                color: {text_color};
                font-size: 14px;
            }}

            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
                background-color: {card_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 5px;
                padding: 8px;
                min-height: 30px;
                selection-background-color: {highlight_color};
            }}

            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 2px solid {highlight_color};
            }}

            QPushButton {{
                background-color: {button_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 34px;
            }}

            QPushButton:hover {{
                background-color: {button_hover};
                border: 1px solid {highlight_color};
            }}

            QPushButton:pressed {{
                background-color: {button_pressed};
                border: 2px solid {highlight_color};
            }}

            QGroupBox {{
                font-weight: bold;
                border: 1px solid {border_color};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: {card_bg};
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
                background-color: {card_bg};
            }}

            /* Spinbox styling */
            QSpinBox::up-button, QDoubleSpinBox::up-button {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid {border_color};
                border-bottom: 1px solid {border_color};
                border-top-right-radius: 5px;
                background-color: {button_color};
            }}

            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 20px;
                border-left: 1px solid {border_color};
                border-top: 1px solid {border_color};
                border-bottom-right-radius: 5px;
                background-color: {button_color};
            }}

            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
                background-color: {button_hover};
            }}

            QCheckBox {{
                spacing: 7px;
                color: {text_color};
            }}

            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {border_color};
                border-radius: 3px;
                background-color: {card_bg};
            }}

            QCheckBox::indicator:checked {{
                background-color: {highlight_color};
                border: 1px solid {highlight_color};
                image: url(resources/check_icon.png);
            }}
        """)