import sys
import logging
from pathlib import Path
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, \
    QStackedWidget, QMessageBox
from PyQt5.QtGui import QIcon

# Import widgets
from widgets.layout import HeaderWidget, FooterWidget, CopyrightWidget
from widgets.search import TopBarWidget  # Import the new class name
from widgets.products import ProductsWidget
from widgets.statistics import StatisticsWidget
from widgets.settings import SettingsWidget
from widgets.help import HelpWidget
from home_page import HomePageWidget

from translator import Translator
from database.settings_db import SettingsDB
from database.car_parts_db import CarPartsDB
from themes import set_theme, get_color


class GUI(QMainWindow):
    language_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        # Initialize databases
        self.settings_db = SettingsDB()
        self.parts_db = CarPartsDB()

        # Load theme
        saved_theme = self.settings_db.get_setting('theme', 'classic')
        set_theme(saved_theme)

        # Initialize language and direction
        self.current_language = self.settings_db.get_setting('language', 'en')
        self.rtl_enabled = self.settings_db.get_rtl_setting()
        self.translator = Translator(self.current_language)

        # Setup UI components
        self.setup_window_properties()
        self.preload_views()
        self.setup_ui()
        self.apply_theme()

        # Set initial layout direction
        self._apply_layout_direction_initially()

    def setup_window_properties(self):
        """Set window title, size, and icon"""
        self.setWindowTitle(self.translator.t('window_title'))
        self.setGeometry(100, 100, 1200, 800)

        icon_path = Path(__file__).parent / "resources/window_icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def preload_views(self):
        """Initialize all view widgets"""
        self.products_widget = ProductsWidget(self.translator, self.parts_db)
        self.statistics_widget = StatisticsWidget(self.translator)
        self.settings_widget = SettingsWidget(self.translator, self.update_language, self)
        self.help_widget = HelpWidget(self.translator)

    def setup_ui(self):
        """Create and arrange all UI components"""
        navigation_functions = {
            'products_button': self.show_products,
            'statistics_button': self.show_statistics,
            'settings_button': self.show_settings,
            'help_button': self.show_help,
            'parts_button': self.show_parts,  # New function
            'web_search_button': self.show_web_search,  # New function
            'exit_button': self.exit_app
        }

        # Create main widgets
        self.home_page = HomePageWidget(self.translator, navigation_functions)
        self.header = HeaderWidget(self.translator, self.show_home)
        self.top_bar = TopBarWidget(self.translator,
                                    self.parts_db)  # Use the new class name
        self.footer = FooterWidget(self.translator)
        copyright_widget = CopyrightWidget(self.translator)

        # Connect top bar signals
        self.top_bar.home_clicked.connect(self.show_home)
        self.top_bar.notification_clicked.connect(self.show_notifications)
        self.top_bar.chat_clicked.connect(self.show_chat)

        # Create stacked widget for content
        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.home_page)
        self.content_stack.addWidget(self.products_widget)
        self.content_stack.addWidget(self.statistics_widget)
        self.content_stack.addWidget(self.settings_widget)
        self.content_stack.addWidget(self.help_widget)

        # Main layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self.header)
        main_layout.addWidget(self.top_bar)  # Updated variable name
        main_layout.addWidget(self.content_stack, 1)  # Content expands to fill space
        main_layout.addWidget(self.footer)
        main_layout.addWidget(copyright_widget)

        # Set as central widget
        self.setCentralWidget(main_widget)

        # Start with home page
        self.show_home()

    def apply_theme(self):
        """Apply current theme to main window and components"""
        bg_color = get_color('background')
        text_color = get_color('text')

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {bg_color};
            }}
            QWidget {{
                color: {text_color};
                font-family: 'Segoe UI', sans-serif;
            }}
        """)

        # Apply theme to all components that support it
        for widget in self.findChildren(QWidget):
            if hasattr(widget, 'apply_theme'):
                widget.apply_theme()

    def _apply_layout_direction_initially(self):
        """Set initial layout direction based on settings"""
        direction = Qt.RightToLeft if self.rtl_enabled else Qt.LeftToRight
        QApplication.setLayoutDirection(direction)
        self._apply_layout_direction_recursive(self, direction)

    def _apply_layout_direction_recursive(self, widget, direction):
        """Recursively set layout direction for all child widgets"""
        widget.setLayoutDirection(direction)
        for child in widget.findChildren(QWidget):
            child.setLayoutDirection(direction)

    def show_home(self):
        """Switch to home page view"""
        try:
            self.content_stack.setCurrentWidget(self.home_page)
        except Exception as e:
            print(f"Error showing home page: {str(e)}")

    def show_products(self):
        """Switch to products view"""
        self.content_stack.setCurrentWidget(self.products_widget)

    def show_statistics(self):
        """Switch to statistics view"""
        self.content_stack.setCurrentWidget(self.statistics_widget)

    def show_settings(self):
        """Switch to settings view"""
        self.content_stack.setCurrentWidget(self.settings_widget)

    def show_help(self):
        """Switch to help documentation view"""
        self.content_stack.setCurrentWidget(self.help_widget)

    # Add these new methods to handle the new top bar buttons
    def show_notifications(self):
        """Show notifications panel"""
        QMessageBox.information(self, "Notifications",
                                "Notifications feature will be available soon")

    def show_chat(self):
        """Show chatbot interface"""
        QMessageBox.information(self, "Chat Assistant",
                                "Chat assistant feature will be available soon")

    def on_search_entered(self):
        """Handle search queries"""
        search_text = self.top_bar.search_input.text().strip()
        if search_text:
            self.show_products()
            self.products_widget.highlight_product(search_text)

    def exit_app(self):
        """Close the application"""
        self.close()

    def update_language(self, new_lang):
        """Change the application language"""
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)

            # Save settings
            is_rtl = (new_lang == 'he')
            self.settings_db.save_setting('rtl', str(is_rtl).lower())
            self.settings_db.save_setting('language', new_lang)

            # Update state
            self.current_language = new_lang
            self.rtl_enabled = is_rtl
            self.translator.set_language(new_lang)

            # Apply direction changes
            direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
            QApplication.setLayoutDirection(direction)
            self._apply_layout_direction_recursive(self, direction)

            # Refresh theme and translations
            self.apply_theme()
            self._full_ui_refresh()

        except Exception as e:
            logging.error(f"Language update error: {str(e)}")
            QMessageBox.critical(self, "Error", self.translator.t('settings_save_error'))
        finally:
            QApplication.restoreOverrideCursor()

    def _full_ui_refresh(self):
        """Refresh all UI components after language change"""
        # Update all widgets with translations
        self.header.update_translations()
        self.top_bar.update_translations()  # Updated variable name
        self.footer.update_translations()
        self.home_page.update_translations()
        self.products_widget.update_translations()
        self.statistics_widget.update_translations()
        self.settings_widget.update_translations()
        self.help_widget.update_translations()

        # Force layout update
        self.updateGeometry()
        QApplication.processEvents()

    def closeEvent(self, event):
        """Handle application closing"""
        try:
            # Close database connections
            self.parts_db.close_connection()
            self.settings_db.close()

            # Clean up resources
            self.top_bar.deleteLater()  # Updated variable name
            self.content_stack.deleteLater()

            # Process pending events
            QApplication.processEvents()

            import gc
            gc.collect()  # Force garbage collection

            event.accept()
        except Exception as e:
            logging.error(f"Shutdown error: {str(e)}")
            sys.exit(1)

    def show_parts(self):
        """Open the parts management screen"""
        # You'll need to implement this view
        QMessageBox.information(self, "Parts",
                                "Parts management feature will be available soon")

    def show_web_search(self):
        """Open web search for car parts"""
        # You'll need to implement this feature
        QMessageBox.information(self, "Web Search",
                                "Web search feature will be available soon")

    def apply_theme_to_all(self):
        """Apply current theme to all components"""
        try:
            # Apply theme to main window
            self.apply_theme()

            # Apply theme to all widgets that support it
            widgets_with_theme = [
                self.header,
                self.top_bar,  # Updated variable name
                self.home_page,
                self.footer,
                self.products_widget,
                self.statistics_widget,
                self.settings_widget,
                self.help_widget
            ]

            for widget in widgets_with_theme:
                if hasattr(widget, 'apply_theme'):
                    widget.apply_theme()
        except Exception as e:
            print(f"Error applying theme to all components: {str(e)}")

    def set_current_user(self, username):
        """Set the current logged-in username and update displays"""
        self.current_username = username

        # Update home page if it exists
        if hasattr(self, 'home_page') and self.home_page:
            self.home_page.update_user(username)


import time
from datetime import datetime
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QSize, QPoint, QPropertyAnimation, \
    QEasingCurve
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel,
    QVBoxLayout, QFrame, QToolButton, QSizePolicy,
    QDialog, QLineEdit, QScrollArea, QCompleter,
    QApplication, QGraphicsDropShadowEffect, QDialogButtonBox
)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor, QPalette, QLinearGradient

from themes import get_color
from shared import SCRIPT_DIR


def is_dark_color(color_str):
    """Determine if a color is dark to ensure proper text contrast"""
    if not color_str:
        return True

    # Handle hex colors
    if color_str.startswith('#'):
        if len(color_str) == 7:  # #RRGGBB
            r = int(color_str[1:3], 16)
            g = int(color_str[3:5], 16)
            b = int(color_str[5:7], 16)
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            return brightness < 128

    # Default to assuming it's dark
    return True


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


class ElegantSearchBar(QLineEdit):
    """A stylish search bar with clear button"""

    search_triggered = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Search for settings, products, reports...")

        # Add search icon
        search_icon_path = SCRIPT_DIR / "resources/search_icon.png"
        if search_icon_path.exists():
            search_action = self.addAction(QIcon(str(search_icon_path)),
                                           QLineEdit.LeadingPosition)

        # Add clear button
        self.setClearButtonEnabled(True)

        # Connect signals
        self.returnPressed.connect(self._on_search)

        # Add auto-complete suggestions
        self.setUpAutoComplete()

    def setUpAutoComplete(self):
        # Common search terms in the app
        suggestions = [
            "Products", "Settings", "Statistics", "Reports",
            "Parts", "Database", "Users", "Help", "Search",
            "Car Parts", "Import", "Export", "Inventory",
            "BMW", "Toyota", "Honda", "Ford", "Brake Pads",
            "Filters", "Oil", "Battery", "Tires", "Engine"
        ]

        completer = QCompleter(suggestions, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(completer)

    def _on_search(self):
        text = self.text().strip()
        if text:
            self.search_triggered.emit(text)


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

        # Scroll area for messages
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)
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

    def add_message(self, message, title=None, is_bot=True):
        """Add a message to the content area"""
        message_frame = QFrame()
        message_frame.setObjectName("botMessage" if is_bot else "userMessage")

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
        time_label = QLabel(datetime.now().strftime("%H:%M"))
        time_label.setObjectName("timestamp")
        time_label.setAlignment(Qt.AlignRight)
        message_layout.addWidget(time_label)

        self.content_layout.addWidget(message_frame)

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

        # Determine if we're using dark theme
        is_dark = is_dark_color(bg_color)

        # Set contrasting colors
        header_bg = QColor(primary_color).darker(110).name() if is_dark else QColor(
            primary_color).lighter(110).name()
        content_bg = bg_color
        footer_bg = QColor(bg_color).darker(110).name() if is_dark else QColor(
            bg_color).lighter(110).name()

        # For message bubbles
        bot_message_bg = primary_color
        user_message_bg = secondary_color

        # Ensure text has contrast - force white on dark backgrounds, black on light
        bot_text_color = "#FFFFFF" if is_dark_color(bot_message_bg) else "#000000"
        user_text_color = "#FFFFFF" if is_dark_color(user_message_bg) else "#000000"

        # Center message text (use theme text color)
        center_text_color = text_color

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
                color: {center_text_color};
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

    def __init__(self, notifications=None, parent=None):
        super().__init__("Notifications", parent)
        self.show_notifications(notifications)

    def show_notifications(self, notifications=None):
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
                self.add_message(
                    notification.get('message', ''),
                    title=notification.get('title', ''),
                    is_bot=True
                )


# Improved dialog classes with more elegant styling
class EnhancedDialog(QDialog):
    """Enhanced dialog base class with elegant styling"""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(500, 600)  # Larger size for expanded view

        # Set window flags for a more modern look
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)

        self.setup_ui()
        self.apply_theme()

        # Add shadow effect for elegance
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)  # Remove spacing for a more integrated look
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for cleaner look

        # Header with title
        self.header = QFrame()
        self.header.setObjectName("dialogHeader")
        self.header.setMinimumHeight(50)

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(15, 10, 15, 10)

        title_label = QLabel(self.windowTitle())
        title_label.setObjectName("dialogTitle")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        header_layout.addWidget(title_label)

        layout.addWidget(self.header)

        # Content area with scroll
        content_frame = QFrame()
        content_frame.setObjectName("dialogContent")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(15, 15, 15, 15)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)  # Remove frame border
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(10)
        self.scroll_area.setWidget(self.content_widget)

        content_layout.addWidget(self.scroll_area)
        layout.addWidget(content_frame, 1)  # 1 = stretch factor

        # Footer with buttons
        self.footer = QFrame()
        self.footer.setObjectName("dialogFooter")
        self.footer.setMinimumHeight(60)

        footer_layout = QHBoxLayout(self.footer)
        footer_layout.setContentsMargins(15, 10, 15, 10)
        footer_layout.addStretch()

        # Close button in an elegant button box
        button_box = QDialogButtonBox()
        self.close_button = QPushButton("Close")
        self.close_button.setObjectName("closeButton")
        self.close_button.setMinimumSize(100, 35)
        button_box.addButton(self.close_button, QDialogButtonBox.RejectRole)
        button_box.rejected.connect(self.accept)

        footer_layout.addWidget(button_box)
        layout.addWidget(self.footer)

    def apply_theme(self):
        bg_color = get_color('background')
        text_color = get_color('text')
        primary_color = get_color('button')
        border_color = get_color('border')

        # Determine if we're using a dark theme
        is_dark = is_dark_color(bg_color)

        # Create contrasting colors for headers and footers
        header_bg = QColor(primary_color).darker(110).name() if is_dark else QColor(
            primary_color).lighter(110).name()
        footer_bg = QColor(bg_color).darker(110).name() if is_dark else QColor(
            bg_color).lighter(110).name()

        # Force text to contrast with backgrounds
        header_text = "#FFFFFF" if is_dark_color(header_bg) else "#000000"

        # Create a gradient for the header
        grad_start = QColor(header_bg).darker(120).name()
        grad_end = header_bg

        self.setStyleSheet(f"""
            EnhancedDialog {{
                background-color: {bg_color};
                color: {text_color};
            }}

            QFrame#dialogHeader {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 {grad_start}, 
                                           stop:1 {grad_end});
                color: {header_text};
                border-bottom: 1px solid {border_color};
            }}

            QLabel#dialogTitle {{
                color: {header_text};
            }}

            QFrame#dialogContent {{
                background-color: {bg_color};
                color: {text_color};
            }}

            QFrame#dialogFooter {{
                background-color: {footer_bg};
                border-top: 1px solid {border_color};
            }}

            QScrollArea {{
                border: none;
                background-color: transparent;
            }}

            QScrollArea > QWidget > QWidget {{
                background-color: transparent;
            }}

            QPushButton#closeButton {{
                background-color: {primary_color};
                color: {text_color};
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}

            QPushButton#closeButton:hover {{
                background-color: {QColor(primary_color).lighter(110).name()};
            }}

            QPushButton {{
                background-color: {primary_color};
                color: {text_color};
                padding: 8px 16px;
                border-radius: 4px;
            }}

            QPushButton:hover {{
                background-color: {QColor(primary_color).lighter(110).name()};
            }}
        """)


class ChatBoxDialog(EnhancedDialog):
    """Enhanced chat dialog"""

    def __init__(self, parent=None):
        super().__init__("Chat Assistant", parent)
        self.show_coming_soon()

    def show_coming_soon(self):
        # Add a sleek container for the message
        container = QFrame()
        container.setObjectName("messageContainer")
        container_layout = QVBoxLayout(container)

        # Add an icon (optional)
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)

        # Try to load the chatbot icon
        chatbot_icon_path = SCRIPT_DIR / "resources/chatbot.png"
        if chatbot_icon_path.exists():
            pixmap = QPixmap(str(chatbot_icon_path)).scaled(64, 64, Qt.KeepAspectRatio,
                                                            Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
            container_layout.addWidget(icon_label)
            container_layout.addSpacing(15)

        # Add title
        title = QLabel("Chat Assistant")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18pt; font-weight: bold;")
        container_layout.addWidget(title)
        container_layout.addSpacing(10)

        # Add a simple message with better styling
        message = QLabel(
            "Chat functionality will be available in the next update. Stay tuned!")
        message.setWordWrap(True)
        message.setAlignment(Qt.AlignCenter)
        message.setStyleSheet(
            f"padding: 20px; font-size: 14pt; color: {get_color('text')};")
        container_layout.addWidget(message)

        # Add version info
        version = QLabel("Coming in v1.2")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("font-style: italic; color: gray;")
        container_layout.addWidget(version)

        # Add container to content
        container_layout.addStretch(1)
        self.content_layout.addWidget(container)
        self.content_layout.addStretch(1)

        # Style the container
        container.setStyleSheet(f"""
            QFrame#messageContainer {{
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                padding: 20px;
            }}
        """)


class NotificationsDialog(EnhancedDialog):
    """Enhanced notifications dialog"""

    def __init__(self, notifications=None, parent=None):
        super().__init__("Notifications", parent)
        self.show_notifications(notifications)

    def show_notifications(self, notifications=None):
        # Clear existing content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Show notifications or 'no notifications' message
        if not notifications or len(notifications) == 0:
            # Container for empty state
            empty_container = QFrame()
            empty_container.setObjectName("emptyContainer")
            empty_layout = QVBoxLayout(empty_container)

            # Try to load notification icon
            icon_label = QLabel()
            icon_label.setAlignment(Qt.AlignCenter)

            bell_icon_path = SCRIPT_DIR / "resources/danger.png"  # Reuse danger icon
            if bell_icon_path.exists():
                pixmap = QPixmap(str(bell_icon_path)).scaled(64, 64, Qt.KeepAspectRatio,
                                                             Qt.SmoothTransformation)
                icon_label.setPixmap(pixmap)
                empty_layout.addWidget(icon_label)
                empty_layout.addSpacing(15)

            # No notifications message
            no_notif = QLabel("No notifications at this time")
            no_notif.setAlignment(Qt.AlignCenter)
            no_notif.setStyleSheet(f"""
                font-size: 16pt;
                color: {get_color('text')};
                font-style: italic;
                padding: 20px;
            """)
            empty_layout.addWidget(no_notif)

            # Explanatory text
            explanation = QLabel(
                "You'll see notifications here when there are updates, alerts, or messages about your car parts inventory.")
            explanation.setWordWrap(True)
            explanation.setAlignment(Qt.AlignCenter)
            explanation.setStyleSheet("color: gray; padding: 10px;")
            empty_layout.addWidget(explanation)

            empty_layout.addStretch(1)

            # Style the container
            empty_container.setStyleSheet(f"""
                QFrame#emptyContainer {{
                    background-color: rgba(255, 255, 255, 0.05);
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px;
                }}
            """)

            self.content_layout.addWidget(empty_container)
            self.content_layout.addStretch()
        else:
            # Add header for notifications
            header = QLabel("Recent Notifications")
            header.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 10px 0;")
            self.content_layout.addWidget(header)

            # Add notifications with improved styling
            for notification in notifications:
                notif_frame = QFrame()
                notif_frame.setObjectName("notificationItem")

                notif_layout = QVBoxLayout(notif_frame)
                notif_layout.setContentsMargins(15, 10, 15, 10)

                # Title with icon
                title_layout = QHBoxLayout()

                # Title
                title = QLabel(notification.get('title', 'Notification'))
                title.setStyleSheet("font-weight: bold; font-size: 13pt;")
                title_layout.addWidget(title)

                # Time (right-aligned)
                time_label = QLabel(notification.get('time', ''))
                time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                time_label.setStyleSheet("font-size: 10pt; color: gray;")
                title_layout.addWidget(time_label)

                notif_layout.addLayout(title_layout)

                # Message
                message = QLabel(notification.get('message', ''))
                message.setWordWrap(True)
                message.setStyleSheet("font-size: 12pt; padding: 5px 0;")
                notif_layout.addWidget(message)

                # Style the notification card
                notif_frame.setStyleSheet(f"""
                    QFrame#notificationItem {{
                        background-color: {get_color('card_bg')};
                        border-radius: 8px;
                        margin: 5px 0;
                    }}
                """)

                self.content_layout.addWidget(notif_frame)

            # Add spacer at the end
            self.content_layout.addStretch()

            # Add a "Clear All" button
            clear_button = QPushButton("Clear All")
            clear_button.setObjectName("clearButton")
            clear_button.clicked.connect(self.clear_notifications)

            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(clear_button)

            self.content_layout.addLayout(button_layout)

    def clear_notifications(self):
        """Handle clearing all notifications"""
        # We'll just show the empty state
        self.show_notifications([])

        # In a real app, you'd connect this to the parent's clear_notifications method
        parent = self.parent()
        if parent and hasattr(parent, 'clear_notifications'):
            parent.clear_notifications()


class TopBarWidget(QWidget):
    """
    Top bar widget containing navigation buttons, time display,
    notifications, and chatbot access.
    """
    home_clicked = pyqtSignal()
    notification_clicked = pyqtSignal()
    chat_clicked = pyqtSignal()
    search_triggered = pyqtSignal(str)

    def __init__(self, translator, parts_db=None):
        super().__init__()
        self.translator = translator
        self.parts_db = parts_db

        # Sample notifications with useful information for car parts inventory
        self.notifications = [
            {
                'title': 'Low Stock Alert',
                'message': 'BMW 3 Series brake pads (Part #BP-3872) are running low. Current inventory: 5 units.',
                'time': 'Today 10:45'
            },
            {
                'title': 'Price Update',
                'message': 'Price changes have been applied to 15 items in the Toyota category.',
                'time': 'Today 09:30'
            },
            {
                'title': 'Order Received',
                'message': 'New shipment of Honda filters has arrived and is ready for inventory check.',
                'time': 'Yesterday'
            }
        ]

        self.setup_ui()
        self.apply_theme()

        # Update the time every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

        # Initial time update
        self.update_time()

        # Create dropdown widgets (but don't show them yet)
        self.chat_dropdown = ChatDropdown(self)
        self.chat_dropdown.popped_out.connect(self.show_chat_dialog)
        self.notification_dropdown = NotificationDropdown(self.notifications, self)
        self.notification_dropdown.popped_out.connect(self.show_notifications_dialog)

        # Set notification count
        self.notification_button.set_notification_count(len(self.notifications))

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
        car_icon_path = SCRIPT_DIR / "resources/car-icon.jpg"
        if car_icon_path.exists():
            pixmap = QPixmap(str(car_icon_path)).scaled(32, 32, Qt.KeepAspectRatio,
                                                        Qt.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        logo_layout.addWidget(self.logo_label)

        # Home button with transparent background
        self.home_button = QPushButton()
        home_icon_path = SCRIPT_DIR / "resources/home_icon.png"
        if home_icon_path.exists():
            home_icon = QIcon(str(home_icon_path))
            self.home_button.setIcon(home_icon)
            self.home_button.setIconSize(QSize(24, 24))
        else:
            self.home_button.setText("🏠")
            self.home_button.setFont(QFont("Arial", 14))

        self.home_button.setToolTip(self.translator.t("home_tooltip"))
        self.home_button.setCursor(Qt.PointingHandCursor)
        self.home_button.setFixedSize(40, 40)
        self.home_button.setStyleSheet("background: transparent;")
        self.home_button.clicked.connect(self.home_clicked.emit)
        logo_layout.addWidget(self.home_button)

        main_layout.addWidget(logo_frame)

        # Search bar (replacing app_title)
        self.search_bar = ElegantSearchBar()
        self.search_bar.setFixedWidth(300)  # Good width for search bar
        self.search_bar.search_triggered.connect(self.search_triggered.emit)
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
        self.chat_button.setStyleSheet("background: transparent;")
        chatbot_icon_path = SCRIPT_DIR / "resources/chatbot.png"
        if chatbot_icon_path.exists():
            self.chat_button.setIcon(QIcon(str(chatbot_icon_path)))
            self.chat_button.setIconSize(QSize(28, 28))
        else:
            self.chat_button.setText("💬")
            self.chat_button.setFont(QFont("Arial", 14))

        self.chat_button.setToolTip(self.translator.t("chat_tooltip"))
        self.chat_button.setCursor(Qt.PointingHandCursor)
        self.chat_button.setFixedSize(40, 40)
        self.chat_button.clicked.connect(self.toggle_chat_dropdown)
        chat_layout.addWidget(self.chat_button)

        # Chat label
        chat_label = QLabel(self.translator.t("chat_assistant"))
        chat_label.setStyleSheet("font-size: 12pt; font-weight: 500;")
        chat_layout.addWidget(chat_label)

        main_layout.addWidget(chat_frame)

        # Simple elegant time display
        self.datetime_frame = QFrame()
        self.datetime_frame.setStyleSheet(f"""
            background-color: {QColor(get_color('button')).name()};
            border-radius: 10px;
            padding: 4px;
        """)
        self.datetime_frame.setFixedSize(140, 50)

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
        danger_icon_path = SCRIPT_DIR / "resources/danger.png"
        if danger_icon_path.exists():
            self.notification_button.setIcon(QIcon(str(danger_icon_path)))
            self.notification_button.setIconSize(QSize(28, 28))
        else:
            self.notification_button.setText("🔔")
            self.notification_button.setFont(QFont("Arial", 14))

        self.notification_button.setToolTip(self.translator.t("notifications_tooltip"))
        self.notification_button.setFixedSize(42, 42)
        self.notification_button.clicked.connect(self.toggle_notification_dropdown)

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

            # Update notifications and show dropdown
            self.notification_dropdown.show_notifications(self.notifications)
            self.notification_dropdown.show_at_button(self.notification_button)

    def show_chat_dialog(self):
        """Show the chatbox dialog when chat button is clicked"""
        chat_dialog = ChatBoxDialog(self)
        chat_dialog.exec_()

    def show_notifications_dialog(self):
        """Show the notifications dialog when notification button is clicked"""
        notif_dialog = NotificationsDialog(self.notifications, self)
        notif_dialog.exec_()

    def update_time(self):
        """Update the time display"""
        now = datetime.now()
        self.time_label.setText(now.strftime("%H:%M:%S"))
        self.date_label.setText(now.strftime("%a, %b %d"))

    def add_notification(self, title, message, time_str=None):
        """Add a new notification"""
        if time_str is None:
            time_str = datetime.now().strftime("%H:%M")

        self.notifications.append({
            'title': title,
            'message': message,
            'time': time_str
        })
        self.notification_button.set_notification_count(len(self.notifications))

    def clear_notifications(self):
        """Clear all notifications"""
        self.notifications = []
        self.notification_button.set_notification_count(0)

    def apply_theme(self):
        """Apply the current theme to this widget"""
        bg_color = get_color('background')
        text_color = get_color('text')
        button_color = get_color('button')
        input_bg = get_color('input_bg')
        border_color = get_color('border')

        self.setStyleSheet(f"""
            TopBarWidget {{
                background-color: {bg_color};
                color: {text_color};
                border-bottom: 1px solid {border_color};
            }}

            QPushButton {{
                border: none;
                border-radius: 20px;
            }}

            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}

            QToolButton {{
                color: {text_color};
                border: none;
                border-radius: 20px;
            }}

            QToolButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}

            QLineEdit {{
                background-color: {input_bg};
                color: {text_color};
                border: none;
                border-radius: 16px;
                padding: 8px 16px;
                font-size: 12pt;
            }}
        """)

        # Update the datetime frame style
        self.datetime_frame.setStyleSheet(f"""
            background-color: {QColor(button_color).name()};
            border-radius: 10px;
        """)

        # Make sure dropdowns follow theme
        if hasattr(self, 'chat_dropdown'):
            self.chat_dropdown.apply_theme()

        if hasattr(self, 'notification_dropdown'):
            self.notification_dropdown.apply_theme()

    def update_translations(self):
        """Update all translated text elements"""
        self.home_button.setToolTip(self.translator.t("home_tooltip"))
        self.notification_button.setToolTip(self.translator.t("notifications_tooltip"))
        self.chat_button.setToolTip(self.translator.t("chat_tooltip"))
        self.search_bar.setPlaceholderText(self.translator.t("search_placeholder"))

    def set_notification_count(self, count):
        """Update the notification count display"""
        self.notification_button.set_notification_count(count)