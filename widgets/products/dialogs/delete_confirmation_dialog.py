from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor, QFont

from themes import get_color
from widgets.products.dialogs.base_dialog import ElegantDialog


class DeleteConfirmationDialog(ElegantDialog):
    """An elegant confirmation dialog for deleting products."""

    def __init__(self, products, translator, parent=None):
        super().__init__(translator, parent, title='confirm_delete')
        self.setWindowTitle(self.translator.t('confirm_delete'))
        self.setMinimumWidth(450)
        self.products = products
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Warning icon and title
        title_layout = QHBoxLayout()
        warning_icon = QLabel()
        warning_icon.setPixmap(QIcon("resources/warning_icon.png").pixmap(48, 48))
        warning_label = QLabel(self.translator.t('confirm_delete'))
        warning_font = warning_label.font()
        warning_font.setPointSize(16)
        warning_font.setBold(True)
        warning_label.setFont(warning_font)
        title_layout.addWidget(warning_icon)
        title_layout.addWidget(warning_label, 1)
        main_layout.addLayout(title_layout)

        # Confirmation message
        msg = self.translator.t('delete_confirmation').format(count=len(self.products))
        confirmation_label = QLabel(msg)
        confirmation_label.setWordWrap(True)
        main_layout.addWidget(confirmation_label)

        # List of products to delete (if not too many)
        if len(self.products) <= 10:
            products_frame = QFrame()
            products_frame.setFrameShape(QFrame.StyledPanel)
            products_frame.setStyleSheet(f"background-color: {get_color('card_bg')};")
            products_layout = QVBoxLayout(products_frame)

            for pid, name in self.products:
                product_label = QLabel(f"• {name} (ID: {pid})")
                products_layout.addWidget(product_label)

            main_layout.addWidget(products_frame)
        else:
            # Just show count for many products
            count_label = QLabel(
                self.translator.t('items_selected').format(count=len(self.products)))
            count_label.setAlignment(Qt.AlignCenter)
            count_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            main_layout.addWidget(count_label)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Cancel button
        self.cancel_btn = QPushButton(self.translator.t('cancel'))
        self.cancel_btn.setIcon(QIcon("resources/cancel_icon.png"))
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        button_layout.addWidget(self.cancel_btn)

        # Delete button (danger styled)
        self.delete_btn = QPushButton(
            self.translator.t('yes_btn').format(count=len(self.products)))
        self.delete_btn.setIcon(QIcon("resources/delete_icon.png"))
        self.delete_btn.clicked.connect(self.accept)
        self.delete_btn.setCursor(Qt.PointingHandCursor)

        # Style delete button as danger button
        danger_color = "#f44336"  # Red color for danger
        danger_hover = "#e53935"
        danger_pressed = "#d32f2f"
        text_color = "#ffffff"  # White text

        danger_style = f"""
            QPushButton {{
                background-color: {danger_color};
                color: {text_color};
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {danger_hover};
            }}
            QPushButton:pressed {{
                background-color: {danger_pressed};
            }}
        """
        self.delete_btn.setStyleSheet(danger_style)

        button_layout.addWidget(self.delete_btn)

        main_layout.addLayout(button_layout)