from PyQt5.QtCore import Qt, pyqtSignal, QSize  # Correct import for QSize
from PyQt5.QtWidgets import QWidget, QToolButton, QHBoxLayout
from PyQt5.QtGui import QIcon
from pathlib import Path


class NavigationWidget(QWidget):
    """Widget for handling navigation buttons in the top bar"""
    home_clicked = pyqtSignal()

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.setup_ui()

    def setup_ui(self):
        """Create the navigation buttons"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Home button
        self.home_btn = QToolButton()
        self.home_btn.setCursor(Qt.PointingHandCursor)
        self.home_btn.setToolTip(self.translator.t('home_button_tooltip'))
        self.home_btn.clicked.connect(self.home_clicked)

        # Add home icon if available
        home_icon_path = Path(
            __file__).resolve().parent.parent.parent / "resources/home_icon.png"
        if home_icon_path.exists():
            self.home_btn.setIcon(QIcon(str(home_icon_path)))
            self.home_btn.setIconSize(QSize(24, 24))  # Fixed: use QSize directly
        else:
            self.home_btn.setText("🏠")
            self.home_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)

        # Add to layout
        layout.addWidget(self.home_btn)

    def update_translations(self):
        """Update translations for this widget"""
        self.home_btn.setToolTip(self.translator.t('home_button_tooltip'))

    def apply_theme(self):
        """Apply current theme to this widget"""
        from themes import get_color

        button_style = f"""
            QToolButton {{
                background-color: transparent;
                border: none;
                padding: 5px;
            }}
            QToolButton:hover {{
                background-color: {get_color('button_hover')};
                border-radius: 15px;
            }}
        """

        self.home_btn.setStyleSheet(button_style)