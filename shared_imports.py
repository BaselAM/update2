
from pathlib import Path
from database.car_parts_db import CarPartsDB
from database.settings_db import SettingsDB
# --- Qt Imports ---
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSlot, \
    QMetaObject, Q_ARG, QThread, pyqtSignal, QStringListModel, QSize,QRect
from PyQt5.QtGui import QPixmap, QPainter, QIcon, QColor, QIntValidator, QDoubleValidator, \
    QPalette, QFont
from PyQt5.QtWidgets import (
    QApplication, QWidget, QDesktopWidget, QLabel, QHBoxLayout, QVBoxLayout,
    QStackedLayout, QGraphicsOpacityEffect, QTableWidget, QHeaderView, QTableWidgetItem,
    QLineEdit, QPushButton, QScrollArea, QFormLayout, QComboBox, QColorDialog,
    QGroupBox, QAction, QGridLayout,  QListWidget, QStyledItemDelegate,
    QMessageBox, QDialog, QDialogButtonBox, QCompleter,QAbstractItemView,QCheckBox,QSizePolicy,QFrame,QSpinBox,QDoubleSpinBox,QTextEdit,QBoxLayout
)
from datetime import datetime
import time


from pathlib import Path

from datetime import datetime
# Define SCRIPT_DIR as the directory where this file resides.
SCRIPT_DIR = Path(__file__).resolve().parent

from database.car_parts_db import CarPartsDB


from database.settings_db import SettingsDB

from translator import *