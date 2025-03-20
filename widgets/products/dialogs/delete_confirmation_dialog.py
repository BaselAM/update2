from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QScrollArea, QWidget)
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt
from themes import get_color

class DeleteConfirmationDialog(QDialog):
    """Custom elegant delete confirmation dialog"""

    def __init__(self, products, translator, parent=None):
        super().__init__(parent)
        self.setWindowTitle(translator.t('confirm_removal'))
        self.setWindowIcon(QIcon("resources/delete_icon.png"))
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        icon = QLabel()
        icon.setPixmap(QIcon("resources/warning_icon.png").pixmap(32, 32))
        header_layout.addWidget(icon)
        title = QLabel(
            f"<h3 style='color:{get_color('error')};'>{translator.t('confirm_removal')}</h3>")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addWidget(header)

        # Content
        content = QLabel(
            translator.t('confirm_delete_count').format(count=len(products)))
        layout.addWidget(content)

        # Product list
        scroll_area = QScrollArea()
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        for pid, name in products:
            item = QLabel(f"<b>#{pid}</b> - {name}")
            item.setStyleSheet(
                f"padding: 5px; border-bottom: 1px solid {get_color('border')};")
            scroll_layout.addWidget(item)

        scroll_area.setWidget(scroll_content)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)
        layout.addWidget(scroll_area)

        # Buttons
        btn_box = QHBoxLayout()
        cancel_btn = QPushButton(translator.t('no_btn'))
        cancel_btn.setIcon(QIcon("resources/cancel_icon.png"))
        delete_btn = QPushButton(translator.t('yes_btn').format(count=len(products)))
        delete_btn.setIcon(QIcon("resources/delete_icon.png"))

        # Button styling
        btn_style = f"""
            QPushButton {{
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 100px;
            }}
        """
        cancel_style = f"""
            {btn_style}
            QPushButton {{
                background-color: {get_color('secondary')};
                color: {get_color('text')};
                border: 1px solid {get_color('border')};
            }}
            QPushButton:hover {{
                background-color: {get_color('button_hover')};
            }}
        """
        delete_style = f"""
            {btn_style}
            QPushButton {{
                background-color: {get_color('error')};
                color: white;
                border: 1px solid {get_color('error')};
            }}
            QPushButton:hover {{
                background-color: {QColor(get_color('error')).darker(120).name()};
            }}
        """

        cancel_btn.setStyleSheet(cancel_style)
        delete_btn.setStyleSheet(delete_style)

        btn_box.addStretch()
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(delete_btn)
        layout.addLayout(btn_box)

        # Connections
        cancel_btn.clicked.connect(self.reject)
        delete_btn.clicked.connect(self.accept)

        self.setLayout(layout)