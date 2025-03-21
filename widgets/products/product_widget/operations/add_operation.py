from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QTimer

from widgets.products.dialogs.themed_meesage import ThemedMessageDialog
from widgets.products.dialogs import AddProductDialog


class AddOperation:
    """Handles adding products"""

    def __init__(self, parent_widget, translator, db, validator, status_bar):
        self.parent = parent_widget
        self.translator = translator
        self.db = db
        self.validator = validator
        self.status_bar = status_bar

    def show_add_dialog(self):
        """Show the add product dialog"""
        try:
            dialog = AddProductDialog(self.translator, self.parent)
            dialog.finished.connect(lambda: self._handle_dialog_result(dialog))
            dialog.show()
        except Exception as e:
            print(f"Dialog error: {e}")
            self.status_bar.show_message(self.translator.t('dialog_error'), "error")

    def _handle_dialog_result(self, dialog):
        """Process the result from the add product dialog"""
        if dialog.result() == QDialog.Accepted:
            try:
                data = dialog.get_data()
                self.process_add_product(data)
            except Exception as e:
                print(f"Data processing error: {e}")
                self.status_bar.show_message(self.translator.t('data_error'), "error")

    def process_add_product(self, data):
        """Process the product addition request"""
        try:
            print(f"Processing add product request: {data}")
            sanitized_data = self.validator.sanitize_product_data(data)
            is_valid, error_msg = self.validator.validate_product(sanitized_data)

            if not is_valid:
                self.status_bar.show_message(error_msg, "error")
                return None

            existing = self.db.get_part_by_name(sanitized_data['product_name'])
            if existing:
                # Get confirmation for overwriting
                confirm = ThemedMessageDialog.confirm(
                    self.translator.t('overwrite_title'),
                    self.translator.t('overwrite_message'),
                    parent=self.parent,
                    icon_type="question"
                )

                if confirm:
                    print(f"Updating existing product with ID: {existing[0]}")
                    success = self.db.update_part(existing[0], **sanitized_data)
                    if not success:
                        raise Exception("Failed to update existing product")

                    # Show success message immediately
                    success_message = self.translator.t('product_updated')
                    self.status_bar.show_message(success_message, "success")

                    # Signal to parent to reload products
                    QTimer.singleShot(1500,
                                      lambda: self.parent.on_product_added(existing[0]))
                    return existing[0]
                else:
                    return None
            else:
                print(f"Adding new product: {sanitized_data['product_name']}")
                success = self.db.add_part(**sanitized_data)
                if not success:
                    raise Exception("Failed to add new product")

                print("Add successful, verifying in database...")
                verify_product = self.db.get_part_by_name(sanitized_data['product_name'])
                if not verify_product:
                    print(
                        "ERROR: Product appears in UI but couldn't be verified in database!")
                    raise Exception("Product verification failed - database update issue")

                print(f"Product verified in database with ID: {verify_product[0]}")

                # Show success message immediately
                success_message = self.translator.t('product_added')
                self.status_bar.show_message(success_message, "success")

                # Signal to parent to reload products
                QTimer.singleShot(1500,
                                  lambda: self.parent.on_product_added(verify_product[0]))
                return verify_product[0]

        except Exception as e:
            print(f"Add product error: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            self.status_bar.show_message(self.translator.t('add_error'), "error")
            QTimer.singleShot(500, lambda: self.parent.load_products())
            return None