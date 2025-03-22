from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from .chat_ui import ChatUI
from .chat_ai import ChatAI


class ChatWidget(QWidget):
    """
    Complete chat widget with UI and AI integration.
    This is the main class to use in your application.
    """
    chat_submitted = pyqtSignal(str)  # For compatibility with existing code

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create UI component
        self.chat_ui = ChatUI(translator)

        # Create AI component
        self.chat_ai = ChatAI()

        # Connect signals
        self.chat_ui.message_sent.connect(self.handle_message)

        # Add UI to layout
        layout.addWidget(self.chat_ui)

        # Add welcome message
        self.chat_ui.add_message(
            f"Hello {self.chat_ai.username}! I'm your AI assistant. How can I help you today?",
            False)

    def handle_message(self, message):
        """Handle a new message from the user"""
        # Forward to any external handlers
        self.chat_submitted.emit(message)

        # Show thinking bubble
        thinking_bubble = self.chat_ui.show_thinking()

        # Process with AI and handle response
        def on_response(response):
            # Remove thinking bubble
            self.chat_ui.remove_bubble(thinking_bubble)

            # Add AI response
            self.chat_ui.add_message(response, False)

        # Process the message
        self.chat_ai.process_message(message, on_response)

    # Forward UI methods to maintain compatibility with existing code
    def update_translations(self):
        """Update translations in the UI"""
        pass  # The chat_ui handles this internally

    def apply_theme(self):
        """Apply theme to the UI"""
        self.chat_ui.apply_theme()