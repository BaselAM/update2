from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSpacerItem, QSizePolicy
from .search_widget import SearchWidget
from .notifications_widget import NotificationsWidget
from .navigation_widget import NavigationWidget
from .chat_widget import ChatWidget
from themes import get_color


class TopBarWidget(QWidget):
    """Main top bar widget that combines search, notifications, chat, and navigation"""
    search_submitted = pyqtSignal(str)
    home_clicked = pyqtSignal()
    notification_clicked = pyqtSignal()
    chat_clicked = pyqtSignal()

    def __init__(self, translator, database, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.database = database
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        """Create and arrange the top bar components"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 10, 20, 10)

        # Create the navigation widget with home button
        self.navigation_widget = NavigationWidget(self.translator)
        self.navigation_widget.home_clicked.connect(self.home_clicked)

        # Create search widget with expanded functionality
        self.search_widget = SearchWidget(self.translator, self.database)
        self.search_widget.search_submitted.connect(self.search_submitted)

        # Create chat widget with expandable chat interface
        self.chat_widget = ChatWidget(self.translator)
        self.chat_widget.chat_submitted.connect(self.chat_clicked)

        # Create notifications widget with dropdown
        self.notifications_widget = NotificationsWidget(self.translator)
        self.notifications_widget.notification_clicked.connect(self.notification_clicked)

        # Arrange components with proper spacing
        main_layout.addWidget(self.navigation_widget)
        main_layout.addSpacerItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        main_layout.addWidget(self.search_widget)
        main_layout.addSpacerItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        main_layout.addWidget(self.chat_widget)
        main_layout.addWidget(self.notifications_widget)

        # Set fixed height for the top bar
        self.setFixedHeight(60)

    def clear_search(self):
        """Clear the search input"""
        self.search_widget.clear_search()

    def set_notification_count(self, count):
        """Set the notification count"""
        self.notifications_widget.set_notification_count(count)

    def update_translations(self):
        """Update translations for all components"""
        self.search_widget.update_translations()
        self.notifications_widget.update_translations()
        self.navigation_widget.update_translations()
        self.chat_widget.update_translations()

    def apply_theme(self):
        """Apply theme to the top bar and its components"""
        # Apply theme to the top bar container
        self.setStyleSheet(f"""
            TopBarWidget {{
                background-color: {get_color('header')};
                border-bottom: 1px solid {get_color('border')};
            }}
        """)

        # Apply theme to all components
        self.search_widget.apply_theme()
        self.notifications_widget.apply_theme()
        self.navigation_widget.apply_theme()
        self.chat_widget.apply_theme()