from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtGui import QColor
from themes import get_color

class ThemedNumericDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        if editor:
            editor.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {get_color('input_bg')};
                    color: {get_color('text')};
                    border: 1px solid {get_color('border')};
                    font-size: 14px;
                    padding: 5px;
                }}
            """)
        return editor

    def paint(self, painter, option, index):
        option.backgroundColor = QColor(get_color('secondary'))
        super().paint(painter, option, index)