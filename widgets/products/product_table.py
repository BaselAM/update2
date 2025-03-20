from PyQt5.QtWidgets import (QTableView, QAbstractItemView, QHeaderView,
                             QTableWidget, QTableWidgetItem, QFrame, QVBoxLayout)
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal
from PyQt5.QtGui import QColor
from themes import get_color
from .components import ThemedNumericDelegate


class ProductsTable(QFrame):
    """Enhanced table widget for products with proper styling"""

    cellChanged = pyqtSignal(int, int)  # Row, column

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.setObjectName("tableContainer")

        # Setup layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 15)  # Add bottom margin for scrollbar

        # Create table widget
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.update_headers()
        self.table.verticalHeader().setVisible(False)

        # Set row height to make cells larger
        self.table.verticalHeader().setDefaultSectionSize(40)  # Taller rows

        # Custom column widths instead of stretch
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.cellChanged.connect(self._on_cell_changed)
        self.table.setAlternatingRowColors(True)

        # Use delegates for better numeric editing
        self.quantity_delegate = ThemedNumericDelegate(self.table)
        self.price_delegate = ThemedNumericDelegate(self.table)
        self.table.setItemDelegateForColumn(5, self.quantity_delegate)  # Quantity
        self.table.setItemDelegateForColumn(6, self.price_delegate)  # Price

        layout.addWidget(self.table)

        # Apply initial styling
        self.apply_theme()

    def update_headers(self):
        """Update table headers with current translations"""
        headers = [
            self.translator.t('id'),
            self.translator.t('category'),
            self.translator.t('car'),
            self.translator.t('model'),
            self.translator.t('product_name'),
            self.translator.t('quantity'),
            self.translator.t('price')
        ]
        self.table.setHorizontalHeaderLabels(headers)

    def _on_cell_changed(self, row, column):
        """Internal handler for cell changes that emits the public signal"""
        self.cellChanged.emit(row, column)

    def update_table_data(self, products):
        """Update table with the given products data"""
        try:
            # Save current scroll position
            scroll_value = self.table.verticalScrollBar().value()

            self.table.blockSignals(True)
            self.table.setSortingEnabled(False)

            # Set the row count
            self.table.setRowCount(len(products))

            # Populate the data row by row
            for row, prod in enumerate(products):
                # ID column (non-editable)
                id_item = QTableWidgetItem(str(prod[0]))
                id_item.setFlags(id_item.flags() ^ Qt.ItemIsEditable)
                id_item.setTextAlignment(Qt.AlignCenter)  # Center align ID
                self.table.setItem(row, 0, id_item)

                # Other columns
                for col in range(1, 5):
                    text = str(prod[col]) if prod[col] not in [None, ""] else "-"
                    item = QTableWidgetItem(text)
                    # Left align text fields
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    self.table.setItem(row, col, item)

                # Quantity - center align
                qty_item = QTableWidgetItem(str(prod[5]))
                qty_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 5, qty_item)

                # Price - right align
                price_item = QTableWidgetItem(f"{float(prod[6]):.2f}")
                price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row, 6, price_item)

            # Re-enable sorting and signals after all data is loaded
            self.table.setSortingEnabled(True)
            self.table.blockSignals(False)

            # Restore scroll position if possible
            self.table.verticalScrollBar().setValue(
                min(scroll_value, self.table.verticalScrollBar().maximum()))

            return True
        except Exception as e:
            print(f"Error updating table: {e}")
            import traceback
            print(traceback.format_exc())
            return False

    def adjust_column_widths(self):
        """Set custom column widths based on data importance"""
        # Total width calculation (approximate)
        total_width = self.width() - 40  # Subtract scrollbar width and some padding

        # Column width distribution (percentages)
        # ID: 8%, Category: 12%, Car: 15%, Model: 15%, Name: 28%, Qty: 10%, Price: 12%
        col_widths = [8, 12, 15, 15, 28, 10, 12]

        # Apply the widths
        for i, width_percent in enumerate(col_widths):
            width = int(total_width * width_percent / 100)
            self.table.setColumnWidth(i, width)

    def set_selection_mode(self, enable_multi_select):
        """Toggle between single cell and multi-row selection modes"""
        if enable_multi_select:
            # Enable row selection mode
            self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.table.setSelectionMode(QAbstractItemView.MultiSelection)
            self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        else:
            # Restore normal mode
            self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
            self.table.setSelectionMode(QAbstractItemView.SingleSelection)
            self.table.setEditTriggers(QAbstractItemView.DoubleClicked |
                                       QAbstractItemView.EditKeyPressed)
            self.table.clearSelection()

    def get_selected_rows_data(self):
        """Get data from selected rows for deletion

        Returns:
            list: List of tuples (id, name) for selected rows
        """
        selected_rows = self.table.selectionModel().selectedRows()
        product_details = []

        for index in selected_rows:
            row = index.row()
            try:
                id_item = self.table.item(row, 0)
                name_item = self.table.item(row, 4)
                if id_item and name_item and id_item.text().isdigit():
                    product_details.append((
                        int(id_item.text()),
                        name_item.text() or self.translator.t('unnamed_product')
                    ))
            except Exception as e:
                print(f"Error parsing row {row}: {e}")

        return product_details

    def highlight_product(self, search_text):
        """Scroll to and highlight matching product"""
        search_text = search_text.lower()
        for row in range(self.table.rowCount()):
            product_item = self.table.item(row, 4)
            if product_item and search_text in product_item.text().lower():
                self.table.scrollToItem(product_item)
                self.table.blockSignals(True)
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(QColor(get_color('highlight')))
                        item.setForeground(QColor(get_color('background')))
                self.table.blockSignals(False)
                return True
        return False

    def apply_theme(self):
        """Apply current theme to table"""
        bg_color = get_color('background')
        text_color = get_color('text')
        border_color = get_color('border')

        # Table styling with larger elements and enhanced borders
        table_style = f"""
            QTableWidget {{
                background-color: {bg_color};
                alternate-background-color: {get_color('secondary')};
                gridline-color: {border_color};
                border: 2px solid {border_color};
                border-radius: 6px;
                font-size: 14px;
            }}
            QTableWidget::item {{
                padding: 8px;
                transition: background 0.3s ease, color 0.3s ease;
            }}
            QHeaderView::section {{
                background-color: {get_color('header')};
                color: {text_color};
                padding: 10px;
                border: none;
                border-right: 1px solid {border_color};
                font-weight: bold;
                font-size: 15px;
            }}
            QTableWidget::item:selected {{
                background-color: {get_color('highlight')};
                color: {bg_color};
            }}
        """
        self.table.setStyleSheet(table_style)

        # Scrollbar styling
        scroll_style = f"""
            QScrollBar:vertical {{
                background: {bg_color};
                width: 14px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {get_color('button')};
                min-height: 20px;
                border-radius: 7px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                background: none;
            }}

            QScrollBar:horizontal {{
                background: {bg_color};
                height: 14px;
                margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background: {get_color('button')};
                min-width: 20px;
                border-radius: 7px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                background: none;
            }}
        """
        self.table.verticalScrollBar().setStyleSheet(scroll_style)
        self.table.horizontalScrollBar().setStyleSheet(scroll_style)

    def resizeEvent(self, event):
        """Handle resize events to adjust column widths"""
        super().resizeEvent(event)
        self.adjust_column_widths()

    # def highlight_row_by_id(self, product_id):
    #     """Highlight a row containing the product with the given ID."""
    #     try:
    #         for row in range(self.table.rowCount()):
    #             id_item = self.table.item(row, 0)
    #             if id_item and id_item.text() == str(product_id):
    #                 # Highlight the row
    #                 for col in range(self.table.columnCount()):
    #                     cell_item = self.table.item(row, col)
    #                     if cell_item:
    #                         cell_item.setBackground(
    #                             QColor(230, 255, 230))  # Light green background
    #
    #                 # Scroll to the row
    #                 self.table.scrollToItem(id_item)
    #
    #                 # Schedule removing the highlight after 3 seconds
    #                 QTimer.singleShot(3000, lambda r=row: self._remove_highlight(r))
    #                 return True
    #         return False
    #     except Exception as e:
    #         print(f"Error highlighting row: {e}")
    #         return False
    #
    # def _remove_highlight(self, row):
    #     """Remove highlighting from a row."""
    #     try:
    #         if row < 0 or row >= self.table.rowCount():
    #             return
    #
    #         for col in range(self.table.columnCount()):
    #             cell_item = self.table.item(row, col)
    #             if cell_item:
    #                 cell_item.setBackground(
    #                     QColor(255, 255, 255))  # Reset to white/default
    #     except Exception as e:
    #         print(f"Error removing highlight: {e}")