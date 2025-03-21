from PyQt5.QtWidgets import (QTableView, QAbstractItemView, QHeaderView,
                             QTableWidget, QTableWidgetItem, QFrame, QVBoxLayout,
                             QWidget, QAbstractButton)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from themes import get_color
from .components.table_delegates import ThemedNumericDelegate, ThemedItemDelegate


class ProductsTable(QFrame):
    """Enhanced table widget for products with proper styling"""

    cellChanged = pyqtSignal(int, int)  # Row, column

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.setObjectName("tableContainer")

        # Setup layout with no margins for better scrollbar alignment
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove all margins
        layout.setSpacing(0)  # Remove spacing

        # Create table widget
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.update_headers()

        # Hide vertical header completely - this removes row numbers
        self.table.verticalHeader().setVisible(False)

        # Try to hide the corner button if we can find it
        try:
            corner_button = self.table.findChild(QAbstractButton)
            if corner_button:
                corner_button.hide()
        except:
            pass  # Ignore any errors

        # Set row height to make cells larger
        self.table.verticalHeader().setDefaultSectionSize(40)  # Taller rows

        # Custom column widths instead of stretch
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        # Configure selection and interaction behavior
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.cellChanged.connect(self._on_cell_changed)
        self.table.setAlternatingRowColors(True)

        # Set edit triggers - make it easier to enter edit mode
        self.table.setEditTriggers(
            QAbstractItemView.DoubleClicked |
            QAbstractItemView.EditKeyPressed
        )

        # Modern scrollbar configuration
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setVerticalScrollMode(
            QAbstractItemView.ScrollPerPixel)  # Smooth scrolling
        self.table.setHorizontalScrollMode(
            QAbstractItemView.ScrollPerPixel)  # Smooth scrolling

        # Remove grid for a sleeker look
        self.table.setShowGrid(False)

        # Disable the corner button - safely try another approach
        try:
            self.table.setCornerButtonEnabled(False)
        except:
            pass  # Ignore any errors if this method doesn't exist

        # Apply themed delegates for elegant editing experience
        self.item_delegate = ThemedItemDelegate()
        self.numeric_delegate = ThemedNumericDelegate()

        # Apply delegates to different column types
        for col in range(1, 5):  # Text columns
            self.table.setItemDelegateForColumn(col, self.item_delegate)
        self.table.setItemDelegateForColumn(5, self.numeric_delegate)  # Quantity
        self.table.setItemDelegateForColumn(6, self.numeric_delegate)  # Price

        # Add table to layout
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
        """Apply current theme to table with enhanced styling"""
        bg_color = get_color('background')
        text_color = get_color('text')
        border_color = get_color('border')
        highlight_color = get_color('highlight')
        secondary_color = get_color('secondary')

        # Table styling with refined cell appearance
        table_style = f"""
            QTableWidget {{
                background-color: {bg_color};
                alternate-background-color: {secondary_color};
                gridline-color: {border_color};
                border: 2px solid {border_color};
                border-radius: 6px;
                font-size: 14px;
            }}
            QTableWidget::item {{
                padding: 0px;
                border: none;
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
                background-color: {highlight_color};
                color: {bg_color};
            }}
            /* Completely removes focus indicators */
            QTableView:focus {{
                outline: none;
            }}
            QTableView::item:focus {{
                outline: none;
                border: none;
            }}
            /* Smoother hover effect */
            QTableWidget::item:hover:!selected {{
                background-color: {highlight_color}25;
            }}

            /* Modern scrollbar styling integrated directly in the table style */
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {get_color('button')};
                min-height: 30px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {highlight_color};
            }}
            QScrollBar::add-line:vertical, 
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, 
            QScrollBar::sub-page:vertical {{
                background: transparent;
                height: 0px;
                width: 0px;
            }}

            QScrollBar:horizontal {{
                background: transparent;
                height: 8px;
                margin: 0px;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: {get_color('button')};
                min-width: 30px;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {highlight_color};
            }}
            QScrollBar::add-line:horizontal, 
            QScrollBar::sub-line:horizontal,
            QScrollBar::add-page:horizontal, 
            QScrollBar::sub-page:horizontal {{
                background: transparent;
                height: 0px;
                width: 0px;
            }}

            /* Comprehensive corner styling */
            QScrollBar::corner {{
                background: {bg_color};
                border: none;
            }}
            QAbstractScrollArea::corner {{
                background: {bg_color};
                border: none;
            }}

            /* Ensure header corners are styled too */
            QHeaderView {{ 
                background-color: {bg_color}; 
            }}
            QHeaderView::corner {{
                background-color: {bg_color};
                border: none;
            }}

            /* Target scroll bar corner specifically */
            QAbstractScrollArea QScrollBar::corner {{
                background: {bg_color};
                border: none;
            }}

            /* Style any other potential widgets in the table */
            QTableWidget > QWidget {{
                background-color: {bg_color};
                border: none;
            }}
        """
        self.table.setStyleSheet(table_style)

        # As a fallback, directly set the background of the table viewport
        self.table.viewport().setStyleSheet(f"background: {bg_color};")

        # Style all child widgets to prevent any white boxes
        for child in self.table.findChildren(QWidget):
            child.setStyleSheet(f"background-color: {bg_color}; border: none;")

    def resizeEvent(self, event):
        """Handle resize events to adjust column widths"""
        super().resizeEvent(event)
        self.adjust_column_widths()