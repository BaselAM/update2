from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QTimer, \
    pyqtProperty, QSize
from PyQt5.QtWidgets import QLabel, QWidget
from PyQt5.QtGui import QFont, QPainter, QColor


class AnimatedTitleWidget(QWidget):
    """
    An animated title widget that scrolls text horizontally with a pause in the middle.
    Supports bilingual text (Hebrew and English).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hebrew_text = "חלקי חילוף אבו מוך"
        self.english_text = "Abu Mukh Car Parts"
        self.text_pos = 0
        self.setMinimumHeight(40)

        # Animation properties
        self._animation_speed = 50  # Lower is faster
        self._pause_time_ms = 2000  # Pause time in the middle in milliseconds
        self._text_color = QColor("#3F51B5")  # Indigo blue color
        self._font_size = 16

        # Configure appearance
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: transparent;")

        # Initialize animation
        self.animation = QPropertyAnimation(self, b"textPosition")
        self.animation.setEasingCurve(QEasingCurve.Linear)
        self.animation.finished.connect(self.on_animation_finished)

        # Start the animation
        QTimer.singleShot(500, self.start_animation)

    def get_text_position(self):
        return self.text_pos

    def set_text_position(self, pos):
        self.text_pos = pos
        self.update()

    textPosition = pyqtProperty(int, get_text_position, set_text_position)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        # Hebrew font (right to left)
        hebrew_font = QFont("Arial", self._font_size)
        hebrew_font.setBold(True)

        # English font
        english_font = QFont("Arial", self._font_size - 2)  # Slightly smaller for English

        # Calculate text widths
        painter.setFont(hebrew_font)
        hebrew_width = painter.fontMetrics().width(self.hebrew_text)

        painter.setFont(english_font)
        english_width = painter.fontMetrics().width(self.english_text)

        # Calculate total width needed and vertical positioning
        total_width = hebrew_width + english_width + 30  # 30px spacing between texts

        # Draw Hebrew text
        painter.setFont(hebrew_font)
        painter.setPen(self._text_color)
        hebrew_x = self.text_pos
        painter.drawText(hebrew_x,
                         self.height() // 2 + painter.fontMetrics().ascent() // 2,
                         self.hebrew_text)

        # Draw English text
        painter.setFont(english_font)
        english_x = hebrew_x + hebrew_width + 30  # 30px after Hebrew text
        painter.drawText(english_x,
                         self.height() // 2 + painter.fontMetrics().ascent() // 2,
                         self.english_text)

    def start_animation(self):
        # Calculate positions for animation
        width = self.width()
        painter = QPainter()

        # Hebrew font
        hebrew_font = QFont("Arial", self._font_size)
        hebrew_font.setBold(True)
        painter.setFont(hebrew_font)
        hebrew_width = painter.fontMetrics().boundingRect(self.hebrew_text).width()

        # English font
        english_font = QFont("Arial", self._font_size - 2)
        painter.setFont(english_font)
        english_width = painter.fontMetrics().boundingRect(self.english_text).width()

        total_text_width = hebrew_width + english_width + 30

        # Define animation stages:
        # 1. Start from right, move to center
        start_pos = width  # Start off-screen to the right
        middle_pos = (width - total_text_width) // 2  # Center position
        end_pos = -total_text_width  # End off-screen to the left

        self.text_pos = start_pos  # Reset position to start

        # Animation to the center
        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(middle_pos)
        self.animation.setDuration(
            abs(start_pos - middle_pos) * self._animation_speed // 10)
        self.animation_state = "to_middle"
        self.animation.start()

    def on_animation_finished(self):
        # Handle the different animation stages
        if self.animation_state == "to_middle":
            # When reached middle, pause
            self.animation_state = "paused"
            QTimer.singleShot(self._pause_time_ms, self.start_middle_to_left)
        elif self.animation_state == "to_left":
            # When reached end, restart
            self.start_animation()

    def start_middle_to_left(self):
        # Animation from middle to left
        width = self.width()

        # Get current position (middle)
        middle_pos = self.text_pos

        # Calculate end position (off-screen left)
        painter = QPainter()
        hebrew_font = QFont("Arial", self._font_size)
        painter.setFont(hebrew_font)
        hebrew_width = painter.fontMetrics().boundingRect(self.hebrew_text).width()

        english_font = QFont("Arial", self._font_size - 2)
        painter.setFont(english_font)
        english_width = painter.fontMetrics().boundingRect(self.english_text).width()

        total_text_width = hebrew_width + english_width + 30
        end_pos = -total_text_width  # Off-screen to the left

        # Animation from middle to left
        self.animation.setStartValue(middle_pos)
        self.animation.setEndValue(end_pos)
        self.animation.setDuration(
            abs(middle_pos - end_pos) * self._animation_speed // 10)
        self.animation_state = "to_left"
        self.animation.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Restart animation when widget is resized
        if hasattr(self,
                   'animation') and self.animation.state() == QPropertyAnimation.Running:
            self.animation.stop()
            self.start_animation()

    def set_colors(self, text_color):
        """Set the text color of the animated title"""
        self._text_color = QColor(text_color)
        self.update()