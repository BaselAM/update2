from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt5.QtWidgets import (
    QWidget, QToolButton, QHBoxLayout, QLabel,
    QVBoxLayout, QScrollArea, QFrame, QPushButton,
    QDialog, QApplication, QGraphicsDropShadowEffect,
    QMenu
)
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor
from pathlib import Path
import themes
from database.notification_db import NotificationDatabaseConnector
import os
from datetime import datetime


def is_dark_theme():
    """Determine if the current theme is dark based on background color"""
    bg_color = themes.get_color('card_bg')
    bg_color = bg_color.lstrip('#')
    r, g, b = tuple(int(bg_color[i:i + 2], 16) for i in (0, 2, 4))
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return brightness < 128


def format_timestamp(db_timestamp):
    """Format database timestamp into a human-readable string"""
    try:
        # Parse the timestamp string into a datetime object
        dt = datetime.strptime(db_timestamp, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        delta = now - dt

        if delta.days == 0:
            # Today
            if delta.seconds < 3600:
                # Less than an hour ago
                minutes = delta.seconds // 60
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            else:
                # Hours ago
                return dt.strftime("Today, %I:%M %p")
        elif delta.days == 1:
            # Yesterday
            return dt.strftime("Yesterday, %I:%M %p")
        elif delta.days < 7:
            # This week
            return dt.strftime("%A, %I:%M %p")
        else:
            # Older
            return dt.strftime("%b %d, %Y")
    except Exception:
        # If any error occurs, return the original timestamp
        return db_timestamp


class ModernNotificationItem(QFrame):
    """Modern styled notification item with database integration"""
    clicked = pyqtSignal(int)  # Signal emitted when notification is clicked

    def __init__(self, notification_data, parent=None):
        super().__init__(parent)
        self.notification_id = notification_data['id']
        self.is_read = bool(notification_data['is_read'])
        self.setup_ui(notification_data)
        self.apply_theme()

    def setup_ui(self, data):
        """Set up the notification item UI with modern styling"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(5)

        # Extract data from dictionary
        title = data['title']
        message = data['message']
        timestamp = format_timestamp(data['timestamp'])
        priority = data.get('priority', 'normal')
        category = data.get('category', '')

        # Title with icon in a horizontal layout
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)

        # Add icon based on category or priority
        icon_label = QLabel()
        icon_path = self.get_icon_for_notification(category, priority)
        if icon_path:
            icon_pixmap = QPixmap(str(icon_path)).scaled(16, 16, Qt.KeepAspectRatio,
                                                         Qt.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)
            icon_label.setFixedSize(18, 18)
            header.addWidget(icon_label)

        # Title with bold font
        title_label = QLabel(title)
        title_font = QFont("Segoe UI", 10)
        title_font.setBold(True)
        title_label.setFont(title_font)

        header.addWidget(title_label)
        header.addStretch(1)

        # Unread indicator
        if not self.is_read:
            unread_indicator = QLabel("•")
            unread_indicator.setObjectName("unreadIndicator")
            unread_indicator.setFixedWidth(15)
            unread_indicator.setAlignment(Qt.AlignCenter)
            header.addWidget(unread_indicator)

        # Message with normal font
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_font = QFont("Segoe UI", 9)
        message_label.setFont(message_font)

        # Timestamp with smaller gray font
        timestamp_label = QLabel(timestamp)
        timestamp_label.setAlignment(Qt.AlignRight)
        timestamp_font = QFont("Segoe UI", 8)
        timestamp_label.setFont(timestamp_font)
        timestamp_label.setObjectName("timestampLabel")

        # Category label if available
        if category:
            category_label = QLabel(category.capitalize())
            category_label.setObjectName(f"category_{category}")
            category_label.setFixedHeight(22)
            category_label.setAlignment(Qt.AlignCenter)

            # Create a container for timestamp and category
            bottom_container = QHBoxLayout()
            bottom_container.addWidget(category_label)
            bottom_container.addStretch(1)
            bottom_container.addWidget(timestamp_label)

            # Add all elements to layout
            layout.addLayout(header)
            layout.addWidget(message_label)
            layout.addLayout(bottom_container)
        else:
            # Add basic elements
            layout.addLayout(header)
            layout.addWidget(message_label)
            layout.addWidget(timestamp_label)

        # Make the frame clickable to mark as read
        self.setCursor(Qt.PointingHandCursor)

        # Add subtle shadow for depth
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 25))
        self.setGraphicsEffect(shadow)

    def get_icon_for_notification(self, category, priority):
        """Return appropriate icon path based on category and priority"""
        resources_dir = Path(__file__).resolve().parent.parent.parent / "resources"

        # Check priority first
        if priority == "high" and (resources_dir / "danger.png").exists():
            return resources_dir / "danger.png"

        # Then check category
        if category == "system" and (resources_dir / "system.png").exists():
            return resources_dir / "system.png"
        elif category == "inventory" and (resources_dir / "inventory.png").exists():
            return resources_dir / "inventory.png"
        elif category == "sales" and (resources_dir / "sales.png").exists():
            return resources_dir / "sales.png"

        # Default icon
        if (resources_dir / "notification.png").exists():
            return resources_dir / "notification.png"

        return None

    def apply_theme(self):
        """Apply modern theme styling"""
        dark_mode = is_dark_theme()

        # Different styling based on read/unread status
        if self.is_read:
            if dark_mode:
                bg_color = "#1A1D2E"  # Darker blue-gray for read items
                text_color = "#CCCCCC"  # Lighter gray
                timestamp_color = "#707080"  # More muted gray-blue
            else:
                bg_color = "#E8EAED"  # Lighter gray for read items
                text_color = "#5F6368"  # Medium gray
                timestamp_color = "#80868B"  # Gray
        else:
            if dark_mode:
                bg_color = "#1E2334"  # Standard dark blue-gray
                text_color = "#FFFFFF"  # White
                timestamp_color = "#A0A0B0"  # Light gray-blue
            else:
                bg_color = "#F4F6F8"  # Light gray
                text_color = "#36454F"  # Charcoal
                timestamp_color = "#90A4AE"  # Blue-gray

        # Accent color for unread indicator
        accent_color = "#3F51B5" if not dark_mode else "#5C6BC0"

        self.setStyleSheet(f"""
            ModernNotificationItem {{
                background-color: {bg_color};
                border-radius: 8px;
            }}

            QLabel {{
                color: {text_color};
                background-color: transparent;
            }}

            #unreadIndicator {{
                color: {accent_color};
                font-size: 20pt;
                font-weight: bold;
            }}

            #timestampLabel {{
                color: {timestamp_color};
                font-size: 8pt;
            }}

            #category_system {{
                background-color: #26A69980;
                color: {'white' if dark_mode else '#333'};
                border-radius: 11px;
                padding: 2px 8px;
                font-size: 8pt;
            }}

            #category_inventory {{
                background-color: #5C6BC080;
                color: {'white' if dark_mode else '#333'};
                border-radius: 11px;
                padding: 2px 8px;
                font-size: 8pt;
            }}

            #category_sales {{
                background-color: #66BB6A80;
                color: {'white' if dark_mode else '#333'};
                border-radius: 11px;
                padding: 2px 8px;
                font-size: 8pt;
            }}
        """)

    def mousePressEvent(self, event):
        """Handle click events on the notification"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.notification_id)
        super().mousePressEvent(event)


class BadgeButton(QWidget):
    """Button with a notification badge overlay"""

    def __init__(self, icon_path, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.setup_ui(icon_path)
        # Define a default accent color
        self.accent_color = "#3F51B5"  # Default indigo
        self.apply_theme()

    def setup_ui(self, icon_path):
        """Create a button with a badge"""
        self.setFixedSize(40, 40)

        # Create the main button
        self.button = QToolButton(self)
        self.button.setFixedSize(40, 40)
        self.button.setCursor(Qt.PointingHandCursor)
        self.button.setToolTip(self.translator.t('notifications'))

        # Add notification icon
        if Path(icon_path).exists():
            self.button.setIcon(QIcon(str(icon_path)))
            self.button.setIconSize(QSize(26, 26))
        else:
            self.button.setText("🔔")
            self.button.setToolButtonStyle(Qt.ToolButtonTextOnly)

        # Create badge label with absolute positioning
        self.badge = QLabel(self)
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setFixedSize(16, 16)
        self.badge.move(25, 3)  # Position in the top-right corner
        self.badge.setText("0")
        self.badge.setObjectName("notificationBadge")
        self.badge.hide()

    def set_count(self, count):
        """Update the badge count and visibility"""
        if count > 0:
            self.badge.setText(str(count) if count < 10 else "9+")
            self.badge.show()
        else:
            self.badge.hide()

    def apply_theme(self, accent_color=None):
        """Apply modern theme styling"""
        # Use provided accent color or fall back to default
        if accent_color:
            self.accent_color = accent_color

        self.button.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                border: none;
                padding: 6px;
            }}
            QToolButton:hover {{
                background-color: {self.accent_color}40;
                border-radius: 20px;
            }}
            QToolButton:pressed {{
                background-color: {self.accent_color}70;
                border-radius: 20px;
            }}
        """)

        self.badge.setStyleSheet("""
            QLabel#notificationBadge {
                background-color: #F44336;
                color: white;
                border-radius: 8px;
                font-size: 9px;
                font-weight: bold;
            }
        """)


class NotificationsWidget(QWidget):
    """Widget for handling notification functionality with database integration"""
    notification_clicked = pyqtSignal()

    def __init__(self, translator, parent=None, username=None):
        super().__init__(parent)
        self.translator = translator
        self.username = username or os.getenv('USERNAME', 'default_user')
        self.notification_count = 0
        self.notifications_visible = False
        self.is_expanded = False
        self.is_popped_out = False
        self.movable_window = None

        # Initialize database connector
        self.db = NotificationDatabaseConnector()

        # Set up UI
        self.setup_ui()

        # Load notifications from database
        self.load_notifications()

    def set_current_user(self, username):
        """Update the current username and reload notifications"""
        self.username = username
        self.load_notifications()

    def setup_ui(self):
        """Create the notification button and modern dropdown"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create badge button
        icon_path = str(
            Path(__file__).resolve().parent.parent.parent / "resources/notification.png")
        fallback_icon_path = str(
            Path(__file__).resolve().parent.parent.parent / "resources/danger.png")

        # Use fallback if main icon doesn't exist
        if not os.path.exists(icon_path) and os.path.exists(fallback_icon_path):
            icon_path = fallback_icon_path

        self.badge_button = BadgeButton(icon_path, self.translator)
        self.badge_button.button.clicked.connect(self.toggle_notifications)

        # Add right-click context menu
        self.badge_button.button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.badge_button.button.customContextMenuRequested.connect(
            self.show_context_menu)

        # Create container for notifications popup
        self.dropdown_container = QFrame()
        self.dropdown_container.setObjectName("notificationsContainer")
        self.dropdown_container.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.dropdown_container.setAttribute(Qt.WA_TranslucentBackground)

        # Add shadow to the container
        container_shadow = QGraphicsDropShadowEffect()
        container_shadow.setBlurRadius(20)
        container_shadow.setOffset(0, 4)
        container_shadow.setColor(QColor(0, 0, 0, 40))
        self.dropdown_container.setGraphicsEffect(container_shadow)

        # Container layout
        container_layout = QVBoxLayout(self.dropdown_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Inner content frame
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")

        # Content layout
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Header for notifications
        header_container = QWidget()
        header_container.setObjectName("notificationHeader")
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(15, 10, 15, 10)

        # Add title with icon
        icon_label = QLabel()
        if icon_path and os.path.exists(icon_path):
            icon_pixmap = QPixmap(icon_path).scaled(22, 22, Qt.KeepAspectRatio,
                                                    Qt.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)

        title = QLabel(self.translator.t('notifications'))
        title_font = QFont("Segoe UI", 11)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setObjectName("notificationTitle")

        # User label (shows current user)
        self.user_label = QLabel(f"({self.username})")
        self.user_label.setObjectName("userLabel")

        # Add buttons
        # Pop-out button
        self.popout_btn = QToolButton()
        self.popout_btn.setText("⊙")  # Unicode circle symbol
        self.popout_btn.setObjectName("popoutButton")
        self.popout_btn.setToolTip(self.translator.t('popout_notifications'))
        self.popout_btn.setCursor(Qt.PointingHandCursor)
        self.popout_btn.clicked.connect(self.pop_out_notifications)

        # Mark all as read button
        self.mark_read_btn = QToolButton()
        self.mark_read_btn.setText("✓")  # Unicode checkmark
        self.mark_read_btn.setObjectName("markReadButton")
        self.mark_read_btn.setToolTip(self.translator.t('mark_all_read'))
        self.mark_read_btn.setCursor(Qt.PointingHandCursor)
        self.mark_read_btn.clicked.connect(self.mark_all_as_read)

        # Expand button
        self.expand_btn = QToolButton()
        self.expand_btn.setText("⤢")  # Unicode expand symbol
        self.expand_btn.setObjectName("expandButton")
        self.expand_btn.setToolTip(self.translator.t('expand'))
        self.expand_btn.setCursor(Qt.PointingHandCursor)
        self.expand_btn.clicked.connect(self.toggle_expand)

        # Close button
        close_btn = QToolButton()
        close_btn.setText("✕")
        close_btn.setObjectName("closeButton")
        close_btn.setToolTip(self.translator.t('close'))
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.toggle_notifications)

        # Add all header elements
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title)
        header_layout.addWidget(self.user_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.mark_read_btn)
        header_layout.addWidget(self.popout_btn)
        header_layout.addWidget(self.expand_btn)
        header_layout.addWidget(close_btn)

        # Notification content area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setObjectName("notificationScroll")
        scroll_area.setFrameShape(QFrame.NoFrame)  # Remove any frame

        # Container for notification items
        self.notifications_widget = QWidget()
        self.notifications_widget.setObjectName("notificationsContainer")
        self.notifications_layout = QVBoxLayout(self.notifications_widget)
        self.notifications_layout.setSpacing(10)
        self.notifications_layout.setContentsMargins(15, 15, 15, 15)

        scroll_area.setWidget(self.notifications_widget)

        # No notifications message (hidden by default)
        self.no_notifications_label = QLabel("No notifications")
        self.no_notifications_label.setAlignment(Qt.AlignCenter)
        self.no_notifications_label.setObjectName("noNotificationsLabel")
        self.no_notifications_label.hide()

        # "See all" button area
        button_container = QWidget()
        button_container.setObjectName("buttonContainer")
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(15, 15, 15, 15)

        see_all_btn = QPushButton(self.translator.t('see_all_notifications'))
        see_all_btn.setObjectName("seeAllButton")
        see_all_btn.setCursor(Qt.PointingHandCursor)
        see_all_btn.clicked.connect(self.notification_clicked)

        refresh_btn = QPushButton(self.translator.t('refresh'))
        refresh_btn.setObjectName("refreshButton")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.load_notifications)

        button_layout.addWidget(refresh_btn)
        button_layout.addStretch(1)
        button_layout.addWidget(see_all_btn)

        # Add everything to content layout
        content_layout.addWidget(header_container)
        content_layout.addWidget(self.no_notifications_label)
        content_layout.addWidget(scroll_area, 1)
        content_layout.addWidget(button_container)

        # Add content frame to container
        container_layout.addWidget(content_frame)

        # Set size for the popup
        self.dropdown_container.setFixedWidth(320)
        self.dropdown_container.setFixedHeight(420)

        # Add badge button to main layout
        layout.addWidget(self.badge_button)

        # Apply theme
        self.apply_theme()

    def show_context_menu(self, pos):
        """Show context menu for notification button"""
        menu = QMenu(self)

        refresh_action = menu.addAction("Refresh Notifications")
        mark_all_read_action = menu.addAction("Mark All as Read")
        add_test_action = menu.addAction("Add Sample Notifications")

        # Add divider
        menu.addSeparator()

        # About action
        about_action = menu.addAction("About Notifications")

        # Show the menu
        action = menu.exec_(self.badge_button.button.mapToGlobal(pos))

        # Handle actions
        if action == refresh_action:
            self.load_notifications()
        elif action == mark_all_read_action:
            self.mark_all_as_read()
        elif action == add_test_action:
            self.add_sample_notifications()
        elif action == about_action:
            self.show_about_dialog()

    def show_about_dialog(self):
        """Show information about the notification system"""
        dialog = QDialog(self)
        dialog.setWindowTitle("About Notifications")
        dialog.resize(300, 200)

        layout = QVBoxLayout(dialog)

        info_text = f"""
        <h3>Notification System</h3>
        <p>Current user: <b>{self.username}</b></p>
        <p>Database: {os.path.basename(self.db.db_path)}</p>
        <p>Unread notifications: {self.notification_count}</p>
        """

        info_label = QLabel(info_text)
        info_label.setTextFormat(Qt.RichText)
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignCenter)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)

        layout.addWidget(info_label)
        layout.addWidget(close_btn)

        self.apply_theme_to_dialog(dialog)
        dialog.exec_()

    def toggle_notifications(self):
        """Toggle visibility of notifications dropdown"""
        self.notifications_visible = not self.notifications_visible

        if self.notifications_visible:
            # Position the popup near the button
            btn_global_pos = self.badge_button.mapToGlobal(
                QPoint(0, self.badge_button.height()))

            # Calculate position to make sure it's visible
            screen = QApplication.desktop().screenGeometry()
            x = min(btn_global_pos.x(),
                    screen.width() - self.dropdown_container.width() - 20)
            x = max(20, x)

            self.dropdown_container.move(x, btn_global_pos.y() + 5)
            self.dropdown_container.show()
        else:
            self.dropdown_container.hide()

    def toggle_expand(self):
        """Toggle between normal and expanded notification panel"""
        self.is_expanded = not self.is_expanded

        if self.is_expanded:
            self.dropdown_container.setFixedWidth(400)
            self.dropdown_container.setFixedHeight(500)
            self.expand_btn.setText("⤡")  # Unicode collapse symbol
            self.expand_btn.setToolTip(self.translator.t('collapse'))
        else:
            self.dropdown_container.setFixedWidth(320)
            self.dropdown_container.setFixedHeight(420)
            self.expand_btn.setText("⤢")  # Unicode expand symbol
            self.expand_btn.setToolTip(self.translator.t('expand'))

    def pop_out_notifications(self):
        """Create a movable notification window"""
        # Hide the embedded dropdown first
        self.dropdown_container.hide()
        self.notifications_visible = False

        # Create a simple dialog for now
        dialog = QDialog()
        dialog.setWindowTitle("Notifications")
        dialog.resize(350, 450)
        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(20, 20, 20, 20)

        label = QLabel(
            "This is a movable notifications window.\nYou can drag it anywhere on your screen.")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 12pt; margin: 20px;")
        dialog_layout.addWidget(label)

        # Apply theme
        self.apply_theme_to_dialog(dialog)

        dialog.exec_()

    def load_notifications(self):
        """Load notifications from database"""
        # Clear existing notifications from UI
        self.clear_notifications()

        # Get notifications from database
        notifications = self.db.get_notifications_for_user(self.username, limit=10)

        # Update notification count (unread only)
        self.notification_count = self.db.get_unread_notification_count(self.username)
        self.badge_button.set_count(self.notification_count)

        # Update user label
        self.user_label.setText(f"({self.username})")

        # Show "no notifications" message if needed
        if not notifications:
            self.no_notifications_label.show()
            return
        else:
            self.no_notifications_label.hide()

        # Add notifications to UI
        for notification_data in notifications:
            notification_item = ModernNotificationItem(notification_data)
            notification_item.clicked.connect(self.on_notification_clicked)
            self.notifications_layout.addWidget(notification_item)

        # Add some space at the bottom
        self.notifications_layout.addStretch(1)

    def clear_notifications(self):
        """Remove all notification items from the layout"""
        # Remove all children from the layout
        while self.notifications_layout.count():
            item = self.notifications_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def on_notification_clicked(self, notification_id):
        """Handle clicking on a notification item"""
        # Mark as read in the database
        success = self.db.mark_notification_as_read(notification_id, self.username)

        if success:
            # Reload notifications to update UI
            self.load_notifications()

    def mark_all_as_read(self):
        """Mark all notifications as read"""
        self.db.mark_all_as_read(self.username)
        self.load_notifications()

    def add_sample_notifications(self):
        """Add sample notifications to the database"""
        self.db.add_sample_notifications(self.username)
        self.load_notifications()

    def add_notification(self, title, message, category=None, priority='normal'):
        """Add a new notification to the database"""
        self.db.add_notification(self.username, title, message, category, priority)
        self.load_notifications()

    def update_translations(self):
        """Update translations for this widget"""
        self.badge_button.button.setToolTip(self.translator.t('notifications'))
        self.expand_btn.setToolTip(self.translator.t('expand'))
        self.popout_btn.setToolTip(self.translator.t('popout_notifications'))
        self.mark_read_btn.setToolTip(self.translator.t('mark_all_read'))

    def apply_theme(self):
        """Apply modern theme styling"""
        # Determine if we're in dark mode
        dark_mode = is_dark_theme()

        # Define blue accent colors (dim blue to match chat widget)
        if dark_mode:
            accent_color = "#3949AB"  # Indigo blue for dark theme
            accent_hover = "#5C6BC0"  # Lighter indigo for hover
            button_text = "#FFFFFF"
        else:
            accent_color = "#3F51B5"  # Standard indigo for light theme
            accent_hover = "#5C6BC0"  # Lighter indigo for hover
            button_text = "#FFFFFF"

        # Apply to badge button
        self.badge_button.apply_theme(accent_color)

        # Get theme colors
        bg_color = themes.get_color('card_bg')
        text_color = themes.get_color('text')

        # Modern clean container style
        self.dropdown_container.setStyleSheet(f"""
            QFrame#notificationsContainer {{
                background-color: transparent;
                border: none;
            }}

            QFrame#contentFrame {{
                background-color: {bg_color};
                border-radius: 10px;
                border: none;
            }}

            #notificationHeader {{
                background-color: {accent_color};
                color: {button_text};
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }}

            #notificationTitle {{
                color: {button_text};
                font-weight: bold;
            }}

            #userLabel {{
                color: {button_text}CC;
                font-size: 9pt;
                margin-left: 5px;
            }}

            #noNotificationsLabel {{
                color: {text_color};
                font-size: 11pt;
                padding: 30px;
            }}

            #expandButton, #popoutButton, #closeButton, #markReadButton {{
                background-color: transparent;
                color: {button_text};
                border: none;
                padding: 3px;
                border-radius: 4px;
            }}

            #expandButton:hover, #popoutButton:hover, #closeButton:hover, #markReadButton:hover {{
                background-color: {accent_hover};
            }}

            #notificationScroll {{
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

            #buttonContainer {{
                background-color: {bg_color};
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }}

            #seeAllButton {{
                background-color: {accent_color};
                color: white;
                border: none;
                border-radius: 18px;
                padding: 8px 15px;
                font-size: 10pt;
            }}

            #seeAllButton:hover {{
                background-color: {accent_hover};
            }}

            #refreshButton {{
                background-color: transparent;
                color: {text_color};
                border: 1px solid {accent_color}80;
                border-radius: 18px;
                padding: 8px 15px;
                font-size: 10pt;
            }}

            #refreshButton:hover {{
                background-color: {accent_color}20;
                border: 1px solid {accent_color};
            }}
        """)

    def apply_theme_to_dialog(self, dialog):
        """Apply modern theme to the pop-out dialog"""
        dark_mode = is_dark_theme()
        bg_color = themes.get_color('card_bg')
        text_color = themes.get_color('text')
        accent_color = "#3949AB" if dark_mode else "#3F51B5"

        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                border-radius: 10px;
            }}
            QLabel {{
                color: {text_color};
            }}
            QPushButton {{
                background-color: {accent_color};
                color: white;
                border: none;
                border-radius: 18px;
                padding: 8px 15px;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background-color: {accent_color}E6;
            }}
        """)