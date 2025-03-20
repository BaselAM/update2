import sys
import logging
from pathlib import Path
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, \
    QStackedWidget, QMessageBox
from PyQt5.QtGui import QIcon

# Import widgets
from widgets.layout import HeaderWidget, FooterWidget, CopyrightWidget
from widgets.header import TopBarWidget
from widgets.products.product_widget import ProductsWidget
from widgets.statistics import StatisticsWidget
from widgets.settings import SettingsWidget
from widgets.help import HelpWidget
from home_page import HomePageWidget

from translator import Translator
from database.settings_db import SettingsDB
from database.car_parts_db import CarPartsDB
from themes import set_theme, get_color
# Add these imports near the top of gui.py
from widgets.parts_navigation import PartsNavigationContainer
from PyQt5.QtWidgets import QMessageBox  # Make sure this is imported


class GUI(QMainWindow):
    language_changed = pyqtSignal()

    def __init__(self, car_parts_db=None):
        super().__init__()
        # Initialize databases
        self.settings_db = SettingsDB()

        # Use provided database instance or create a new one
        self.parts_db = car_parts_db if car_parts_db else CarPartsDB()
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
        # Add this line:
        self.parts_navigation_widget = PartsNavigationContainer(self.translator,
                                                                self.parts_db)
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
        # Add this line right here:
        self.content_stack.addWidget(self.parts_navigation_widget)

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
        """Open the parts navigation system"""
        try:
            self.content_stack.setCurrentWidget(self.parts_navigation_widget)
        except Exception as e:
            print(f"Error showing parts navigation: {str(e)}")
            QMessageBox.warning(self, "Parts Navigation",
                                f"Could not load parts navigation: {str(e)}")

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