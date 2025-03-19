from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QPropertyAnimation, QEasingCurve
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import (QFont, QFontMetrics, QColor, QPainter, QPainterPath,
                         QLinearGradient, QRadialGradient, QPen, QBrush)

from themes import get_color


class ExquisiteTitleLabel(QWidget):
    """
    Ultra-premium title with advanced visual effects and meticulous styling.
    """

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator

        # Set generous size for visual prominence
        self.setMinimumHeight(60)
        self.setMinimumWidth(400)

        # Create premium typography
        self.font_primary = QFont("Arial", 32)  # Luxury size
        self.font_primary.setWeight(QFont.Black)
        self.font_primary.setLetterSpacing(QFont.AbsoluteSpacing, 3)  # Expansive spacing

        # Visual effect properties
        self.glow_opacity = 15  # Subtle glow effect
        self.shadow_offset = 2  # Slightly deeper shadow for dimension
        self.hover_active = False

        # Track state for visual effects
        self.setMouseTracking(True)

        # Update text initially
        self.update_text()

    def update_text(self):
        """Update the title text based on current language"""
        try:
            if getattr(self.translator, 'language', 'en') == 'he':
                self.text = "חלקי חילוף אבו מוך"
                # Right-to-left layout
                self.setLayoutDirection(Qt.RightToLeft)
            else:
                self.text = "ABU MUKH CAR PARTS"  # All caps for luxury feel
                self.setLayoutDirection(Qt.LeftToRight)
        except:
            self.text = "ABU MUKH CAR PARTS"
            self.setLayoutDirection(Qt.LeftToRight)

    def enterEvent(self, event):
        """Subtle hover effect"""
        self.hover_active = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Reset hover effect"""
        self.hover_active = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        """Premium paint implementation with exquisite details"""
        # Create painter with highest quality settings
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

        # Get base colors from theme
        base_color = self.palette().color(self.foregroundRole())
        bg_color = self.palette().color(self.backgroundRole())

        # Create refined font metrics
        painter.setFont(self.font_primary)
        fm = QFontMetrics(self.font_primary)

        # Calculate precise text dimensions
        text_width = fm.horizontalAdvance(self.text) if hasattr(fm,
                                                                'horizontalAdvance') else fm.width(
            self.text)
        text_height = fm.height()

        # Calculate perfect centering position
        x = (self.width() - text_width) / 2
        y = (self.height() + text_height) / 2 - fm.descent()

        # Create refined text path for advanced effects
        text_path = QPainterPath()
        text_path.addText(x, y, self.font_primary, self.text)

        # Draw subtle background glow if hovered (ultra-subtle effect)
        if self.hover_active:
            glow = QRadialGradient(self.width() / 2, self.height() / 2, self.width() / 2)
            glow_color = QColor(base_color)
            glow_color.setAlpha(5)  # Almost imperceptible
            glow.setColorAt(0, glow_color)
            glow_color.setAlpha(0)
            glow.setColorAt(1, glow_color)
            painter.fillRect(self.rect(), glow)

        # Draw multi-layered shadows for depth (3 layers with decreasing opacity)
        for i in range(3):
            shadow_color = QColor(0, 0, 0, 40 - (i * 10))  # Decreasing opacity
            offset = self.shadow_offset - (i * 0.5)  # Decreasing offset
            shadow_path = QPainterPath(text_path)
            shadow_path.translate(offset, offset)
            painter.fillPath(shadow_path, shadow_color)

        # Draw main text with subtle gradient effect
        text_gradient = QLinearGradient(x, y - text_height, x, y)
        brightness = 100 if self.hover_active else 0  # Subtle brightening on hover

        # Create elegant gradient effect
        main_color = QColor(base_color)
        highlight_color = QColor(base_color).lighter(105 + brightness)

        text_gradient.setColorAt(0, highlight_color)
        text_gradient.setColorAt(1, main_color)

        # Apply gradient to text
        painter.fillPath(text_path, QBrush(text_gradient))

        # Draw ultra-thin outline for definition (0.5px equivalent)
        outline_pen = QPen(QColor(base_color).darker(110))
        outline_pen.setWidthF(0.5)
        painter.strokePath(text_path, outline_pen)

        # Optional: Draw subtle accent lines for luxury branding
        accent_color = QColor(base_color)
        accent_color.setAlpha(40)
        accent_pen = QPen(accent_color)
        accent_pen.setWidthF(1)

        # Draw two thin accent lines above and below
        line_width = min(text_width + 100, self.width() - 60)
        line_y_top = y - text_height - 10
        line_y_bottom = y + 12

        # Calculate line positions
        line_x_start = (self.width() - line_width) / 2
        line_x_end = line_x_start + line_width

        # Draw top decorative line
        painter.setPen(accent_pen)
        painter.drawLine(line_x_start, line_y_top, line_x_end, line_y_top)

        # Draw bottom decorative line
        painter.drawLine(line_x_start, line_y_bottom, line_x_end, line_y_bottom)

    def update_translations(self):
        """Handle language changes with refined update"""
        self.update_text()
        self.update()


class HeaderWidget(QWidget):
    """Refined luxury header for the application"""

    def __init__(self, translator, home_callback=None):
        super().__init__()
        self.translator = translator
        self.home_callback = home_callback
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        # Create layout with generous spacing
        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)  # Extremely generous margins

        # Add exquisite title
        self.title_label = ExquisiteTitleLabel(self.translator, self)
        layout.addWidget(self.title_label)

        # Expansive header height for dramatic presence
        self.setFixedHeight(90)  # Commanding presence

    def paintEvent(self, event):
        """Enhanced header background with subtle gradient"""
        super().paintEvent(event)

        # Background will be handled by stylesheet and theme
        # This allows for custom gradient if desired later

    def apply_theme(self):
        header_bg = get_color('header')
        text_color = get_color('text')

        # Determine if using dark theme for effect adjustments
        is_dark_theme = QColor(header_bg).lightness() < 128

        # Create subtle border effect for separation
        border_color = QColor(text_color)
        border_color.setAlpha(30)  # Very subtle

        # Apply luxurious styling to the header
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {header_bg};
                color: {text_color};
                border-bottom: 1px solid rgba({border_color.red()}, {border_color.green()}, {border_color.blue()}, 0.3);
            }}
        """)

        # Title label styling is mostly handled in paint event for maximum control

    def update_translations(self):
        # Update the title for language change
        self.title_label.update_translations()


class FooterWidget(QWidget):
    """The footer widget shown at the bottom of the application"""

    def __init__(self, translator):
        super().__init__()
        self.translator = translator
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        self.status_label = QLabel(self.translator.t("status_ready"))
        layout.addWidget(self.status_label)

        layout.addStretch()

        self.version_label = QLabel(f"v1.0.0")
        layout.addWidget(self.version_label)

        self.setFixedHeight(30)

    def apply_theme(self):
        footer_bg = get_color('footer')
        text_color = get_color('text')

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {footer_bg};
                color: {text_color};
            }}
        """)

    def update_translations(self):
        self.status_label.setText(self.translator.t("status_ready"))


class CopyrightWidget(QWidget):
    """A small copyright notice at the bottom of the application"""

    def __init__(self, translator):
        super().__init__()
        self.translator = translator
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        copyright_text = "© 2023 Auto Parts Ltd. All rights reserved."
        self.copyright_label = QLabel(copyright_text)
        self.copyright_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.copyright_label)

        self.setFixedHeight(20)

    def apply_theme(self):
        bg_color = get_color('background')
        text_color = get_color('text')

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                color: {text_color};
            }}
            QLabel {{
                font-size: 8pt;
                color: {text_color};
            }}
        """)

    def update_translations(self):
        # No translation needed for copyright
        pass