from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
                             QAbstractItemView, QMessageBox, QDialog, QFileDialog,
                             QStyledItemDelegate, QFrame, QApplication,QScrollArea,QProgressDialog)
from PyQt5.QtGui import QIcon, QColor, QPainter, QPixmap
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSlot, QMetaObject, Q_ARG,QEventLoop
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
import csv
import datetime
from translator import Translator
from widgets.dialogs import FilterDialog, AddProductDialog, ItemDetailsDialog
from widgets.workers import DatabaseWorker
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


class StatusBar(QFrame):
    """Status bar for displaying operation results and info"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("productsContainer")  # Added for CSS styling
        self.setMaximumHeight(40)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)

        self.status_icon = QLabel()
        self.status_icon.setFixedSize(24, 24)
        self.status_text = QLabel()
        self.status_text.setWordWrap(True)
        self.current_type = "info"

        layout.addWidget(self.status_icon)
        layout.addWidget(self.status_text, 1)

        # Add clear button
        self.clear_btn = QPushButton()
        self.clear_btn.setIcon(QIcon("resources/close_icon.png"))
        self.clear_btn.setIconSize(QSize(12, 12))
        self.clear_btn.setFixedSize(20, 20)
        self.clear_btn.setStyleSheet("background: transparent; border: none;")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear)
        layout.addWidget(self.clear_btn)

        self.hide()  # Start hidden

    def show_message(self, message, message_type="info"):
        """Display a status message with icon"""
        self.status_text.setText(message)
        self.current_type = message_type

        # Set icon based on message type
        icon_map = {
            "info": "resources/info_icon.png",
            "success": "resources/success_icon.png",
            "error": "resources/error_icon.png",
            "warning": "resources/warning_icon.png"
        }

        # Use default info icon if type not recognized
        icon_path = icon_map.get(message_type, icon_map["info"])
        self.status_icon.setPixmap(QPixmap(icon_path).scaled(24, 24, Qt.KeepAspectRatio,
                                                             Qt.SmoothTransformation))

        # Auto-hide after 5 seconds for success messages
        self.show()
        if message_type == "success":
            QTimer.singleShot(5000, self.clear)

    def clear(self):
        """Clear and hide the status bar"""
        self.status_text.clear()
        self.hide()


class ProductsWidget(QWidget):
    def __init__(self, translator, db):
        super().__init__()
        self._is_closing = False
        self.worker_thread = None
        self.translator = translator
        self.db = db
        self.all_products = []
        self.setup_ui()
        self.apply_theme()
        QTimer.singleShot(100, self.load_products)

    def setup_ui(self):
        # Add object name for the container to apply enhanced borders
        self.setObjectName("productsContainer")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # --- Button Panel ---
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # Increase spacing between buttons

        # Create buttons with icons - add more visual feedback
        self.add_btn = QPushButton(self.translator.t('add_product'))
        self.add_btn.setIcon(QIcon("resources/add_icon.png"))
        self.add_btn.setIconSize(QSize(18, 18))
        self.add_btn.clicked.connect(self.show_add_dialog)
        self.add_btn.setCursor(Qt.PointingHandCursor)  # Add cursor change
        button_layout.addWidget(self.add_btn)

        self.select_toggle = QPushButton(self.translator.t('select_button'))
        self.select_toggle.setIcon(QIcon("resources/select_icon.png"))
        self.select_toggle.setIconSize(QSize(18, 18))
        self.select_toggle.setCheckable(True)
        self.select_toggle.toggled.connect(self.on_select_toggled)
        self.select_toggle.setCursor(Qt.PointingHandCursor)  # Add cursor change
        button_layout.addWidget(self.select_toggle)

        self.remove_btn = QPushButton(self.translator.t('remove'))
        self.remove_btn.setIcon(QIcon("resources/delete_icon.png"))
        self.remove_btn.setIconSize(QSize(18, 18))
        self.remove_btn.clicked.connect(self.universal_remove)
        self.remove_btn.setCursor(Qt.PointingHandCursor)  # Add cursor change
        button_layout.addWidget(self.remove_btn)

        self.filter_btn = QPushButton(self.translator.t('filter_button'))
        self.filter_btn.setIcon(QIcon("resources/filter_icon.png"))
        self.filter_btn.setIconSize(QSize(18, 18))
        self.filter_btn.clicked.connect(self.show_filter_dialog)
        self.filter_btn.setCursor(Qt.PointingHandCursor)  # Add cursor change
        button_layout.addWidget(self.filter_btn)

        # Add export button
        self.export_btn = QPushButton(self.translator.t('export'))
        self.export_btn.setIcon(QIcon("resources/export_icon.png"))
        self.export_btn.setIconSize(QSize(18, 18))
        self.export_btn.clicked.connect(self.export_data)
        self.export_btn.setCursor(Qt.PointingHandCursor)  # Add cursor change
        button_layout.addWidget(self.export_btn)

        # Add refresh button
        self.refresh_btn = QPushButton(self.translator.t('refresh'))
        self.refresh_btn.setIcon(QIcon("resources/refresh_icon.png"))
        self.refresh_btn.setIconSize(QSize(18, 18))
        self.refresh_btn.clicked.connect(self.load_products)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)  # Add cursor change

        button_layout.addStretch()
        button_layout.addWidget(self.refresh_btn)
        main_layout.addLayout(button_layout)

        # --- Search Box ---
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)

        search_label = QLabel(self.translator.t('search_products'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.translator.t('search_placeholder'))
        self.search_input.textChanged.connect(self.on_search)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input, 1)

        main_layout.addLayout(search_layout)

        # --- Table Setup ---
        # Create a container for the table with margin for scrollbar
        table_container = QFrame()
        self.table_container = table_container  # Store reference
        table_container.setObjectName("tableContainer")
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 15)  # Add bottom margin for scrollbar

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.update_headers()
        self.table.verticalHeader().setVisible(False)

        # Set row height to make cells larger
        self.table.verticalHeader().setDefaultSectionSize(40)  # Taller rows

        # Custom column widths instead of stretch
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        # Set specific column widths for different types of data
        self.adjust_column_widths()

        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.cellChanged.connect(self.on_cell_changed)
        self.table.setAlternatingRowColors(True)

        # Use delegates for better numeric editing
        self.quantity_delegate = ThemedNumericDelegate(self.table)
        self.price_delegate = ThemedNumericDelegate(self.table)
        self.table.setItemDelegateForColumn(5, self.quantity_delegate)  # Quantity
        self.table.setItemDelegateForColumn(6, self.price_delegate)  # Price

        table_layout.addWidget(self.table)
        main_layout.addWidget(table_container, 1)  # Add table container to main layout

        # Add status bar for operation messages with proper spacing
        status_container = QFrame()
        self.status_container = status_container  # Store reference for later adjustments
        status_container.setObjectName("statusContainer")
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(0, 10, 0, 0)  # Add top margin to create space

        self.status_bar = StatusBar()
        status_layout.addWidget(self.status_bar)

        main_layout.addWidget(status_container)  # Add status container to main layout

    def apply_theme(self):
        """Apply current theme to all elements with enhanced styling"""
        # Get theme colors
        bg_color = get_color('background')
        text_color = get_color('text')
        card_bg = get_color('card_bg')
        border_color = get_color('border')
        button_color = get_color('button')
        button_hover = get_color('button_hover')
        button_pressed = get_color('button_pressed')
        highlight_color = get_color('highlight')
        try:
            accent_color = get_color('accent')
        except:
            accent_color = highlight_color
        # Create semi-transparent border color for containers
        border_rgba = QColor(accent_color)
        border_rgba.setAlpha(120)  # 47% opacity
        border_str = f"rgba({border_rgba.red()}, {border_rgba.green()}, {border_rgba.blue()}, 0.47)"

        # Define shadow effect based on theme darkness
        is_dark_theme = QColor(bg_color).lightness() < 128
        shadow_opacity = "0.4" if is_dark_theme else "0.15"
        shadow_color = f"rgba(0, 0, 0, {shadow_opacity})"

        # Base styles
        base_style = f"""
            QWidget {{
                color: {text_color};
                font-family: 'Segoe UI';
                font-size: 14px;
            }}

            /* Enhanced borders for the main container */
            #productsContainer {{
                background-color: {bg_color};
                border: 3px solid {border_str};
                border-radius: 12px;
                padding: 5px;
            }}

            /* Enhanced borders for table container */
            #tableContainer {{
                background-color: {card_bg};
                border: 2px solid {border_str};
                border-radius: 8px;
                padding: 5px;
                margin: 2px;
            }}

            /* Status container with enhanced styling */
            #statusContainer {{
                border: 2px solid {border_str};
                border-radius: 8px;
                background-color: {card_bg};
                margin-top: 5px;
            }}
        """
        self.setStyleSheet(base_style)

        # Enhanced button styling with visual feedback
        btn_style = f"""
            QPushButton {{
                background-color: {button_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 10px 18px;
                margin: 3px;
                font-size: 15px;
                font-weight: bold;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {button_hover};
                border: 1px solid {highlight_color};
                box-shadow: 0px 2px 4px {shadow_color};
            }}
            QPushButton:pressed {{
                background-color: {button_pressed};
                border: 2px solid {highlight_color};
                padding: 9px 17px; /* Adjust padding to prevent size change */
            }}
            QPushButton:disabled {{
                background-color: {card_bg};
                color: {border_color};
                border: 1px solid {border_color};
            }}
            QPushButton:checked {{
                background-color: {highlight_color};
                color: {bg_color};
                border: 2px solid {highlight_color};
            }}
        """

        for btn in [self.add_btn, self.select_toggle, self.remove_btn, self.filter_btn,
                    self.export_btn, self.refresh_btn]:
            btn.setStyleSheet(btn_style)

        # Search box styling
        search_style = f"""
            QLineEdit {{
                background-color: {get_color('input_bg')};
                color: {text_color};
                border: 2px solid {border_color};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {highlight_color};
                background-color: {QColor(get_color('input_bg')).lighter(105).name()};
            }}
            QLabel {{
                font-weight: bold;
            }}
        """
        self.search_input.setStyleSheet(search_style)

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
                       background-color: {highlight_color};
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
                background: {button_color};
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
                background: {button_color};
                min-width: 20px;
                border-radius: 7px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                background: none;
            }}
        """
        self.table.verticalScrollBar().setStyleSheet(scroll_style)
        self.table.horizontalScrollBar().setStyleSheet(scroll_style)

        # Status bar styling with enhanced borders
        self.status_bar.setStyleSheet(f"""
            QFrame#statusContainer {{
                background-color: {card_bg};
                border: 2px solid {border_str};
                border-radius: 6px;
                padding: 5px;
                margin-bottom: 5px;
            }}
            QLabel {{
                color: {text_color};
            }}
        """)

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

    def resizeEvent(self, event):
        """Handle resize events to adjust column widths and status bar position"""
        super().resizeEvent(event)
        self.adjust_column_widths()
        self.adjust_statusbar_position()  # Add this line
    def on_search(self, text):
        """Filter table based on search text"""
        search_text = text.lower().strip()
        if not search_text:
            # If search is cleared, show all products
            self.update_table_data(self.all_products)
            return

        # Filter products based on search text
        filtered_products = []
        for product in self.all_products:
            # Search in product name, category, car, and model
            searchable_fields = [
                str(product[1] or ""),  # Category
                str(product[2] or ""),  # Car
                str(product[3] or ""),  # Model
                str(product[4] or "")  # Product name
            ]

            searchable_text = " ".join(searchable_fields).lower()
            if search_text in searchable_text:
                filtered_products.append(product)

        self.update_table_data(filtered_products)

        # Show status message
        if len(filtered_products) < len(self.all_products):
            self.status_bar.show_message(
                self.translator.t('search_results').format(
                    count=len(filtered_products),
                    total=len(self.all_products)
                ),
                "info"
            )
        else:
            self.status_bar.clear()

    def adjust_statusbar_position(self):
        """Ensure status bar doesn't overlap with horizontal scrollbar"""
        # Add extra margin between table and status bar
        if hasattr(self, 'table') and hasattr(self, 'status_bar'):
            # Get scrollbar height if visible
            h_scrollbar = self.table.horizontalScrollBar()
            scrollbar_height = h_scrollbar.height() if h_scrollbar.isVisible() else 0

            # Add margin to status container
            if hasattr(self, 'status_container'):
                margins = self.status_container.layout().contentsMargins()
                self.status_container.layout().setContentsMargins(
                    margins.left(),
                    max(10, scrollbar_height + 5),  # Use at least 10px or scrollbar + 5px
                    margins.right(),
                    margins.bottom()
                )
    def highlight_product(self, search_text):
        """Scroll to and highlight matching product using theme colors"""
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
                QTimer.singleShot(2000, lambda r=row: self.clear_highlight(r))
                return True
        return False

    def clear_highlight(self, row):
        """Clear highlight using theme background color"""
        self.table.blockSignals(True)
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setBackground(QColor(
                    get_color('background') if row % 2 == 0 else get_color('secondary')))
                item.setForeground(QColor(get_color('text')))
        self.table.blockSignals(False)

    def on_select_toggled(self, checked):
        """Handle selection mode toggle with proper error handling"""
        try:
            if checked:
                # Enable row selection mode
                self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
                self.table.setSelectionMode(QAbstractItemView.MultiSelection)
                self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

                # Visual feedback
                self.select_toggle.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {get_color('highlight')};
                        color: {get_color('background')};
                        border: 2px solid {get_color('highlight')};
                        border-radius: 6px;
                        padding: 10px 18px;
                        margin: 3px;
                        font-size: 15px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: {QColor(get_color('highlight')).darker(110).name()};
                        border-color: {QColor(get_color('highlight')).darker(120).name()};
                    }}
                """)
                self.status_bar.show_message(self.translator.t('select_mode_enabled'),
                                             "info")

            else:
                # Restore normal mode
                self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
                self.table.setSelectionMode(QAbstractItemView.SingleSelection)
                self.table.setEditTriggers(QAbstractItemView.DoubleClicked |
                                           QAbstractItemView.EditKeyPressed)
                self.table.clearSelection()

                # Restore original styling
                self.select_toggle.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {get_color('button')};
                        color: {get_color('text')};
                        border: 1px solid {get_color('border')};
                        border-radius: 6px;
                        padding: 10px 18px;
                        margin: 3px;
                        font-size: 15px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: {get_color('button_hover')};
                        border-color: {get_color('highlight')};
                    }}
                    QPushButton:pressed {{
                        background-color: {get_color('button_pressed')};
                        border: 2px solid {get_color('highlight')};
                    }}
                """)
                self.status_bar.clear()

        except Exception as e:
            # Handle any unexpected errors
            error_msg = f"{self.translator.t('selection_mode_error')}: {str(e)}"
            print(f"Selection mode error: {error_msg}")
            self.status_bar.show_message(error_msg, "error")

            # Reset to safe state
            self.select_toggle.blockSignals(True)
            self.select_toggle.setChecked(False)
            self.select_toggle.blockSignals(False)
            self.table.setSelectionMode(QAbstractItemView.SingleSelection)
            self.table.setEditTriggers(QAbstractItemView.DoubleClicked |
                                       QAbstractItemView.EditKeyPressed)


    def update_headers(self):
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

    def show_filter_dialog(self):
        dialog = FilterDialog(self.translator, self)
        if dialog.exec_() == QDialog.Accepted:
            filters = dialog.get_filters()
            self.filter_products(filters)

    def filter_products(self, filters):
        try:
            # Get all products from the database if we don't have them cached
            if not self.all_products:
                self.all_products = self.db.get_all_parts()

            filtered = []
            # Apply filters
            for prod in self.all_products:
                category = prod[1] if prod[1] else ""
                name = prod[4] if prod[4] else ""
                price = float(prod[6])

                # Apply filters
                if filters["category"] and filters[
                    "category"].lower() not in category.lower():
                    continue
                if filters["name"] and filters["name"].lower() not in name.lower():
                    continue
                if filters["min_price"] is not None and price < filters["min_price"]:
                    continue
                if filters["max_price"] is not None and price > filters["max_price"]:
                    continue
                filtered.append(prod)

            # Update the table with filtered products
            self.update_table_data(filtered)

            # Show status message
            self.status_bar.show_message(
                self.translator.t('filter_results').format(
                    count=len(filtered),
                    total=len(self.all_products)
                ),
                "info"
            )

        except Exception as e:
            print("Error filtering products:", e)
            self.status_bar.show_message(self.translator.t('filter_error'), "error")

    def update_table_data(self, products):
        """Update table with the given products data"""
        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)
        self.table.clearContents()
        self.table.setRowCount(len(products))

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

            if row % 10 == 0:
                QApplication.processEvents()

        self.table.setSortingEnabled(True)
        self.table.blockSignals(False)

    def load_products(self):
        if self._is_closing:
            return
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait(1000)

        # Clear existing data first
        self.table.blockSignals(True)
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.blockSignals(False)

        # Show loading status
        self.status_bar.show_message(self.translator.t('loading_products'), "info")

        # Create and start worker thread
        self.worker_thread = DatabaseWorker(self.db, "load")
        self.worker_thread.finished.connect(self.handle_loaded_products)
        self.worker_thread.error.connect(self.show_error)
        self.worker_thread.start()

    def export_data(self):
        """Export the current table data to a CSV file"""
        try:
            # Get current table data
            rows = self.table.rowCount()
            cols = self.table.columnCount()

            if rows == 0:
                self.status_bar.show_message(self.translator.t('no_data_to_export'),
                                             "warning")
                return

            # Ask for file location
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                self.translator.t('export_title'),
                "",
                "CSV Files (*.csv);;All Files (*)"
            )

            if not file_name:
                return

            # Add .csv extension if not present
            if not file_name.endswith('.csv'):
                file_name += '.csv'

            with open(file_name, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Write headers
                headers = []
                for col in range(cols):
                    headers.append(self.table.horizontalHeaderItem(col).text())
                writer.writerow(headers)

                # Write data
                for row in range(rows):
                    row_data = []
                    for col in range(cols):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)

            self.status_bar.show_message(
                self.translator.t('export_success').format(file=file_name),
                "success"
            )

        except Exception as e:
            print(f"Export error: {e}")
            self.status_bar.show_message(self.translator.t('export_error'), "error")

    def on_cell_changed(self, row, column):
        try:
            # Only allow cell edits for columns 1-6 (skip ID column)
            if not (0 <= row < self.table.rowCount() and 1 <= column < 7):
                return
            item = self.table.item(row, column)
            id_item = self.table.item(row, 0)
            if not item or not id_item:
                return
            try:
                part_id = int(id_item.text())
            except ValueError:
                self.status_bar.show_message(self.translator.t('invalid_id'), "error")
                return
            field_map = {
                1: 'category',
                2: 'car_name',
                3: 'model',
                4: 'product_name',
                5: 'quantity',
                6: 'price'
            }
            field = field_map.get(column)
            new_value = item.text().strip()
            # For product name, don't allow empty (if editing column 4)
            if field == 'product_name' and not new_value:
                self.status_bar.show_message(self.translator.t('product_name_required'),
                                             "error")
                self._revert_cell(row, column)
                return
            if field in ['quantity', 'price']:
                try:
                    new_value = int(new_value) if field == 'quantity' else round(
                        float(new_value), 2)
                    if new_value < 0:
                        raise ValueError
                except ValueError:
                    self.status_bar.show_message(self.translator.t('invalid_number'),
                                                 "error")
                    self._revert_cell(row, column)
                    return
            if self.db.update_part(part_id, **{field: new_value}):
                updated = self.db.get_part(part_id)
                if not updated:
                    raise ValueError("Product not found after update")
                self._refresh_row(row, updated)

                # Update the cached product in all_products
                for i, prod in enumerate(self.all_products):
                    if prod[0] == part_id:
                        # Create a new tuple with the updated value
                        new_prod = list(prod)
                        new_prod[column] = new_value
                        self.all_products[i] = tuple(new_prod)
                        break

                self.show_update_effect(row, column)
                self.status_bar.show_message(self.translator.t('update_success'),
                                             "success")
            else:
                self.show_error_effect(row, column)
                raise RuntimeError("Database update failed")
        except Exception as e:
                self.show_error_effect(row, column)
                self.status_bar.show_message(self.translator.t('update_error'), "error")
                self._revert_cell(row, column)

    def show_error_effect(self, row, column):
        """Visual feedback for errors"""
        item = self.table.item(row, column)
        if item:
            original_bg = item.background()
            original_fg = item.foreground()
            item.setBackground(QColor(get_color('error')))
            item.setForeground(QColor(get_color('background')))
            QTimer.singleShot(1000,
                              lambda: self.clear_error_effect(row, column, original_bg,
                                                              original_fg))

    def clear_error_effect(self, row, column, bg, fg):
        """Clear error highlight"""
        item = self.table.item(row, column)
        if item:
            item.setBackground(bg)
            item.setForeground(fg)

    def show_update_effect(self, row, column):
        """Visual feedback for successful updates"""
        item = self.table.item(row, column)
        if item:
            original_bg = item.background()
            original_fg = item.foreground()
            item.setBackground(QColor(get_color('highlight')))
            item.setForeground(QColor(get_color('background')))
            QTimer.singleShot(500, lambda: self.clear_update_effect(row, column, original_bg, original_fg))

    def clear_update_effect(self, row, column, bg, fg):
        """Clear update highlight"""
        item = self.table.item(row, column)
        if item:
            item.setBackground(bg)
            item.setForeground(fg)

    def _refresh_row(self, row, data):
        self.table.blockSignals(True)
        try:
            for col in range(7):
                if col == 0:
                    val = str(data[0])
                elif col in [1, 2, 3, 4]:
                    val = str(data[col]) if data[col] else "-"
                elif col == 5:
                    val = str(int(data[5]))
                elif col == 6:
                    val = f"{float(data[6]):.2f}"
                else:
                    val = ""
                if self.table.item(row, col):
                    self.table.item(row, col).setText(val)
        finally:
            self.table.blockSignals(False)

    def _revert_cell(self, row, column):
        self.table.blockSignals(True)
        try:
            id_item = self.table.item(row, 0)
            if id_item:
                part_id = int(id_item.text())
                part = self.db.get_part(part_id)
                if part:
                    val = ""
                    if column == 0:
                        val = str(part[0])
                    elif column in [1, 2, 3, 4]:
                        val = str(part[column]) if part[column] else "-"
                    elif column == 5:
                        val = str(int(part[5]))
                    elif column == 6:
                        val = f"{float(part[6]):.2f}"

                    if self.table.item(row, column):
                        self.table.item(row, column).setText(val)
        except Exception as e:
            print(f"Error reverting cell: {e}")
        finally:
            self.table.blockSignals(False)

    def show_add_dialog(self):
        try:
            dialog = AddProductDialog(self.translator, self)
            dialog.finished.connect(lambda: self.safe_load_data(dialog))
            dialog.show()
        except Exception as e:
            print(f"Dialog error: {e}")
            self.status_bar.show_message(self.translator.t('dialog_error'), "error")

    def safe_load_data(self, dialog):
        if dialog.result() == QDialog.Accepted:
            try:
                data = dialog.get_data()
                QMetaObject.invokeMethod(self, "process_add_product", Qt.QueuedConnection,
                                         Q_ARG(dict, data))
            except Exception as e:
                print(f"Data processing error: {e}")
                self.status_bar.show_message(self.translator.t('data_error'), "error")

    @pyqtSlot(dict)
    def process_add_product(self, data):
        try:
            existing = self.db.get_part_by_name(data['product_name'])
            if existing:
                confirm = QMessageBox.question(
                    self,
                    self.translator.t('overwrite_title'),
                    self.translator.t('overwrite_message'),
                    QMessageBox.Yes | QMessageBox.No
                )
                if confirm == QMessageBox.Yes:
                    success = self.db.update_part(existing[0], **data)
                    if not success:
                        raise Exception("Failed to update existing product")
                    self.status_bar.show_message(self.translator.t('product_updated'),
                                                 "success")
                else:
                    return
            else:
                success = self.db.add_part(**data)
                if not success:
                    raise Exception("Failed to add new product")
                self.status_bar.show_message(self.translator.t('product_added'),
                                             "success")

            self.load_products()

        except Exception as e:
            print(f"Add product error: {e}")
            self.status_bar.show_message(self.translator.t('add_error'), "error")

    @pyqtSlot(object)
    def handle_loaded_products(self, products):
        try:
            # Cache the products
            self.all_products = products

            # Update the table
            self.update_table_data(products)

            # Update status
            self.status_bar.show_message(
                self.translator.t('products_loaded').format(count=len(products)),
                "success"
            )

        except Exception as e:
            print(f"Load error: {e}")
            self.status_bar.show_message(self.translator.t('load_error'), "error")



    def show_error(self, message):
        """Display an error message in the status bar"""
        if self._is_closing:
            return
        self.status_bar.show_message(message, "error")

    def update_translations(self):
        """Update all text elements when language changes"""
        # Update button labels
        self.add_btn.setText(self.translator.t('add_product'))
        self.select_toggle.setText(self.translator.t('select_button'))
        self.remove_btn.setText(self.translator.t('remove'))
        self.filter_btn.setText(self.translator.t('filter_button'))
        self.export_btn.setText(self.translator.t('export'))
        self.refresh_btn.setText(self.translator.t('refresh'))

        # Update search
        self.search_input.setPlaceholderText(self.translator.t('search_placeholder'))

        # Update table headers
        self.update_headers()

        # Update any visible status message
        if self.status_bar.isVisible():
            # Preserve the current message type if possible
            message_type = "info"
            if hasattr(self.status_bar, 'current_type'):
                message_type = self.status_bar.current_type

            current_text = self.status_bar.status_text.text()
            # Try to find a matching translation key based on patterns
            if current_text.startswith("Found "):
                self.status_bar.show_message(
                    self.translator.t('search_results').format(
                        count=len([r for r in range(self.table.rowCount()) if not self.table.isRowHidden(r)]),
                        total=len(self.all_products)
                    ),
                    message_type
                )
            elif current_text.startswith("Loaded "):
                self.status_bar.show_message(
                    self.translator.t('products_loaded').format(count=self.table.rowCount()),
                    message_type
                )

    def closeEvent(self, event):
        """Clean up resources before closing"""
        try:
            self._is_closing = True
            # Stop any ongoing worker thread
            if self.worker_thread and self.worker_thread.isRunning():
                self.worker_thread.quit()
                self.worker_thread.wait(1000)

            # Clear cached data
            self.all_products = None

        except Exception as e:
            print(f"Cleanup error: {e}")

        event.accept()


    def _restore_cell_appearance(self, row, column):
        """Restore cell appearance after a highlight animation"""
        item = self.table.item(row, column)
        if not item:
            return

        # Restore normal appearance based on row parity
        is_alternate = row % 2 == 1
        if is_alternate:
            item.setBackground(QColor(get_color('secondary')))
        else:
            item.setBackground(QColor(get_color('background')))
        item.setForeground(QColor(get_color('text')))

    def _flash_button(self, button, times=2):
        """Make a button flash to draw attention to it"""
        original_style = button.styleSheet()
        highlight_style = f"""
            QPushButton {{
                background-color: {get_color('highlight')};
                color: {get_color('background')};
                border: 2px solid {get_color('highlight')};
            }}
        """

        # Create timer for flashing effect
        timer = QTimer(self)
        flash_count = [0]  # Use list to be accessible in the closure

        def toggle_style():
            if flash_count[0] >= times * 2:
                timer.stop()
                button.setStyleSheet(original_style)
                return

            if flash_count[0] % 2 == 0:
                button.setStyleSheet(highlight_style)
            else:
                button.setStyleSheet(original_style)

            flash_count[0] += 1

        timer.timeout.connect(toggle_style)
        timer.start(200)  # Toggle every 200ms

    def _pulse_button(self, button):
        """Subtle pulse animation to indicate success"""
        original_style = button.styleSheet()
        success_style = f"""
            QPushButton {{
                background-color: {get_color('success')};
                color: white;
                border: 2px solid {get_color('success')};
            }}
        """

        button.setStyleSheet(success_style)
        QTimer.singleShot(800, lambda: button.setStyleSheet(original_style))

    def universal_remove(self):
        """Enhanced delete functionality with modern dialog and proper selection handling"""
        try:
            if self.select_toggle.isChecked():
                # Multi-delete mode
                selected_rows = self.table.selectionModel().selectedRows()
                if not selected_rows:
                    self.status_bar.show_message(self.translator.t('no_rows_selected'),
                                                 "warning")
                    self._flash_button(self.remove_btn)
                    return

                # Collect product details with error handling
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

                if not product_details:
                    self.status_bar.show_message(self.translator.t('no_valid_selection'),
                                                 "error")
                    return

                # Create and show confirmation dialog
                dialog = DeleteConfirmationDialog(
                    products=product_details,
                    translator=self.translator,
                    parent=self
                )

                # Apply theme colors to dialog
                dialog.setStyleSheet(f"""
                    QDialog {{
                        background-color: {get_color('background')};
                        border: 2px solid {get_color('border')};
                        border-radius: 8px;
                    }}
                    QLabel#warningMessage {{
                        color: {get_color('text')};
                        font-size: 14px;
                        padding: 10px;
                    }}
                    QScrollArea {{
                        border-top: 1px solid {get_color('border')};
                        border-bottom: 1px solid {get_color('border')};
                        background: {get_color('secondary')};
                    }}
                """)

                # Process user confirmation
                if dialog.exec_() == QDialog.Accepted:
                    # Use a batch operation for better memory management
                    deleted_ids = self._batch_delete_products(product_details)

                    # Update UI and cache
                    if deleted_ids:
                        # Filter out deleted products from the cache
                        self.all_products = [p for p in self.all_products if
                                             p[0] not in deleted_ids]

                        # Reload products from database to ensure consistency
                        QTimer.singleShot(500, self.load_products)

                        # Visual feedback
                        self.table.setStyleSheet(f"""
                            QTableWidget {{
                                border: 2px solid {get_color('success')};
                                transition: border 0.5s ease;
                            }}
                        """)
                        QTimer.singleShot(1000, lambda: self.table.setStyleSheet(
                            self.table.styleSheet().replace(get_color('success'),
                                                            get_color('border'))))

                        self.status_bar.show_message(
                            self.translator.t('items_deleted').format(
                                count=len(deleted_ids)),
                            "success"
                        )
                    else:
                        self.status_bar.show_message(self.translator.t('delete_failed'),
                                                     "error")

                # Explicitly clean up the dialog
                dialog.deleteLater()

            else:
                # Single cell clearing mode
                current_item = self.table.currentItem()
                if not current_item:
                    self.status_bar.show_message(self.translator.t('no_cell_selected'),
                                                 "warning")
                    return

                row = current_item.row()
                column = current_item.column()

                # Prevent ID modification
                if column == 0:
                    self.status_bar.show_message(self.translator.t('cannot_modify_id'),
                                                 "warning")
                    return

                # Simplified field clearing logic
                self._clear_field(row, column)

        except Exception as e:
            import traceback
            self.status_bar.show_message(
                f"{self.translator.t('unexpected_error')}: {str(e)}",
                "error"
            )
            print(f"Universal remove error: {traceback.format_exc()}")

    def _batch_delete_products(self, product_list):
        """Process deletion in optimized batches to prevent memory issues"""
        deleted_ids = []

        # Create a single progress dialog
        progress = QProgressDialog(
            self.translator.t('deleting_items').format(count=len(product_list)),
            self.translator.t('cancel'),
            0, len(product_list), self
        )
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(500)

        try:
            for i, (pid, _) in enumerate(product_list):
                if progress.wasCanceled():
                    break

                progress.setValue(i)
                QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)

                # Use the improved delete_part method
                if self.db.delete_part(pid):
                    deleted_ids.append(pid)

        except Exception as e:
            # Log any exceptions
            print(f"Error during batch deletion: {e}")
            self.status_bar.show_message(
                self.translator.t('delete_error'),
                "error"
            )

        finally:
            # Ensure progress dialog is closed
            progress.setValue(len(product_list))
            progress.deleteLater()

        return deleted_ids

    def _clear_field(self, row, column):
        """Handle single field clearing with proper cleanup"""
        # Get current values for undo capability
        id_item = self.table.item(row, 0)
        current_item = self.table.item(row, column)

        if not id_item or not current_item:
            self.status_bar.show_message(self.translator.t('invalid_selection'),
                                         "error")
            return

        original_value = current_item.text()

        try:
            part_id = int(id_item.text())
            field_map = {
                1: 'category',
                2: 'car_name',
                3: 'model',
                4: 'product_name',
                5: 'quantity',
                6: 'price'
            }
            field = field_map.get(column)

            if not field:
                self.status_bar.show_message(self.translator.t('invalid_column'),
                                             "error")
                return

            # Special handling for product name
            if field == 'product_name' and not original_value.strip():
                self.status_bar.show_message(self.translator.t('name_required'),
                                             "warning")
                return

            # Simplified confirmation dialog
            confirm = QMessageBox(
                QMessageBox.Question,
                self.translator.t('confirm_clear'),
                self.translator.t('confirm_clear_field').format(
                    field=self.translator.t(field)),
                buttons=QMessageBox.Yes | QMessageBox.No,
                parent=self
            )

            # Apply theming but with simplified styling
            confirm.setStyleSheet(f"""
                QMessageBox {{
                    background-color: {get_color('background')};
                    color: {get_color('text')};
                }}
                QMessageBox QLabel {{
                    color: {get_color('text')};
                }}
            """)

            if confirm.exec_() == QMessageBox.Yes:
                new_value = "" if column in [1, 2, 3] else "0"

                if self.db.update_part(part_id, **{field: new_value}):
                    # Update UI
                    self.show_update_effect(row, column)

                    # Update cached data efficiently
                    for i, prod in enumerate(self.all_products):
                        if prod[0] == part_id:
                            updated = list(prod)
                            updated[column] = new_value if new_value != "" else None
                            self.all_products[i] = tuple(updated)
                            break

                    self.status_bar.show_message(
                        self.translator.t('field_cleared'),
                        "success"
                    )
                else:
                    self.show_error_effect(row, column)
                    self.status_bar.show_message(
                        self.translator.t('update_failed'),
                        "error"
                    )
            else:
                # Restore original value if user cancels
                current_item.setText(original_value)

            # Explicit cleanup
            confirm.deleteLater()

        except ValueError:
            self.show_error_effect(row, column)
            self.status_bar.show_message(
                self.translator.t('invalid_id_format'),
                "error"
            )
        except Exception as e:
            self.show_error_effect(row, column)
            self.status_bar.show_message(
                self.translator.t('operation_error'),
                "error"
            )



# Move this class outside of the universal_remove method
# Make it a class-level definition in ProductsWidget
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