from PyQt5.QtWidgets import (QWidget, QStackedWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel)
from PyQt5.QtCore import Qt, pyqtSignal

from .cars_widget import CarsWidget
from .products_widget import ProductsWidget
from .details_widget import DetailsWidget
from .final_widget import FinalWidget
from .utils.navigation import NavigationState
from themes import get_color


class PartsNavigationContainer(QWidget):
    """
    Main container widget that orchestrates the parts navigation flow.
    Contains a stacked widget with all step views and controls navigation.
    """
    # Signal for when a part is fully selected
    part_selected = pyqtSignal(dict)

    def __init__(self, translator, parts_db):
        super().__init__()
        self.translator = translator
        self.parts_db = parts_db
        self.navigation_state = NavigationState()

        # Initialize stacked_widget as attribute before setup_ui
        self.stacked_widget = None

        # Initialize UI components
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        """Initialize and arrange the UI elements"""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(10)

        # Navigation title
        self.title = QLabel(self.translator.t('parts_navigation_title'))
        self.title.setObjectName("navigationTitle")
        self.title.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.title)

        # Breadcrumb navigation
        self.breadcrumb_widget = QWidget()
        self.breadcrumb_layout = QHBoxLayout(self.breadcrumb_widget)
        self.breadcrumb_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.addWidget(self.breadcrumb_widget)

        # Create stacked widget first
        self.stacked_widget = QStackedWidget()

        # Initialize step widgets
        self.cars_widget = CarsWidget(self.translator, self.parts_db)
        self.products_widget = ProductsWidget(self.translator, self.parts_db)
        self.details_widget = DetailsWidget(self.translator, self.parts_db)
        self.final_widget = FinalWidget(self.translator, self.parts_db)

        # Add widgets to stack
        self.stacked_widget.addWidget(self.cars_widget)
        self.stacked_widget.addWidget(self.products_widget)
        self.stacked_widget.addWidget(self.details_widget)
        self.stacked_widget.addWidget(self.final_widget)

        # Update breadcrumbs after stacked_widget is initialized
        self.update_breadcrumbs()

        # Connect signals
        self.cars_widget.car_selected.connect(self.on_car_selected)
        self.products_widget.product_selected.connect(self.on_product_selected)
        self.details_widget.details_selected.connect(self.on_details_selected)
        self.final_widget.back_requested.connect(self.go_back)

        # Add stacked widget to main layout
        self.main_layout.addWidget(self.stacked_widget, 1)  # Takes all available space

        # Back/Next navigation buttons
        self.nav_buttons_widget = QWidget()
        self.nav_buttons_layout = QHBoxLayout(self.nav_buttons_widget)

        self.back_button = QPushButton(self.translator.t('back_button'))
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setVisible(False)  # Hidden on first page

        self.nav_buttons_layout.addWidget(self.back_button)
        self.nav_buttons_layout.addStretch(1)  # Push buttons to opposite sides

        self.main_layout.addWidget(self.nav_buttons_widget)

        # Start with the cars widget
        self.stacked_widget.setCurrentWidget(self.cars_widget)
    def update_translations(self):
        """Update all translatable text when language changes"""
        self.title.setText(self.translator.t('parts_navigation_title'))
        self.back_button.setText(self.translator.t('back_button'))
        self.update_breadcrumbs()

        # Update all step widgets
        self.cars_widget.update_translations()
        self.products_widget.update_translations()
        self.details_widget.update_translations()
        self.final_widget.update_translations()

    def apply_theme(self):
        """Apply current theme to the widget"""
        bg_color = get_color('background')
        text_color = get_color('text')
        button_color = get_color('button')
        button_hover = get_color('button_hover')
        card_bg = get_color('card_bg')

        # Title styling
        title_style = f"""
            #navigationTitle {{
                color: {text_color};
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
        """

        # Breadcrumb styling
        breadcrumb_style = f"""
            QPushButton {{
                background-color: {button_color};
                color: {text_color};
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {button_hover};
            }}
            QPushButton:disabled {{
                background-color: {card_bg};
                color: #888888;
            }}
        """

        # Navigation buttons styling
        nav_button_style = f"""
            QPushButton {{
                background-color: {button_color};
                color: {text_color};
                border: none;
                border-radius: 15px;
                padding: 8px 20px;
                font-size: 14px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {button_hover};
            }}
        """

        # Apply styles
        self.setStyleSheet(f"""
            PartsNavigationContainer {{
                background-color: {bg_color};
            }}
            QLabel {{
                color: {text_color};
            }}
            {title_style}
            {breadcrumb_style}
            {nav_button_style}
        """)

        # Make children apply their themes
        for widget in [self.cars_widget, self.products_widget,
                       self.details_widget, self.final_widget]:
            if hasattr(widget, 'apply_theme'):
                widget.apply_theme()

    def on_car_selected(self, car_data):
        """Handle car selection"""
        self.navigation_state.car = car_data
        self.products_widget.set_car_filter(car_data)
        self.stacked_widget.setCurrentWidget(self.products_widget)
        self.back_button.setVisible(True)
        self.update_breadcrumbs()

    def on_product_selected(self, product_data):
        """Handle product selection"""
        self.navigation_state.product = product_data
        self.details_widget.set_product(product_data)
        self.stacked_widget.setCurrentWidget(self.details_widget)
        self.update_breadcrumbs()

    def on_details_selected(self, details_data):
        """Handle details selection"""
        self.navigation_state.details = details_data
        # Combine all data for the final view
        complete_data = {
            **self.navigation_state.car,
            **self.navigation_state.product,
            **details_data
        }
        self.final_widget.set_complete_data(complete_data)
        self.stacked_widget.setCurrentWidget(self.final_widget)
        self.update_breadcrumbs()

        # Emit signal with complete data
        self.part_selected.emit(complete_data)

    def go_back(self):
        """Navigate back one step"""
        current_index = self.stacked_widget.currentIndex()
        if current_index > 0:
            self.stacked_widget.setCurrentIndex(current_index - 1)
            # Hide back button on first page
            self.back_button.setVisible(current_index > 1)
            self.update_breadcrumbs()

    def jump_to_step(self, step_index):
        """Jump to a specific step if it's available in the navigation path"""
        if step_index <= self.stacked_widget.currentIndex():
            self.stacked_widget.setCurrentIndex(step_index)
            self.back_button.setVisible(step_index > 0)
            self.update_breadcrumbs()

    def reset_navigation(self):
        """Reset the navigation to the beginning"""
        self.navigation_state.reset()
        self.stacked_widget.setCurrentIndex(0)
        self.back_button.setVisible(False)
        self.update_breadcrumbs()

    def update_breadcrumbs(self):
        """Update the breadcrumb navigation based on current state"""
        # Ensure stacked_widget exists
        if not hasattr(self, 'stacked_widget') or self.stacked_widget is None:
            return

        # Clear existing breadcrumbs
        for i in reversed(range(self.breadcrumb_layout.count())):
            item = self.breadcrumb_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        # Create new breadcrumbs based on navigation state
        steps = [
            ('cars_step', 0),
            ('products_step', 1),
            ('details_step', 2),
            ('final_step', 3)
        ]

        current_index = self.stacked_widget.currentIndex()

        for i, (key, step_index) in enumerate(steps):
            # Create breadcrumb button
            crumb = QPushButton(self.translator.t(key))

            # Add separator if not the first item
            if i > 0:
                separator = QLabel(" > ")
                separator.setStyleSheet(f"color: {get_color('text')};")
                self.breadcrumb_layout.addWidget(separator)

            # If this step is completed or current, make it clickable
            if step_index <= current_index:
                crumb.clicked.connect(
                    lambda checked, idx=step_index: self.jump_to_step(idx))
            else:
                crumb.setEnabled(False)

            # Highlight current step
            if step_index == current_index:
                crumb.setStyleSheet(f"""
                    background-color: {get_color('highlight')} !important;
                    font-weight: bold;
                """)

            self.breadcrumb_layout.addWidget(crumb)

        # Add stretch to keep breadcrumbs left-aligned
        self.breadcrumb_layout.addStretch(1)