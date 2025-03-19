from shared_imports import *
from translator import Translator
from themes import set_theme, get_color, THEMES
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QFrame,
    QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton, QScrollArea,
    QSizePolicy, QMessageBox, QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIntValidator, QColor

# Constant for fixed label width
LABEL_WIDTH = 150

def fix_form_layout_labels(form_layout, width=LABEL_WIDTH):
    """Force every label in a QFormLayout to a constant width."""
    for i in range(form_layout.rowCount()):
        label_item = form_layout.itemAt(i, QFormLayout.LabelRole)
        if label_item and label_item.widget():
            label_item.widget().setFixedWidth(width)

class SettingsWidget(QWidget):
    def __init__(self, translator, on_save, gui, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.gui = gui
        self.on_save_callback = on_save

        # Theme mappings
        self.theme_names = ["classic", "dark", "light"]
        self.theme_display_names = ["Classic", "Dark", "Light"]

        self.setup_ui()
        self.load_initial_settings()
        self.apply_theme()
        self.initial_settings = self.get_current_settings()

    def setup_ui(self):
        # Main layout with uniform margins
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(15)

        # Main container frame for settings
        self.container_frame = QFrame(self)
        self.container_frame.setObjectName("settingsContainer")
        self.container_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.container_frame.setMinimumWidth(750)

        container_layout = QVBoxLayout(self.container_frame)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Header section
        self.header = QFrame()
        self.header.setObjectName("settingsHeader")
        self.header.setFixedHeight(60)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        self.settings_title = QLabel(self.translator.t('settings_page'))
        self.settings_title.setObjectName("settingsTitle")
        header_layout.addWidget(self.settings_title)
        container_layout.addWidget(self.header)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setObjectName("headerDivider")
        container_layout.addWidget(divider)

        # Scrollable content area
        content_container = QWidget()
        content_container.setObjectName("contentContainer")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("settingsScroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content = QWidget()
        content.setObjectName("scrollContent")
        scroll_layout = QVBoxLayout(content)
        scroll_layout.setContentsMargins(10, 10, 25, 10)  # Extra right margin for scrollbar
        scroll_layout.setSpacing(20)

        # Create groups using helper functions
        self.language_group = self._create_language_group(content)
        self.appearance_group = self._create_appearance_group(content)
        self.technical_group = self._create_technical_group(content)
        self.inventory_group = self._create_inventory_group(content)

        scroll_layout.addWidget(self.language_group)
        scroll_layout.addWidget(self.appearance_group)
        scroll_layout.addWidget(self.technical_group)
        scroll_layout.addWidget(self.inventory_group)
        scroll_layout.addStretch()

        content.setLayout(scroll_layout)
        self.scroll_area.setWidget(content)
        content_layout.addWidget(self.scroll_area)
        container_layout.addWidget(content_container, 1)

        # Button panel at bottom
        button_panel = QWidget()
        button_panel.setObjectName("buttonPanel")
        button_panel.setFixedHeight(70)
        btn_layout = QHBoxLayout(button_panel)
        btn_layout.setContentsMargins(20, 10, 20, 10)
        btn_layout.setSpacing(20)

        self.save_btn = QPushButton(self.translator.t('save'))
        self.cancel_btn = QPushButton(self.translator.t('cancel'))
        self.save_btn.setFixedSize(150, 45)
        self.cancel_btn.setFixedSize(150, 45)
        self.save_btn.setObjectName("saveButton")
        self.cancel_btn.setObjectName("cancelButton")

        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn.clicked.connect(self.cancel_changes)

        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        container_layout.addWidget(button_panel)

        main_layout.addWidget(self.container_frame)

    def _create_language_group(self, parent):
        group = QGroupBox(self.translator.t('language_settings'), parent)
        layout = QFormLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.setFormAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        self.interface_lang_label = QLabel(self.translator.t('interface_language'))
        self.language_combo = QComboBox()
        self.language_combo.addItem(self.translator.t('english'), "en")
        self.language_combo.addItem(self.translator.t('hebrew'), "he")
        layout.addRow(self.interface_lang_label, self.language_combo)
        fix_form_layout_labels(layout)
        group.setLayout(layout)
        return group

    def _create_appearance_group(self, parent):
        group = QGroupBox(self.translator.t('appearance'), parent)
        layout = QFormLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.setFormAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.color_theme_label = QLabel(self.translator.t('color_theme'))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.theme_display_names)
        layout.addRow(self.color_theme_label, self.theme_combo)
        fix_form_layout_labels(layout)
        group.setLayout(layout)
        return group

    def _create_technical_group(self, parent):
        group = QGroupBox(self.translator.t('technical_settings'), parent)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(10)

        # Auto-backup sub-group
        db_group = QGroupBox(self.translator.t('auto_backup'))
        db_layout = QFormLayout()
        db_layout.setContentsMargins(8, 8, 8, 8)
        db_layout.setSpacing(10)
        self.db_backup_interval = QComboBox()
        self.db_backup_interval.addItems([
            self.translator.t('daily'),
            self.translator.t('weekly'),
            self.translator.t('monthly')
        ])
        db_layout.addRow(QLabel(self.translator.t('auto_backup')), self.db_backup_interval)
        fix_form_layout_labels(db_layout)
        db_group.setLayout(db_layout)

        # Measurement units sub-group
        units_group = QGroupBox(self.translator.t('measurement_units'))
        units_layout = QFormLayout()
        units_layout.setContentsMargins(8, 8, 8, 8)
        units_layout.setSpacing(10)
        self.units_combo = QComboBox()
        self.units_combo.addItems([
            self.translator.t('metric_system'),
            self.translator.t('imperial_system')
        ])
        units_layout.addRow(QLabel(self.translator.t('measurement_units')), self.units_combo)
        fix_form_layout_labels(units_layout)
        units_group.setLayout(units_layout)

        # Invoice template button in its own layout for proper alignment
        self.invoice_template_btn = QPushButton(self.translator.t('select_invoice_template'))
        self.invoice_template_btn.setFixedHeight(40)
        self.invoice_template_btn.clicked.connect(lambda: print("Invoice template selection dialog (placeholder)"))
        invoice_layout = QHBoxLayout()
        invoice_layout.setContentsMargins(8, 8, 8, 8)
        invoice_layout.setSpacing(10)
        invoice_layout.addWidget(self.invoice_template_btn)
        invoice_layout.addStretch()

        main_layout.addWidget(db_group)
        main_layout.addWidget(units_group)
        main_layout.addLayout(invoice_layout)
        main_layout.addStretch()
        group.setLayout(main_layout)
        return group

    def _create_inventory_group(self, parent):
        group = QGroupBox(self.translator.t('inventory_settings'), parent)
        layout = QFormLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.setFormAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        # Low stock threshold row
        self.low_stock_threshold_label = QLabel(self.translator.t('low_stock_threshold'))
        self.low_stock_threshold_input = QLineEdit()
        self.low_stock_threshold_input.setValidator(QIntValidator(0, 10000, self))
        layout.addRow(self.low_stock_threshold_label, self.low_stock_threshold_input)

        # Default currency row
        self.default_currency_label = QLabel(self.translator.t('default_currency'))
        self.default_currency_combo = QComboBox()
        currencies = [
            self.translator.t('usd'),
            self.translator.t('eur'),
            self.translator.t('gbp'),
            self.translator.t('ils')
        ]
        self.default_currency_combo.addItems(currencies)
        self.default_currency_combo.setMinimumWidth(200)
        layout.addRow(self.default_currency_label, self.default_currency_combo)

        # Auto-restock row
        self.auto_restock_label = QLabel(self.translator.t('enable_auto_restock'))
        self.auto_restock_checkbox = QCheckBox()
        self.auto_restock_checkbox.setChecked(True)
        layout.addRow(self.auto_restock_label, self.auto_restock_checkbox)

        fix_form_layout_labels(layout)
        group.setLayout(layout)
        return group

    def get_current_settings(self):
        return {
            'theme': self.theme_names[self.theme_combo.currentIndex()],
            'language': self.language_combo.currentData(),
            'low_stock_threshold': self.low_stock_threshold_input.text().strip(),
            'default_currency': self.default_currency_combo.currentText().lower(),
            'auto_restock': self.auto_restock_checkbox.isChecked(),
            'backup_interval': self.db_backup_interval.currentIndex(),
            'measurement_units': self.units_combo.currentIndex()
        }

    def load_initial_settings(self):
        saved_theme = self.gui.settings_db.get_setting('theme', 'classic')
        try:
            theme_index = self.theme_names.index(saved_theme)
        except ValueError:
            theme_index = 0
        self.theme_combo.setCurrentIndex(theme_index)

        low_stock = self.gui.settings_db.get_setting('low_stock_threshold', '10')
        self.low_stock_threshold_input.setText(low_stock)
        is_rtl = self.gui.settings_db.get_setting('rtl', 'false') == 'true'
        self.language_combo.setCurrentIndex(1 if is_rtl else 0)
        self.initial_settings = self.get_current_settings()

    def save_settings(self):
        """Save settings with validation and error handling."""
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            low_stock = self.low_stock_threshold_input.text().strip()
            if not low_stock.isdigit() or int(low_stock) < 0:
                low_stock = "10"
                self.low_stock_threshold_input.setText(low_stock)

            settings = {
                'theme': self.theme_names[self.theme_combo.currentIndex()],
                'language': self.language_combo.currentData(),
                'low_stock_threshold': low_stock,
                'default_currency': self.default_currency_combo.currentText().lower(),
                'auto_restock': str(self.auto_restock_checkbox.isChecked()),
                'backup_interval': str(self.db_backup_interval.currentIndex()),
                'measurement_units': str(self.units_combo.currentIndex())
            }

            for key, value in settings.items():
                self.gui.settings_db.save_setting(key, value)

            self.initial_settings = self.get_current_settings()

            try:
                if settings['language'] != self.translator.language:
                    self.on_save_callback(settings['language'])
            except Exception as lang_error:
                print(f"Error applying language change: {lang_error}")

            try:
                set_theme(settings['theme'])
                if hasattr(self.gui, 'apply_theme_to_all') and callable(self.gui.apply_theme_to_all):
                    self.gui.apply_theme_to_all()
                else:
                    self.apply_theme()
            except Exception as theme_error:
                print(f"Error applying theme change: {theme_error}")

            QMessageBox.information(
                self,
                self.translator.t('success'),
                self.translator.t('settings_saved'),
                buttons=QMessageBox.Ok
            )
        except Exception as e:
            print(f"Settings save error: {e}")
            QMessageBox.critical(
                self,
                self.translator.t('error'),
                f"{self.translator.t('settings_save_error')}\n{e}",
                buttons=QMessageBox.Ok
            )
        finally:
            QApplication.restoreOverrideCursor()

    def cancel_changes(self):
        """Revert settings and navigate back."""
        try:
            if hasattr(self.gui, 'content') and hasattr(self.gui.content, 'stack'):
                self.gui.content.stack.setCurrentIndex(0)
            elif hasattr(self.gui, 'content_stack'):
                self.gui.content_stack.setCurrentWidget(self.gui.home_page)
            self.load_initial_settings()
        except Exception as e:
            print(f"Cancel settings error: {e}")
            self.load_initial_settings()

    def _apply_theme_change(self, theme_name):
        try:
            set_theme(theme_name)
            if hasattr(self.gui, 'apply_theme_to_all') and callable(self.gui.apply_theme_to_all):
                self.gui.apply_theme_to_all()
            elif hasattr(self.gui, 'apply_theme') and callable(self.gui.apply_theme):
                self.gui.apply_theme()
            self.apply_theme()
        except Exception as e:
            print(f"Theme change error: {e}")

    def apply_theme(self):
        """Apply theme styling."""
        current_theme = self.theme_names[self.theme_combo.currentIndex()]
        text_color = get_color('text')
        primary_color = get_color('primary')
        border_color = get_color('border')
        button_color = get_color('button')
        success_color = get_color('success')

        base_style = f"""
            QWidget {{
                background-color: {primary_color};
                color: {text_color};
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }}
            #settingsContainer {{
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
            #settingsHeader {{
                background-color: {primary_color};
            }}
            #settingsTitle {{
                font-size: 20px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }}
            QGroupBox {{
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 20px;
            }}
            QGroupBox::title {{
                padding: 0 8px;
                font-weight: bold;
                font-size: 15px;
            }}
            QFormLayout {{
                margin: 8px;
                spacing: 10px;
            }}
            QLabel {{
                padding: 2px 0;
            }}
            QLineEdit, QComboBox, QSpinBox {{
                background-color: {get_color('input_bg')};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 8px 12px;
                min-height: 18px;
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
                border: 2px solid {success_color};
            }}
            QPushButton {{
                background-color: {button_color};
                border: none;
                border-radius: 20px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 14px;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background-color: {button_color};
                opacity: 0.8;
            }}
            QPushButton:pressed {{
                background-color: {success_color};
            }}
            QScrollBar:vertical {{
                background: {QColor(primary_color).lighter(110).name() if current_theme != "dark" else QColor(primary_color).darker(105).name()};
                width: 12px;
                margin: 2px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {QColor(button_color).lighter(120).name() if current_theme == "dark" else button_color};
                min-height: 30px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {get_color('button_hover')};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: {QColor(primary_color).lighter(110).name() if current_theme == "dark" else QColor(primary_color).darker(105).name()};
                border-radius: 6px;
            }}
        """
        self.setStyleSheet(base_style)

    def _apply_layout_direction(self):
        new_direction = Qt.RightToLeft if self.translator.language == 'he' else Qt.LeftToRight
        self.setLayoutDirection(new_direction)
        self.header.setLayoutDirection(new_direction)

        # Remove the old title widget from header layout
        header_layout = self.header.layout()
        while header_layout.count():
            item = header_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Create a new title widget with the updated text and alignment
        self.settings_title = QLabel(self.translator.t('settings_page'))
        self.settings_title.setObjectName("settingsTitle")
        if new_direction == Qt.RightToLeft:
            self.settings_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.settings_title.setContentsMargins(0, 0, 10, 0)
        else:
            self.settings_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.settings_title.setContentsMargins(10, 0, 0, 0)

        # Re-add the title widget with a stretch to position it correctly
        if new_direction == Qt.RightToLeft:
            header_layout.addStretch()
            header_layout.addWidget(self.settings_title)
        else:
            header_layout.addWidget(self.settings_title)
            header_layout.addStretch()

        header_layout.update()
        self.header.update()

    def update_header_title_direction(self):
        # Get the container layout that holds the header
        container_layout = self.container_frame.layout()

        # Remove the existing header widget from the container layout and delete it.
        container_layout.removeWidget(self.header)
        self.header.deleteLater()

        # Create a new header frame and layout.
        self.header = QFrame()
        self.header.setObjectName("settingsHeader")
        self.header.setFixedHeight(60)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        # Determine new direction.
        new_direction = Qt.RightToLeft if self.translator.language == 'he' else Qt.LeftToRight
        self.header.setLayoutDirection(new_direction)

        # Create a new title widget with updated text.
        self.settings_title = QLabel(self.translator.t('settings_page'))
        self.settings_title.setObjectName("settingsTitle")

        # Set alignment and margins based on new direction.
        if new_direction == Qt.RightToLeft:
            self.settings_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.settings_title.setContentsMargins(0, 0, 10, 0)
            header_layout.addStretch()  # Stretch before title pushes it to the right.
            header_layout.addWidget(self.settings_title)
        else:
            self.settings_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.settings_title.setContentsMargins(10, 0, 0, 0)
            header_layout.addWidget(self.settings_title)
            header_layout.addStretch()  # Stretch after title keeps it left.

        # Re-insert the header into the container layout at the top.
        container_layout.insertWidget(0, self.header)

        # Force a refresh.
        self.header.updateGeometry()
        self.header.update()

    def refresh_scrollbar(self):
        if hasattr(self, 'scroll_area') and self.scroll_area:
            self.scroll_area.widget().updateGeometry()
            self.scroll_area.updateGeometry()
            self.scroll_area.verticalScrollBar().setValue(0)
            current_theme = self.theme_names[self.theme_combo.currentIndex()]
            is_dark = current_theme == "dark"
            primary_color = get_color('primary')
            button_color = get_color('button')
            button_hover = get_color('button_hover')
            scrollbar_style = f"""
                QScrollBar:vertical {{
                    background: transparent;
                    width: 14px;
                    margin: 2px;
                    border-radius: 7px;
                }}
                QScrollBar::handle:vertical {{
                    background: {QColor(button_color).lighter(120).name() if is_dark else button_color};
                    min-height: 30px;
                    border-radius: 7px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background: {button_hover};
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    height: 0px;
                }}
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                    background: {QColor(primary_color).lighter(110).name() if is_dark else QColor(primary_color).darker(105).name()};
                    border-radius: 7px;
                }}
            """
            self.scroll_area.verticalScrollBar().setStyleSheet(scrollbar_style)
            content_widget = self.scroll_area.widget()
            if content_widget:
                content_widget.setMinimumHeight(self.scroll_area.height() + 50)

    def add_entrance_animation(self):
        opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(opacity_effect)
        opacity_effect.setOpacity(0)
        self.fade_animation = QPropertyAnimation(opacity_effect, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        QTimer.singleShot(100, self.fade_animation.start)

    def update_translations(self):
        # Update texts for language group.
        self.language_group.setTitle(self.translator.t('language_settings'))
        self.interface_lang_label.setText(self.translator.t('interface_language'))
        self.language_combo.setItemText(0, self.translator.t('english'))
        self.language_combo.setItemText(1, self.translator.t('hebrew'))

        # Update other groups.
        self.appearance_group.setTitle(self.translator.t('appearance'))
        self.color_theme_label.setText(self.translator.t('color_theme'))

        self.technical_group.setTitle(self.translator.t('technical_settings'))
        self.db_backup_interval.setItemText(0, self.translator.t('daily'))
        self.db_backup_interval.setItemText(1, self.translator.t('weekly'))
        self.db_backup_interval.setItemText(2, self.translator.t('monthly'))
        self.units_combo.setItemText(0, self.translator.t('metric_system'))
        self.units_combo.setItemText(1, self.translator.t('imperial_system'))
        self.invoice_template_btn.setText(self.translator.t('select_invoice_template'))

        self.inventory_group.setTitle(self.translator.t('inventory_settings'))
        self.low_stock_threshold_label.setText(self.translator.t('low_stock_threshold'))
        self.default_currency_label.setText(self.translator.t('default_currency'))
        self.auto_restock_label.setText(self.translator.t('enable_auto_restock'))

        self.save_btn.setText(self.translator.t('save'))
        self.cancel_btn.setText(self.translator.t('cancel'))

        # Determine the new layout direction.
        new_direction = Qt.RightToLeft if self.translator.language == 'he' else Qt.LeftToRight
        self.setLayoutDirection(new_direction)
        for child in self.findChildren(QWidget):
            child.setLayoutDirection(new_direction)

        self.updateGeometry()
        self._update_labels()
        self._update_combo_boxes()
        self._apply_layout_direction()
        self.apply_theme()  # Reapply theme

        # Finally, re-create the header so its title picks up the new direction.
        self.update_header_title_direction()

    def _update_labels(self):
        """Update group titles and individual labels."""
        self.language_group.setTitle(self.translator.t('language_settings'))
        self.appearance_group.setTitle(self.translator.t('appearance'))
        self.technical_group.setTitle(self.translator.t('technical_settings'))
        self.inventory_group.setTitle(self.translator.t('inventory_settings'))

        self.interface_lang_label.setText(self.translator.t('interface_language'))
        self.color_theme_label.setText(self.translator.t('color_theme'))
        self.low_stock_threshold_label.setText(self.translator.t('low_stock_threshold'))
        self.default_currency_label.setText(self.translator.t('default_currency'))
        self.auto_restock_label.setText(self.translator.t('enable_auto_restock'))
        self.invoice_template_btn.setText(self.translator.t('select_invoice_template'))
        self.save_btn.setText(self.translator.t('save'))
        self.cancel_btn.setText(self.translator.t('cancel'))

    def _update_combo_boxes(self):
        """Update texts of combo boxes if necessary."""
        self.language_combo.setItemText(0, self.translator.t('english'))
        self.language_combo.setItemText(1, self.translator.t('hebrew'))
        self.db_backup_interval.setItemText(0, self.translator.t('daily'))
        self.db_backup_interval.setItemText(1, self.translator.t('weekly'))
        self.db_backup_interval.setItemText(2, self.translator.t('monthly'))
        self.units_combo.setItemText(0, self.translator.t('metric_system'))
        self.units_combo.setItemText(1, self.translator.t('imperial_system'))
