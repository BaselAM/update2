"""
This file contains a wrapper class that prevents the 'coming soon' message
from appearing when using the chat.
"""

from PyQt5.QtCore import pyqtSignal, QObject


class ChatSignalBlocker(QObject):
    """Dummy signal emitter that doesn't trigger any handlers"""
    chat_submitted = pyqtSignal(str)

    def __init__(self):
        super().__init__()