from datetime import datetime
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
# Change this line in dropdown.py
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel,
    QVBoxLayout, QFrame, QLineEdit, QScrollArea,
    QApplication, QGraphicsDropShadowEffect, QMenu, QAction  # Move the effect here
)
from PyQt5.QtGui import QColor

from themes import get_color
from widgets.utils import is_dark_color


class DropdownChatbox(QWidget):
    """A dropdown chatbox that appears below buttons"""

    popped_out = pyqtSignal()

    def __init__(self, title, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.title = title
        self.parent_widget = parent
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)

        # Set initial size
        self.setMinimumWidth(350)
        self.setMinimumHeight(400)

        self.setup_ui()
        self.apply_theme()

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)  # Thin border

        # Header with title and pop-out button
        header = QFrame()
        header.setObjectName("dropdownHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 5, 10, 5)

        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Pop-out button
        popout_button = QPushButton()
        popout_button.setToolTip("Pop out")
        popout_button.setCursor(Qt.PointingHandCursor)
        popout_button.setFixedSize(28, 28)
        popout_button.setObjectName("popoutButton")
        popout_button.setText("⊞")  # Unicode for maximize icon
        popout_button.clicked.connect(self.emit_popout)
        header_layout.addWidget(popout_button)

        main_layout.addWidget(header)

        # Content area
        content = QFrame()
        content.setObjectName("dropdownContent")
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(5, 5, 5, 5)

        # Scroll area for messages
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setSpacing(8)
        self.scroll_area.setWidget(self.content_widget)
        content_layout.addWidget(self.scroll_area)

        main_layout.addWidget(content, 1)  # 1 = stretch factor

        # Optional footer (can be empty for notification, or have input for chat)
        self.footer = QFrame()
        self.footer.setObjectName("dropdownFooter")
        self.footer_layout = QHBoxLayout(self.footer)
        self.footer_layout.setContentsMargins(10, 5, 10, 5)

        main_layout.addWidget(self.footer)

    def emit_popout(self):
        """Emit signal to pop out to full dialog"""
        self.hide()
        self.popped_out.emit()

    def show_at_button(self, button):
        """Show the dropdown below the button"""
        # Calculate position
        global_pos = button.mapToGlobal(QPoint(0, button.height()))

        # Adjust if near screen edge
        screen = QApplication.desktop().screenGeometry()
        if global_pos.x() + self.width() > screen.width():
            global_pos.setX(screen.width() - self.width())

        # Show with animation
        self.move(global_pos)
        self.show()

        # Animate appearance
        self.setMaximumHeight(0)
        self.animation = QPropertyAnimation(self, b"maximumHeight")
        self.animation.setDuration(200)
        self.animation.setStartValue(0)
        self.animation.setEndValue(400)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.start()

    def add_message(self, message, title=None, is_bot=True, time_str=None,
                    notification_id=None):
        """Add a message to the content area"""
        message_frame = QFrame()
        message_frame.setObjectName("botMessage" if is_bot else "userMessage")

        if notification_id is not None:
            message_frame.setProperty("notification_id", notification_id)

        message_layout = QVBoxLayout(message_frame)
        message_layout.setContentsMargins(10, 5, 10, 5)
        message_layout.setSpacing(3)

        # Add sender label if provided
        if title:
            sender = QLabel(title)
            sender.setObjectName("sender")
            message_layout.addWidget(sender)

        # Message text
        text = QLabel(message)
        text.setWordWrap(True)
        text.setObjectName("messageText")
        message_layout.addWidget(text)

        # Time
        if time_str is None:
            time_str = datetime.now().strftime("%H:%M")

        time_label = QLabel(time_str)
        time_label.setObjectName("timestamp")
        time_label.setAlignment(Qt.AlignRight)
        message_layout.addWidget(time_label)

        self.content_layout.addWidget(message_frame)

        # Scroll to the new message
        QApplication.processEvents()
        self.scroll_area.ensureWidgetVisible(message_frame)

        return message_frame

    def add_center_message(self, message):
        """Add a centered message"""
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)

        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)
        label.setObjectName("centerMessage")
        label.setWordWrap(True)
        center_layout.addWidget(label)

        self.content_layout.addWidget(center_widget)

    def apply_theme(self):
        """Apply current theme to the dropdown"""
        bg_color = get_color('background')
        text_color = get_color('text')
        primary_color = get_color('button')
        secondary_color = get_color('button_hover')
        border_color = get_color('border')

        # Set contrasting colors
        is_dark_bg = is_dark_color(bg_color)

        header_bg = QColor(primary_color).darker(110).name() if is_dark_bg else QColor(
            primary_color).lighter(110).name()
        content_bg = bg_color
        footer_bg = QColor(bg_color).darker(110).name() if is_dark_bg else QColor(
            bg_color).lighter(110).name()

        # For message bubbles
        bot_message_bg = primary_color
        user_message_bg = secondary_color

        # Ensure text has contrast
        bot_text_color = "#FFFFFF" if is_dark_color(bot_message_bg) else "#000000"
        user_text_color = "#FFFFFF" if is_dark_color(user_message_bg) else "#000000"

        self.setStyleSheet(f"""
            DropdownChatbox {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}

            QFrame#dropdownHeader {{
                background-color: {header_bg};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom: 1px solid {border_color};
            }}

            QFrame#dropdownContent {{
                background-color: {content_bg};
            }}

            QFrame#dropdownFooter {{
                background-color: {footer_bg};
                border-top: 1px solid {border_color};
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }}

            QFrame#botMessage, QFrame#userMessage {{
                background-color: {bot_message_bg};
                color: {bot_text_color};
                border-radius: 8px;
                padding: 4px;
                max-width: 300px;
            }}

            QFrame#userMessage {{
                background-color: {user_message_bg};
                color: {user_text_color};
            }}

            QLabel#centerMessage {{
                color: {text_color};
                font-size: 12pt;
                font-style: italic;
                padding: 12px;
            }}

            QLabel#sender {{
                font-weight: bold;
                font-size: 10pt;
                color: {bot_text_color};
            }}

            QLabel#messageText {{
                font-size: 11pt;
                color: {bot_text_color};
            }}

            QLabel#timestamp {{
                font-size: 8pt;
                color: rgba(255, 255, 255, 0.7);
            }}

            QScrollArea {{
                border: none;
                background-color: transparent;
            }}

            QScrollArea > QWidget > QWidget {{
                background-color: transparent;
            }}

            QPushButton#popoutButton {{
                background-color: transparent;
                color: {text_color};
                border: none;
                border-radius: 14px;
            }}

            QPushButton#popoutButton:hover {{
                background-color: rgba(255, 255, 255, 0.2);
            }}

            QPushButton {{
                background-color: {primary_color};
                color: {text_color};
                padding: 5px 10px;
                border-radius: 4px;
            }}

            QPushButton:hover {{
                background-color: {secondary_color};
            }}
        """)


class ChatDropdown(DropdownChatbox):
    """Chat-specific dropdown"""

    def __init__(self, parent=None):
        super().__init__("Chat Assistant", parent)
        self.setup_chat_ui()

    def setup_chat_ui(self):
        # Add coming soon messages
        self.add_message(
            "Hello! I'm your car parts assistant. I'll be available soon to help you find parts and answer questions.",
            title="Car Parts Assistant",
            is_bot=True
        )

        self.add_message(
            "The full chatbot functionality will be available in the next update.",
            title="Car Parts Assistant",
            is_bot=True
        )

        # Add input field (disabled for now)
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setDisabled(True)
        self.footer_layout.addWidget(self.message_input)

        send_button = QPushButton("Send")
        send_button.setDisabled(True)
        send_button.setFixedWidth(60)
        self.footer_layout.addWidget(send_button)


class NotificationDropdown(DropdownChatbox):
    """Notification-specific dropdown"""

    notification_clicked = pyqtSignal(int)  # Signal for when a notification is clicked
    mark_all_read = pyqtSignal()  # Signal for marking all as read

    def __init__(self, parent=None):
        super().__init__("Notifications", parent)

        # Add actions to footer
        self.setup_action_buttons()

    def setup_action_buttons(self):
        """Set up action buttons in the footer"""
        mark_all_button = QPushButton("Mark All Read")
        mark_all_button.setObjectName("markAllButton")
        mark_all_button.clicked.connect(self._handle_mark_all_read)

        manage_button = QPushButton("Manage")
        manage_button.setObjectName("manageButton")
        manage_button.setToolTip("Manage notifications")
        manage_button.clicked.connect(self._show_manage_menu)

        self.footer_layout.addWidget(mark_all_button)
        self.footer_layout.addStretch()
        self.footer_layout.addWidget(manage_button)

    def _handle_mark_all_read(self):
        """Handle marking all as read"""
        self.mark_all_read.emit()
        self.hide()

    def _show_manage_menu(self):
        """Show management options menu"""
        menu = QMenu(self)

        delete_read = QAction("Delete Read Notifications", self)
        delete_read.triggered.connect(self._delete_read)

        delete_all = QAction("Delete All Notifications", self)
        delete_all.triggered.connect(self._delete_all)

        menu.addAction(delete_read)
        menu.addAction(delete_all)

        # Show at button position
        sender = self.sender()
        menu.exec_(sender.mapToGlobal(QPoint(0, -menu.sizeHint().height())))

    def _delete_read(self):
        """Delete all read notifications"""
        # This would normally connect to the database
        pass

    def _delete_all(self):
        """Delete all notifications (dangerous!)"""
        # This would normally connect to the database
        pass

    def show_notifications(self, notifications=None):
        """Show notifications list"""
        # Clear existing content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Show notifications or 'no notifications' message
        if not notifications or len(notifications) == 0:
            self.add_center_message("No notifications at this time")
        else:
            for notification in notifications:
                # Get the notification ID safely
                notif_id = notification.get('id')
                frame = self.add_message(
                    notification.get('message', ''),
                    title=notification.get('title', ''),
                    time_str=notification.get('time', ''),
                    is_bot=True,
                    notification_id=notif_id
                )

                # Make it clickable if we have an ID
                if notif_id is not None:
                    frame.setCursor(Qt.PointingHandCursor)
                    # Fix: Create a click handler with proper variable binding
                    self._make_clickable(frame, notif_id)

    def _make_clickable(self, widget, id_value):
        """Helper to make widget clickable with correct ID binding"""
        widget.mousePressEvent = lambda e, id_val=id_value: self._notification_clicked(
            id_val)

    def _notification_clicked(self, notification_id):
        """Handle notification click event"""
        self.notification_clicked.emit(notification_id)

    def show_notifications_from_db(self, include_read=False):
        """Load and show notifications from database if available"""
        # This method is a placeholder for when database integration is added
        # For now, just show any provided notifications or a placeholder
        if hasattr(self, 'db') and self.db:
            notifications = self.db.get_notifications(include_read=include_read)
            self.show_notifications(notifications)
        else:
            self.add_center_message("Notification database not available")