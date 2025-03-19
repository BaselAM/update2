from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtWidgets import (QWidget, QLineEdit, QHBoxLayout, QPushButton,
                             QCompleter, QListView, QFrame)
from PyQt5.QtGui import QFont, QColor

from themes import get_color


class ModernSearchWidget(QWidget):
    """Sleek, modern expandable search widget with elegant styling"""
    search_submitted = pyqtSignal(str)

    def __init__(self, translator, database, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.database = database

        # Configuration
        self.expanded = False
        self.collapsed_width = 40
        self.expanded_width = 280

        # Setup UI
        self.setup_ui()

        # Setup animation
        self.setup_animation()

        # Initial collapsed state
        self.setFixedWidth(self.collapsed_width)
        self.setMaximumWidth(self.collapsed_width)

    def setup_ui(self):
        """Create sleek, modern UI"""
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Container for elegant styling
        self.container = QFrame()
        self.container.setObjectName("searchContainer")
        self.container.setFixedHeight(36)

        # Container layout
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(2, 2, 2, 2)
        container_layout.setSpacing(0)

        # Expand button (for collapsed state)
        self.expand_button = QPushButton("🔍")
        self.expand_button.setObjectName("searchExpandButton")
        self.expand_button.setCursor(Qt.PointingHandCursor)
        self.expand_button.setFixedSize(32, 32)
        self.expand_button.clicked.connect(self.expand)

        # Search input
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("searchInput")
        self.search_edit.setFont(QFont("Arial", 10))
        self.search_edit.returnPressed.connect(self.submit_search)
        self.search_edit.hide()  # Initially hidden when collapsed

        # Search button (for expanded state)
        self.search_button = QPushButton("⏎")
        self.search_button.setObjectName("searchSubmitButton")
        self.search_button.setCursor(Qt.PointingHandCursor)
        self.search_button.setFixedSize(32, 32)
        self.search_button.clicked.connect(self.submit_search)
        self.search_button.hide()  # Initially hidden when collapsed

        # Add widgets to container
        container_layout.addWidget(self.expand_button)
        container_layout.addWidget(self.search_edit)
        container_layout.addWidget(self.search_button)

        # Add container to main layout
        layout.addWidget(self.container)

        # Setup suggestions with sleek styling
        self.setup_suggestions()

        # Set placeholder text
        self.update_translations()

    def setup_animation(self):
        """Setup smooth animation for expansion/collapse"""
        self.animation = QPropertyAnimation(self, b"maximumWidth")
        self.animation.setDuration(200)  # Fast, sleek animation
        self.animation.setEasingCurve(QEasingCurve.OutQuad)
        self.animation.finished.connect(self.animation_finished)

    def setup_suggestions(self):
        """Setup elegant search suggestions"""
        try:
            # Simple suggestions
            suggestions = self.get_search_suggestions()

            # Create completer
            self.completer = QCompleter(suggestions)
            self.completer.setCaseSensitivity(Qt.CaseInsensitive)

            # Create sleek popup
            popup = QListView()
            popup.setObjectName("suggestionsPopup")
            popup.setFont(QFont("Arial", 10))

            # Set popup to completer
            self.completer.setPopup(popup)

            # Add to search edit
            self.search_edit.setCompleter(self.completer)
        except:
            # Fail silently - not critical
            pass

    def get_search_suggestions(self):
        """Get search suggestions"""
        try:
            # Get translator function
            t = getattr(self.translator, 't', lambda x: x)

            # Return suggestions
            return [
                t("suggestion_parts"),
                t("suggestion_service"),
                t("suggestion_repair"),
                t("suggestion_brands")
            ]
        except:
            # Fallback suggestions
            return ["Parts", "Service", "Repair", "Brands"]

    def expand(self):
        """Expand with elegant animation"""
        if self.expanded:
            return

        self.expanded = True

        # Update UI for expanded state
        self.expand_button.hide()
        self.search_edit.show()
        self.search_button.show()

        # Animate expansion
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(self.expanded_width)
        self.animation.start()

    def collapse(self):
        """Collapse with elegant animation"""
        if not self.expanded:
            return

        self.expanded = False

        # Clear focus
        self.search_edit.clearFocus()

        # Animate collapse
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(self.collapsed_width)
        self.animation.start()

    def animation_finished(self):
        """Handle animation completion"""
        if self.expanded:
            # Focus search when expanded
            self.search_edit.setFocus()
        else:
            # Update UI for collapsed state
            self.search_edit.hide()
            self.search_button.hide()
            self.expand_button.show()

    def submit_search(self):
        """Submit search query"""
        search_text = self.search_edit.text().strip()
        if search_text:
            # Emit signal
            self.search_submitted.emit(search_text)

            # Clear search
            self.search_edit.clear()

            # Collapse after short delay
            QTimer.singleShot(200, self.collapse)

    def clear_search(self):
        """Clear search and collapse"""
        self.search_edit.clear()
        self.collapse()

    def update_translations(self):
        """Update translations"""
        try:
            placeholder = self.translator.t("search_placeholder")
            self.search_edit.setPlaceholderText(placeholder)
        except:
            self.search_edit.setPlaceholderText("Search...")

    def apply_theme(self):
        """Apply sleek, modern styling"""
        try:
            # Get colors from theme
            bg_color = get_color('header')
            text_color = get_color('text')

            # Get QColor object for calculations
            bg = QColor(bg_color)
            is_dark = bg.lightness() < 128

            # Create elegant color variations
            if is_dark:
                container_bg = "rgba(255, 255, 255, 0.12)"
                button_bg = "rgba(255, 255, 255, 0.15)"
                button_hover = "rgba(255, 255, 255, 0.25)"
                selection_bg = "rgba(255, 255, 255, 0.2)"
            else:
                container_bg = "rgba(0, 0, 0, 0.05)"
                button_bg = "rgba(0, 0, 0, 0.08)"
                button_hover = "rgba(0, 0, 0, 0.15)"
                selection_bg = "rgba(0, 0, 0, 0.1)"

            # Apply modern styling
            self.setStyleSheet(f"""
                #searchContainer {{
                    background-color: {container_bg};
                    border-radius: 18px;
                    border: none;
                }}

                #searchInput {{
                    background-color: transparent;
                    color: {text_color};
                    border: none;
                    padding: 0px 5px;
                    margin: 0px 5px;
                    font-size: 10pt;
                    selection-background-color: {selection_bg};
                }}

                #searchExpandButton, #searchSubmitButton {{
                    background-color: {button_bg};
                    color: {text_color};
                    border-radius: 16px;
                    border: none;
                    padding: 0px;
                    font-size: 14px;
                }}

                #searchExpandButton:hover, #searchSubmitButton:hover {{
                    background-color: {button_hover};
                }}

                #suggestionsPopup {{
                    background-color: {container_bg};
                    border: none;
                    border-radius: 10px;
                    padding: 5px;
                }}

                #suggestionsPopup::item {{
                    padding: 5px 10px;
                    border-radius: 5px;
                }}

                #suggestionsPopup::item:selected {{
                    background-color: {button_hover};
                }}
            """)
        except:
            # Fallback styling
            self.setStyleSheet("""
                #searchContainer {
                    background-color: rgba(255, 255, 255, 0.1);
                    border-radius: 18px;
                }

                #searchInput {
                    background-color: transparent;
                    color: white;
                    border: none;
                    padding: 0px 5px;
                }

                #searchExpandButton, #searchSubmitButton {
                    background-color: rgba(255, 255, 255, 0.15);
                    color: white;
                    border-radius: 16px;
                    border: none;
                }

                #searchExpandButton:hover, #searchSubmitButton:hover {
                    background-color: rgba(255, 255, 255, 0.25);
                }
            """)


# For backward compatibility
class SearchWidget(ModernSearchWidget):
    """Alias for backward compatibility"""
    pass


# Additional aliases for existing imports
class UltraDeluxeSearchWidget(ModernSearchWidget):
    """Alias for compatibility"""
    pass


class SimpleElegantSearchWidget(ModernSearchWidget):
    """Alias for compatibility"""
    pass


class PremiumSearchWidget(ModernSearchWidget):
    """Alias for compatibility"""
    pass