from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QSize
from PyQt5.QtWidgets import (
    QWidget, QToolButton, QVBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QSizePolicy
)
from PyQt5.QtGui import QIcon
from pathlib import Path
import time


class ChatBubble(QFrame):
    """Individual chat message bubble"""

    def __init__(self, message, is_user=True, parent=None):
        super().__init__(parent)
        self.setup_ui(message, is_user)

    def setup_ui(self, message, is_user):
        """Set up the chat bubble UI with alignment based on sender"""
        layout = QHBoxLayout(self)

        # Create message container
        message_container = QLabel(message)
        message_container.setWordWrap(True)
        message_container.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # Add spacers and widget to layout based on sender
        if is_user:
            layout.addStretch(1)
            layout.addWidget(message_container)
            self.setObjectName("userMessage")
        else:
            layout.addWidget(message_container)
            layout.addStretch(1)
            self.setObjectName("systemMessage")


class ChatWidget(QWidget):
    """Widget for handling chat functionality in the top bar"""
    chat_submitted = pyqtSignal(str)

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.chat_visible = False
        self.is_expanded = False
        self.setup_ui()

    def setup_ui(self):
        """Create the chat button and expandable chat interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create chat button
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.chat_btn = QToolButton()
        self.chat_btn.setCursor(Qt.PointingHandCursor)
        self.chat_btn.setToolTip(self.translator.t('chat'))
        self.chat_btn.clicked.connect(self.toggle_chat)

        # Add chat icon if available
        chat_icon_path = Path(
            __file__).resolve().parent.parent.parent / "resources/chat_icon.png"
        if chat_icon_path.exists():
            self.chat_btn.setIcon(QIcon(str(chat_icon_path)))
            self.chat_btn.setIconSize(QSize(24, 24))
        else:
            self.chat_btn.setText("💬")
            self.chat_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)

        button_layout.addWidget(self.chat_btn)

        # Create chat container
        self.chat_container = QFrame()
        chat_layout = QVBoxLayout(self.chat_container)
        chat_layout.setContentsMargins(10, 10, 10, 10)

        # Chat header with title and expand/close buttons
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 5)

        chat_title = QLabel(self.translator.t('chat_assistant'))
        chat_title.setAlignment(Qt.AlignCenter)
        chat_title.setStyleSheet("font-weight: bold;")

        # Expand button
        self.expand_btn = QToolButton()
        self.expand_btn.setText("⤢")
        self.expand_btn.setToolTip(self.translator.t('expand_chat'))
        self.expand_btn.clicked.connect(self.toggle_expand)

        # Close button
        close_btn = QToolButton()
        close_btn.setText("✕")
        close_btn.setToolTip(self.translator.t('close'))
        close_btn.clicked.connect(self.toggle_chat)

        header_layout.addWidget(chat_title)
        header_layout.addStretch(1)
        header_layout.addWidget(self.expand_btn)
        header_layout.addWidget(close_btn)

        # Chat messages area (scrollable)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Container for chat bubbles
        messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(messages_widget)
        self.messages_layout.addStretch(1)  # Push messages up

        scroll_area.setWidget(messages_widget)

        # Message input area
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 5, 0, 0)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText(self.translator.t('type_message'))
        self.message_input.returnPressed.connect(self.send_message)

        send_btn = QPushButton()
        send_btn.setText(self.translator.t('send'))
        send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(send_btn)

        # Add everything to chat layout
        chat_layout.addWidget(header_container)
        chat_layout.addWidget(scroll_area, 1)  # Give stretch to the scroll area
        chat_layout.addWidget(input_container)

        # Set initial size and hide chat
        self.chat_container.setMinimumWidth(300)
        self.chat_container.setMinimumHeight(400)
        self.chat_container.hide()

        # Add welcome messages
        self.add_message("Welcome to the chat assistant! How can I help you today?",
                         False)

        # Add widgets to main layout
        layout.addWidget(button_container)
        layout.addWidget(self.chat_container)

        # Animation for expansion
        self.width_animation = QPropertyAnimation(self.chat_container, b"minimumWidth")
        self.width_animation.setDuration(300)
        self.width_animation.setEasingCurve(QEasingCurve.InOutCubic)

        self.height_animation = QPropertyAnimation(self.chat_container, b"minimumHeight")
        self.height_animation.setDuration(300)
        self.height_animation.setEasingCurve(QEasingCurve.InOutCubic)

    def toggle_chat(self):
        """Toggle chat visibility"""
        self.chat_visible = not self.chat_visible

        if self.chat_visible:
            self.chat_container.show()
            self.message_input.setFocus()
        else:
            self.chat_container.hide()

    def toggle_expand(self):
        """Toggle between normal and expanded chat size"""
        self.is_expanded = not self.is_expanded

        if self.is_expanded:
            self.width_animation.setStartValue(300)
            self.width_animation.setEndValue(450)
            self.height_animation.setStartValue(400)
            self.height_animation.setEndValue(550)
            self.expand_btn.setText("⤡")
            self.expand_btn.setToolTip(self.translator.t('collapse_chat'))
        else:
            self.width_animation.setStartValue(450)
            self.width_animation.setEndValue(300)
            self.height_animation.setStartValue(550)
            self.height_animation.setEndValue(400)
            self.expand_btn.setText("⤢")
            self.expand_btn.setToolTip(self.translator.t('expand_chat'))

        self.width_animation.start()
        self.height_animation.start()

    def send_message(self):
        """Send user message and get response"""
        message = self.message_input.text().strip()
        if not message:
            return

        # Add user message
        self.add_message(message, True)

        # Clear input
        self.message_input.clear()

        # Emit signal for external handling
        self.chat_submitted.emit(message)

        # Simulate a response (would be replaced with actual backend call)
        # Just for demonstration purposes
        time.sleep(0.5)  # Simulate processing time
        self.add_message(
            "I received your message. This is a simulated response to demonstrate the chat widget.",
            False)

    def add_message(self, message, is_user=True):
        """Add a chat message bubble"""
        bubble = ChatBubble(message, is_user)
        self.messages_layout.addWidget(bubble)

    def update_translations(self):
        """Update translations for this widget"""
        self.chat_btn.setToolTip(self.translator.t('chat'))
        self.message_input.setPlaceholderText(self.translator.t('type_message'))

    def apply_theme(self):
        """Apply current theme to this widget"""
        from themes import get_color

        self.chat_btn.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                border: none;
                padding: 5px;
            }}
            QToolButton:hover {{
                background-color: {get_color('button_hover')};
                border-radius: 15px;
            }}
        """)

        self.chat_container.setStyleSheet(f"""
            QFrame {{
                background-color: {get_color('card_bg')};
                border: 1px solid {get_color('border')};
                border-radius: 8px;
            }}

            #userMessage {{
                background-color: {get_color('button')};
                color: {get_color('text')};
                border-radius: 15px;
                padding: 8px 12px;
                margin: 2px;
                max-width: 80%;
            }}

            #systemMessage {{
                background-color: {get_color('secondary')};
                color: {get_color('text')};
                border-radius: 15px;
                padding: 8px 12px;
                margin: 2px;
                max-width: 80%;
            }}

            QLineEdit {{
                background-color: {get_color('input_bg')};
                color: {get_color('text')};
                border: 1px solid {get_color('border')};
                border-radius: 15px;
                padding: 8px 12px;
            }}

            QPushButton {{
                background-color: {get_color('highlight')};
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 15px;
            }}

            QPushButton:hover {{
                background-color: {get_color('button_hover')};
            }}
        """)