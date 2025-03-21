from PyQt5.QtWidgets import QWidget, QDialog
from PyQt5.QtCore import Qt, QTimer, pyqtSlot

from .product_widget.core.product_loader import ProductLoader
from .product_widget.core.product_manager import ProductManager
from .product_widget.handlers.ui_handler import UIHandler
from .product_widget.handlers.search_handler import SearchHandler
from .product_widget.handlers.filter_handler import FilterHandler
from .product_widget.handlers.edit_handler import EditHandler
from .product_widget.handlers.selection_handler import SelectionHandler
from .product_widget.operations.add_operation import AddOperation
from .product_widget.operations.delete_operation import DeleteOperation
from .product_widget.operations.export_operation import ExportOperation

from .utils import ProductValidator
from .dialogs import FilterDialog


class ProductsWidget(QWidget):
    def __init__(self, translator, db):
        super().__init__()
        self._is_closing = False
        self.translator = translator
        self.db = db

        # Initialize validator
        self.validator = ProductValidator(translator)

        # Initialize UI handler
        self.ui_handler = UIHandler(self, translator)
        ui_components = self.ui_handler.setup_ui()

        # Store UI components
        self.add_btn = ui_components['add_btn']
        self.select_toggle = ui_components['select_toggle']
        self.remove_btn = ui_components['remove_btn']
        self.filter_btn = ui_components['filter_btn']
        self.export_btn = ui_components['export_btn']
        self.refresh_btn = ui_components['refresh_btn']
        self.search_input = ui_components['search_input']
        self.product_table = ui_components['product_table']
        self.status_bar = ui_components['status_bar']

        # Apply theme
        self.ui_handler.apply_theme()

        # Initialize core components
        self.product_manager = ProductManager(db)
        self.product_loader = ProductLoader(db, self)

        # Initialize handlers
        self.search_handler = SearchHandler(translator)
        self.filter_handler = FilterHandler(translator)
        self.edit_handler = EditHandler(translator, db)
        self.selection_handler = SelectionHandler(translator, self.product_table,
                                                  self.ui_handler)

        # Initialize operations
        self.add_operation = AddOperation(self, translator, db, self.validator,
                                          self.status_bar)
        self.delete_operation = DeleteOperation(self, translator, db, self.status_bar)
        self.export_operation = ExportOperation(self, translator, self.status_bar)

        # Connect signals
        self._connect_signals()

        # Load products after initialization
        QTimer.singleShot(100, self.load_products)

    def _connect_signals(self):
        """Connect all signals for the widget"""
        # Connect button signals
        self.add_btn.clicked.connect(self.add_operation.show_add_dialog)
        self.select_toggle.toggled.connect(self.toggle_selection_mode)
        self.remove_btn.clicked.connect(self.delete_selected_products)
        self.filter_btn.clicked.connect(self.show_filter_dialog)
        self.export_btn.clicked.connect(self.export_products)
        self.refresh_btn.clicked.connect(self.load_products)

        # Connect search signal
        self.search_input.textChanged.connect(self.on_search)

        # Connect table signals
        self.product_table.cellChanged.connect(self.on_cell_changed)

        # Connect cancel auto-hide when buttons clicked
        self.select_toggle.clicked.connect(self.cancel_status_timer)
        self.refresh_btn.clicked.connect(self.cancel_status_timer)

        # Connect data loader signals
        self.product_loader.products_loaded.connect(self.handle_loaded_products)
        self.product_loader.error_occurred.connect(self.show_error)

    def toggle_selection_mode(self, checked):
        """Toggle product selection mode"""
        success, message = self.selection_handler.toggle_selection_mode(checked)

        if not success:
            self.status_bar.show_message(message, "error")
            self.select_toggle.blockSignals(True)
            self.select_toggle.setChecked(False)
            self.select_toggle.blockSignals(False)
            self.ui_handler.apply_theme()
        elif message:
            self.status_bar.show_message(message, "info")
        else:
            self.status_bar.clear()

    def on_search(self, text):
        """Handle search text changes"""
        filtered_products, message = self.search_handler.search_products(
            self.product_manager.get_products(),
            text
        )
        self.product_table.update_table_data(filtered_products)

        if message:
            self.status_bar.show_message(message, "info")
        else:
            self.status_bar.clear()

    def on_cell_changed(self, row, column):
        """Handle cell value changes"""
        success, product_id, field, new_value, message = self.edit_handler.handle_cell_change(
            row, column, self.product_table.table, self.product_manager.get_products()
        )

        if success:
            # Update in-memory product data
            self.product_manager.update_product_in_memory(product_id, field, new_value,
                                                          column)
            self.status_bar.show_message(message, "success", 3000)

    def show_filter_dialog(self):
        """Show filter dialog"""
        dialog = FilterDialog(self.translator, self)
        dialog.initialize_from_saved_settings(
            self.filter_handler.get_last_filter_settings())

        if dialog.exec_() == QDialog.Accepted:
            filters = dialog.get_filters()
            self.filter_handler.save_filter_settings(filters)
            self.apply_filters(filters)

    def apply_filters(self, filters):
        """Apply filters to products"""
        filtered_products, message = self.filter_handler.filter_products(
            self.product_manager.get_products(),
            filters
        )
        self.product_table.update_table_data(filtered_products)
        self.status_bar.show_message(message, "info")

    def delete_selected_products(self):
        """Delete selected products"""
        self.delete_operation.delete_selected_products(
            self.select_toggle.isChecked(),
            self.product_table
        )

    def export_products(self):
        """Export products to CSV"""
        self.export_operation.export_to_csv(
            self.product_table,
            self.product_manager.get_products()
        )

    def load_products(self):
        """Load products from database"""
        self.status_bar.show_message(self.translator.t('loading_products'), "info")
        self.product_loader.load_products(self._is_closing)

        # Reset filter settings when loading all products
        self.filter_handler.reset_filters()

    @pyqtSlot(list)
    def handle_loaded_products(self, products):
        """Handle loaded products data"""
        try:
            self.product_manager.set_products(products)
            self.product_table.update_table_data(products)
            self.status_bar.show_message(
                self.translator.t('products_loaded').format(count=len(products)),
                "success"
            )
        except Exception as e:
            print(f"Load error: {e}")
            self.status_bar.show_message(self.translator.t('load_error'), "error")

    def on_product_added(self, product_id):
        """Called after a product is added or updated"""
        self.load_products()
        QTimer.singleShot(100, lambda: self._highlight_product(product_id))

    def on_products_deleted(self, deleted_ids):
        """Called after products are deleted"""
        # Update in-memory products list
        self.product_manager.remove_products_by_ids(deleted_ids)

        # Reload products
        self.load_products()

    def _highlight_product(self, product_id):
        """Highlight a product in the table"""
        if product_id is None:
            return

        try:
            # Try to highlight row
            if hasattr(self.product_table, 'highlight_row_by_id'):
                self.product_table.highlight_row_by_id(product_id)
            else:
                self.product_table.highlight_product(str(product_id))

            # Show loaded message
            loaded_message = self.translator.t('products_loaded').format(
                count=len(self.product_manager.get_products()))
            self.status_bar.show_message(loaded_message, "info", 5000)
        except Exception as e:
            print(f"Error highlighting product: {e}")

    def cancel_status_timer(self):
        """Cancel the status bar's auto-hide timer"""
        if hasattr(self.status_bar, 'cancel_auto_hide'):
            self.status_bar.cancel_auto_hide()

    def show_error(self, message):
        """Show error message"""
        if self._is_closing:
            return
        self.status_bar.show_message(message, "error")

    def highlight_product(self, search_text):
        """Highlight a product in the table"""
        return self.product_table.highlight_product(search_text)

    def update_translations(self):
        """Update all translations in the UI"""
        self.ui_handler.update_translations()

    def closeEvent(self, event):
        """Handle widget close event"""
        try:
            self._is_closing = True
            if hasattr(self.product_loader, 'cleanup'):
                self.product_loader.cleanup()
            self.product_manager.clear()
        except Exception as e:
            print(f"Cleanup error: {e}")
        event.accept()