from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QListWidget, QListWidgetItem, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from themes import get_color


class CarsWidget(QWidget):
    """
    First step in the parts navigation - selecting a car
    Displays a list of available cars from the database
    """
    car_selected = pyqtSignal(dict)

    def __init__(self, translator, parts_db):
        super().__init__()
        self.translator = translator
        self.parts_db = parts_db
        self.setup_ui()
        self.load_cars()
        self.apply_theme()

    def setup_ui(self):
        """Initialize and arrange UI elements"""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(15)

        # Title
        self.title = QLabel(self.translator.t('select_car'))
        self.title.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.title)

        # Search box
        self.search_layout = QHBoxLayout()
        self.search_label = QLabel(self.translator.t('search_cars'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.translator.t('search_cars_placeholder'))
        self.search_input.textChanged.connect(self.filter_cars)

        self.search_layout.addWidget(self.search_label)
        self.search_layout.addWidget(self.search_input, 1)
        self.main_layout.addLayout(self.search_layout)

        # Cars list
        self.cars_list = QListWidget()
        self.cars_list.itemDoubleClicked.connect(self.on_car_double_clicked)
        self.main_layout.addWidget(self.cars_list, 1)  # Take all available space

        # Help text at bottom
        self.help_text = QLabel(self.translator.t('select_car_help'))
        self.help_text.setAlignment(Qt.AlignCenter)
        self.help_text.setWordWrap(True)
        self.main_layout.addWidget(self.help_text)

    def load_cars(self):
        """Load cars from database"""
        try:
            # Get unique cars from database
            cars = self.parts_db.get_unique_cars()
            self.all_cars = cars

            # Clear and populate the list
            self.cars_list.clear()
            for car in cars:
                item = QListWidgetItem()
                display_text = f"{car['make']} {car['model']} ({car['year']})"
                item.setText(display_text)
                item.setData(Qt.UserRole, car)
                self.cars_list.addItem(item)

        except Exception as e:
            print(f"Error loading cars: {str(e)}")

    def filter_cars(self, search_text):
        """Filter the car list based on search text"""
        search_text = search_text.lower()
        self.cars_list.clear()

        for car in self.all_cars:
            # Check if search text is in make, model, or year
            make = car['make'].lower()
            model = car['model'].lower()
            year = str(car['year']).lower()

            if (search_text in make or search_text in model or
                    search_text in year):
                item = QListWidgetItem()
                display_text = f"{car['make']} {car['model']} ({car['year']})"
                item.setText(display_text)
                item.setData(Qt.UserRole, car)
                self.cars_list.addItem(item)

    def on_car_double_clicked(self, item):
        """Handle double-click on a car item"""
        car_data = item.data(Qt.UserRole)
        self.car_selected.emit(car_data)

    def update_translations(self):
        """Update all translatable text"""
        self.title.setText(self.translator.t('select_car'))
        self.search_label.setText(self.translator.t('search_cars'))
        self.search_input.setPlaceholderText(self.translator.t('search_cars_placeholder'))
        self.help_text.setText(self.translator.t('select_car_help'))

    def apply_theme(self):
        """Apply current theme"""
        bg_color = get_color('background')
        card_bg = get_color('card_bg')
        text_color = get_color('text')
        border_color = get_color('border')

        # Set styles
        self.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-size: 14px;
            }}

            QLineEdit {{
                background-color: {card_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }}

            QListWidget {{
                background-color: {card_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
                outline: none;
            }}

            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {border_color};
            }}

            QListWidget::item:selected {{
                background-color: {get_color('highlight')};
                color: {get_color('highlight_text')};
            }}

            QListWidget::item:hover {{
                background-color: {get_color('button_hover')};
            }}
        """)

        # Title style
        self.title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            color: {text_color};
        """)

        # Help text style
        self.help_text.setStyleSheet(f"""
            color: {get_color('secondary_text')};
            font-size: 13px;
            font-style: italic;
            margin-top: 5px;
        """)