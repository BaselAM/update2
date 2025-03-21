from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFrame, QSpacerItem, QSizePolicy)
from PyQt5.QtGui import QIcon, QPixmap, QColor
from PyQt5.QtCore import Qt, QSize
from themes import get_color


class ThemedMessageDialog(QDialog):
    """A styled message dialog that replaces standard QMessageBox for better theme integration"""

    def __init__(self, title, message, icon_type="warning", parent=None):
        super().__init__(parent)

        # Set window properties
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)

        # Configure the dialog
        self.setup_ui(title, message, icon_type)
        self.apply_theme()

    def setup_ui(self, title, message, icon_type):
        # Main layout with proper padding
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create a frame to hold everything with proper styling
        self.frame = QFrame()
        self.frame.setObjectName("messageFrame")
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(20, 20, 20, 20)
        frame_layout.setSpacing(15)

        # Header with title and icon
        header_layout = QHBoxLayout()

        # Icon setup based on type
        self.icon_label = QLabel()
        if icon_type == "warning":
            icon_path = "resources/warning_icon.png"
        elif icon_type == "question":
            icon_path = "resources/question_icon.png"
        elif icon_type == "error":
            icon_path = "resources/error_icon.png"
        elif icon_type == "info":
            icon_path = "resources/info_icon.png"
        else:
            icon_path = "resources/warning_icon.png"

        try:
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                self.icon_label.setPixmap(
                    pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                # Fallback to emoji if icon not found
                self.icon_label.setText("⚠️" if icon_type == "warning" else
                                        "❓" if icon_type == "question" else
                                        "❌" if icon_type == "error" else "ℹ️")
                self.icon_label.setStyleSheet("font-size: 24px;")
        except:
            # Fallback to emoji if loading fails
            self.icon_label.setText("⚠️" if icon_type == "warning" else
                                    "❓" if icon_type == "question" else
                                    "❌" if icon_type == "error" else "ℹ️")
            self.icon_label.setStyleSheet("font-size: 24px;")

        self.icon_label.setFixedSize(32, 32)
        header_layout.addWidget(self.icon_label)

        # Title with bold font
        self.title_label = QLabel(title)
        self.title_label.setObjectName("dialogTitle")
        header_layout.addWidget(self.title_label)

        # Add spacer to push everything to the left
        header_layout.addSpacerItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        frame_layout.addLayout(header_layout)

        # Separator line
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)
        self.separator.setObjectName("dialogSeparator")
        frame_layout.addWidget(self.separator)

        # Message text with proper wrapping
        self.message_label = QLabel(message)
        self.message_label.setObjectName("dialogMessage")
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.message_label.setMinimumHeight(50)
        frame_layout.addWidget(self.message_label)

        # Button layout - right aligned
        button_layout = QHBoxLayout()
        button_layout.addSpacerItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Create buttons
        self.yes_button = QPushButton("Yes")
        self.yes_button.setObjectName("primaryButton")
        self.yes_button.setFixedWidth(100)
        self.yes_button.clicked.connect(self.accept)
        self.yes_button.setCursor(Qt.PointingHandCursor)

        self.no_button = QPushButton("No")
        self.no_button.setObjectName("secondaryButton")
        self.no_button.setFixedWidth(100)
        self.no_button.clicked.connect(self.reject)
        self.no_button.setCursor(Qt.PointingHandCursor)

        button_layout.addWidget(self.no_button)
        button_layout.addWidget(self.yes_button)

        frame_layout.addLayout(button_layout)

        # Add the frame to the main layout
        main_layout.addWidget(self.frame)

    def apply_theme(self):
        """Apply theming to the dialog"""
        bg_color = get_color('background')
        text_color = get_color('text')
        border_color = get_color('border')
        highlight_color = get_color('highlight')
        button_color = get_color('button')
        button_hover = get_color('button_hover')
        button_pressed = get_color('button_pressed')

        # Check if it's a dark theme
        is_dark_theme = QColor(bg_color).lightness() < 128
        shadow_color = f"rgba(0, 0, 0, {0.5 if is_dark_theme else 0.2})"

        # Dialog styling with drop shadow
        dialog_style = f"""
            QDialog {{
                background-color: transparent;
            }}

            #messageFrame {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 12px;
                padding: 20px;
            }}

            #dialogTitle {{
                color: {text_color};
                font-size: 18px;
                font-weight: bold;
            }}

            #dialogMessage {{
                color: {text_color};
                font-size: 14px;
                margin: 10px 0;
            }}

            #dialogSeparator {{
                background-color: {border_color};
                height: 1px;
            }}

            #primaryButton {{
                background-color: {highlight_color};
                color: {bg_color if is_dark_theme else "white"};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 14px;
            }}

            #primaryButton:hover {{
                background-color: {QColor(highlight_color).lighter(110).name()};
            }}

            #primaryButton:pressed {{
                background-color: {QColor(highlight_color).darker(110).name()};
            }}

            #secondaryButton {{
                background-color: {button_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }}

            #secondaryButton:hover {{
                background-color: {button_hover};
                border-color: {highlight_color};
            }}

            #secondaryButton:pressed {{
                background-color: {button_pressed};
            }}
        """

        self.setStyleSheet(dialog_style)

        # Apply drop shadow effect
        self.frame.setGraphicsEffect(None)  # Clear any existing effect

        # Set focus to No button by default for safety
        self.no_button.setFocus()

    @staticmethod
    def confirm(title, message, parent=None, icon_type="question"):
        """Static method to create and show the dialog directly"""
        dialog = ThemedMessageDialog(title, message, icon_type, parent)
        result = dialog.exec_()
        return result == QDialog.Accepted