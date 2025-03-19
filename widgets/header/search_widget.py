from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QLineEdit, QHBoxLayout, QPushButton,
                             QCompleter, QListView)
from PyQt5.QtGui import QIcon, QPainter, QColor, QPen, QFont

from themes import get_color


class LuxurySearchBox(QLineEdit):
    """Premium styled search input with simplified implementation"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("luxurySearchBox")

        # Refined styling - simpler and safer
        self.setMinimumWidth(250)
        self.setFixedHeight(36)

        # Setup premium font
        font = QFont("Arial", 11)
        self.setFont(font)

        # Tracking states
        self.hover = False

        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)

        # Remove standard border
        self.setFrame(False)

    def enterEvent(self, event):
        """Handle hover state"""
        self.hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle hover state"""
        self.hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        """Custom paint with premium details but safer implementation"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Get theme colors
        bg_color = self.palette().color(self.backgroundRole())
        text_color = self.palette().color(self.foregroundRole())

        # Create elegant rounded rectangle
        rect = self.rect().adjusted(2, 2, -2, -2)

        # Determine background color based on state
        if self.hasFocus():
            bg_color = bg_color.lighter(
                110) if bg_color.lightness() < 128 else bg_color.darker(105)
        elif self.hover:
            bg_color = bg_color.lighter(
                105) if bg_color.lightness() < 128 else bg_color.darker(102)

        # Draw background
        painter.setPen(Qt.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(rect, 18, 18)

        # Draw subtle border
        border_color = QColor(text_color)
        border_color.setAlpha(30)
        if self.hasFocus():
            border_color.setAlpha(60)

        pen = QPen(border_color)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 18, 18)

        # Need to call the parent's paint method for the text
        super().paintEvent(event)


class LuxurySearchButton(QPushButton):
    """Elegant search button with premium styling"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("luxurySearchButton")
        self.setCursor(Qt.PointingHandCursor)

        # Set fixed size for search button
        self.setFixedSize(36, 36)

        # States for visual effects
        self.hover = False
        self.pressed = False

        # Enable mouse tracking
        self.setMouseTracking(True)

    def enterEvent(self, event):
        """Handle hover state"""
        self.hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle hover state"""
        self.hover = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Handle press state"""
        self.pressed = True
        self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle release state"""
        self.pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        """Custom paint with premium details - safer implementation"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Get theme colors
        bg_color = self.palette().color(self.backgroundRole())
        text_color = self.palette().color(self.foregroundRole())

        # Create elegant circle path
        rect = self.rect()
        center_x = rect.width() // 2
        center_y = rect.height() // 2
        radius = min(rect.width(), rect.height()) // 2 - 4

        # Background
        if self.pressed:
            bg_color = bg_color.darker(105)
        elif self.hover:
            bg_color = bg_color.lighter(
                110) if bg_color.lightness() < 128 else bg_color.darker(105)

        painter.setPen(Qt.NoPen)
        painter.setBrush(bg_color)
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

        # Draw search icon
        icon_pen = QPen(text_color)
        icon_pen.setWidth(2)
        icon_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(icon_pen)

        # Draw search circle (simpler method)
        search_radius = radius * 0.55
        painter.drawEllipse(center_x - search_radius * 0.7,
                            center_y - search_radius * 0.7,
                            search_radius * 1.4, search_radius * 1.4)

        # Search handle
        handle_start_x = center_x + search_radius * 0.6
        handle_start_y = center_y + search_radius * 0.6
        handle_end_x = center_x + radius * 0.8
        handle_end_y = center_y + radius * 0.8
        painter.drawLine(handle_start_x, handle_start_y, handle_end_x, handle_end_y)


class SearchSuggestionView(QListView):
    """Elegant suggestion dropdown with premium styling"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("searchSuggestions")

        # Refined styling
        self.setFont(QFont("Arial", 10))
        self.setFrameShape(QListView.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Elegant selection style via stylesheet
        self.setStyleSheet("""
            QListView::item {
                padding: 8px 12px;
                border-radius: 4px;
            }
            QListView::item:selected {
                background-color: rgba(120, 120, 120, 0.2);
            }
            QListView::item:hover:!selected {
                background-color: rgba(120, 120, 120, 0.1);
            }
        """)


class SearchWidget(QWidget):
    """Premium search widget with elegant styling and comprehensive functionality"""
    search_submitted = pyqtSignal(str)

    def __init__(self, translator, database, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.database = database

        self.setup_ui()
        self.setup_completer()

    def setup_ui(self):
        """Create and arrange the premium UI components"""
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Luxury search container
        container = QWidget()
        container.setObjectName("searchContainer")
        container.setFixedHeight(38)
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(1, 1, 1, 1)
        container_layout.setSpacing(0)

        # Premium search box
        self.search_box = LuxurySearchBox()
        self.search_box.returnPressed.connect(self.submit_search)

        # Elegant search button
        self.search_button = LuxurySearchButton()
        self.search_button.clicked.connect(self.submit_search)

        # Add widgets to container
        container_layout.addWidget(self.search_box)
        container_layout.addWidget(self.search_button)

        # Add container to main layout
        layout.addWidget(container)

        # Update placeholder text
        self.update_translations()

    def setup_completer(self):
        """Setup autocomplete with elegant styling"""
        # Get recent searches - use a safer approach
        suggestions = []
        try:
            suggestions = self.get_search_suggestions()
        except:
            # Fallback suggestions if there's an error
            suggestions = ["parts", "service", "repair"]

        self.completer = QCompleter(suggestions)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)

        # Set popup with premium styling
        self.popup = SearchSuggestionView()
        self.completer.setPopup(self.popup)

        # Set completer for search box
        self.search_box.setCompleter(self.completer)

    def get_search_suggestions(self):
        """Get search suggestions safely"""
        try:
            # Implement database query for search history/suggestions
            # For now, return sample suggestions with safer translator calls
            t = getattr(self.translator, 't', lambda x: x)
            return [
                t("suggestion_parts"),
                t("suggestion_service"),
                t("suggestion_repair"),
                t("suggestion_brands")
            ]
        except:
            return ["parts", "service", "repair", "brands"]

    def submit_search(self):
        """Handle search submission with validation"""
        search_text = self.search_box.text().strip()
        if search_text:
            self.search_submitted.emit(search_text)

    def clear_search(self):
        """Clear the search input"""
        self.search_box.clear()

    def update_translations(self):
        """Update translations for all text elements"""
        try:
            placeholder = self.translator.t("search_placeholder")
            self.search_box.setPlaceholderText(placeholder)
        except:
            self.search_box.setPlaceholderText("Search...")

    def apply_theme(self):
        """Apply current theme colors"""
        try:
            # Get theme colors safely
            bg_color = get_color('header')
            text_color = get_color('text')

            # Main container styling - simplified
            self.setStyleSheet(f"""
                #searchContainer {{
                    background-color: transparent;
                    border-radius: 20px;
                }}

                #luxurySearchBox {{
                    color: {text_color};
                    background-color: transparent;
                    border: none;
                    padding-left: 12px;
                    padding-right: 12px;
                }}
            """)
        except:
            # Fallback styling if there's an error
            self.setStyleSheet("""
                #searchContainer {
                    background-color: transparent;
                    border-radius: 20px;
                }

                #luxurySearchBox {
                    color: white;
                    background-color: transparent;
                    border: none;
                    padding-left: 12px;
                    padding-right: 12px;
                }
            """)