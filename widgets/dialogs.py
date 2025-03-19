from shared_imports import *
from themes import *
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QScrollArea, QDialogButtonBox,
    QWidget, QGraphicsDropShadowEffect  # Move the effect here
)
from PyQt5.QtGui import QColor, QPixmap

from themes import get_color
from shared import SCRIPT_DIR
from widgets.utils import is_dark_color
class ItemDetailsDialog(QDialog):
    def __init__(self, item_data, translator, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.translator = translator
        self.setWindowTitle("Item Details")  # You can translate this too
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        # Assuming item_data is a dict with your fields
        for key, value in self.item_data.items():
            layout.addWidget(QLabel(f"{key}: {value}"))
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
        btn_box.accepted.connect(self.accept)
        layout.addWidget(btn_box)


class AddProductDialog(QDialog):
    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator

        # Apply dialog theme
        apply_dialog_theme(
            self,
            title=self.translator.t('add_product'),
            icon_path="resources/add_icon.png",
            min_width=500
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Create header with icon
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 10)

        icon = QLabel()
        icon.setPixmap(QIcon("resources/add_icon.png").pixmap(32, 32))
        header_layout.addWidget(icon)

        title = QLabel(f"<h2>{self.translator.t('add_product')}</h2>")
        title.setStyleSheet(f"color: {get_color('text')}; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addWidget(header)

        # Create form for product details
        form_container = QGroupBox(self.translator.t('product_details'))
        form_layout = QFormLayout(form_container)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(15, 20, 15, 15)

        # Product name (required)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(self.translator.t('product_name_placeholder'))
        name_label = QLabel(f"{self.translator.t('product_name')}* :")
        name_label.setStyleSheet("font-weight: bold;")
        form_layout.addRow(name_label, self.name_edit)

        # Category
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText(self.translator.t('category_placeholder'))
        form_layout.addRow(QLabel(f"{self.translator.t('category')}:"),
                           self.category_edit)

        # Car name
        self.car_edit = QLineEdit()
        self.car_edit.setPlaceholderText(self.translator.t('car_placeholder'))
        form_layout.addRow(QLabel(f"{self.translator.t('car')}:"), self.car_edit)

        # Model
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText(self.translator.t('model_placeholder'))
        form_layout.addRow(QLabel(f"{self.translator.t('model')}:"), self.model_edit)

        # Quantity
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(0, 9999)
        self.quantity_spin.setValue(1)
        form_layout.addRow(QLabel(f"{self.translator.t('quantity')}:"),
                           self.quantity_spin)

        # Price
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 999999.99)
        self.price_spin.setDecimals(2)
        self.price_spin.setSuffix(" ₪")  # Change to your currency
        self.price_spin.setValue(0.00)
        form_layout.addRow(QLabel(f"{self.translator.t('price')}:"), self.price_spin)

        layout.addWidget(form_container)

        # Add note about required fields
        note = QLabel(f"* {self.translator.t('required_field')}")
        note.setStyleSheet(
            f"color: {get_color('highlight')}; font-style: italic; font-size: 12px;")
        layout.addWidget(note)

        # Buttons
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)

        clear_btn = QPushButton(self.translator.t('clear_all'))
        clear_btn.setIcon(QIcon("resources/clear_icon.png"))
        clear_btn.clicked.connect(self.clear_fields)

        save_btn = QPushButton(self.translator.t('save'))
        save_btn.setObjectName("primaryButton")  # For special styling
        save_btn.setIcon(QIcon("resources/save_icon.png"))
        save_btn.clicked.connect(self.validate_and_accept)

        cancel_btn = QPushButton(self.translator.t('cancel'))
        cancel_btn.setIcon(QIcon("resources/cancel_icon.png"))
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(clear_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)

        layout.addWidget(button_container)

        # Set focus to name field
        self.name_edit.setFocus()

    def clear_fields(self):
        """Clear all input fields"""
        self.name_edit.clear()
        self.category_edit.clear()
        self.car_edit.clear()
        self.model_edit.clear()
        self.quantity_spin.setValue(1)
        self.price_spin.setValue(0.00)
        self.name_edit.setFocus()

    def validate_and_accept(self):
        """Validate inputs before accepting"""
        if not self.name_edit.text().strip():
            self.show_error(self.translator.t('name_required'))
            self.name_edit.setFocus()
            return

        self.accept()

    def show_error(self, message):
        """Show styled error message"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(self.translator.t('validation_error'))
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)

        # Apply theme to message box
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {get_color('background')};
                color: {get_color('text')};
            }}
            QLabel {{
                color: {get_color('text')};
                min-width: 250px;
            }}
            QPushButton {{
                background-color: {get_color('button')};
                color: {get_color('text')};
                border: 1px solid {get_color('border')};
                border-radius: 4px;
                padding: 6px 12px;
            }}
        """)

        msg.exec_()

    def get_data(self):
        """Return the product data"""
        return {
            'product_name': self.name_edit.text().strip(),
            'category': self.category_edit.text().strip() or None,
            'car_name': self.car_edit.text().strip() or None,
            'model': self.model_edit.text().strip() or None,
            'quantity': self.quantity_spin.value(),
            'price': self.price_spin.value()
        }


    def closeEvent(self, event):
        """Cleanup resources"""
        self.deleteLater()
        super().closeEvent(event)


class FilterDialog(QDialog):
    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator

        # Set up the dialog with theme
        apply_dialog_theme(
            self,
            title=self.translator.t('filter_title'),
            icon_path="resources/filter_icon.png"
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Create header with icon
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 10)

        icon = QLabel()
        icon.setPixmap(QIcon("resources/filter_icon.png").pixmap(32, 32))
        header_layout.addWidget(icon)

        title = QLabel(f"<h2>{self.translator.t('filter_title')}</h2>")
        title.setStyleSheet(f"color: {get_color('text')}; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addWidget(header)

        # Create form layout for filter fields
        form_container = QGroupBox(self.translator.t('filter_criteria'))
        form_layout = QFormLayout(form_container)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(15, 20, 15, 15)

        # Category filter
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText(self.translator.t('category_placeholder'))
        form_layout.addRow(QLabel(f"{self.translator.t('category')}:"),
                           self.category_edit)

        # Name filter
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(self.translator.t('name_placeholder'))
        form_layout.addRow(QLabel(f"{self.translator.t('product_name')}:"),
                           self.name_edit)

        # Price range
        price_widget = QWidget()
        price_layout = QHBoxLayout(price_widget)
        price_layout.setContentsMargins(0, 0, 0, 0)

        self.min_price = QDoubleSpinBox()
        self.min_price.setRange(0, 999999)
        self.min_price.setDecimals(2)
        self.min_price.setSuffix(" ₪")  # You can change to your currency
        self.min_price.setSpecialValueText(self.translator.t('no_min_price'))

        self.max_price = QDoubleSpinBox()
        self.max_price.setRange(0, 999999)
        self.max_price.setDecimals(2)
        self.max_price.setSuffix(" ₪")  # You can change to your currency
        self.max_price.setSpecialValueText(self.translator.t('no_max_price'))
        self.max_price.setValue(0)

        price_layout.addWidget(self.min_price)
        price_layout.addWidget(QLabel("-"))
        price_layout.addWidget(self.max_price)

        form_layout.addRow(QLabel(f"{self.translator.t('price_range')}:"), price_widget)

        layout.addWidget(form_container)

        # Buttons with unified styling
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)

        reset_btn = QPushButton(self.translator.t('reset'))
        reset_btn.setIcon(QIcon("resources/reset_icon.png"))
        reset_btn.clicked.connect(self.reset_filters)

        apply_btn = QPushButton(self.translator.t('apply_filter'))
        apply_btn.setIcon(QIcon("resources/check_icon.png"))
        apply_btn.clicked.connect(self.accept)
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {get_color('highlight')};
                color: white;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {QColor(get_color('highlight')).darker(115).name()};
            }}
        """)

        cancel_btn = QPushButton(self.translator.t('cancel'))
        cancel_btn.setIcon(QIcon("resources/cancel_icon.png"))
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(apply_btn)

        layout.addWidget(button_container)

    def reset_filters(self):
        """Clear all filter fields"""
        self.category_edit.clear()
        self.name_edit.clear()
        self.min_price.setValue(0)
        self.max_price.setValue(0)

    def get_filters(self):
        """Return the current filter values"""
        return {
            "category": self.category_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "min_price": self.min_price.value() if self.min_price.value() > 0 else None,
            "max_price": self.max_price.value() if self.max_price.value() > 0 else None
        }


class EnhancedDialog(QDialog):
    """Enhanced dialog base class with elegant styling"""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(500, 600)  # Larger size for expanded view

        # Set window flags for a more modern look
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)

        self.setup_ui()
        self.apply_theme()

        # Add shadow effect for elegance
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)  # Remove spacing for a more integrated look
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for cleaner look

        # Header with title
        self.header = QFrame()
        self.header.setObjectName("dialogHeader")
        self.header.setMinimumHeight(50)

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(15, 10, 15, 10)

        title_label = QLabel(self.windowTitle())
        title_label.setObjectName("dialogTitle")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        header_layout.addWidget(title_label)

        layout.addWidget(self.header)

        # Content area with scroll
        content_frame = QFrame()
        content_frame.setObjectName("dialogContent")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(15, 15, 15, 15)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)  # Remove frame border
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(10)
        self.scroll_area.setWidget(self.content_widget)

        content_layout.addWidget(self.scroll_area)
        layout.addWidget(content_frame, 1)  # 1 = stretch factor

        # Footer with buttons
        self.footer = QFrame()
        self.footer.setObjectName("dialogFooter")
        self.footer.setMinimumHeight(60)

        footer_layout = QHBoxLayout(self.footer)
        footer_layout.setContentsMargins(15, 10, 15, 10)
        footer_layout.addStretch()

        # Close button in an elegant button box
        button_box = QDialogButtonBox()
        self.close_button = QPushButton("Close")
        self.close_button.setObjectName("closeButton")
        self.close_button.setMinimumSize(100, 35)
        button_box.addButton(self.close_button, QDialogButtonBox.RejectRole)
        button_box.rejected.connect(self.accept)

        footer_layout.addWidget(button_box)
        layout.addWidget(self.footer)

    def apply_theme(self):
        """Apply the current theme to this dialog"""
        bg_color = get_color('background')
        text_color = get_color('text')
        primary_color = get_color('button')
        border_color = get_color('border')

        # Determine if we're using a dark theme
        is_dark_bg = is_dark_color(bg_color)

        # Create contrasting colors for headers and footers
        header_bg = QColor(primary_color).darker(110).name() if is_dark_bg else QColor(
            primary_color).lighter(110).name()
        footer_bg = QColor(bg_color).darker(110).name() if is_dark_bg else QColor(
            bg_color).lighter(110).name()

        # Force text to contrast with backgrounds
        header_text = "#FFFFFF" if is_dark_color(header_bg) else "#000000"

        # Create a gradient for the header
        grad_start = QColor(header_bg).darker(120).name()
        grad_end = header_bg

        self.setStyleSheet(f"""
            EnhancedDialog {{
                background-color: {bg_color};
                color: {text_color};
            }}

            QFrame#dialogHeader {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 {grad_start}, 
                                           stop:1 {grad_end});
                color: {header_text};
                border-bottom: 1px solid {border_color};
            }}

            QLabel#dialogTitle {{
                color: {header_text};
            }}

            QFrame#dialogContent {{
                background-color: {bg_color};
                color: {text_color};
            }}

            QFrame#dialogFooter {{
                background-color: {footer_bg};
                border-top: 1px solid {border_color};
            }}

            QScrollArea {{
                border: none;
                background-color: transparent;
            }}

            QScrollArea > QWidget > QWidget {{
                background-color: transparent;
            }}

            QPushButton#closeButton {{
                background-color: {primary_color};
                color: {text_color};
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}

            QPushButton#closeButton:hover {{
                background-color: {QColor(primary_color).lighter(110).name()};
            }}

            QPushButton {{
                background-color: {primary_color};
                color: {text_color};
                padding: 8px 16px;
                border-radius: 4px;
            }}

            QPushButton:hover {{
                background-color: {QColor(primary_color).lighter(110).name()};
            }}
        """)


class ChatBoxDialog(EnhancedDialog):
    """Enhanced chat dialog"""

    def __init__(self, parent=None):
        super().__init__("Chat Assistant", parent)
        self.show_coming_soon()

    def show_coming_soon(self):
        # Add a sleek container for the message
        container = QFrame()
        container.setObjectName("messageContainer")
        container_layout = QVBoxLayout(container)

        # Add an icon (optional)
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)

        # Try to load the chatbot icon
        chatbot_icon_path = SCRIPT_DIR / "resources/chatbot.png"
        if chatbot_icon_path.exists():
            pixmap = QPixmap(str(chatbot_icon_path)).scaled(64, 64, Qt.KeepAspectRatio,
                                                            Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
            container_layout.addWidget(icon_label)
            container_layout.addSpacing(15)

        # Add title
        title = QLabel("Chat Assistant")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18pt; font-weight: bold;")
        container_layout.addWidget(title)
        container_layout.addSpacing(10)

        # Add a simple message with better styling
        message = QLabel(
            "Chat functionality will be available in the next update. Stay tuned!")
        message.setWordWrap(True)
        message.setAlignment(Qt.AlignCenter)
        message.setStyleSheet(
            f"padding: 20px; font-size: 14pt; color: {get_color('text')};")
        container_layout.addWidget(message)

        # Add version info
        version = QLabel("Coming in v1.2")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("font-style: italic; color: gray;")
        container_layout.addWidget(version)

        # Add container to content
        container_layout.addStretch(1)
        self.content_layout.addWidget(container)
        self.content_layout.addStretch(1)

        # Style the container
        container.setStyleSheet(f"""
            QFrame#messageContainer {{
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                padding: 20px;
            }}
        """)


class NotificationsDialog(EnhancedDialog):
    """Enhanced notifications dialog"""

    notification_clicked = pyqtSignal(int)  # Signal for when a notification is clicked

    def __init__(self, notifications=None, parent=None, db=None):
        super().__init__("Notifications", parent)
        self.db = db
        self.show_notifications(notifications)

    def show_notifications(self, notifications=None):
        # If we have a DB and no notifications provided, load from DB
        if notifications is None and hasattr(self, 'db') and self.db is not None:
            try:
                notifications = self.db.get_notifications(include_read=True, limit=100)
            except Exception:
                # Fallback if DB operation fails
                notifications = None

        # Clear existing content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Show notifications or 'no notifications' message
        if not notifications or len(notifications) == 0:
            # Container for empty state
            empty_container = QFrame()
            empty_container.setObjectName("emptyContainer")
            empty_layout = QVBoxLayout(empty_container)

            # Try to load notification icon
            icon_label = QLabel()
            icon_label.setAlignment(Qt.AlignCenter)

            bell_icon_path = SCRIPT_DIR / "resources/danger.png"  # Reuse danger icon
            if bell_icon_path.exists():
                pixmap = QPixmap(str(bell_icon_path)).scaled(64, 64, Qt.KeepAspectRatio,
                                                             Qt.SmoothTransformation)
                icon_label.setPixmap(pixmap)
                empty_layout.addWidget(icon_label)
                empty_layout.addSpacing(15)

            # No notifications message
            no_notif = QLabel("No notifications at this time")
            no_notif.setAlignment(Qt.AlignCenter)
            no_notif.setStyleSheet(f"""
                font-size: 16pt;
                color: {get_color('text')};
                font-style: italic;
                padding: 20px;
            """)
            empty_layout.addWidget(no_notif)

            # Explanatory text
            explanation = QLabel(
                "You'll see notifications here when there are updates, alerts, or messages about your car parts inventory.")
            explanation.setWordWrap(True)
            explanation.setAlignment(Qt.AlignCenter)
            explanation.setStyleSheet("color: gray; padding: 10px;")
            empty_layout.addWidget(explanation)

            empty_layout.addStretch(1)

            # Style the container
            empty_container.setStyleSheet("""
                QFrame#emptyContainer {
                    background-color: rgba(255, 255, 255, 0.05);
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px;
                }
            """)

            self.content_layout.addWidget(empty_container)
            self.content_layout.addStretch()
        else:
            # Add header for notifications
            header = QLabel("Recent Notifications")
            header.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 10px 0;")
            self.content_layout.addWidget(header)

            # Add filter options
            filter_layout = QHBoxLayout()
            filter_label = QLabel("Filter:")
            filter_layout.addWidget(filter_label)

            all_button = QPushButton("All")
            all_button.setCheckable(True)
            all_button.setChecked(True)
            all_button.clicked.connect(lambda: self.filter_notifications("all"))

            unread_button = QPushButton("Unread")
            unread_button.setCheckable(True)
            unread_button.clicked.connect(lambda: self.filter_notifications("unread"))

            filter_layout.addWidget(all_button)
            filter_layout.addWidget(unread_button)
            filter_layout.addStretch()

            self.content_layout.addLayout(filter_layout)
            self.content_layout.addSpacing(10)

            # Add notifications
            for notification in notifications:
                self._add_notification_item(notification)

            # Add action buttons at the bottom if we have a database
            if hasattr(self, 'db') and self.db is not None:
                button_layout = QHBoxLayout()

                mark_all_button = QPushButton("Mark All as Read")
                mark_all_button.clicked.connect(self.mark_all_as_read)
                button_layout.addWidget(mark_all_button)

                button_layout.addStretch()

                delete_read_button = QPushButton("Delete Read")
                delete_read_button.clicked.connect(self.delete_read_notifications)
                button_layout.addWidget(delete_read_button)

                self.content_layout.addSpacing(10)
                self.content_layout.addLayout(button_layout)

    def _add_notification_item(self, notification):
        """Add a single notification item to the dialog"""
        notif_frame = QFrame()
        notif_frame.setObjectName("notificationItem")

        # Store notification ID for later reference
        notif_id = notification.get('id')
        if notif_id is not None:
            notif_frame.setProperty("notification_id", notif_id)

        # Style read vs unread notifications differently
        if notification.get('read', False):
            notif_frame.setProperty("read", True)
            # Use card_bg if available, otherwise use a default color
            card_bg = get_color('card_bg')
            if not card_bg:
                card_bg = '#2f3136'

            notif_frame.setStyleSheet(f"""
                QFrame#notificationItem[read="true"] {{
                    background-color: {card_bg};
                    border-radius: 8px;
                    margin: 5px 0;
                    opacity: 0.7;
                }}
            """)
        else:
            # Use card_bg and accent if available, otherwise use default colors
            card_bg = get_color('card_bg')
            if not card_bg:
                card_bg = '#2f3136'

            accent = get_color('accent')
            if not accent:
                accent = '#3498db'

            notif_frame.setStyleSheet(f"""
                QFrame#notificationItem {{
                    background-color: {card_bg};
                    border-radius: 8px;
                    margin: 5px 0;
                    border-left: 4px solid {accent};
                }}
            """)

        notif_layout = QVBoxLayout(notif_frame)
        notif_layout.setContentsMargins(15, 10, 15, 10)

        # Title with icon
        title_layout = QHBoxLayout()

        # Title
        title = QLabel(notification.get('title', 'Notification'))
        title.setStyleSheet("font-weight: bold; font-size: 13pt;")
        title_layout.addWidget(title)

        # Time (right-aligned)
        time_label = QLabel(notification.get('time', ''))
        time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        time_label.setStyleSheet("font-size: 10pt; color: gray;")
        title_layout.addWidget(time_label)

        notif_layout.addLayout(title_layout)

        # Message
        message = QLabel(notification.get('message', ''))
        message.setWordWrap(True)
        message.setStyleSheet("font-size: 12pt; padding: 5px 0;")
        notif_layout.addWidget(message)

        # Add category tag if available
        category = notification.get('category', '')
        if category and category != 'general':
            category_label = QLabel(f"#{category}")
            category_label.setStyleSheet("""
                color: gray;
                font-size: 10pt;
                font-style: italic;
            """)
            notif_layout.addWidget(category_label)

        # Make notification clickable
        if notif_id is not None:
            notif_frame.setCursor(Qt.PointingHandCursor)
            # Fix to ensure proper binding of notification_id in lambdas
            self._make_clickable(notif_frame, notif_id)

        self.content_layout.addWidget(notif_frame)

    def _make_clickable(self, widget, id_value):
        """Helper to make widget clickable with correct ID binding"""
        widget.mousePressEvent = lambda e, id_val=id_value: self._notification_clicked(
            id_val)

    def _notification_clicked(self, notification_id):
        """Handle notification click"""
        if hasattr(self, 'db') and self.db is not None:
            try:
                self.db.mark_as_read(notification_id)
            except Exception:
                pass

        self.notification_clicked.emit(notification_id)

        # Refresh the display to show it as read now
        if hasattr(self, 'db') and self.db is not None:
            try:
                self.show_notifications(self.db.get_notifications(include_read=True))
            except Exception:
                pass

    def filter_notifications(self, filter_type):
        """Filter notifications by type"""
        if not hasattr(self, 'db') or self.db is None:
            return

        try:
            if filter_type == "unread":
                notifications = self.db.get_notifications(include_read=False)
            else:
                notifications = self.db.get_notifications(include_read=True)

            self.show_notifications(notifications)
        except Exception:
            # Handle any database errors
            pass

    def mark_all_as_read(self):
        """Mark all notifications as read"""
        if hasattr(self, 'db') and self.db is not None:
            try:
                self.db.mark_all_as_read()
                self.show_notifications(self.db.get_notifications(include_read=True))
            except Exception:
                pass

    def delete_read_notifications(self):
        """Delete read notifications"""
        if hasattr(self, 'db') and self.db is not None:
            try:
                self.db.delete_all_read()
                self.show_notifications(self.db.get_notifications(include_read=True))
            except Exception:
                pass