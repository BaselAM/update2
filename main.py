import sys
import logging
from pathlib import Path
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

from shared import SCRIPT_DIR
from shared_imports import *
from widgets.splash import SplashScreen
from gui import GUI
from database.settings_db import SettingsDB
from database.car_parts_db import CarPartsDB
from translator import Translator
from widgets.login_widget import LoginWidget
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger('main')

# Global variables to hold references
login_widget = None
main_gui = None
db_instance = None


def create_db_instance():
    """Create a database instance with proper error handling"""
    try:
        logger.info("Initializing database connection...")
        db = CarPartsDB()
        # Verify the database is accessible
        parts_count = len(db.get_all_parts())
        logger.info(f"Connected to database. Found {parts_count} parts.")
        return db
    except Exception as e:
        error_msg = f"Database connection error: {str(e)}"
        logger.error(error_msg)
        QMessageBox.critical(None, "Database Error", error_msg)
        sys.exit(1)


def cleanup_resources():
    """Properly clean up resources at application exit"""
    logger.info("Cleaning up application resources...")
    try:
        # Close database connections
        if db_instance:
            logger.info("Closing database connection...")
            db_instance.close_connection()

        # Additional cleanup as needed
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")


if __name__ == "__main__":
    logger.info(f"Application starting at: 2025-03-20 00:09:53")
    logger.info(f"Current user: BaselAM")

    QApplication.setAttribute(Qt.AA_UseSoftwareOpenGL)
    app = QApplication(sys.argv)

    # Ensure proper cleanup at exit
    app.aboutToQuit.connect(cleanup_resources)

    try:
        # Validate resources
        for fname in ["resources/intro.jpg", "resources/car-icon.jpg",
                      "resources/search_icon.png"]:
            if not (SCRIPT_DIR / fname).exists():
                raise FileNotFoundError(f"Missing file: {SCRIPT_DIR / fname}")

        # Create resources folder and icons if they don't exist
        resources_dir = SCRIPT_DIR / "resources"
        if not resources_dir.exists():
            resources_dir.mkdir(exist_ok=True)
            logger.info("Created resources directory")

        # Check for required icon files for ProductsWidget
        required_icons = [
            "add_icon.png", "select_icon.png", "delete_icon.png",
            "filter_icon.png", "export_icon.png", "refresh_icon.png",
            "info_icon.png", "success_icon.png", "error_icon.png",
            "warning_icon.png", "close_icon.png"
        ]

        # Report missing icons but don't fail - the app will still work
        for icon in required_icons:
            if not (resources_dir / icon).exists():
                logger.warning(f"Missing icon file: {icon}")

        # Initialize database once and share the instance
        db_instance = create_db_instance()

        # Show splash screen
        splash = SplashScreen()
        splash.show()

        # Pre-create the main GUI with shared database instance
        main_gui = GUI(car_parts_db=db_instance)
        main_gui.hide()

        # Create the login widget
        login_widget = LoginWidget()
        login_widget.hide()  # start hidden


        # When login is successful, close the login widget and show the main GUI
        def on_login(username):
            logger.info(f"User logged in: {username}")
            login_widget.close()
            main_gui.set_current_user(username)
            main_gui.show()


        login_widget.login_successful.connect(on_login)


        # After the splash, show the login widget
        def show_login():
            splash.close()
            login_widget.show()


        QTimer.singleShot(2000, show_login)

        exit_code = app.exec_()
        sys.exit(exit_code)

    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}", exc_info=True)
        QMessageBox.critical(None, "Fatal Error",
                             f"An unrecoverable error occurred: {str(e)}")
        sys.exit(1)