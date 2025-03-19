from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt5.QtWidgets import (
    QWidget, QToolButton, QVBoxLayout,
    QLineEdit, QPushButton, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QDialog, QApplication,
    QGraphicsDropShadowEffect, QStyleOption, QStyle
)
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor, QPainter
from pathlib import Path
import themes


def is_dark_theme():
    """Determine if the current theme is dark based on background color"""
    bg_color = themes.get_color('card_bg')
    bg_color = bg_color.lstrip('#')
    r, g, b = tuple(int(bg_color[i:i + 2], 16) for i in (0, 2, 4))
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return brightness < 128


class ModernChatBubble(QFrame):
    """Modern chat message bubble"""

    def __init__(self, message, is_user=True, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.setup_ui(message)
        self.apply_theme()

    def setup_ui(self, message):
        """Set up the chat bubble UI with modern styling"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)

        # Create message label
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        self.message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # Modern font
        font = QFont("Segoe UI", 10)
        self.message_label.setFont(font)
        self.message_label.setMinimumWidth(150)

        # Add contents to layout
        if self.is_user:
            layout.addStretch(1)
            layout.addWidget(self.message_label)
            self.setObjectName("userMessage")
        else:
            # Avatar for system messages
            self.avatar_label = QLabel()
            avatar_path = Path(
                __file__).resolve().parent.parent.parent / "resources/chatbot.png"
            if avatar_path.exists():
                avatar_pixmap = QPixmap(str(avatar_path)).scaled(22, 22,
                                                                 Qt.KeepAspectRatio,
                                                                 Qt.SmoothTransformation)
                self.avatar_label.setPixmap(avatar_pixmap)
            else:
                self.avatar_label.setText("🤖")

            self.avatar_label.setFixedSize(22, 22)
            layout.addWidget(self.avatar_label)
            layout.addWidget(self.message_label)
            layout.addStretch(1)
            self.setObjectName("systemMessage")

        # Subtle shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)

    def apply_theme(self):
        """Apply modern theme styling"""
        dark_mode = is_dark_theme()

        if self.is_user:
            if dark_mode:
                # Modern blue for user in dark theme
                bubble_color = "#2979FF"  # Bright blue
                text_color = "#FFFFFF"  # White text
            else:
                # Modern blue for light theme
                bubble_color = "#2962FF"  # Slightly darker blue
                text_color = "#FFFFFF"  # White text
        else:
            if dark_mode:
                # Subtle dark blue-gray for system in dark theme
                bubble_color = "#1E2334"  # Dark blue-gray
                text_color = "#E0E0FF"  # Light blue-ish text
            else:
                # Light gray for system in light theme
                bubble_color = "#F4F6F8"  # Very light gray
                text_color = "#36454F"  # Charcoal text

        self.setStyleSheet(f"""
            QFrame#{self.objectName()} {{
                background-color: {bubble_color};
                border-radius: 18px;
            }}

            QLabel {{
                color: {text_color};
                background-color: transparent;
                padding: 4px;
            }}
        """)


class ChatWidget(QWidget):
    """Modern chat widget with clean design"""
    chat_submitted = pyqtSignal(str)

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.chat_visible = False
        self.is_expanded = False
        self.is_popped_out = False
        self.movable_window = None
        self.setup_ui()

    def setup_ui(self):
        """Create the chat button and modern chat interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create chat button with modern styling
        self.chat_btn = QToolButton()
        self.chat_btn.setCursor(Qt.PointingHandCursor)
        self.chat_btn.setToolTip(self.translator.t('chat'))
        self.chat_btn.clicked.connect(self.toggle_chat)

        # Add chat icon
        chat_icon_path = Path(
            __file__).resolve().parent.parent.parent / "resources/chatbot.png"
        if chat_icon_path.exists():
            self.chat_btn.setIcon(QIcon(str(chat_icon_path)))
            self.chat_btn.setIconSize(QSize(26, 26))
        else:
            self.chat_btn.setText("💬")
            self.chat_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)

        # Make button appropriately sized
        self.chat_btn.setMinimumSize(40, 40)

        # Create clean chat container with popup behavior
        self.chat_container = QFrame()
        self.chat_container.setObjectName("chatContainer")
        self.chat_container.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.chat_container.setAttribute(Qt.WA_TranslucentBackground)

        # Add shadow to the container
        container_shadow = QGraphicsDropShadowEffect()
        container_shadow.setBlurRadius(20)
        container_shadow.setOffset(0, 4)
        container_shadow.setColor(QColor(0, 0, 0, 40))
        self.chat_container.setGraphicsEffect(container_shadow)

        # Container layout with small margins
        container_layout = QVBoxLayout(self.chat_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Inner content frame
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")

        # Modern content layout
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Chat header with title and buttons
        header_container = QWidget()
        header_container.setObjectName("chatHeader")
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(15, 10, 15, 10)

        # Add avatar in header
        header_avatar = QLabel()
        if chat_icon_path.exists():
            avatar_pixmap = QPixmap(str(chat_icon_path)).scaled(22, 22,
                                                                Qt.KeepAspectRatio,
                                                                Qt.SmoothTransformation)
            header_avatar.setPixmap(avatar_pixmap)

        chat_title = QLabel(self.translator.t('chat_assistant'))
        font = QFont("Segoe UI", 11)
        font.setBold(True)
        chat_title.setFont(font)
        chat_title.setObjectName("chatTitle")

        # Expand button
        self.expand_btn = QToolButton()
        self.expand_btn.setText("⤢")  # Unicode expand symbol
        self.expand_btn.setObjectName("expandButton")
        self.expand_btn.setToolTip(self.translator.t('expand_chat'))
        self.expand_btn.setCursor(Qt.PointingHandCursor)
        self.expand_btn.clicked.connect(self.toggle_expand)

        # Pop-out button
        self.popout_btn = QToolButton()
        self.popout_btn.setText("⊙")  # Unicode circle symbol
        self.popout_btn.setObjectName("popoutButton")
        self.popout_btn.setToolTip(self.translator.t('popout_chat'))
        self.popout_btn.setCursor(Qt.PointingHandCursor)
        self.popout_btn.clicked.connect(self.pop_out_chat)

        # Close button
        close_btn = QToolButton()
        close_btn.setText("✕")
        close_btn.setObjectName("closeButton")
        close_btn.setToolTip(self.translator.t('close'))
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.toggle_chat)

        header_layout.addWidget(header_avatar)
        header_layout.addWidget(chat_title)
        header_layout.addStretch(1)
        header_layout.addWidget(self.popout_btn)
        header_layout.addWidget(self.expand_btn)
        header_layout.addWidget(close_btn)

        # Chat messages area with minimal styling
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setObjectName("chatScroll")
        scroll_area.setFrameShape(QFrame.NoFrame)  # Remove any frame

        # Container for chat bubbles
        messages_widget = QWidget()
        messages_widget.setObjectName("messagesContainer")
        self.messages_layout = QVBoxLayout(messages_widget)
        self.messages_layout.setSpacing(12)
        self.messages_layout.setContentsMargins(15, 15, 15, 15)
        self.messages_layout.addStretch(1)  # Push messages up

        scroll_area.setWidget(messages_widget)

        # Message input area with modern styling
        input_container = QWidget()
        input_container.setObjectName("inputContainer")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(15, 15, 15, 15)
        input_layout.setSpacing(10)

        self.message_input = QLineEdit()
        self.message_input.setObjectName("messageInput")
        self.message_input.setPlaceholderText(self.translator.t('type_message'))
        self.message_input.returnPressed.connect(self.send_message)
        self.message_input.setFixedHeight(38)  # Taller input for modern look

        send_btn = QPushButton()
        send_btn.setText(self.translator.t('send'))
        send_btn.setObjectName("sendButton")
        send_btn.setFixedSize(70, 38)
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(send_btn)

        # Add everything to content layout
        content_layout.addWidget(header_container)
        content_layout.addWidget(scroll_area, 1)  # Give stretch to the scroll area
        content_layout.addWidget(input_container)

        # Add the content frame to the container
        container_layout.addWidget(content_frame)

        # Set fixed size for the popup
        self.chat_container.setFixedWidth(320)
        self.chat_container.setFixedHeight(420)

        # Add welcome messages
        self.add_message("Welcome! How can I help you today?", False)

        # Add button to main layout
        layout.addWidget(self.chat_btn)

        # Apply theme
        self.apply_theme()

    def toggle_chat(self):
        """Toggle chat visibility"""
        self.chat_visible = not self.chat_visible

        if self.chat_visible:
            # Position the popup near the button
            btn_global_pos = self.chat_btn.mapToGlobal(QPoint(0, self.chat_btn.height()))

            # Calculate position to make sure it's visible
            screen = QApplication.desktop().screenGeometry()
            x = min(btn_global_pos.x(), screen.width() - self.chat_container.width() - 20)
            x = max(20, x)

            self.chat_container.move(x, btn_global_pos.y() + 5)
            self.chat_container.show()
            self.message_input.setFocus()
        else:
            self.chat_container.hide()

    def toggle_expand(self):
        """Toggle between normal and expanded chat size"""
        self.is_expanded = not self.is_expanded

        if self.is_expanded:
            self.chat_container.setFixedWidth(400)
            self.chat_container.setFixedHeight(500)
            self.expand_btn.setText("⤡")  # Unicode collapse symbol
            self.expand_btn.setToolTip(self.translator.t('collapse_chat'))
        else:
            self.chat_container.setFixedWidth(320)
            self.chat_container.setFixedHeight(420)
            self.expand_btn.setText("⤢")  # Unicode expand symbol
            self.expand_btn.setToolTip(self.translator.t('expand_chat'))

    def pop_out_chat(self):
        """Create a movable chat window"""
        # Hide the embedded chat first
        self.chat_container.hide()
        self.chat_visible = False

        # Create a simple dialog for now
        dialog = QDialog()
        dialog.setWindowTitle("Chat")
        dialog.resize(350, 450)
        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(20, 20, 20, 20)

        # Add content
        label = QLabel(
            "This is a movable chat window.\nYou can drag it anywhere on your screen.")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 12pt; margin: 20px;")
        dialog_layout.addWidget(label)

        # Apply theme
        self.apply_theme_to_dialog(dialog)

        dialog.exec_()

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

        # Simple response for demonstration
        response = "I'll help you with that request!"
        self.add_message(response, False)

    def add_message(self, message, is_user=True):
        """Add a chat message bubble"""
        bubble = ModernChatBubble(message, is_user)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)

    def update_translations(self):
        """Update translations for this widget"""
        self.chat_btn.setToolTip(self.translator.t('chat'))
        self.message_input.setPlaceholderText(self.translator.t('type_message'))
        self.expand_btn.setToolTip(self.translator.t('expand_chat'))
        self.popout_btn.setToolTip(self.translator.t('popout_chat'))

    def apply_theme(self):
        """Apply modern theme styling"""
        # Determine if we're in dark mode
        dark_mode = is_dark_theme()

        # Define blue accent colors (dim blue as requested)
        if dark_mode:
            accent_color = "#3949AB"  # Indigo blue for dark theme
            accent_hover = "#5C6BC0"  # Lighter indigo for hover
            button_text = "#FFFFFF"
        else:
            accent_color = "#3F51B5"  # Standard indigo for light theme
            accent_hover = "#5C6BC0"  # Lighter indigo for hover
            button_text = "#FFFFFF"

        # Get theme colors
        bg_color = themes.get_color('card_bg')
        text_color = themes.get_color('text')
        input_bg = themes.get_color('input_bg')

        # Button style - blue instead of yellow when pressed/hovered
        self.chat_btn.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                border: none;
                padding: 6px;
            }}
            QToolButton:hover {{
                background-color: {accent_color}40;
                border-radius: 20px;
            }}
            QToolButton:pressed {{
                background-color: {accent_color}70;
                border-radius: 20px;
            }}
        """)

        # Modern clean container style
        self.chat_container.setStyleSheet(f"""
            QFrame#chatContainer {{
                background-color: transparent;
                border: none;
            }}

            QFrame#contentFrame {{
                background-color: {bg_color};
                border-radius: 10px;
                border: none;
            }}

            #chatHeader {{
                background-color: {accent_color};
                color: {button_text};
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }}

            #chatTitle {{
                color: {button_text};
                font-weight: bold;
            }}

            #expandButton, #popoutButton, #closeButton {{
                background-color: transparent;
                color: {button_text};
                border: none;
                padding: 3px;
                border-radius: 4px;
            }}

            #expandButton:hover, #popoutButton:hover, #closeButton:hover {{
                background-color: {accent_hover};
            }}

            #chatScroll {{
                border: none;
                background-color: transparent;
            }}

            QScrollBar:vertical {{
                background-color: transparent;
                width: 8px;
                margin: 0px;
            }}

            QScrollBar::handle:vertical {{
                background-color: {accent_color}50;
                min-height: 20px;
                border-radius: 4px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {accent_color}80;
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            #messagesContainer {{
                background-color: transparent;
            }}

            #inputContainer {{
                background-color: {bg_color};
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }}

            #messageInput {{
                background-color: {input_bg};
                color: {text_color};
                border: none;
                border-radius: 19px;
                padding: 8px 15px;
                font-size: 10pt;
            }}

            #messageInput:focus {{
                border: 1px solid {accent_color};
            }}

            #sendButton {{
                background-color: {accent_color};
                color: white;
                border: none;
                border-radius: 19px;
                padding: 5px 10px;
                font-size: 10pt;
                font-weight: bold;
            }}

            #sendButton:hover {{
                background-color: {accent_hover};
            }}
        """)

    def apply_theme_to_dialog(self, dialog):
        """Apply modern theme to the pop-out dialog"""
        bg_color = themes.get_color('card_bg')
        text_color = themes.get_color('text')

        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                border-radius: 10px;
            }}
            QLabel {{
                color: {text_color};
            }}
        """)