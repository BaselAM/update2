from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QLineEdit, QCompleter
from PyQt5.QtGui import QIcon

from shared import SCRIPT_DIR


class ElegantSearchBar(QLineEdit):
    """A stylish search bar with clear button"""

    search_triggered = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Search for settings, products, reports...")

        # Add search icon
        search_icon_path = SCRIPT_DIR / "resources/search_icon.png"
        if search_icon_path.exists():
            search_action = self.addAction(QIcon(str(search_icon_path)),
                                           QLineEdit.LeadingPosition)

        # Add clear button
        self.setClearButtonEnabled(True)

        # Connect signals
        self.returnPressed.connect(self._on_search)

        # Add auto-complete suggestions
        self.setUpAutoComplete()

    def setUpAutoComplete(self):
        # Common search terms in the app
        suggestions = [
            "Products", "Settings", "Statistics", "Reports",
            "Parts", "Database", "Users", "Help", "Search",
            "Car Parts", "Import", "Export", "Inventory",
            "BMW", "Toyota", "Honda", "Ford", "Brake Pads",
            "Filters", "Oil", "Battery", "Tires", "Engine"
        ]

        completer = QCompleter(suggestions, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(completer)

    def _on_search(self):
        text = self.text().strip()
        if text:
            self.search_triggered.emit(text)