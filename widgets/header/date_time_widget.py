from PyQt5.QtCore import Qt, QTimer, QDateTime, QLocale
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QFontMetrics

from themes import get_color


class LuxuryDateTimeWidget(QWidget):
    """
    Elegant date and time display with premium styling.
    Updates automatically and supports multiple languages.
    """

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator

        # Setup timer for regular updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)  # Update every second

        # Setup UI
        self.setup_ui()
        self.update_datetime()

        # Enable mouse hover tracking for visual effects
        self.setMouseTracking(True)
        self.hover = False

    def setup_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Time label
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        font = QFont("Arial", 13)
        font.setBold(True)
        self.time_label.setFont(font)

        # Date label
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignCenter)
        font = QFont("Arial", 10)
        self.date_label.setFont(font)

        # Add to layout
        layout.addWidget(self.time_label)
        layout.addWidget(self.date_label)

        # Set fixed width for consistency
        self.setFixedWidth(150)

    def update_datetime(self):
        """Update the date and time display"""
        try:
            now = QDateTime.currentDateTime()

            # Get locale for the current language
            lang = getattr(self.translator, 'language', 'en')
            locale = QLocale(QLocale.Hebrew if lang == 'he' else QLocale.English)

            # Format time based on locale
            time_str = locale.toString(now, "hh:mm:ss")
            self.time_label.setText(time_str)

            # Format date based on locale
            if lang == 'he':
                # Hebrew date format
                date_str = locale.toString(now, "dd MMMM yyyy")
            else:
                # English date format
                date_str = locale.toString(now, "MMMM dd, yyyy")

            self.date_label.setText(date_str)
        except (RuntimeError, AttributeError, KeyboardInterrupt):
            # Handle errors during shutdown
            pass

    def enterEvent(self, event):
        """Handle mouse enter event for hover effects"""
        self.hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle mouse leave event for hover effects"""
        self.hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        """Custom paint for luxury appearance"""
        super().paintEvent(event)

        # Create painter with antialiasing
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Get text colors from theme
        text_color = self.palette().color(self.foregroundRole())

        # Calculate dimensions
        width = self.width()
        height = self.height()

        # Draw subtle container if hovered
        if self.hover:
            # Create elegant glow effect on hover
            glow_color = QColor(text_color)
            glow_color.setAlpha(10)  # Very subtle

            painter.setPen(Qt.NoPen)
            painter.setBrush(glow_color)
            painter.drawRoundedRect(2, 2, width - 4, height - 4, 8, 8)

        # Draw elegant separator line between time and date
        line_pen = QPen(text_color)
        line_pen.setWidthF(0.5)  # Thin elegant line
        line_pen.setCapStyle(Qt.RoundCap)

        # Get position for the line (between labels)
        time_height = self.time_label.height()

        # Only draw line if not too narrow
        if width > 60:
            line_width = min(width - 40, 70)  # Limit line width for elegance
            line_x_start = (width - line_width) / 2
            line_x_end = line_x_start + line_width

            # Draw the line with slight opacity for elegance
            line_color = QColor(text_color)
            line_color.setAlpha(80)  # Subtle transparency
            line_pen.setColor(line_color)

            painter.setPen(line_pen)
            painter.drawLine(line_x_start, time_height, line_x_end, time_height)

    def apply_theme(self):
        """Apply current theme colors"""
        text_color = get_color('text')

        self.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                background-color: transparent;
            }}
        """)

    def update_translations(self):
        """Update when language changes"""
        self.update_datetime()

    def closeEvent(self, event):
        """Handle widget close event"""
        self.stop_timer()
        super().closeEvent(event)

    def stop_timer(self):
        """Safely stop the timer"""
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()

    def hideEvent(self, event):
        """Handle widget hide event"""
        # Stop timer when widget is hidden (like when window is closed)
        self.stop_timer()
        super().hideEvent(event)

    def __del__(self):
        """Destructor to ensure timer is stopped"""
        try:
            self.stop_timer()
        except:
            pass