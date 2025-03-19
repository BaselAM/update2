from PyQt5.QtWidgets import QToolButton
from PyQt5.QtCore import Qt


class NotificationButton(QToolButton):
    """Custom notification button with count badge"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.notification_count = 0
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background: transparent;")

    def set_notification_count(self, count):
        """Set notification count and update display"""
        self.notification_count = count
        self.update()

        # Set tooltip to show count
        if count > 0:
            self.setToolTip(f"{count} notification{'s' if count > 1 else ''}")
        else:
            self.setToolTip("No notifications")