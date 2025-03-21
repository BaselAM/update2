from PyQt5.QtCore import QObject, pyqtSignal
from widgets.workers import DatabaseWorker


class ProductLoader(QObject):
    """Handles loading product data from the database"""

    # Signals
    products_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.worker_thread = None

    def load_products(self, is_closing=False):
        """Load products from database using worker thread"""
        print("Loading products from database")
        if is_closing:
            print("Application is closing, skipping product load")
            return

        if self.worker_thread and self.worker_thread.isRunning():
            print("Stopping existing worker thread")
            self.worker_thread.quit()
            self.worker_thread.wait(1000)

        try:
            self.worker_thread = DatabaseWorker(self.db, "load")
            self.worker_thread.finished.connect(self.products_loaded.emit)
            self.worker_thread.error.connect(self.error_occurred.emit)
            self.worker_thread.start()
            print("Worker thread started for loading products")

        except Exception as e:
            print(f"Error starting worker thread: {e}")
            try:
                print("Fallback: Loading products directly")
                products = self.db.get_all_parts()
                print(f"Loaded {len(products)} products directly")
                self.products_loaded.emit(products)
            except Exception as direct_error:
                print(f"Direct loading also failed: {direct_error}")
                self.error_occurred.emit("Failed to load products")

    def emergency_reload(self):
        """Emergency reload of products when normal loading fails"""
        print("Emergency reload initiated")
        try:
            import gc
            gc.collect()
            products = self.db.get_all_parts()
            print(f"Loaded {len(products)} products directly from database")
            self.products_loaded.emit(products)
            return products
        except Exception as e:
            print(f"Emergency reload failed: {e}")
            import traceback
            print(traceback.format_exc())
            self.error_occurred.emit(f"Emergency reload failed: {str(e)}")
            return []

    def cleanup(self):
        """Clean up resources before closing"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait(1000)