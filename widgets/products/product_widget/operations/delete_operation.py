from PyQt5.QtWidgets import QProgressDialog, QApplication, QDialog
from PyQt5.QtCore import Qt, QTimer, QEventLoop
from PyQt5.QtGui import QColor

from themes import get_color
from widgets.products.dialogs import DeleteConfirmationDialog


class DeleteOperation:
    """Handles deleting products"""

    def __init__(self, parent_widget, translator, db, status_bar):
        self.parent = parent_widget
        self.translator = translator
        self.db = db
        self.status_bar = status_bar

    def delete_selected_products(self, select_mode_enabled, product_table):
        """Delete products based on selection"""
        if not select_mode_enabled:
            self.status_bar.show_message(
                self.translator.t('select_mode_required'),
                "warning"
            )
            return

        product_details = product_table.get_selected_rows_data()
        if not product_details:
            self.status_bar.show_message(
                self.translator.t('no_rows_selected'),
                "warning"
            )
            return

        # Create the confirmation dialog
        dialog = DeleteConfirmationDialog(
            products=product_details,
            translator=self.translator,
            parent=self.parent
        )

        if dialog.exec_() == QDialog.Accepted:
            deleted_ids = self._perform_deletion(product_details)
            if deleted_ids:
                success_message = self.translator.t('items_deleted').format(
                    count=len(deleted_ids))
                self.status_bar.show_message(success_message, "success")

                # Signal parent to reload products after a delay
                QTimer.singleShot(1500,
                                  lambda: self.parent.on_products_deleted(deleted_ids))
            else:
                self.status_bar.show_message(
                    self.translator.t('delete_failed'),
                    "error"
                )

    def _perform_deletion(self, product_list):
        """
        Delete the selected products

        Args:
            product_list: List of (id, name) tuples of products to delete

        Returns:
            list: IDs of successfully deleted products
        """
        if not product_list:
            return []

        print(f"Starting deletion of {len(product_list)} products")
        deleted_ids = []

        # Create progress dialog
        progress = QProgressDialog(
            self.translator.t('deleting_items').format(count=len(product_list)),
            self.translator.t('cancel'),
            0, len(product_list), self.parent
        )
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(500)
        progress.setMinimumWidth(350)

        # Apply theme to progress dialog
        self._apply_theme_to_progress(progress)

        try:
            for i, (pid, name) in enumerate(product_list):
                if progress.wasCanceled():
                    print("Deletion canceled by user")
                    self.status_bar.show_message(
                        self.translator.t('operation_canceled'),
                        "warning"
                    )
                    break

                progress.setValue(i)
                QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
                print(f"Deleting product #{pid} - {name}")
                success = self.db.delete_part(pid)

                if success:
                    deleted_ids.append(pid)
                    print(f"Successfully deleted product #{pid}")
                else:
                    print(f"Failed to delete product #{pid}")

        except Exception as e:
            print(f"Error during deletion: {e}")
            import traceback
            print(traceback.format_exc())
            self.status_bar.show_message(
                self.translator.t('delete_error'),
                "error"
            )

        finally:
            progress.setValue(len(product_list))
            progress.deleteLater()

        return deleted_ids

    def _apply_theme_to_progress(self, progress):
        """Apply theme styling to progress dialog"""
        bg_color = get_color('background')
        text_color = get_color('text')
        border_color = get_color('border')
        highlight_color = get_color('highlight')

        progress_style = f"""
            QProgressDialog {{
                background-color: {get_color('card_bg')};
                border: 2px solid {border_color};
                border-radius: 8px;
                min-width: 350px;
                padding: 10px;
            }}
            QLabel {{
                color: {text_color};
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            QProgressBar {{
                border: 1px solid {border_color};
                border-radius: 5px;
                background-color: {bg_color};
                text-align: center;
                height: 25px;
            }}
            QProgressBar::chunk {{
                background-color: {highlight_color};
                border-radius: 4px;
            }}
            QPushButton {{
                background-color: {get_color('button')};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 5px;
                padding: 6px 12px;
                min-width: 80px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {get_color('button_hover')};
                border: 1px solid {highlight_color};
            }}
        """
        progress.setStyleSheet(progress_style)