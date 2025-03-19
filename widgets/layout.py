from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, \
    QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPixmap

from shared import SCRIPT_DIR
from themes import get_color


class HeaderWidget(QWidget):
    """The header widget shown at the top of the application"""

    def __init__(self, translator, home_callback=None):
        super().__init__()
        self.translator = translator
        self.home_callback = home_callback
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        # Create layout for header
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        # Add spacer at the beginning to center the title
        layout.addStretch(1)

        # Title in the center (now the main element in the header)
        self.title_label = QLabel(self.translator.t("app_header_title"))
        self.title_label.setStyleSheet("font-size: 20pt; font-weight: bold;")
        layout.addWidget(self.title_label)

        # Add spacer at the end to center the title
        layout.addStretch(1)

        # Set a fixed height for the header
        self.setFixedHeight(50)

    def apply_theme(self):
        header_bg = get_color('header')
        text_color = get_color('text')

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {header_bg};
                color: {text_color};
            }}
            QPushButton {{
                background-color: transparent;
                color: {text_color};
                border: none;
                padding: 8px 16px;
                font-size: 14pt;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {get_color('button_hover')};
            }}
        """)

    def update_translations(self):
        self.title_label.setText(self.translator.t("app_header_title"))


class FooterWidget(QWidget):
    """The footer widget shown at the bottom of the application"""

    def __init__(self, translator):
        super().__init__()
        self.translator = translator
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        self.status_label = QLabel(self.translator.t("status_ready"))
        layout.addWidget(self.status_label)

        layout.addStretch()

        self.version_label = QLabel(f"v1.0.0")
        layout.addWidget(self.version_label)

        self.setFixedHeight(30)

    def apply_theme(self):
        footer_bg = get_color('footer')
        text_color = get_color('text')

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {footer_bg};
                color: {text_color};
            }}
        """)

    def update_translations(self):
        self.status_label.setText(self.translator.t("status_ready"))


class CopyrightWidget(QWidget):
    """A small copyright notice at the bottom of the application"""

    def __init__(self, translator):
        super().__init__()
        self.translator = translator
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        copyright_text = "© 2023 Auto Parts Ltd. All rights reserved."
        self.copyright_label = QLabel(copyright_text)
        self.copyright_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.copyright_label)

        self.setFixedHeight(20)

    def apply_theme(self):
        bg_color = get_color('background')
        text_color = get_color('text')

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                color: {text_color};
            }}
            QLabel {{
                font-size: 8pt;
                color: {text_color};
            }}
        """)

    def update_translations(self):
        # No translation needed for copyright
        pass