from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPoint, QEvent
from PyQt5.QtWidgets import (QWidget, QLineEdit, QHBoxLayout, QPushButton,
                             QCompleter, QListView, QFrame, QShortcut,
                             QAbstractItemView, QStyledItemDelegate)
from PyQt5.QtGui import QFont, QColor, QKeySequence, QPainter, QPen, QBrush, QPainterPath
from typing import List, Optional

from themes import get_color


class SuggestionDelegate(QStyledItemDelegate):
    """Custom delegate for styling suggestion items in the completer popup"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hover_index = -1

    def paint(self, painter, option, index):
        """Override paint method to provide custom styling for each suggestion item"""
        # Get colors from parent theme if available
        try:
            bg_color = get_color('background')
            text_color = get_color('text')
            accent_color = get_color('highlight')

            # Determine if we need dark or light theme colors
            is_dark = QColor(bg_color).lightness() < 128
            hover_bg = QColor(accent_color).lighter(130) if is_dark else QColor(
                accent_color).lighter(150)
            hover_bg.setAlpha(70)  # Semi-transparent hover effect
        except:
            # Fallback colors
            bg_color = "#ffffff" if option.state & QAbstractItemView.State_Selected else "#f5f5f5"
            text_color = "#333333"
            accent_color = "#4a90e2"
            hover_bg = QColor(accent_color)
            hover_bg.setAlpha(70)
            is_dark = False

        # Selected item styling
        if option.state & QAbstractItemView.State_Selected:
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(accent_color))

            # Draw rounded rectangle for selection
            path = QPainterPath()
            path.addRoundedRect(option.rect.adjusted(4, 2, -4, -2), 6, 6)
            painter.drawPath(path)

            # Draw text in white or contrasting color
            text_brush = QBrush(QColor("white" if is_dark else "#ffffff"))
            painter.setPen(QPen(text_brush, 1))
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(option.rect.adjusted(15, 0, -10, 0), Qt.AlignVCenter,
                             index.data())
            painter.restore()

        # Hover styling (not selected)
        elif self.hover_index == index.row():
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(hover_bg)

            # Draw rounded rectangle for hover
            path = QPainterPath()
            path.addRoundedRect(option.rect.adjusted(4, 2, -4, -2), 6, 6)
            painter.drawPath(path)

            # Draw text
            painter.setPen(QPen(QColor(text_color), 1))
            painter.drawText(option.rect.adjusted(15, 0, -10, 0), Qt.AlignVCenter,
                             index.data())
            painter.restore()

        # Normal item styling
        else:
            painter.save()
            painter.setPen(QPen(QColor(text_color), 1))
            painter.drawText(option.rect.adjusted(15, 0, -10, 0), Qt.AlignVCenter,
                             index.data())
            painter.restore()

    def sizeHint(self, option, index):
        """Adjust the size of suggestion items for better spacing"""
        size = super().sizeHint(option, index)
        return QPoint(size.width(), size.height() + 10)  # Add vertical padding


class ModernCompleterPopup(QListView):
    """Enhanced list view for search suggestions with elegant visuals"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("suggestionsPopup")
        self.setFont(QFont("Arial", 10))
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.NoFrame)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setMouseTracking(True)  # Enable mouse tracking for hover effects

        # Use custom delegate for item rendering
        self.delegate = SuggestionDelegate(self)
        self.setItemDelegate(self.delegate)

    def mouseMoveEvent(self, event):
        """Track mouse position for hover effects"""
        index = self.indexAt(event.pos())
        if index.isValid():
            self.delegate.hover_index = index.row()
        else:
            self.delegate.hover_index = -1
        self.viewport().update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        """Clear hover state when mouse leaves the widget"""
        self.delegate.hover_index = -1
        self.viewport().update()
        super().leaveEvent(event)


class ModernSearchWidget(QWidget):
    """
    Sleek, modern search widget with elegant styling.

    Provides a permanently visible search interface with autocomplete
    suggestions and theme support.
    """
    search_submitted = pyqtSignal(str)

    def __init__(self, translator, database, parent=None):
        """
        Initialize the search widget with translator and database.

        Args:
            translator: Translation service object
            database: Database connection for suggestions
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.translator = translator
        self.database = database

        # Configuration - always visible at fixed width
        self.default_width = 350  # Increased default width

        # Setup components
        self._setup_ui()
        self._setup_shortcuts()

        # Set fixed width
        self.setMinimumWidth(self.default_width)

        # Apply initial theme
        self.apply_theme()

    def _setup_ui(self) -> None:
        """Create and arrange UI components with modern styling."""
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Container for styling and visual grouping
        self.container = QFrame()
        self.container.setObjectName("searchContainer")
        self.container.setFixedHeight(36)

        # Container layout
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(8, 2, 2, 2)
        container_layout.setSpacing(0)

        # Search icon (non-clickable)
        self.search_icon = QPushButton("🔍")
        self.search_icon.setObjectName("searchIcon")
        self.search_icon.setFixedSize(28, 28)
        self.search_icon.setEnabled(False)  # Just a visual element
        self.search_icon.setCursor(Qt.ArrowCursor)

        # Search input field
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("searchInput")
        self.search_edit.setFont(QFont("Arial", 10))
        self.search_edit.returnPressed.connect(self.submit_search)
        self.search_edit.setPlaceholderText(self._translate("search_placeholder"))
        self.search_edit.textChanged.connect(self._on_text_changed)

        # Search submit button (enter key icon)
        self.search_button = QPushButton("⏎")
        self.search_button.setObjectName("searchSubmitButton")
        self.search_button.setCursor(Qt.PointingHandCursor)
        self.search_button.setFixedSize(28, 28)
        self.search_button.setToolTip(
            self._translate("search_submit_tooltip", "Submit search"))
        self.search_button.clicked.connect(self.submit_search)

        # Add components to container
        container_layout.addWidget(self.search_icon)
        container_layout.addWidget(self.search_edit)
        container_layout.addWidget(self.search_button)

        # Add container to main layout
        layout.addWidget(self.container)

        # Setup search suggestions
        self._setup_suggestions()

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts for the search widget."""
        # Escape key to clear search
        self.escape_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.escape_shortcut.activated.connect(self.clear_search)

        # Ctrl+F to focus search
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self.window())
        self.search_shortcut.activated.connect(self._focus_search)

    def _focus_search(self) -> None:
        """Focus the search input field."""
        self.search_edit.setFocus()
        self.search_edit.selectAll()

    def _setup_suggestions(self) -> None:
        """Setup search suggestions with autocomplete functionality."""
        suggestions = self._get_search_suggestions()
        if not suggestions:
            return

        # Create and configure completer
        self.completer = QCompleter(suggestions)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(
            Qt.MatchContains)  # Match anywhere in suggestion text

        # Create custom popup for suggestions
        popup = ModernCompleterPopup()  # Use the enhanced popup class
        popup.setMinimumWidth(300)  # Ensure popup is wide enough for suggestions

        # Style the popup scrollbar to match theme
        self.completer.setPopup(popup)

        # Set completer for search input
        self.search_edit.setCompleter(self.completer)

        # Connect completer activated signal
        self.completer.activated.connect(self.submit_search)

    def _get_search_suggestions(self) -> List[str]:
        """
        Get search suggestions from database or translation service.

        Returns:
            List of suggestion strings
        """
        try:
            # First try to get suggestions from database if available
            if hasattr(self.database, 'get_search_suggestions'):
                db_suggestions = self.database.get_search_suggestions()
                if db_suggestions and len(db_suggestions) > 0:
                    return db_suggestions

            # Fall back to translated static suggestions
            return [
                self._translate("suggestion_parts"),
                self._translate("suggestion_service"),
                self._translate("suggestion_repair"),
                self._translate("suggestion_brands"),
                self._translate("suggestion_inventory")
            ]
        except Exception as e:
            # Log error instead of silently failing
            print(f"Error loading search suggestions: {str(e)}")
            return ["Parts", "Service", "Repair", "Brands", "Inventory"]

    def _translate(self, key: str, default: str = "") -> str:
        """
        Get translated text for the given key.

        Args:
            key: Translation key
            default: Default text if translation fails

        Returns:
            Translated string or default/key if translation fails
        """
        try:
            if hasattr(self.translator, 't'):
                return self.translator.t(key)
            return default or key
        except Exception:
            return default or key

    def _on_text_changed(self, text: str) -> None:
        """
        Handle text changes in the search input.

        Args:
            text: Current text in the search field
        """
        # For future enhancements - real-time search behavior
        pass

    def submit_search(self) -> None:
        """Submit the current search query."""
        search_text = self.search_edit.text().strip()
        if search_text:
            # Emit signal with search text
            self.search_submitted.emit(search_text)

            # Clear search
            self.search_edit.clear()

            # Visual feedback (optional)
            self.search_button.setStyleSheet(
                "background-color: rgba(255, 255, 255, 0.25);")
            QTimer.singleShot(200, self._reset_button_style)

    def _reset_button_style(self) -> None:
        """Reset button style after visual feedback."""
        self.search_button.setStyleSheet("")
        self.apply_theme()

    def clear_search(self) -> None:
        """Clear search input."""
        self.search_edit.clear()

    def update_translations(self) -> None:
        """Update all translated text elements."""
        self.search_edit.setPlaceholderText(
            self._translate("search_placeholder", "Search..."))
        self.search_button.setToolTip(
            self._translate("search_submit_tooltip", "Submit search"))

        # Refresh suggestions if needed
        if hasattr(self, 'completer'):
            self.completer.setModel(None)  # Clear old model
            self.completer = QCompleter(self._get_search_suggestions())
            self.completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.completer.setFilterMode(Qt.MatchContains)

            # Preserve popup settings
            popup = ModernCompleterPopup()
            popup.setMinimumWidth(300)
            self.completer.setPopup(popup)

            self.search_edit.setCompleter(self.completer)

    def apply_theme(self) -> None:
        """Apply theme styling to all components."""
        try:
            # Get colors from theme system
            bg_color = get_color('header')
            text_color = get_color('text')
            card_bg = get_color('card_bg', get_color('background'))

            # Try to get accent color, fall back to a default if not available
            try:
                accent_color = get_color('accent')
            except:
                # Create a lighter/darker variation of border color as fallback
                border_color = get_color('border')
                border_qcolor = QColor(border_color)
                bg_qcolor = QColor(bg_color)
                is_dark = bg_qcolor.lightness() < 128

                if is_dark:
                    accent_color = border_qcolor.lighter(150).name()
                else:
                    accent_color = border_qcolor.darker(150).name()

            # Get QColor object for luminance calculations
            bg = QColor(bg_color)
            is_dark = bg.lightness() < 128

            # Create color variations based on theme brightness
            if is_dark:
                container_bg = "rgba(255, 255, 255, 0.12)"
                button_bg = "rgba(255, 255, 255, 0.15)"
                button_hover = "rgba(255, 255, 255, 0.25)"
                selection_bg = accent_color
                focus_border = accent_color
                popup_bg = QColor(card_bg).darker(110).name()
                shadow_color = "rgba(0, 0, 0, 0.7)"
            else:
                container_bg = "rgba(0, 0, 0, 0.05)"
                button_bg = "rgba(0, 0, 0, 0.08)"
                button_hover = "rgba(0, 0, 0, 0.15)"
                selection_bg = accent_color
                focus_border = accent_color
                popup_bg = QColor(card_bg).lighter(103).name()
                shadow_color = "rgba(0, 0, 0, 0.2)"

            # Apply unified styling with focus states and transitions
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
                    selection-color: white;
                }}

                #searchInput:focus {{
                    border: none;
                    outline: none;
                }}

                #searchContainer:focus-within {{
                    border: 1px solid {focus_border};
                }}

                #searchIcon {{
                    background-color: transparent;
                    color: {text_color};
                    border: none;
                    padding: 0px;
                    font-size: 14px;
                    min-width: 28px;
                    min-height: 28px;
                }}

                #searchSubmitButton {{
                    background-color: {button_bg};
                    color: {text_color};
                    border-radius: 14px;
                    border: none;
                    padding: 0px;
                    font-size: 14px;
                    min-width: 28px;
                    min-height: 28px;
                    transition: background-color 0.2s;
                }}

                #searchSubmitButton:hover {{
                    background-color: {button_hover};
                }}

                #searchSubmitButton:pressed {{
                    background-color: {accent_color};
                    color: white;
                }}

                /* Enhanced suggestion popup styling */
                #suggestionsPopup {{
                    background-color: {popup_bg};
                    border: 1px solid {focus_border};
                    border-radius: 12px;
                    padding: 8px 4px;
                    margin-top: 2px;
                    font-size: 11pt;
                }}

                /* Scrollbar styling for suggestions popup */
                #suggestionsPopup QScrollBar:vertical {{
                    background: transparent;
                    width: 6px;
                    margin: 4px 2px;
                    border-radius: 3px;
                }}

                #suggestionsPopup QScrollBar::handle:vertical {{
                    background: {focus_border};
                    border-radius: 3px;
                    min-height: 20px;
                }}

                #suggestionsPopup QScrollBar::handle:vertical:hover {{
                    background: {accent_color};
                }}

                #suggestionsPopup QScrollBar::add-line:vertical,
                #suggestionsPopup QScrollBar::sub-line:vertical {{
                    height: 0px;
                }}

                #suggestionsPopup QScrollBar::add-page:vertical,
                #suggestionsPopup QScrollBar::sub-page:vertical {{
                    background: transparent;
                }}
            """)

            # Style the completer popup if it exists
            if hasattr(self, 'completer') and self.completer:
                popup = self.completer.popup()
                if popup:
                    # Apply a drop shadow effect to the popup
                    popup.setStyleSheet(f"""
                        #suggestionsPopup {{
                            background-color: {popup_bg};
                            border: 1px solid {focus_border};
                            border-radius: 12px;
                            padding: 8px 4px;
                            margin-top: 2px;
                            font-size: 11pt;
                        }}

                        /* Scrollbar styling for suggestions popup */
                        QScrollBar:vertical {{
                            background: transparent;
                            width: 6px;
                            margin: 4px 2px;
                            border-radius: 3px;
                        }}

                        QScrollBar::handle:vertical {{
                            background: {focus_border};
                            border-radius: 3px;
                            min-height: 20px;
                        }}

                        QScrollBar::handle:vertical:hover {{
                            background: {accent_color};
                        }}

                        QScrollBar::add-line:vertical,
                        QScrollBar::sub-line:vertical {{
                            height: 0px;
                        }}

                        QScrollBar::add-page:vertical,
                        QScrollBar::sub-page:vertical {{
                            background: transparent;
                        }}
                    """)

        except Exception as e:
            print(f"Error applying theme: {str(e)}")
            # Fall back to basic styling that works in most cases
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

                #searchIcon {
                    background-color: transparent;
                    color: white;
                    border: none;
                }

                #searchSubmitButton {
                    background-color: rgba(255, 255, 255, 0.15);
                    color: white;
                    border-radius: 14px;
                    border: none;
                }

                #searchSubmitButton:hover {
                    background-color: rgba(255, 255, 255, 0.25);
                }
            """)


# Primary alias for backward compatibility
class SearchWidget(ModernSearchWidget):
    """Alias for backward compatibility with existing imports."""
    pass