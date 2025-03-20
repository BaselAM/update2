from shared_imports import *
from database.car_parts_db import CarPartsDB


class DatabaseWorker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, db, operation, **kwargs):
        super().__init__()
        self.db = db
        self.operation = operation
        self.kwargs = kwargs

    def run(self):
        try:
            # Each worker thread will get its own database connection
            if self.operation == "load":
                # Get all parts using the thread-local connection
                result = self.db.get_all_parts()
                self.finished.emit(result)
            elif self.operation == "delete":
                # Delete using thread-local connection
                part_id = self.kwargs.get('part_id')
                success = self.db.delete_part(part_id)
                self.finished.emit(success)
            # Add other operations as needed
        except Exception as e:
            import traceback
            self.error.emit(f"Database worker error: {str(e)}")
            print(f"Worker thread error: {traceback.format_exc()}")