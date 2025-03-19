import os
import sys
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, \
    QStackedWidget, QFrame, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon

# Import the refactored components
from widgets.search import ElegantSearchBar
from widgets.notification_button import NotificationButton
from widgets.dropdown import ChatDropdown, NotificationDropdown
from widgets.dialogs import *
from database.notification_db import NotificationDatabase  # If you've created this file

# Import other necessary components
from widgets.sidebar import SidebarWidget
from languages import Translator
from themes import set_theme, get_color
from database.parts_db import PartsDatabase
from views.home import HomeView
from views.inventory import InventoryView
from views.billing import BillingView
from views.settings import SettingsView
from views.customers import CustomersView
from views.reports import ReportsView
from views.help import HelpView


class TopBarWidget(QWidget):
    """
    Top bar widget containing navigation buttons, time display,
    notifications, and chatbot access
    """

    def __init__(self, translator, parts_db=None):
        super().__init__()
        self.translator = translator
        self.parts_db = parts_db

        # Initialize notification database
        self.notification_db = NotificationDatabase() if 'NotificationDatabase' in globals() else None

        # Load sample notifications for testing if needed
        self.notifications = []
        if self.notification_db:
            self.notifications = self.notification_db.get_notifications(
                include_read=False)
            # Add sample notifications if none exist (for testing)
            if not self.notifications:
                self.add_sample_notifications()

        self.setup_ui()
        self.apply_theme()

        # Update the time every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

        # Initial time update
        self.update_time()

        # Create dropdown widgets
        self.chat_dropdown = ChatDropdown(self)
        self.chat_dropdown.popped_out.connect(self.show_chat_dialog)

        self.notification_dropdown = NotificationDropdown(self)
        self.notification_dropdown.popped_out.connect(self.show_notifications_dialog)

    def add_sample_notifications(self):
        """Add sample notifications for testing"""
        if not self.notification_db:
            return

        sample_notifications = [
            {
                'title': 'Low Stock Alert',
                'message': 'BMW 3 Series brake pads (Part #BP-3872) are running low. Current inventory: 5 units.',
                'category': 'inventory'
            },
            {
                'title': 'Price Update',
                'message': 'Price changes have been applied to 15 items in the Toyota category.',
                'category': 'price'
            },
            {
                'title': 'Order Received',
                'message': 'New shipment of Honda filters has arrived and is ready for inventory check.',
                'category': 'shipment'
            }
        ]

        for notif in sample_notifications:
            self.notification_db.add_notification(
                title=notif['title'],
                message=notif['message'],
                category=notif['category'],
                importance=1
            )

        self.notifications = self.notification_db.get_notifications(include_read=False)

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(20)

        # Left section - Car logo and Home button
        logo_frame = QFrame()
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(15)

        # Car logo
        self.logo_label = QLabel()
        script_dir = Path(__file__).parent
        car_icon_path = script_dir / "resources/car-icon.jpg"
        if car_icon_path.exists():
            self.logo_label.setPixmap(QIcon(str(car_icon_path)).pixmap(32, 32))
        logo_layout.addWidget(self.logo_label)

        main_layout.addWidget(logo_frame)

        # Search bar
        self.search_bar = ElegantSearchBar()
        self.search_bar.setFixedWidth(300)
        main_layout.addWidget(self.search_bar)

        # Expand in the middle
        main_layout.addStretch(1)

        # Right-center section - Chatbot button
        chat_frame = QFrame()
        chat_layout = QHBoxLayout(chat_frame)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(10)

        # Chatbot button
        self.chat_button = QToolButton()
        self.chat_button.setIcon(QIcon(str(script_dir / "resources/chatbot.png")))
        self.chat_button.setIconSize(QSize(28, 28))
        self.chat_button.setToolTip(self.translator.t("chat_tooltip"))
        self.chat_button.setCursor(Qt.PointingHandCursor)
        self.chat_button.setFixedSize(40, 40)
        self.chat_button.setStyleSheet("background: transparent;")
        self.chat_button.clicked.connect(self.toggle_chat_dropdown)
        chat_layout.addWidget(self.chat_button)

        # Chat label
        chat_label = QLabel(self.translator.t("chat_assistant"))
        chat_label.setStyleSheet("font-size: 12pt; font-weight: 500;")
        chat_layout.addWidget(chat_label)

        main_layout.addWidget(chat_frame)

        # Simple elegant time display
        self.datetime_frame = QFrame()
        datetime_layout = QVBoxLayout(self.datetime_frame)
        datetime_layout.setContentsMargins(10, 5, 10, 5)
        datetime_layout.setSpacing(0)

        # Time in large font
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("font-size: 15pt; font-weight: bold;")
        datetime_layout.addWidget(self.time_label)

        # Date in smaller font
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setStyleSheet("font-size: 9pt; opacity: 0.8;")
        datetime_layout.addWidget(self.date_label)

        main_layout.addWidget(self.datetime_frame)

        # Notification button
        self.notification_button = NotificationButton()
        self.notification_button.setIcon(QIcon(str(script_dir / "resources/danger.png")))
        self.notification_button.setIconSize(QSize(28, 28))
        self.notification_button.setToolTip(self.translator.t("notifications_tooltip"))
        self.notification_button.setFixedSize(42, 42)
        self.notification_button.clicked.connect(self.toggle_notification_dropdown)

        # Set notification count
        unread_count = len(self.notifications)
        self.notification_button.set_notification_count(unread_count)

        main_layout.addWidget(self.notification_button)

        # Set a nice height for the top bar
        self.setFixedHeight(64)

    def toggle_chat_dropdown(self):
        """Toggle the chat dropdown visibility"""
        if self.chat_dropdown.isVisible():
            self.chat_dropdown.hide()
        else:
            # Hide notification dropdown if it's visible
            if self.notification_dropdown.isVisible():
                self.notification_dropdown.hide()

            # Show chat dropdown
            self.chat_dropdown.show_at_button(self.chat_button)

    def toggle_notification_dropdown(self):
        """Toggle the notification dropdown visibility"""
        if self.notification_dropdown.isVisible():
            self.notification_dropdown.hide()
        else:
            # Hide chat dropdown if it's visible
            if self.chat_dropdown.isVisible():
                self.chat_dropdown.hide()

            # Show notification dropdown
            self.notification_dropdown.show_notifications(self.notifications)
            self.notification_dropdown.show_at_button(self.notification_button)

    def show_chat_dialog(self):
        """Show the chatbox dialog when chat button is clicked"""
        chat_dialog = ChatBoxDialog(self)
        chat_dialog.exec_()

    def show_notifications_dialog(self):
        """Show the notifications dialog when notification button is clicked"""
        notif_dialog = NotificationsDialog(self.notifications, self, self.notification_db)
        notif_dialog.exec_()

    def update_time(self):
        """Update the time display"""
        now = datetime.now()
        self.time_label.setText(now.strftime("%H:%M:%S"))
        self.date_label.setText(now.strftime("%a, %b %d"))

    def apply_theme(self):
        """Apply the current theme to this widget"""
        bg_color = get_color('background')
        text_color = get_color('text')
        button_color = get_color('button')
        border_color = get_color('border')

        self.setStyleSheet(f"""
            TopBarWidget {{
                background-color: {bg_color};
                color: {text_color};
                border-bottom: 1px solid {border_color};
            }}

            QToolButton {{
                color: {text_color};
                border: none;
                border-radius: 20px;
            }}

            QToolButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}

            QFrame#datetime_frame {{
                background-color: {button_color};
                border-radius: 10px;
            }}
        """)

        # Apply to datetime frame separately (as it needs a different style)
        self.datetime_frame.setStyleSheet(f"""
            background-color: {button_color};
            border-radius: 10px;
        """)

    def update_translations(self):
        """Update all translated text elements"""
        self.notification_button.setToolTip(self.translator.t("notifications_tooltip"))
        self.chat_button.setToolTip(self.translator.t("chat_tooltip"))
        self.search_bar.setPlaceholderText(self.translator.t("search_placeholder"))


class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Car Parts Inventory Management")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize services
        self.translator = Translator()
        self.parts_db = PartsDatabase()

        # Set up the UI
        self.init_ui()

        # Apply default theme
        set_theme("dark")
        self.apply_theme()

    def init_ui(self):
        # Main container
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar (using refactored component)
        self.top_bar = TopBarWidget(self.translator, self.parts_db)
        main_layout.addWidget(self.top_bar)

        # Main content layout (sidebar + content)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar
        self.sidebar = SideBar(self.translator)
        self.sidebar.page_changed.connect(self.change_page)
        content_layout.addWidget(self.sidebar)

        # Stacked widget for main content
        self.stacked_widget = QStackedWidget()

        # Add pages
        self.home_view = HomeView(self.translator, self.parts_db)
        self.inventory_view = InventoryView(self.translator, self.parts_db)
        self.customers_view = CustomersView(self.translator, self.parts_db)
        self.billing_view = BillingView(self.translator, self.parts_db)
        self.reports_view = ReportsView(self.translator, self.parts_db)
        self.settings_view = SettingsView(self.translator, self.parts_db)
        self.help_view = HelpView(self.translator)

        self.stacked_widget.addWidget(self.home_view)
        self.stacked_widget.addWidget(self.inventory_view)
        self.stacked_widget.addWidget(self.customers_view)
        self.stacked_widget.addWidget(self.billing_view)
        self.stacked_widget.addWidget(self.reports_view)
        self.stacked_widget.addWidget(self.settings_view)
        self.stacked_widget.addWidget(self.help_view)

        content_layout.addWidget(self.stacked_widget)

        # Add content layout to main layout
        main_layout.addLayout(content_layout)

    def change_page(self, index):
        """Change the current page"""
        self.stacked_widget.setCurrentIndex(index)

    def apply_theme(self):
        """Apply the current theme to all components"""
        bg_color = get_color('background')

        # Apply to main window
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {bg_color};
            }}
        """)

        # Apply to child widgets
        self.top_bar.apply_theme()
        self.sidebar.apply_theme()

        # Apply to all views
        for i in range(self.stacked_widget.count()):
            view = self.stacked_widget.widget(i)
            if hasattr(view, 'apply_theme'):
                view.apply_theme()