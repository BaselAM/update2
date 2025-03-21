from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                             QLineEdit, QFrame, QMessageBox, QDialog, QFileDialog,
                             QApplication, QProgressDialog)
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSlot, QMetaObject, Q_ARG, QEventLoop

from themes import get_color
from .dialogs import FilterDialog, AddProductDialog, DeleteConfirmationDialog
from .dialogs.themed_meesage import ThemedMessageDialog
from .components import StatusBar
from .product_table import ProductsTable
from .utils import ProductValidator, export_to_csv
from widgets.workers import DatabaseWorker


class ProductsWidget(QWidget):
    def __init__(self, translator, db):
        super().__init__()
        self._is_closing = False
        self.worker_thread = None
        self.translator = translator
        self.db = db
        self.all_products = []
        self.validator = ProductValidator(translator)

        # Add this line to store the last filter configuration
        self.last_filter_settings = {
            "category": "",
            "name": "",
            "car_name": "",
            "model": "",
            "min_price": None,
            "max_price": None,
            "stock_status": None
        }

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
        # Cancel auto-hide when the select button is clicked
        self.select_toggle.clicked.connect(self.cancel_status_timer)
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
        # Cancel auto-hide when refresh button is clicked
        self.refresh_btn.clicked.connect(self.cancel_status_timer)

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
        self.product_table = ProductsTable(self.translator)
        self.product_table.cellChanged.connect(self.on_cell_changed)
        main_layout.addWidget(self.product_table, 1)  # Give table most of the space

        # --- Status Bar ---
        self.status_bar = StatusBar()
        self.status_bar.setObjectName("statusBar")
        main_layout.addWidget(self.status_bar)

    def cancel_status_timer(self):
        """Cancel the status bar's auto-hide timer to keep the message visible upon interaction."""
        self.status_bar.cancel_auto_hide()

    def apply_theme(self):
        """Apply current theme to all elements with enhanced styling."""
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

        border_rgba = QColor(accent_color)
        border_rgba.setAlpha(120)
        border_str = f"rgba({border_rgba.red()}, {border_rgba.green()}, {border_rgba.blue()}, 0.47)"

        is_dark_theme = QColor(bg_color).lightness() < 128
        shadow_opacity = "0.4" if is_dark_theme else "0.15"
        shadow_color = f"rgba(0, 0, 0, {shadow_opacity})"

        base_style = f"""
            QWidget {{
                color: {text_color};
                font-family: 'Segoe UI';
                font-size: 14px;
            }}
            #productsContainer {{
                background-color: {bg_color};
                border: 3px solid {border_str};
                border-radius: 12px;
                padding: 5px;
            }}
        """
        self.setStyleSheet(base_style)

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
                padding: 9px 17px;
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
        self.product_table.apply_theme()

        # Set up the status bar theme so its colors match your system themes
        theme_status = {
            "success": {"bg": get_color('status_success_bg') or "#e8f5e9",
                        "border": get_color('status_success_border') or "#81c784",
                        "text": get_color('status_success_text') or "#2E7D32"},
            "error": {"bg": get_color('status_error_bg') or "#ffebee",
                      "border": get_color('status_error_border') or "#e57373",
                      "text": get_color('status_error_text') or "#C62828"},
            "warning": {"bg": get_color('status_warning_bg') or "#fff8e1",
                        "border": get_color('status_warning_border') or "#ffd54f",
                        "text": get_color('status_warning_text') or "#EF6C00"},
            "info": {"bg": get_color('status_info_bg') or "#e3f2fd",
                     "border": get_color('status_info_border') or "#64b5f6",
                     "text": get_color('status_info_text') or "#1565C0"}
        }
        self.status_bar.set_theme(theme_status)

    def on_select_toggled(self, checked):
        try:
            self.product_table.set_selection_mode(checked)

            bg_color = get_color('background')
            text_color = get_color('text')
            border_color = get_color('border')
            highlight_color = get_color('highlight')
            button_color = get_color('button')
            button_hover = get_color('button_hover')
            button_pressed = get_color('button_pressed')
            card_bg = get_color('card_bg')

            is_dark_theme = QColor(bg_color).lightness() < 128
            shadow_opacity = "0.4" if is_dark_theme else "0.15"
            shadow_color = f"rgba(0, 0, 0, {shadow_opacity})"

            if checked:
                highlight_style = f"""
                    QPushButton {{
                        background-color: {highlight_color};
                        color: {bg_color};
                        border: 1px solid {highlight_color};
                        border-radius: 6px;
                        padding: 10px 18px;
                        margin: 3px;
                        font-size: 15px;
                        font-weight: bold;
                        min-width: 100px;
                        box-sizing: border-box;
                    }}
                    QPushButton:hover {{
                        background-color: {QColor(highlight_color).darker(110).name()};
                        border-color: {QColor(highlight_color).darker(120).name()};
                    }}
                """
                self.select_toggle.setStyleSheet(highlight_style)
                self.status_bar.show_message(self.translator.t('select_mode_enabled'), "info")
            else:
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
                        box-sizing: border-box;
                    }}
                    QPushButton:hover {{
                        background-color: {button_hover};
                        border: 1px solid {highlight_color};
                        box-shadow: 0px 2px 4px {shadow_color};
                    }}
                    QPushButton:pressed {{
                        background-color: {button_pressed};
                        border: 1px solid {highlight_color};
                        padding: 10px 18px;
                    }}
                    QPushButton:disabled {{
                        background-color: {card_bg};
                        color: {border_color};
                        border: 1px solid {border_color};
                    }}
                    QPushButton:checked {{
                        background-color: {highlight_color};
                        color: {bg_color};
                        border: 1px solid {highlight_color};
                        padding: 10px 18px;
                    }}
                """
                self.select_toggle.setStyleSheet(btn_style)
                self.status_bar.clear()

        except Exception as e:
            error_msg = f"{self.translator.t('selection_mode_error')}: {str(e)}"
            print(f"Selection mode error: {error_msg}")
            self.status_bar.show_message(error_msg, "error")
            self.select_toggle.blockSignals(True)
            self.select_toggle.setChecked(False)
            self.select_toggle.blockSignals(False)
            self.apply_theme()

    def on_search(self, text):
        search_text = text.lower().strip()
        if not search_text:
            self.product_table.update_table_data(self.all_products)
            return

        filtered_products = []
        for product in self.all_products:
            searchable_fields = [
                str(product[1] or ""),
                str(product[2] or ""),
                str(product[3] or ""),
                str(product[4] or "")
            ]
            searchable_text = " ".join(searchable_fields).lower()
            if search_text in searchable_text:
                filtered_products.append(product)

        self.product_table.update_table_data(filtered_products)

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

    def highlight_product(self, search_text):
        return self.product_table.highlight_product(search_text)

    def show_filter_dialog(self):
        dialog = FilterDialog(self.translator, self)

        # Initialize dialog with last filter settings
        dialog.initialize_from_saved_settings(self.last_filter_settings)

        if dialog.exec_() == QDialog.Accepted:
            filters = dialog.get_filters()
            # Save the current filter settings for next time
            self.last_filter_settings = filters.copy()
            self.filter_products(filters)

    # Update the filter_products method in ProductsWidget class
    def filter_products(self, filters):
        try:
            if not self.all_products:
                self.all_products = self.db.get_all_parts()

            filtered = []
            for prod in self.all_products:
                category = prod[1] if prod[1] else ""
                name = prod[4] if prod[4] else ""
                car_name = prod[2] if prod[2] else ""
                model = prod[3] if prod[3] else ""
                price = float(prod[6]) if prod[6] else 0
                quantity = int(prod[5]) if prod[5] else 0

                # Check category
                if filters["category"] and filters[
                    "category"].lower() not in category.lower():
                    continue

                # Check name
                if filters["name"] and filters["name"].lower() not in name.lower():
                    continue

                # Check car name
                if filters["car_name"] and filters[
                    "car_name"].lower() not in car_name.lower():
                    continue

                # Check model
                if filters["model"] and filters["model"].lower() not in model.lower():
                    continue

                # Check price range
                if filters["min_price"] is not None and price < filters["min_price"]:
                    continue
                if filters["max_price"] is not None and price > filters["max_price"]:
                    continue

                # Check stock status
                if filters["stock_status"] == "in_stock" and quantity <= 0:
                    continue
                if filters["stock_status"] == "out_of_stock" and quantity > 0:
                    continue

                filtered.append(prod)

            self.product_table.update_table_data(filtered)
            self.status_bar.show_message(
                self.translator.t('filter_results').format(
                    count=len(filtered),
                    total=len(self.all_products)
                ),
                "info"
            )

        except Exception as e:
            print("Error filtering products:", e)
            import traceback
            print(traceback.format_exc())
            self.status_bar.show_message(self.translator.t('filter_error'), "error")

    def on_cell_changed(self, row, column):
        table = self.product_table.table
        if row < 0 or column < 0 or row >= table.rowCount() or column >= table.columnCount():
            return

        if column == 0:
            return

        try:
            item = table.item(row, column)
            id_item = table.item(row, 0)

            if not item or not id_item:
                return

            try:
                part_id = int(id_item.text())
            except (ValueError, TypeError):
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
            if not field:
                return

            new_value = item.text().strip()

            if field == 'quantity':
                try:
                    new_value = int(new_value)
                except ValueError:
                    table.blockSignals(True)
                    item.setText('0')
                    table.blockSignals(False)
                    new_value = 0

            elif field == 'price':
                try:
                    new_value = float(new_value)
                except ValueError:
                    table.blockSignals(True)
                    item.setText('0.0')
                    table.blockSignals(False)
                    new_value = 0.0

            if field == 'product_name' and not new_value:
                original_part = self.db.get_part(part_id)
                original_name = original_part[4] if original_part else "Product"
                table.blockSignals(True)
                item.setText(original_name)
                table.blockSignals(False)
                return

            update_data = {field: new_value}
            success = self.db.update_part(part_id, **update_data)

            if success:
                for i, prod in enumerate(self.all_products):
                    if prod[0] == part_id:
                        prod_list = list(prod)
                        if column == 5:
                            prod_list[5] = int(new_value)
                        elif column == 6:
                            prod_list[6] = float(new_value)
                        else:
                            prod_list[column] = new_value
                        self.all_products[i] = tuple(prod_list)
                        break

                if field == 'quantity':
                    table.blockSignals(True)
                    item.setText(str(int(new_value)))
                    table.blockSignals(False)
                elif field == 'price':
                    table.blockSignals(True)
                    item.setText(f"{float(new_value):.2f}")
                    table.blockSignals(False)

                # Simply show success message, no need to reload products
                success_message = self.translator.t('product_updated')
                self.status_bar.show_message(success_message, "success", 3000)

        except Exception as e:
            print(f"Error handling cell change: {e}")
            import traceback
            print(traceback.format_exc())

    # Also update process_add_product to use sequential messaging:

    def load_products(self):
        print("Loading products from database")
        if self._is_closing:
            print("Application is closing, skipping product load")
            return

        if self.worker_thread and self.worker_thread.isRunning():
            print("Stopping existing worker thread")
            self.worker_thread.quit()
            self.worker_thread.wait(1000)

        self.status_bar.show_message(self.translator.t('loading_products'), "info")

        try:
            self.worker_thread = DatabaseWorker(self.db, "load")
            self.worker_thread.finished.connect(self.handle_loaded_products)
            self.worker_thread.error.connect(self.show_error)
            self.worker_thread.start()
            print("Worker thread started for loading products")

        except Exception as e:
            print(f"Error starting worker thread: {e}")
            try:
                print("Fallback: Loading products directly")
                products = self.db.get_all_parts()
                print(f"Loaded {len(products)} products directly")
                self.handle_loaded_products(products)
            except Exception as direct_error:
                print(f"Direct loading also failed: {direct_error}")
                self.status_bar.show_message(self.translator.t('load_error'), "error")

        # Reset filter settings when loading all products
        self.last_filter_settings = {
            "category": "",
            "name": "",
            "car_name": "",
            "model": "",
            "min_price": None,
            "max_price": None,
            "stock_status": None
        }

    @pyqtSlot(object)
    def handle_loaded_products(self, products):
        try:
            self.all_products = products
            self.product_table.update_table_data(products)
            self.status_bar.show_message(
                self.translator.t('products_loaded').format(count=len(products)),
                "success"
            )
        except Exception as e:
            print(f"Load error: {e}")
            self.status_bar.show_message(self.translator.t('load_error'), "error")

    def show_error(self, message):
        if self._is_closing:
            return
        self.status_bar.show_message(message, "error")

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
            print(f"[{self.__class__.__name__}] Processing add product request: {data}")
            sanitized_data = self.validator.sanitize_product_data(data)
            is_valid, error_msg = self.validator.validate_product(sanitized_data)

            if not is_valid:
                self.status_bar.show_message(error_msg, "error")
                return

            existing = self.db.get_part_by_name(sanitized_data['product_name'])
            if existing:
                # Replace QMessageBox with ThemedMessageDialog
                confirm = ThemedMessageDialog.confirm(
                    self.translator.t('overwrite_title'),
                    self.translator.t('overwrite_message'),
                    parent=self,
                    icon_type="question"
                )

                if confirm:
                    print(
                        f"[{self.__class__.__name__}] Updating existing product with ID: {existing[0]}")
                    success = self.db.update_part(existing[0], **sanitized_data)
                    if not success:
                        raise Exception("Failed to update existing product")

                    # Show success message immediately
                    success_message = self.translator.t('product_updated')
                    self.status_bar.show_message(success_message, "success")

                    # Delay loading products to ensure message is visible
                    QTimer.singleShot(1500,
                                      lambda: self._complete_add_product(existing[0]))
                else:
                    return
            else:
                print(
                    f"[{self.__class__.__name__}] Adding new product: {sanitized_data['product_name']}")
                success = self.db.add_part(**sanitized_data)
                if not success:
                    raise Exception("Failed to add new product")

                print(
                    "[{self.__class__.__name__}] Add successful, verifying in database...")
                verify_product = self.db.get_part_by_name(sanitized_data['product_name'])
                if not verify_product:
                    print(
                        "[{self.__class__.__name__}] ERROR: Product appears in UI but couldn't be verified in database!")
                    raise Exception("Product verification failed - database update issue")

                print(
                    f"[{self.__class__.__name__}] Product verified in database with ID: {verify_product[0]}")

                # Show success message immediately
                success_message = self.translator.t('product_added')
                self.status_bar.show_message(success_message, "success")

                # Delay loading products to ensure message is visible
                QTimer.singleShot(1500,
                                  lambda: self._complete_add_product(verify_product[0]))

        except Exception as e:
            print(f"[{self.__class__.__name__}] Add product error: {e}")
            import traceback
            print(f"[{self.__class__.__name__}] Traceback: {traceback.format_exc()}")
            self.status_bar.show_message(self.translator.t('add_error'), "error")
            QTimer.singleShot(500, self.load_products)

    def _complete_add_product(self, product_id):
        """Complete the product addition process after showing success message."""
        try:
            # Now load products
            print(
                f"[{self.__class__.__name__}] Completing product add/update for ID: {product_id}")
            self.load_products()

            # After products are loaded, show count message
            QTimer.singleShot(100, lambda: self._show_products_loaded_message(product_id))
        except Exception as e:
            print(f"[{self.__class__.__name__}] Error completing product add: {e}")

    def _show_products_loaded_message(self, product_id=None):
        """Show products loaded message and highlight row if product_id is provided."""
        try:
            loaded_message = self.translator.t('products_loaded').format(
                count=len(self.all_products))
            self.status_bar.show_message(loaded_message, "info", 5000)

            # If we have a product ID, try to highlight that row
            if product_id is not None and hasattr(self.product_table,
                                                  'highlight_row_by_id'):
                self.product_table.highlight_row_by_id(product_id)
            elif product_id is not None:
                # Fallback if highlight method doesn't exist
                self.product_table.highlight_product(str(product_id))
        except Exception as e:
            print(
                f"[{self.__class__.__name__}] Error showing products loaded message: {e}")

    def universal_remove(self):
        try:
            if self.select_toggle.isChecked():
                product_details = self.product_table.get_selected_rows_data()
                if not product_details:
                    self.status_bar.show_message(self.translator.t('no_rows_selected'),
                                                 "warning")
                    return

                # Create the dialog
                dialog = DeleteConfirmationDialog(
                    products=product_details,
                    translator=self.translator,
                    parent=self
                )

                # Now we can safely use dialog
                if dialog.exec_() == QDialog.Accepted:
                    deleted_ids = self._batch_delete_products(product_details)
                    if deleted_ids:
                        print("Loading fresh data after deletion")

                        # Show success message before loading products
                        success_message = self.translator.t('items_deleted').format(
                            count=len(deleted_ids))
                        self.status_bar.show_message(success_message, "success")

                        # Wait before loading products
                        QTimer.singleShot(1500, self._complete_remove_operation)
                    else:
                        self.status_bar.show_message(self.translator.t('delete_failed'),
                                                     "error")

            else:
                self.status_bar.show_message(
                    self.translator.t(
                        'select_mode_required') or "Select mode must be enabled for deletion",
                    "warning"
                )
                return

        except Exception as e:
            import traceback

            # Handle missing translation gracefully
            error_message = str(e)
            try:
                error_prefix = self.translator.t('unexpected_error')
            except:
                error_prefix = "Unexpected error"

            self.status_bar.show_message(
                f"{error_prefix}: {error_message}",
                "error"
            )
            print(f"Universal remove error: {traceback.format_exc()}")
            self.load_products()

    def _complete_remove_operation(self):
        """Complete the product removal process after showing success message."""
        try:
            # Load products
            self.load_products()

            # Show count message after products are loaded
            loaded_message = self.translator.t('products_loaded').format(
                count=len(self.all_products))
            self.status_bar.show_message(loaded_message, "info", 5000)
        except Exception as e:
            print(f"Error completing product removal: {e}")
    # For cell editing, add a success message in the on_cell_changed method:

    def _batch_delete_products(self, product_list):
        if not product_list:
            print("No products selected for deletion")
            return []

        print(f"Starting deletion of {len(product_list)} products")
        print(f"Operation started at: 2025-03-20 17:49:58")
        print(f"Current user: BaselAM")
        deleted_ids = []

        progress = QProgressDialog(
            self.translator.t('deleting_items').format(count=len(product_list)),
            self.translator.t('cancel'),
            0, len(product_list), self
        )
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(500)
        progress.setMinimumWidth(350)

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

        try:
            original_count = len(self.all_products)
            print(f"Original product count: {original_count}")

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

            if deleted_ids:
                print(f"Successfully deleted {len(deleted_ids)} products")
                remaining_products = [p for p in self.all_products if p[0] not in deleted_ids]
                print(f"Original count: {len(self.all_products)}, New count: {len(remaining_products)}")
                self.all_products = remaining_products
                print("Updating table with remaining products")
                self.product_table.update_table_data(self.all_products)
                expected_count = original_count - len(deleted_ids)
                actual_count = self.product_table.table.rowCount()
                print(f"Expected row count: {expected_count}, Actual: {actual_count}")

        except Exception as e:
            print(f"Error during deletion: {e}")
            import traceback
            print(traceback.format_exc())
            self.status_bar.show_message(
                self.translator.t('delete_error'),
                "error"
            )
            print("Emergency recovery - reloading all products")
            QTimer.singleShot(100, self.load_products)

        finally:
            progress.setValue(len(product_list))
            progress.deleteLater()

        print(f"Deletion operation completed at: 2025-03-20 17:50:58")
        return deleted_ids

    def emergency_reload(self):
        print("Emergency reload initiated")
        try:
            self.all_products = None
            import gc
            gc.collect()
            self.all_products = self.db.get_all_parts()
            print(f"Loaded {len(self.all_products)} products directly from database")
            self.product_table.update_table_data(self.all_products)
            print(f"Table updated with {self.product_table.table.rowCount()} rows")
            self.status_bar.show_message(
                f"Emergency reload complete. {len(self.all_products)} products loaded.",
                "info"
            )
        except Exception as e:
            print(f"Emergency reload failed: {e}")
            import traceback
            print(traceback.format_exc())

    def update_translations(self):
        self.add_btn.setText(self.translator.t('add_product'))
        self.select_toggle.setText(self.translator.t('select_button'))
        self.remove_btn.setText(self.translator.t('remove'))
        self.filter_btn.setText(self.translator.t('filter_button'))
        self.export_btn.setText(self.translator.t('export'))
        self.refresh_btn.setText(self.translator.t('refresh'))
        self.search_input.setPlaceholderText(self.translator.t('search_placeholder'))
        self.product_table.update_headers()
        if self.status_bar.isVisible():
            message_type = "info"
            if hasattr(self.status_bar, 'current_type'):
                message_type = self.status_bar.current_type

            current_text = self.status_bar.status_text.text()
            if current_text.startswith("Found "):
                self.status_bar.show_message(
                    self.translator.t('search_results').format(
                        count=len([r for r in range(self.product_table.table.rowCount())
                                   if not self.product_table.table.isRowHidden(r)]),
                        total=len(self.all_products)
                    ),
                    message_type
                )
            elif current_text.startswith("Loaded "):
                self.status_bar.show_message(
                    self.translator.t('products_loaded').format(
                        count=self.product_table.table.rowCount()),
                    message_type
                )

    def closeEvent(self, event):
        try:
            self._is_closing = True
            if self.worker_thread and self.worker_thread.isRunning():
                self.worker_thread.quit()
                self.worker_thread.wait(1000)
            self.all_products = None
        except Exception as e:
            print(f"Cleanup error: {e}")
        event.accept()

    # Add this method to the ProductsWidget class:

    def export_data(self):
        try:
            table = self.product_table.table
            rows = table.rowCount()
            cols = table.columnCount()

            if rows == 0:
                self.status_bar.show_message(self.translator.t('no_data_to_export'),
                                             "warning")
                return

            file_name, _ = QFileDialog.getSaveFileName(
                self,
                self.translator.t('export_title'),
                "",
                "CSV Files (*.csv);;All Files (*)"
            )

            if not file_name:
                return

            headers = []
            for col in range(cols):
                headers.append(table.horizontalHeaderItem(col).text())

            data = []
            for row in range(rows):
                row_data = []
                for col in range(cols):
                    item = table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            success = export_to_csv(file_name, headers, data)

            if success:
                # Show sequential messages for export success, then product count
                success_message = self.translator.t('export_success').format(
                    file=file_name)
                loaded_message = self.translator.t('products_loaded').format(
                    count=len(self.all_products))
                self.status_bar.show_sequential_messages(
                    success_message,
                    loaded_message,
                    "success",
                    "info",
                    3000,  # Show success for 3 seconds
                    5000  # Show loaded message for 5 seconds
                )
            else:
                self.status_bar.show_message(self.translator.t('export_error'), "error")

        except Exception as e:
            print(f"Export error: {e}")
            self.status_bar.show_message(self.translator.t('export_error'), "error")

    def highlight_row_by_id(self, product_id):
        """Highlight a row containing the product with the given ID."""
        for row in range(self.table.rowCount()):
            id_item = self.table.item(row, 0)
            if id_item and id_item.text() == str(product_id):
                # Highlight the row
                for col in range(self.table.columnCount()):
                    cell_item = self.table.item(row, col)
                    if cell_item:
                        cell_item.setBackground(
                            QColor(230, 255, 230))  # Light green background

                # Scroll to the row
                self.table.scrollToItem(id_item)

                # Schedule removing the highlight after 3 seconds
                QTimer.singleShot(3000, lambda r=row: self._remove_highlight(r))
                return True
        return False

    def _remove_highlight(self, row):
        """Remove highlighting from a row."""
        if row < 0 or row >= self.table.rowCount():
            return

        for col in range(self.table.columnCount()):
            cell_item = self.table.item(row, col)
            if cell_item:
                cell_item.setBackground(QColor(255, 255, 255))  # Reset to white/default

    # Replace your existing filter_products method or similar with this:

    def open_filter_dialog(self):
        """Open the filter dialog and apply the selected filters."""
        try:
            # Get currency symbol from settings or use default
            currency_symbol = "₪"  # Default to ILS
            try:
                # Try to get currency from settings if available
                settings = self.db.get_settings()
                if settings and "default_currency" in settings:
                    currency_code = settings["default_currency"].lower()
                    currency_map = {"usd": "$", "eur": "€", "gbp": "£", "ils": "₪"}
                    currency_symbol = currency_map.get(currency_code, "₪")
            except Exception as e:
                print(f"Could not get currency setting: {e}")

            # Create dialog with currency symbol passed directly
            filter_dialog = FilterDialog(self.translator, parent=self,
                                         currency_symbol=currency_symbol)

            # If user accepts the dialog, apply the filters
            if filter_dialog.exec_() == QDialog.Accepted:
                self.apply_filters(filter_dialog.get_filters())

        except Exception as e:
            self.status_bar.show_message(self.translator.t('filter_error'), "error")
            print(f"Error in filter dialog: {e}")

    def apply_filters(self, filters):
        """Apply the filters from the filter dialog to the product table with improved stock filtering."""
        try:
            # Store original products for reference
            original_products = self.all_products.copy() if hasattr(self,
                                                                    'all_products') else []

            # Add debug print to see what filters are being applied
            print(f"Applying filters: {filters}")
            print(f"Total products before filtering: {len(original_products)}")

            filtered_products = []
            count = 0

            for product in original_products:
                # Check all filter criteria
                match = True

                # Debug print for a sample product
                if count == 0:
                    print(f"Sample product: {product}")

                # Category filter
                if filters["category"] and filters["category"].lower() not in str(
                        product.get("category", "")).lower():
                    match = False

                # Name filter
                if filters["name"] and filters["name"].lower() not in str(
                        product.get("product_name", "")).lower():
                    match = False

                # Car filter
                if filters["car_name"] and filters["car_name"].lower() not in str(
                        product.get("car_name", "")).lower():
                    match = False

                # Model filter
                if filters["model"] and filters["model"].lower() not in str(
                        product.get("model", "")).lower():
                    match = False

                # Price filters
                if filters["min_price"] is not None:
                    try:
                        product_price = float(product.get("price", 0))
                        if product_price < filters["min_price"]:
                            match = False
                    except (ValueError, TypeError):
                        pass  # Skip invalid price values

                if filters["max_price"] is not None:
                    try:
                        product_price = float(product.get("price", 0))
                        if product_price > filters["max_price"]:
                            match = False
                    except (ValueError, TypeError):
                        pass  # Skip invalid price values

                # Stock status filter - simplified
                if filters.get("stock_status") == "in_stock":
                    # Try several field names that might contain quantity
                    quantity = 0
                    try:
                        for field in ["quantity", "qty", "stock", "inventory"]:
                            if field in product:
                                quantity = int(product[field])
                                break
                    except (ValueError, TypeError):
                        quantity = 0

                    if quantity <= 0:
                        match = False

                elif filters.get("stock_status") == "out_of_stock":
                    # Try several field names that might contain quantity
                    quantity = 1  # Default to in-stock
                    try:
                        for field in ["quantity", "qty", "stock", "inventory"]:
                            if field in product:
                                quantity = int(product[field])
                                break
                    except (ValueError, TypeError):
                        quantity = 1

                    if quantity > 0:
                        match = False

                if match:
                    filtered_products.append(product)
                    count += 1

            # Display filtered products
            if hasattr(self, 'product_table') and hasattr(self.product_table,
                                                          'display_products'):
                self.product_table.display_products(filtered_products)

            # Update status message
            status_msg = self.translator.t('filter_status').format(count=count, total=len(
                original_products))

            if hasattr(self, 'status_bar') and hasattr(self.status_bar, 'show_message'):
                self.status_bar.show_message(status_msg, "info")

            # Debug print final results
            print(f"Matched products after filtering: {count}")

        except Exception as e:
            print(f"Error applying filters: {e}")
            import traceback
            traceback.print_exc()

            if hasattr(self, 'status_bar') and hasattr(self.status_bar, 'show_message'):
                self.status_bar.show_message(self.translator.t('filter_error'), "error")

