from PyQt5.QtWidgets import QStyledItemDelegate, QLineEdit
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QRect
from themes import get_color


class ThemedItemDelegate(QStyledItemDelegate):
    """A delegate for styling table items with an elegant, sleek editing appearance"""

    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        if isinstance(editor, QLineEdit):
            # Use a more refined style for the editor
            bg_color = get_color('background')
            highlight_color = get_color('highlight')
            text_color = get_color('text')

            editor.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {bg_color};
                    color: {text_color};
                    border: none;
                    border-radius: 0px;
                    border-bottom: 2px solid {highlight_color};
                    selection-background-color: {highlight_color};
                    selection-color: {bg_color};
                    padding-left: 8px;
                    padding-right: 8px;
                    padding-top: 0px;
                    padding-bottom: 0px;
                    font-size: 14px;
                }}
            """)
        return editor

    def updateEditorGeometry(self, editor, option, index):
        # Create a precise rectangle that fully covers the cell content
        rect = QRect(option.rect)

        # Adjust to perfectly align with cell content and remove gaps
        rect.setLeft(rect.left())
        rect.setRight(rect.right())
        rect.setTop(rect.top())
        rect.setBottom(rect.bottom())

        editor.setGeometry(rect)


class ThemedNumericDelegate(ThemedItemDelegate):
    """A delegate specifically for numeric fields with right alignment"""

    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        if isinstance(editor, QLineEdit):
            editor.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return editor

    def setModelData(self, editor, model, index):
        if not isinstance(editor, QLineEdit):
            super().setModelData(editor, model, index)
            return

        try:
            text = editor.text().strip()
            if text:
                # Format as number with 2 decimal places for price column (index 6)
                if index.column() == 6:  # Price column
                    value = float(text.replace(',', '.'))
                    model.setData(index, f"{value:.2f}")
                else:  # Quantity column (index 5)
                    value = int(text)
                    model.setData(index, str(value))
            else:
                model.setData(index, "0")
        except (ValueError, TypeError):
            # If conversion fails, keep the original data
            pass