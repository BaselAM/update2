class EditHandler:
    """Handles product editing functionality"""

    def __init__(self, translator, db):
        self.translator = translator
        self.db = db

    def handle_cell_change(self, row, column, table, all_products):
        """
        Handle cell change in the product table

        Args:
            row: Row index
            column: Column index
            table: Product table widget
            all_products: List of all products

        Returns:
            tuple: (success, product_id, field, new_value, message)
        """
        if row < 0 or column < 0 or row >= table.rowCount() or column >= table.columnCount():
            return False, None, None, None, None

        if column == 0:  # Skip ID column
            return False, None, None, None, None

        try:
            item = table.item(row, column)
            id_item = table.item(row, 0)

            if not item or not id_item:
                return False, None, None, None, None

            try:
                part_id = int(id_item.text())
            except (ValueError, TypeError):
                return False, None, None, None, None

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
                return False, None, None, None, None

            new_value = item.text().strip()

            # Handle special field types
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

            # Ensure product name is not empty
            if field == 'product_name' and not new_value:
                original_part = self.db.get_part(part_id)
                original_name = original_part[4] if original_part else "Product"
                table.blockSignals(True)
                item.setText(original_name)
                table.blockSignals(False)
                return False, None, None, None, None

            # Update the database
            update_data = {field: new_value}
            success = self.db.update_part(part_id, **update_data)

            if success:
                # Format display if necessary
                if field == 'quantity':
                    table.blockSignals(True)
                    item.setText(str(int(new_value)))
                    table.blockSignals(False)
                elif field == 'price':
                    table.blockSignals(True)
                    item.setText(f"{float(new_value):.2f}")
                    table.blockSignals(False)

                # Show success message
                success_message = self.translator.t('product_updated')
                return True, part_id, field, new_value, success_message

            return False, None, None, None, None

        except Exception as e:
            print(f"Error handling cell change: {e}")
            import traceback
            print(traceback.format_exc())
            return False, None, None, None, None