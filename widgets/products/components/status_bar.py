from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize, QTimer

class StatusBar(QFrame):
    """Status bar for displaying operation results and info"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("productsContainer")  # Added for CSS styling
        self.setMaximumHeight(40)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)

        self.status_icon = QLabel()
        self.status_icon.setFixedSize(24, 24)
        self.status_text = QLabel()
        self.status_text.setWordWrap(True)
        self.current_type = "info"

        layout.addWidget(self.status_icon)
        layout.addWidget(self.status_text, 1)

        # Add clear button
        self.clear_btn = QPushButton()
        self.clear_btn.setIcon(QIcon("resources/close_icon.png"))
        self.clear_btn.setIconSize(QSize(12, 12))
        self.clear_btn.setFixedSize(20, 20)
        self.clear_btn.setStyleSheet("background: transparent; border: none;")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear)
        layout.addWidget(self.clear_btn)

        self.hide()  # Start hidden

    def show_message(self, message, message_type="info"):
        """Display a status message with icon"""
        self.status_text.setText(message)
        self.current_type = message_type

        # Set icon based on message type
        icon_map = {
            "info": "resources/info_icon.png",
            "success": "resources/success_icon.png",
            "error": "resources/error_icon.png",
            "warning": "resources/warning_icon.png"
        }

        # Use default info icon if type not recognized
        icon_path = icon_map.get(message_type, icon_map["info"])
        self.status_icon.setPixmap(QPixmap(icon_path).scaled(24, 24, Qt.KeepAspectRatio,
                                                           Qt.SmoothTransformation))

        # Auto-hide after 5 seconds for success messages
        self.show()
        if message_type == "success":
            QTimer.singleShot(5000, self.clear)

    def clear(self):
        """Clear and hide the status bar"""
        self.status_text.clear()
        self.hide()