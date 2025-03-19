from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtWidgets import (
    QWidget, QToolButton, QHBoxLayout, QLabel,
    QVBoxLayout, QScrollArea, QFrame
)
from PyQt5.QtGui import QIcon
from pathlib import Path


class NotificationItem(QFrame):
    """Individual notification item"""

    def __init__(self, title, message, timestamp, parent=None):
        super().__init__(parent)
        self.setup_ui(title, message, timestamp)

    def setup_ui(self, title, message, timestamp):
        """Set up the notification item UI"""
        layout = QVBoxLayout(self)

        # Title with bold font
        title_label = QLabel(f"<b>{title}</b>")

        # Message with normal font
        message_label = QLabel(message)
        message_label.setWordWrap(True)

        # Timestamp with smaller gray font
        timestamp_label = QLabel(timestamp)
        timestamp_label.setStyleSheet("color: gray; font-size: 10px;")

        # Add to layout
        layout.addWidget(title_label)
        layout.addWidget(message_label)
        layout.addWidget(timestamp_label)

        # Set frame style
        self.setFrameShape(QFrame.StyledPanel)
        self.setAutoFillBackground(True)


class NotificationsWidget(QWidget):
    """Widget for handling notification functionality in the top bar"""
    notification_clicked = pyqtSignal()

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.notification_count = 0
        self.notifications_visible = False
        self.setup_ui()

    def setup_ui(self):
        """Create the notification button with counter and dropdown"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Top container for button and badge
        top_container = QWidget()
        top_layout = QHBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Notification button
        self.notification_btn = QToolButton()
        self.notification_btn.setCursor(Qt.PointingHandCursor)
        self.notification_btn.setToolTip(self.translator.t('notifications'))
        self.notification_btn.clicked.connect(self.toggle_notifications)

        # Add notification icon if available
        notification_icon_path = Path(
            __file__).resolve().parent.parent.parent / "resources/notification_icon.png"
        if notification_icon_path.exists():
            self.notification_btn.setIcon(QIcon(str(notification_icon_path)))
            self.notification_btn.setIconSize(QSize(24, 24))
        else:
            self.notification_btn.setText("🔔")
            self.notification_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)

        # Badge for notification count
        self.notification_badge = QLabel("0")
        self.notification_badge.setAlignment(Qt.AlignCenter)
        self.notification_badge.setMaximumSize(16, 16)
        self.notification_badge.setMinimumSize(16, 16)
        self.notification_badge.hide()

        # Add to top layout
        top_layout.addWidget(self.notification_btn)

        # Notifications dropdown container
        self.dropdown_container = QFrame()
        dropdown_layout = QVBoxLayout(self.dropdown_container)

        # Scroll area for notifications
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)
        scroll_area.setMinimumWidth(300)

        # Notification content widget
        notifications_widget = QWidget()
        self.notifications_layout = QVBoxLayout(notifications_widget)

        # Add some example notifications
        self.add_notification("New Products", "5 new products have been added",
                              "Today, 10:45 AM")
        self.add_notification("Low Stock Alert", "Oil filters are running low",
                              "Yesterday, 3:20 PM")

        scroll_area.setWidget(notifications_widget)
        dropdown_layout.addWidget(scroll_area)

        # Add a "See all" button
        see_all_btn = QToolButton()
        see_all_btn.setText(self.translator.t('see_all_notifications'))
        see_all_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
        see_all_btn.clicked.connect(self.notification_clicked)
        dropdown_layout.addWidget(see_all_btn)

        # Hide dropdown initially
        self.dropdown_container.hide()

        # Add to main layout
        layout.addWidget(top_container)
        layout.addWidget(self.dropdown_container)

    def toggle_notifications(self):
        """Toggle visibility of notifications dropdown"""
        self.notifications_visible = not self.notifications_visible

        if self.notifications_visible:
            self.dropdown_container.show()
            # Reset notification count when opened
            self.set_notification_count(0)
        else:
            self.dropdown_container.hide()

    def add_notification(self, title, message, timestamp):
        """Add a new notification item to the list"""
        notification = NotificationItem(title, message, timestamp)
        self.notifications_layout.addWidget(notification)

        # Increment notification count
        self.set_notification_count(self.notification_count + 1)

    def set_notification_count(self, count):
        """Update the notification count and badge visibility"""
        self.notification_count = count

        if count > 0:
            self.notification_badge.setText(str(count) if count < 10 else "9+")
            self.notification_badge.show()
        else:
            self.notification_badge.hide()

    def update_translations(self):
        """Update translations for this widget"""
        self.notification_btn.setToolTip(self.translator.t('notifications'))

    def apply_theme(self):
        """Apply current theme to this widget"""
        from themes import get_color

        self.notification_btn.setStyleSheet(f"""
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

        self.notification_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {get_color('error')};
                color: white;
                border-radius: 8px;
                font-size: 10px;
                font-weight: bold;
            }}
        """)

        self.dropdown_container.setStyleSheet(f"""
            QFrame {{
                background-color: {get_color('card_bg')};
                border: 1px solid {get_color('border')};
                border-radius: 8px;
            }}
        """)