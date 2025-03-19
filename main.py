import sys
from pathlib import Path
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication

from shared import SCRIPT_DIR
from shared_imports import *
from widgets.splash import SplashScreen
from gui import GUI
from database.settings_db import SettingsDB
from database.car_parts_db import CarPartsDB
from translator import Translator
from widgets.login_widget import LoginWidget

# Global variables to hold references.
login_widget = None
main_gui = None

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_UseSoftwareOpenGL)
    app = QApplication(sys.argv)

    try:
        # Validate resources.
        for fname in ["resources/intro.jpg", "resources/car-icon.jpg",
                      "resources/search_icon.png"]:
            if not (SCRIPT_DIR / fname).exists():
                raise FileNotFoundError(f"Missing file: {SCRIPT_DIR / fname}")

        # Create resources folder and icons if they don't exist
        resources_dir = SCRIPT_DIR / "resources"
        if not resources_dir.exists():
            resources_dir.mkdir(exist_ok=True)
            print("Created resources directory")

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
                print(f"Note: Missing icon file: {icon}")
                # The app will use text fallbacks if icons are missing

        splash = SplashScreen()
        splash.show()

        # Pre-create the main GUI, but hide it until login is successful.
        main_gui = GUI()
        main_gui.hide()

        # Create the login widget (which now matches your GUI theme).
        login_widget = LoginWidget()
        login_widget.hide()  # start hidden


        # When login is successful, close the login widget and show the main GUI.
        def on_login(username):
            login_widget.close()
            # Pass the username to the GUI
            main_gui.set_current_user(username)
            main_gui.show()


        login_widget.login_successful.connect(on_login)


        # After the splash, show the login widget.
        def show_login():
            splash.close()
            login_widget.show()


        QTimer.singleShot(2000, show_login)

        exit_code = app.exec_()
        sys.exit(exit_code)

    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)
