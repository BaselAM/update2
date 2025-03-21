class SelectionHandler:
    """Handles product selection mode functionality"""

    def __init__(self, translator, product_table, ui_handler):
        self.translator = translator
        self.product_table = product_table
        self.ui_handler = ui_handler

    def toggle_selection_mode(self, checked):
        """
        Toggle selection mode for products

        Args:
            checked: Whether selection mode is enabled

        Returns:
            tuple: (success, message)
        """
        try:
            self.product_table.set_selection_mode(checked)
            self.ui_handler.update_select_button_style(checked)

            if checked:
                message = self.translator.t('select_mode_enabled')
                return True, message
            else:
                return True, None

        except Exception as e:
            error_msg = f"{self.translator.t('selection_mode_error')}: {str(e)}"
            print(f"Selection mode error: {error_msg}")
            return False, error_msg