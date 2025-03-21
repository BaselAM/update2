from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                             QLineEdit)
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt, QSize

from themes import get_color
from widgets.products.components import StatusBar
from widgets.products.product_table import ProductsTable


class UIHandler:
    """Handles the UI setup and theme for the Products Widget"""

    def __init__(self, widget, translator):
        self.widget = widget
        self.translator = translator

        # UI components
        self.add_btn = None
        self.select_toggle = None
        self.remove_btn = None
        self.filter_btn = None
        self.export_btn = None
        self.refresh_btn = None
        self.search_input = None
        self.product_table = None
        self.status_bar = None

    def setup_ui(self):
        """Set up the UI components"""
        # Set object name for styling
        self.widget.setObjectName("productsContainer")

        main_layout = QVBoxLayout(self.widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # --- Button Panel ---
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Create buttons with icons
        self.add_btn = QPushButton(self.translator.t('add_product'))
        self.add_btn.setIcon(QIcon("resources/add_icon.png"))
        self.add_btn.setIconSize(QSize(18, 18))
        self.add_btn.setCursor(Qt.PointingHandCursor)
        button_layout.addWidget(self.add_btn)

        self.select_toggle = QPushButton(self.translator.t('select_button'))
        self.select_toggle.setIcon(QIcon("resources/select_icon.png"))
        self.select_toggle.setIconSize(QSize(18, 18))
        self.select_toggle.setCheckable(True)
        self.select_toggle.setCursor(Qt.PointingHandCursor)
        button_layout.addWidget(self.select_toggle)

        self.remove_btn = QPushButton(self.translator.t('remove'))
        self.remove_btn.setIcon(QIcon("resources/delete_icon.png"))
        self.remove_btn.setIconSize(QSize(18, 18))
        self.remove_btn.setCursor(Qt.PointingHandCursor)
        button_layout.addWidget(self.remove_btn)

        self.filter_btn = QPushButton(self.translator.t('filter_button'))
        self.filter_btn.setIcon(QIcon("resources/filter_icon.png"))
        self.filter_btn.setIconSize(QSize(18, 18))
        self.filter_btn.setCursor(Qt.PointingHandCursor)
        button_layout.addWidget(self.filter_btn)

        self.export_btn = QPushButton(self.translator.t('export'))
        self.export_btn.setIcon(QIcon("resources/export_icon.png"))
        self.export_btn.setIconSize(QSize(18, 18))
        self.export_btn.setCursor(Qt.PointingHandCursor)
        button_layout.addWidget(self.export_btn)

        self.refresh_btn = QPushButton(self.translator.t('refresh'))
        self.refresh_btn.setIcon(QIcon("resources/refresh_icon.png"))
        self.refresh_btn.setIconSize(QSize(18, 18))
        self.refresh_btn.setCursor(Qt.PointingHandCursor)

        button_layout.addStretch()
        button_layout.addWidget(self.refresh_btn)
        main_layout.addLayout(button_layout)

        # --- Search Box ---
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)

        search_label = QLabel(self.translator.t('search_products'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.translator.t('search_placeholder'))

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input, 1)

        main_layout.addLayout(search_layout)

        # --- Table Setup ---
        self.product_table = ProductsTable(self.translator)
        main_layout.addWidget(self.product_table, 1)

        # --- Status Bar ---
        self.status_bar = StatusBar()
        self.status_bar.setObjectName("statusBar")
        main_layout.addWidget(self.status_bar)

        return {
            'add_btn': self.add_btn,
            'select_toggle': self.select_toggle,
            'remove_btn': self.remove_btn,
            'filter_btn': self.filter_btn,
            'export_btn': self.export_btn,
            'refresh_btn': self.refresh_btn,
            'search_input': self.search_input,
            'product_table': self.product_table,
            'status_bar': self.status_bar
        }

    def apply_theme(self):
        """Apply theme to all UI components"""
        bg_color = get_color('background')
        text_color = get_color('text')
        card_bg = get_color('card_bg')
        border_color = get_color('border')
        button_color = get_color('button')
        button_hover = get_color('button_hover')
        button_pressed = get_color('button_pressed')
        highlight_color = get_color('highlight')

        try:
            accent_color = get_color('accent')
        except:
            accent_color = highlight_color

        border_rgba = QColor(accent_color)
        border_rgba.setAlpha(120)
        border_str = f"rgba({border_rgba.red()}, {border_rgba.green()}, {border_rgba.blue()}, 0.47)"

        is_dark_theme = QColor(bg_color).lightness() < 128
        shadow_opacity = "0.4" if is_dark_theme else "0.15"
        shadow_color = f"rgba(0, 0, 0, {shadow_opacity})"

        base_style = f"""
            QWidget {{
                color: {text_color};
                font-family: 'Segoe UI';
                font-size: 14px;
            }}
            #productsContainer {{
                background-color: {bg_color};
                border: 3px solid {border_str};
                border-radius: 12px;
                padding: 5px;
            }}
        """
        self.widget.setStyleSheet(base_style)

        btn_style = f"""
            QPushButton {{
                background-color: {button_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 10px 18px;
                margin: 3px;
                font-size: 15px;
                font-weight: bold;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {button_hover};
                border: 1px solid {highlight_color};
                box-shadow: 0px 2px 4px {shadow_color};
            }}
            QPushButton:pressed {{
                background-color: {button_pressed};
                border: 2px solid {highlight_color};
                padding: 9px 17px;
            }}
            QPushButton:disabled {{
                background-color: {card_bg};
                color: {border_color};
                border: 1px solid {border_color};
            }}
            QPushButton:checked {{
                background-color: {highlight_color};
                color: {bg_color};
                border: 2px solid {highlight_color};
            }}
        """

        for btn in [self.add_btn, self.select_toggle, self.remove_btn, self.filter_btn,
                    self.export_btn, self.refresh_btn]:
            btn.setStyleSheet(btn_style)

        search_style = f"""
            QLineEdit {{
                background-color: {get_color('input_bg')};
                color: {text_color};
                border: 2px solid {border_color};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {highlight_color};
                background-color: {QColor(get_color('input_bg')).lighter(105).name()};
            }}
            QLabel {{
                font-weight: bold;
            }}
        """
        self.search_input.setStyleSheet(search_style)
        self.product_table.apply_theme()

        # Set up the status bar theme
        theme_status = {
            "success": {"bg": get_color('status_success_bg') or "#e8f5e9",
                        "border": get_color('status_success_border') or "#81c784",
                        "text": get_color('status_success_text') or "#2E7D32"},
            "error": {"bg": get_color('status_error_bg') or "#ffebee",
                      "border": get_color('status_error_border') or "#e57373",
                      "text": get_color('status_error_text') or "#C62828"},
            "warning": {"bg": get_color('status_warning_bg') or "#fff8e1",
                        "border": get_color('status_warning_border') or "#ffd54f",
                        "text": get_color('status_warning_text') or "#EF6C00"},
            "info": {"bg": get_color('status_info_bg') or "#e3f2fd",
                     "border": get_color('status_info_border') or "#64b5f6",
                     "text": get_color('status_info_text') or "#1565C0"}
        }
        self.status_bar.set_theme(theme_status)

    def update_select_button_style(self, checked):
        """Update the style of the select button based on its state"""
        bg_color = get_color('background')
        text_color = get_color('text')
        border_color = get_color('border')
        highlight_color = get_color('highlight')
        button_color = get_color('button')
        button_hover = get_color('button_hover')
        button_pressed = get_color('button_pressed')
        card_bg = get_color('card_bg')

        is_dark_theme = QColor(bg_color).lightness() < 128
        shadow_opacity = "0.4" if is_dark_theme else "0.15"
        shadow_color = f"rgba(0, 0, 0, {shadow_opacity})"

        if checked:
            highlight_style = f"""
                QPushButton {{
                    background-color: {highlight_color};
                    color: {bg_color};
                    border: 1px solid {highlight_color};
                    border-radius: 6px;
                    padding: 10px 18px;
                    margin: 3px;
                    font-size: 15px;
                    font-weight: bold;
                    min-width: 100px;
                    box-sizing: border-box;
                }}
                QPushButton:hover {{
                    background-color: {QColor(highlight_color).darker(110).name()};
                    border-color: {QColor(highlight_color).darker(120).name()};
                }}
            """
            self.select_toggle.setStyleSheet(highlight_style)
        else:
            btn_style = f"""
                QPushButton {{
                    background-color: {button_color};
                    color: {text_color};
                    border: 1px solid {border_color};
                    border-radius: 6px;
                    padding: 10px 18px;
                    margin: 3px;
                    font-size: 15px;
                    font-weight: bold;
                    min-width: 100px;
                    box-sizing: border-box;
                }}
                QPushButton:hover {{
                    background-color: {button_hover};
                    border: 1px solid {highlight_color};
                    box-shadow: 0px 2px 4px {shadow_color};
                }}
                QPushButton:pressed {{
                    background-color: {button_pressed};
                    border: 1px solid {highlight_color};
                    padding: 10px 18px;
                }}
                QPushButton:disabled {{
                    background-color: {card_bg};
                    color: {border_color};
                    border: 1px solid {border_color};
                }}
                QPushButton:checked {{
                    background-color: {highlight_color};
                    color: {bg_color};
                    border: 1px solid {highlight_color};
                    padding: 10px 18px;
                }}
            """
            self.select_toggle.setStyleSheet(btn_style)

    def update_translations(self):
        """Update translations for all text elements"""
        self.add_btn.setText(self.translator.t('add_product'))
        self.select_toggle.setText(self.translator.t('select_button'))
        self.remove_btn.setText(self.translator.t('remove'))
        self.filter_btn.setText(self.translator.t('filter_button'))
        self.export_btn.setText(self.translator.t('export'))
        self.refresh_btn.setText(self.translator.t('refresh'))
        self.search_input.setPlaceholderText(self.translator.t('search_placeholder'))
        self.product_table.update_headers()
