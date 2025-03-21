from PyQt5.QtWidgets import QFileDialog
from widgets.products.utils import export_to_csv


class ExportOperation:
    """Handles exporting products to CSV"""

    def __init__(self, parent_widget, translator, status_bar):
        self.parent = parent_widget
        self.translator = translator
        self.status_bar = status_bar

    def export_to_csv(self, product_table, all_products):
        """Export product data to CSV file"""
        try:
            table = product_table.table
            rows = table.rowCount()
            cols = table.columnCount()

            if rows == 0:
                self.status_bar.show_message(
                    self.translator.t('no_data_to_export'),
                    "warning"
                )
                return False

            file_name, _ = QFileDialog.getSaveFileName(
                self.parent,
                self.translator.t('export_title'),
                "",
                "CSV Files (*.csv);;All Files (*)"
            )

            if not file_name:
                return False

            # Get headers from table
            headers = []
            for col in range(cols):
                headers.append(table.horizontalHeaderItem(col).text())

            # Get data from table
            data = []
            for row in range(rows):
                row_data = []
                for col in range(cols):
                    item = table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            # Perform export
            success = export_to_csv(file_name, headers, data)

            if success:
                # Show success message
                success_message = self.translator.t('export_success').format(
                    file=file_name)
                loaded_message = self.translator.t('products_loaded').format(
                    count=len(all_products))

                # Check for sequential messages support
                if hasattr(self.status_bar, 'show_sequential_messages'):
                    self.status_bar.show_sequential_messages(
                        success_message,
                        loaded_message,
                        "success",
                        "info",
                        3000,  # Show success for 3 seconds
                        5000  # Show loaded message for 5 seconds
                    )
                else:
                    # Fall back to single message
                    self.status_bar.show_message(success_message, "success")

                return True
            else:
                self.status_bar.show_message(
                    self.translator.t('export_error'),
                    "error"
                )
                return False

        except Exception as e:
            print(f"Export error: {e}")
            import traceback
            print(traceback.format_exc())
            self.status_bar.show_message(
                self.translator.t('export_error'),
                "error"
            )
            return False