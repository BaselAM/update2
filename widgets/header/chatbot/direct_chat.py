"""
Chat widget with resilient design that works with or without API access.
Includes car parts knowledge base for domain-specific information.
"""

from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPoint, QTimer, QObject
from PyQt5.QtWidgets import (
    QWidget, QToolButton, QVBoxLayout,
    QLineEdit, QPushButton, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QApplication, QMessageBox,
    QGraphicsDropShadowEffect, QDialog, QFormLayout,
    QComboBox, QCheckBox
)
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor
from pathlib import Path
import themes
import threading
import time
import random
import re
import os
import json
import base64
from cryptography.fernet import Fernet
import hashlib

# Import OpenAI package
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Add debug logging
def debug_log(message):
    """Log debug messages to console"""
    print(f"[CHAT DEBUG] {message}")

def is_dark_theme():
    """Determine if the current theme is dark based on background color"""
    try:
        bg_color = themes.get_color('card_bg')
        bg_color = bg_color.lstrip('#')
        r, g, b = tuple(int(bg_color[i:i + 2], 16) for i in (0, 2, 4))
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return brightness < 128
    except Exception as e:
        debug_log(f"Error determining theme: {e}")
        return False

# Signal bridge for thread safety
class SignalBridge(QObject):
    update_signal = pyqtSignal(str, bool)
    remove_thinking_signal = pyqtSignal()
    api_error_signal = pyqtSignal(str, str)  # Error message, error type

class ApiKeyManager:
    """Manages secure storage and retrieval of API keys"""

    def __init__(self):
        """Initialize the key manager"""
        # Create directory for storing API key if it doesn't exist
        self.config_dir = Path.home() / ".app_config"
        self.config_dir.mkdir(exist_ok=True)
        self.key_file = self.config_dir / "api_key.dat"

        # Generate encryption key based on machine-specific information
        machine_id = self._get_machine_id()
        self.encryption_key = base64.urlsafe_b64encode(hashlib.sha256(machine_id.encode()).digest())
        self.cipher = Fernet(self.encryption_key)

    def _get_machine_id(self):
        """Get a unique machine identifier for encryption"""
        # Try to get machine-specific identifiers
        try:
            if os.name == 'nt':  # Windows
                import winreg
                reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
                key = winreg.OpenKey(reg, r"SOFTWARE\Microsoft\Cryptography")
                machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
                return machine_guid
            else:  # Linux/Mac
                with open('/etc/machine-id', 'r') as f:
                    return f.read().strip()
        except:
            # Fallback to username + hostname if we can't get a system ID
            return f"{os.getlogin()}-{os.uname().nodename}"

    def save_api_key(self, api_key):
        """Encrypt and save the API key"""
        try:
            # Encrypt the API key
            encrypted_key = self.cipher.encrypt(api_key.encode())

            # Save to file
            with open(self.key_file, 'wb') as f:
                f.write(encrypted_key)

            debug_log("API key saved successfully")
            return True
        except Exception as e:
            debug_log(f"Error saving API key: {e}")
            return False

    def load_api_key(self):
        """Load and decrypt the API key"""
        try:
            if not self.key_file.exists():
                debug_log("No API key file found")
                return None

            # Read encrypted key
            with open(self.key_file, 'rb') as f:
                encrypted_key = f.read()

            # Decrypt and return
            api_key = self.cipher.decrypt(encrypted_key).decode()
            debug_log("API key loaded successfully")
            return api_key
        except Exception as e:
            debug_log(f"Error loading API key: {e}")
            return None

    def delete_api_key(self):
        """Delete the stored API key"""
        try:
            if self.key_file.exists():
                self.key_file.unlink()
                debug_log("API key deleted")
                return True
            return False
        except Exception as e:
            debug_log(f"Error deleting API key: {e}")
            return False

class CarPartsKnowledgeBase:
    """Domain-specific knowledge base for car parts information"""

    def __init__(self):
        """Initialize with car parts information"""
        self.parts_info = {
            "engine": {
                "description": "The power unit of a vehicle that converts fuel into motion through combustion.",
                "common_issues": "Overheating, oil leaks, timing belt failures, misfiring, rough idling.",
                "maintenance": "Regular oil changes, timing belt replacement, air filter changes, cooling system checks."
            },
            "transmission": {
                "description": "Transfers power from the engine to the wheels with different gear ratios.",
                "common_issues": "Fluid leaks, gear slipping, hard shifting, delayed engagement, unusual noises.",
                "maintenance": "Fluid changes, filter replacement, checking for leaks, clutch adjustment (manual)."
            },
            "brakes": {
                "description": "System that slows or stops the vehicle using friction against rotating wheels.",
                "common_issues": "Squeaking/grinding noises, soft pedal feel, vibration when braking, longer stopping distance.",
                "maintenance": "Pad replacement, rotor resurfacing or replacement, fluid flush, caliper maintenance."
            },
            "suspension": {
                "description": "System of springs, shock absorbers and linkages connecting a vehicle to its wheels.",
                "common_issues": "Rough ride, uneven tire wear, vehicle pulling to one side, knocking noises, excessive bouncing.",
                "maintenance": "Shock/strut replacement, alignment checks, bushing inspection, spring assessment."
            },
            "alternator": {
                "description": "Generates electrical power to charge the battery and power electrical systems while the engine runs.",
                "common_issues": "Battery warning light, dim headlights, electrical failures, strange noises, battery not charging.",
                "maintenance": "Belt inspection, terminal cleaning, voltage output testing."
            },
            "battery": {
                "description": "Provides electrical current for starting the engine and powering electrical components when the engine is off.",
                "common_issues": "Difficulty starting, electrical component failures, corrosion on terminals, short battery life.",
                "maintenance": "Terminal cleaning, water level checks (non-sealed types), load testing, replacement every 3-5 years."
            },
            "radiator": {
                "description": "Heat exchanger that prevents the engine from overheating by cooling the circulating coolant.",
                "common_issues": "Leaks, overheating, clogged passages, damaged fins, corrosion.",
                "maintenance": "Coolant flush/replacement, pressure testing, cleaning exterior fins, checking for leaks."
            },
            "starter": {
                "description": "Electric motor that initiates engine operation by turning the flywheel.",
                "common_issues": "Clicking sound without engine turnover, intermittent starting problems, grinding noises.",
                "maintenance": "Connection checking, testing current draw, replacement when worn."
            },
            "fuel pump": {
                "description": "Delivers fuel from the tank to the engine under pressure.",
                "common_issues": "Engine sputtering at high speeds, loss of power during acceleration, engine not starting, whining noise.",
                "maintenance": "Fuel filter replacement, keeping fuel level above 1/4 tank, pressure testing."
            },
            "spark plugs": {
                "description": "Create electric spark to ignite the air-fuel mixture in the engine's combustion chamber.",
                "common_issues": "Misfiring, rough idling, trouble starting, increased fuel consumption, lack of acceleration.",
                "maintenance": "Regular replacement (30,000-100,000 miles depending on type), proper gap adjustment, torque to spec."
            },
            "oil": {
                "description": "Lubricates engine components to reduce friction and wear while helping cool the engine.",
                "common_issues": "Low level, contamination, incorrect viscosity, sludge buildup, leaks.",
                "maintenance": "Regular changes (every 3,000-10,000 miles depending on type), level checks, filter replacement."
            },
            "timing belt": {
                "description": "Synchronizes the rotation of the crankshaft and camshaft to ensure proper engine valve operation.",
                "common_issues": "Cracking, fraying, breaking (catastrophic engine damage in interference engines), noise.",
                "maintenance": "Replacement every 60,000-100,000 miles (as specified by manufacturer), tension checking."
            },
            "air filter": {
                "description": "Prevents dust, dirt and debris from entering the engine while allowing sufficient airflow.",
                "common_issues": "Clogging, reduced engine performance, increased fuel consumption, strange engine sounds.",
                "maintenance": "Regular inspection and replacement (every 15,000-30,000 miles), cleaning (if reusable type)."
            },
            "power steering": {
                "description": "System that assists driver in steering the vehicle by using hydraulic or electric pressure.",
                "common_issues": "Fluid leaks, whining noise, difficulty steering, steering wheel jerking, fluid contamination.",
                "maintenance": "Fluid level checks, fluid replacement, belt inspection, system flushing."
            },
            "exhaust": {
                "description": "System that guides exhaust gases away from the engine and reduces noise and pollution.",
                "common_issues": "Loud noise, exhaust leaks, rust/corrosion, reduced fuel efficiency, hanging pipes.",
                "maintenance": "Regular inspection, rust treatment, hanger replacement, catalytic converter checking."
            },
            "tires": {
                "description": "Rubber components that provide traction, absorb shock, and support the vehicle's weight.",
                "common_issues": "Uneven wear, low pressure, sidewall damage, excessive noise, vibration while driving.",
                "maintenance": "Regular rotation, pressure checks, alignment, balance, replacement when tread is worn."
            },
            "injectors": {
                "description": "Electronically controlled valves that spray fuel into the engine's intake manifold or combustion chamber.",
                "common_issues": "Clogging, leaking, improper spray pattern, engine misfires, rough idle, poor performance.",
                "maintenance": "Fuel system cleaning, occasional professional cleaning, keeping fuel filter changed."
            },
            "מנוע": {  # Engine in Hebrew
                "description": "יחידת הכוח של הרכב, הממירה דלק לתנועה באמצעות בעירה.",
                "common_issues": "התחממות יתר, דליפות שמן, כשלי רצועת תזמון, החטאות, סרק גס.",
                "maintenance": "החלפות שמן סדירות, החלפת רצועת תזמון, החלפות מסנן אוויר, בדיקות מערכת קירור."
            },
            "בלמים": {  # Brakes in Hebrew
                "description": "מערכת המאטה או עוצרת את הרכב באמצעות חיכוך נגד גלגלים מסתובבים.",
                "common_issues": "רעשי חריקה/שיוף, תחושת דוושה רכה, רעידות בזמן בלימה, מרחק עצירה ארוך יותר.",
                "maintenance": "החלפת רפידות, השחזת דיסקיות או החלפתן, שטיפת נוזל, תחזוקת קליפרים."
            }
        }

    def search(self, query):
        """Search for information about a car part"""
        query = query.lower()

        # Exact match
        if query in self.parts_info:
            part = self.parts_info[query]
            return f"{query.title()}: {part['description']}\n\nCommon issues: {part['common_issues']}\n\nMaintenance: {part['maintenance']}"

        # Partial match
        for part_name, info in self.parts_info.items():
            if part_name in query or query in part_name:
                return f"{part_name.title()}: {info['description']}\n\nCommon issues: {info['common_issues']}\n\nMaintenance: {info['maintenance']}"

        # No match
        return None

    def is_car_parts_query(self, query):
        """Check if the query is related to car parts"""
        query = query.lower()

        # Check if any car part is mentioned
        for part_name in self.parts_info:
            if part_name in query:
                return True

        # Check for general car terms
        car_terms = ['car', 'vehicle', 'auto', 'automobile', 'part', 'repair', 'fix', 'issue',
                    'problem', 'maintenance', 'service', 'רכב', 'מכונית', 'חלק', 'תיקון', 'בעיה']

        for term in car_terms:
            if term in query:
                return True

        return False

class LocalChatResponder:
    """Provides local fallback responses without requiring API access"""

    def __init__(self, username="User", car_knowledge=None):
        """Initialize with username for personalized responses"""
        self.username = username
        self.car_knowledge = car_knowledge or CarPartsKnowledgeBase()
        self.initialize_responses()

    def initialize_responses(self):
        """Set up response patterns"""
        # Response patterns with multiple options
        self.response_patterns = {
            r'hello|hi|hey': [
                f"Hello {self.username}! How can I help you today?",
                f"Hi {self.username}! I'm your assistant. What do you need help with?",
                "Hello there! How may I help you today?"
            ],
            r'how are you': [
                "I'm doing well, thanks for asking! How can I help you?",
                "I'm functioning perfectly. What can I assist you with today?",
                "All systems operational! How can I be of service?"
            ],
            r'your name|who are you': [
                "I'm your built-in AI assistant, designed to help with your queries.",
                "I'm an AI assistant integrated into this application to provide help and information.",
                "I'm your virtual assistant, ready to answer questions and provide assistance."
            ],
            r'thanks|thank you': [
                "You're welcome! Feel free to ask if you need anything else.",
                "Happy to help! Let me know if you need more assistance.",
                "Anytime! That's what I'm here for."
            ],
            r'bye|goodbye': [
                "Goodbye! Feel free to chat again when you need assistance.",
                "Until next time! I'll be here if you need help.",
                "Bye! You can reopen this chat whenever you need me."
            ],
            r'help|assist': [
                "I can help with questions about car parts and vehicle maintenance. Just ask!",
                "Need assistance? I'm here to help you with car-related questions.",
                "How can I assist you today? I'm knowledgeable about cars and their components."
            ],
            # Car-specific patterns
            r'engine|motor': [
                "The engine is the power unit of a vehicle, converting fuel into motion through combustion.",
                "Car engines can be classified as inline, V-type, or flat configurations based on cylinder arrangement.",
                "Modern engines feature electronic fuel injection, variable valve timing, and turbocharging for efficiency."
            ],
            r'brake|brakes': [
                "Brakes are crucial safety components that slow or stop the vehicle using friction.",
                "Most cars use disc brakes in front and either disc or drum brakes in the rear.",
                "The brake system includes pads, rotors, calipers, lines, and the master cylinder."
            ],
            r'transmission|gearbox': [
                "The transmission transfers power from the engine to the wheels while allowing gear ratio changes.",
                "Common types include manual, automatic, CVT (Continuously Variable Transmission), and dual-clutch.",
                "Transmission problems often manifest as delayed shifting, strange noises, or fluid leaks."
            ],
            r'suspension|shock': [
                "The suspension system provides a smooth ride by absorbing road imperfections.",
                "Key components include springs, shock absorbers, struts, control arms, and sway bars.",
                "Signs of suspension issues include excessive bouncing, uneven tire wear, and pulling to one side."
            ],
            r'battery|electrical': [
                "The car battery provides power for starting and for electrical systems when the engine is off.",
                "Most modern vehicles use 12-volt lead-acid batteries, though some hybrids use different types.",
                "Battery issues often appear as slow starting, dimming lights, or electrical system failures."
            ],
            r'oil|lubrication': [
                "Engine oil lubricates moving parts, reduces friction, helps with cooling, and prevents corrosion.",
                "It's important to change your oil and filter regularly according to the manufacturer's schedule.",
                "Low oil pressure or contaminated oil can cause serious engine damage and reduced performance."
            ],
            r'tire|wheel': [
                "Tires are your only contact with the road and affect handling, braking, and fuel economy.",
                "Regular rotation, proper inflation, and alignment checks extend tire life and improve safety.",
                "Tire pressure should be checked monthly, and tires should be replaced when tread depth is low."
            ],
            r'fuel|gas|petrol|diesel': [
                "The fuel system delivers the right amount of fuel to the engine for combustion.",
                "Components include the tank, pump, filter, injectors or carburetor, and fuel lines.",
                "Using the recommended fuel grade for your vehicle helps maintain performance and efficiency."
            ],
            r'cooling|radiator|overheat': [
                "The cooling system prevents engine overheating by circulating coolant and releasing heat.",
                "Key components include the radiator, water pump, thermostat, hoses, and cooling fans.",
                "Overheating can cause serious engine damage and should be addressed immediately."
            ],
            # Hebrew patterns
            r'שלום|היי': [
                f"שלום {self.username}! במה אוכל לעזור לך היום?",
                f"היי {self.username}! אני העוזר הדיגיטלי שלך. איך אוכל לסייע?",
                "שלום! במה אוכל לעזור?"
            ],
            r'תודה': [
                "בשמחה! אם תצטרך עוד עזרה, אני כאן.",
                "בכיף! אשמח לעזור בכל דבר נוסף.",
                "תמיד לשירותך!"
            ],
            r'להתראות|ביי': [
                "להתראות! אשמח לעזור שוב בפעם הבאה.",
                "ביי! אני כאן אם תצטרך עוד משהו.",
                "להתראות! תוכל לפתוח את הצ'אט בכל פעם שתרצה."
            ],
            r'מנוע': [
                "המנוע הוא יחידת הכוח של הרכב שממירה דלק לתנועה באמצעות בעירה.",
                "מנועי רכב יכולים להיות מסווגים כתצורת שורה, V או שטוחה על פי סידור הצילינדרים.",
                "מנועים מודרניים כוללים הזרקת דלק אלקטרונית, תזמון שסתומים משתנה וטורבו ליעילות."
            ],
            r'בלמים': [
                "הבלמים הם רכיבי בטיחות קריטיים שמאטים או עוצרים את הרכב באמצעות חיכוך.",
                "רוב המכוניות משתמשות בבלמי דיסק בחזית ובלמי דיסק או תוף מאחור.",
                "מערכת הבלימה כוללת רפידות, דיסקיות, קליפרים, צינורות ובוכנת בלם ראשית."
            ]
        }

        # Default responses for when no pattern matches
        self.default_responses = [
            f"I'm here to help with car-related questions. What would you like to know about your vehicle?",
            "I can provide information about car parts and maintenance. How can I assist you?",
            "I'm specialized in automotive information. What car component are you interested in learning about?",
            "I'm ready to help with your vehicle questions. What would you like to know about car parts or maintenance?"
        ]

        # Hebrew default responses
        self.hebrew_default_responses = [
            f"אני כאן כדי לעזור עם שאלות הקשורות לרכב. מה תרצה לדעת על הרכב שלך?",
            "אני יכול לספק מידע על חלקי רכב ותחזוקה. כיצד אוכל לסייע לך?",
            "אני מתמחה במידע על רכב. באיזה רכיב ברכב אתה מעוניין ללמוד עליו?",
            "אני מוכן לעזור עם שאלות הרכב שלך. מה תרצה לדעת על חלקי רכב או תחזוקה?"
        ]

    def is_hebrew(self, text):
        """Detect if text contains Hebrew characters"""
        hebrew_pattern = re.compile(r'[\u0590-\u05FF\u05D0-\u05EA\u05F0-\u05F4]+')
        return bool(hebrew_pattern.search(text))

    def get_response(self, message):
        """Generate a response based on the message content"""
        # First, check the car parts knowledge base
        if self.car_knowledge.is_car_parts_query(message):
            car_info = self.car_knowledge.search(message)
            if car_info:
                return car_info

        # Check if message is in Hebrew
        is_heb = self.is_hebrew(message)
        message_lower = message.lower()

        # Check patterns for matches
        for pattern, responses in self.response_patterns.items():
            if re.search(pattern, message_lower):
                return random.choice(responses)

        # If no pattern matches, use default responses
        if is_heb:
            return random.choice(self.hebrew_default_responses)
        else:
            return random.choice(self.default_responses)

class OpenAIChat:
    """Simple wrapper for OpenAI chat API with fallback capability"""

    def __init__(self, api_key=None):
        """Initialize with optional API key"""
        self.api_key = api_key
        self.client = None
        self.car_knowledge = CarPartsKnowledgeBase()
        self.fallback = LocalChatResponder(car_knowledge=self.car_knowledge)
        self.use_fallback_mode = not OPENAI_AVAILABLE
        self.messages = [
            {"role": "system", "content": "You are a helpful assistant specialized in providing information about car parts and vehicle maintenance. Provide concise, informative responses. You should respond in multiple languages including Hebrew. Match your response language to the user's language."}
        ]

        if api_key and OPENAI_AVAILABLE:
            self.setup_client(api_key)

    def setup_client(self, api_key):
        """Set up the OpenAI client with the given API key"""
        if not OPENAI_AVAILABLE:
            self.use_fallback_mode = True
            return

        self.api_key = api_key
        if api_key:
            try:
                self.client = openai.OpenAI(api_key=api_key)
                self.use_fallback_mode = False
                debug_log("OpenAI client initialized")
            except Exception as e:
                debug_log(f"Error initializing OpenAI client: {e}")
                self.use_fallback_mode = True
        else:
            self.client = None
            self.use_fallback_mode = True

    def get_response(self, message):
        """Get a response from OpenAI API or fallback to local responses if needed"""
        # First, check if it's a specific car parts query
        if self.car_knowledge.is_car_parts_query(message):
            car_info = self.car_knowledge.search(message)
            if car_info:
                debug_log("Found car parts information in knowledge base")
                return car_info

        # Check if we should use fallback mode
        if self.use_fallback_mode or not OPENAI_AVAILABLE or not self.client or not self.api_key:
            debug_log("Using local response generator")
            return self.fallback.get_response(message)

        # Add user message to history
        self.messages.append({"role": "user", "content": message})

        # Trim conversation history if it gets too long (keep last 5 messages plus system prompt)
        if len(self.messages) > 6:
            self.messages = [self.messages[0]] + self.messages[-5:]

        try:
            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Can be changed to "gpt-4" for better results
                messages=self.messages,
                temperature=0.7,
                max_tokens=150
            )

            # Extract and store the response
            ai_response = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": ai_response})

            return ai_response

        except Exception as e:
            debug_log(f"OpenAI API error: {e}")

            # Check for quota exceeded errors and permanently switch to fallback mode
            error_str = str(e)
            if 'quota' in error_str.lower() or 'rate limit' in error_str.lower() or 'capacity' in error_str.lower():
                self.use_fallback_mode = True
                debug_log("Permanently switching to fallback mode due to API limits")

            # Use fallback for this response
            return self.fallback.get_response(message)


"""
Settings dialog for chat configuration with proper theme integration
"""

"""
Enhanced chat settings dialog with proper theming and elegant design
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QCheckBox,
    QPushButton, QWidget, QSpacerItem, QSizePolicy,
    QGroupBox, QRadioButton, QButtonGroup
)
from PyQt5.QtGui import QIcon, QPixmap, QFont
import themes

"""
Elegant, compact chat settings dialog with refined styling
"""
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QWidget,
    QGroupBox, QRadioButton, QButtonGroup
)
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor, QPainterPath, QPainter
import themes


class ElegantGroupBox(QGroupBox):
    """Custom GroupBox with more elegant appearance"""

    def __init__(self, title, parent=None):
        super().__init__(title, parent)

    def paintEvent(self, event):
        # Custom painting for more elegant group box
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Get colors from theme
        border_color = QColor(themes.get_color('border'))
        bg_color = QColor(themes.get_color('card_bg'))
        title_color = QColor(themes.get_color('text'))

        # Create path for rounded rectangle
        path = QPainterPath()
        rect = self.rect().adjusted(1, 1, -1, -1)
        path.addRoundedRect(rect, 6, 6)

        # Fill background
        painter.fillPath(path, bg_color)

        # Draw border
        painter.setPen(border_color)
        painter.drawPath(path)

        # Draw title
        if self.title():
            title_rect = self.style().subControlRect(
                self.style().CC_GroupBox,
                self.styleOptionFromStyle(self.style()),
                self.style().SC_GroupBoxLabel,
                self
            )

            # Create background for title
            title_bg = QRect(title_rect)
            title_bg.adjust(-5, 0, 5, 0)

            painter.fillRect(title_bg, bg_color)

            # Draw title text
            painter.setPen(title_color)
            painter.drawText(title_rect, Qt.AlignCenter, self.title())

        # Don't call super as we're doing custom painting

    def styleOptionFromStyle(self, style):
        from PyQt5.QtWidgets import QStyleOptionGroupBox
        option = QStyleOptionGroupBox()
        option.initFrom(self)
        option.text = self.title()
        return option


class ChatSettingsDialog(QDialog):
    """Dialog for configuring chat settings with elegant design"""

    def __init__(self, parent=None, current_key=None, api_issue=False):
        super().__init__(parent)

        # Initialize variables
        self.api_key = current_key
        self.api_issue = api_issue
        self.use_fallback_mode = False

        # Set up dialog properties
        self.setWindowTitle("Chat Settings")
        self.setMinimumWidth(400)  # Smaller, more compact
        self.setFixedHeight(400)  # Fixed height for compactness
        self.setModal(True)

        # Apply custom styling
        self.apply_elegant_styling()

        # Center on parent window
        self.center_on_parent()

        # Create layout
        self.setup_ui()

    def center_on_parent(self):
        """Center the dialog on the parent window"""
        if self.parent():
            parent_geometry = self.parent().window().frameGeometry()
            center_point = parent_geometry.center()

            # Calculate position to center this dialog on the parent
            frame_geometry = self.frameGeometry()
            frame_geometry.moveCenter(center_point)
            self.move(frame_geometry.topLeft())

    def apply_elegant_styling(self):
        """Apply refined, elegant styling to the dialog"""
        bg_color = themes.get_color('card_bg')
        text_color = themes.get_color('text')
        border_color = themes.get_color('border')
        highlight_color = themes.get_color('highlight')
        button_color = themes.get_color('button')

        # Make sure text is visible against the background
        input_bg = QColor(bg_color).lighter(
            115).name() if self.is_dark_theme() else QColor(bg_color).darker(105).name()
        button_text = "#FFFFFF"  # White text for buttons

        # Base dialog styling
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}

            QLabel {{
                color: {text_color};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}

            QLabel[cssClass="title"] {{
                font-size: 16px;
                font-weight: bold;
            }}

            QLabel[cssClass="subtitle"] {{
                font-size: 13px;
                color: {QColor(text_color).lighter(120).name() if self.is_dark_theme() else QColor(text_color).darker(120).name()};
            }}

            QRadioButton {{
                color: {text_color};
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                spacing: 8px;
                padding: 2px;
            }}

            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 1px solid {border_color};
            }}

            QRadioButton::indicator:unchecked {{
                background-color: {bg_color};
            }}

            QRadioButton::indicator:checked {{
                background-color: {highlight_color};
                border: 1px solid {highlight_color};
            }}

            QLineEdit {{
                background-color: {input_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
            }}

            QPushButton {{
                background-color: {button_color};
                color: {button_text};
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
                min-width: 80px;
            }}

            QPushButton:hover {{
                background-color: {QColor(button_color).lighter(115).name()};
            }}

            QPushButton:pressed {{
                background-color: {QColor(button_color).darker(110).name()};
            }}

            QPushButton#primaryButton {{
                background-color: {highlight_color};
            }}

            QPushButton#primaryButton:hover {{
                background-color: {QColor(highlight_color).lighter(115).name()};
            }}

            QPushButton#secondaryButton {{
                background-color: transparent;
                color: {text_color};
                border: 1px solid {border_color};
            }}

            QPushButton#secondaryButton:hover {{
                background-color: rgba(128, 128, 128, 0.1);
                border: 1px solid {highlight_color};
            }}

            QGroupBox {{
                font-weight: bold;
                margin-top: 14px;
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 10px;
                padding-top: 20px;
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: {bg_color};
            }}
        """)

    def is_dark_theme(self):
        """Check if current theme is dark"""
        bg_color = themes.get_color('card_bg')
        bg_color = bg_color.lstrip('#')

        # If it's a named color and not a hex, return False as fallback
        if len(bg_color) not in (3, 6):
            return False

        # Convert hex to RGB and calculate brightness
        if len(bg_color) == 3:
            r, g, b = [int(c, 16) * 17 for c in bg_color]
        else:
            r, g, b = [int(bg_color[i:i + 2], 16) for i in (0, 2, 4)]

        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return brightness < 128

    def setup_ui(self):
        """Set up compact UI with elegant elements"""
        # Main layout with smaller margins
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header section - more compact
        header_layout = QHBoxLayout()

        # Small icon if available
        icon_label = QLabel()
        icon_path = "resources/chatbot.png"  # Adjust path as needed
        try:
            pixmap = QPixmap(icon_path).scaled(24, 24, Qt.KeepAspectRatio,
                                               Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
            header_layout.addWidget(icon_label)
        except:
            pass  # Skip icon if not found

        # Title
        title = QLabel("Chat Assistant Settings")
        title.setProperty("cssClass", "title")
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Brief description
        if self.api_issue:
            description = QLabel("API quota exceeded. Choose how to proceed:")
            description.setProperty("cssClass", "subtitle")
            description.setStyleSheet(f"color: {themes.get_color('warning')};")
        else:
            description = QLabel("Configure your chat assistant:")
            description.setProperty("cssClass", "subtitle")

        layout.addWidget(description)

        # Mode selection group
        modes_group = QGroupBox("Operation Mode")
        modes_layout = QVBoxLayout(modes_group)
        modes_layout.setSpacing(8)

        # Local mode option
        self.local_mode_radio = QRadioButton("Built-in car knowledge base")
        self.local_mode_radio.setToolTip("Works offline with no API calls")

        # API mode option
        self.api_mode_radio = QRadioButton("OpenAI API (more advanced)")
        self.api_mode_radio.setToolTip("Requires API key")

        # Create button group
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.local_mode_radio, 1)
        self.mode_group.addButton(self.api_mode_radio, 2)

        # Set default based on current state
        if self.api_issue or not self.api_key:
            self.local_mode_radio.setChecked(True)
        else:
            self.api_mode_radio.setChecked(True)

        # Connect change event
        self.mode_group.buttonClicked.connect(self.toggle_api_section)

        # Add to group layout
        modes_layout.addWidget(self.local_mode_radio)
        modes_layout.addWidget(self.api_mode_radio)

        layout.addWidget(modes_group)

        # API section
        self.api_section = QGroupBox("API Key")
        api_layout = QVBoxLayout(self.api_section)

        # API key input
        self.key_input = QLineEdit()
        if self.api_key:
            self.key_input.setText(self.api_key)
        self.key_input.setPlaceholderText("Enter your OpenAI API key (sk-...)")

        api_layout.addWidget(self.key_input)

        # Small note on security
        key_note = QLabel("Your API key is stored securely on this device only.")
        key_note.setProperty("cssClass", "subtitle")
        key_note.setStyleSheet("font-size: 11px; font-style: italic;")
        api_layout.addWidget(key_note)

        layout.addWidget(self.api_section)

        # Info section - more compact
        info_label = QLabel(
            "<b>Note:</b> The built-in knowledge base works offline with no limits.")
        info_label.setProperty("cssClass", "subtitle")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        links_label = QLabel(
            "<a href='https://platform.openai.com/api-keys'>Get API key</a> | <a href='https://platform.openai.com/billing'>Billing</a>")
        links_label.setTextFormat(Qt.RichText)
        links_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        links_label.setOpenExternalLinks(True)

        # Use a modern, elegant font: Segoe UI (or a fallback if not available), larger size, lighter weight.
        font = QFont("Segoe UI", 16, QFont.Light)
        font.setLetterSpacing(QFont.PercentageSpacing,
                              105)  # Slightly increase letter spacing (105% of default)
        links_label.setFont(font)

        links_label.setStyleSheet("""
            QLabel {
                color: #1E62D0; /* Lighter sapphire blue */
                background: transparent;
            }
            QLabel a {
                color: #1E62D0;
                text-decoration: none;
            }
            QLabel a:hover {
                color: #1E62D0;
                text-decoration: underline;
            }
        """)
        layout.addWidget(links_label)

        # Add stretch to push buttons to bottom
        layout.addStretch()

        # Button section
        button_layout = QHBoxLayout()

        # Clear key button if key exists
        if self.api_key:
            clear_btn = QPushButton("Clear Key")
            clear_btn.setObjectName("secondaryButton")
            clear_btn.clicked.connect(self.clear_key)
            button_layout.addWidget(clear_btn)

        button_layout.addStretch()

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)

        # Save button
        save_btn = QPushButton("Save")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

        # Initial API section visibility
        self.toggle_api_section()

    def toggle_api_section(self):
        """Show or hide API key section based on selected mode"""
        if hasattr(self, 'api_section') and hasattr(self, 'mode_group'):
            # Show API section only if API mode is selected (id 2)
            self.api_section.setVisible(self.mode_group.checkedId() == 2)

    def clear_key(self):
        """Clear the API key"""
        self.key_input.clear()
        self.local_mode_radio.setChecked(True)
        self.toggle_api_section()

    def accept(self):
        """Save settings and close"""
        # Determine which mode is selected
        self.use_fallback_mode = (self.mode_group.checkedId() == 1)

        if not self.use_fallback_mode:
            self.api_key = self.key_input.text().strip()
        else:
            self.api_key = None

        super().accept()

    def showEvent(self, event):
        """Ensure dialog is centered when shown"""
        super().showEvent(event)
        self.center_on_parent()
class DirectChatWidget(QWidget):
    """Chat widget with resilient design for car parts information"""
    dummy_signal = pyqtSignal(str)

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator

        # Debugging info
        debug_log("Initializing DirectChatWidget with car knowledge and resilient design")

        # State variables
        self.chat_visible = False
        self.is_expanded = False

        # Create signal bridge for cross-thread communication
        self.signal_bridge = SignalBridge()
        self.signal_bridge.update_signal.connect(self._add_message_safe)
        self.signal_bridge.remove_thinking_signal.connect(self._remove_thinking_safe)
        self.signal_bridge.api_error_signal.connect(self._show_api_error)

        # Get username
        self.username = os.environ.get('USERNAME', 'User')
        debug_log(f"Username: {self.username}")

        # Initialize API key manager
        self.key_manager = ApiKeyManager()

        # Load API key if available
        api_key = self.key_manager.load_api_key()

        # Initialize OpenAI Chat client with fallback capability
        self.openai_chat = OpenAIChat(api_key)

        # Setup UI
        self.setup_ui()

        # Reference to thinking bubble for removal
        self.thinking_label = None

        # API configuration button
        self.add_settings_button()

    def add_settings_button(self):
        """Add settings button to the header"""
        header = self.chat_container.findChild(QWidget, "chatHeader")
        if header and header.layout():
            # Create settings button
            self.settings_btn = QToolButton()
            self.settings_btn.setText("⚙")  # Gear icon
            self.settings_btn.setObjectName("configButton")
            self.settings_btn.setToolTip("Chat Settings")
            self.settings_btn.setCursor(Qt.PointingHandCursor)
            self.settings_btn.clicked.connect(self.show_settings)

            # Insert before expand button
            header_layout = header.layout()
            header_layout.insertWidget(header_layout.count() - 2, self.settings_btn)

            debug_log("Added settings button")

    def show_settings(self, api_issue=False):
        """Show chat settings dialog"""
        debug_log("Showing chat settings dialog")

        # Use the top-level window as parent to ensure proper centering
        current_key = self.openai_chat.api_key
        # Find the main window/parent
        parent_window = None
        parent = self.parent()
        while parent:
            parent_window = parent
            parent = parent.parent()

        dialog = ChatSettingsDialog(parent_window, current_key, api_issue)

        if dialog.exec_() == QDialog.Accepted:
            new_key = dialog.api_key
            use_fallback = dialog.use_fallback_mode

            if use_fallback:
                # User chose local mode
                self.key_manager.delete_api_key()
                self.openai_chat.use_fallback_mode = True
                debug_log("Using local car knowledge base (no API)")
                self._add_message_safe(
                    "Using built-in car knowledge base for assistance!", False)
            else:
                # User chose API mode
                if new_key:
                    self.key_manager.save_api_key(new_key)
                    self.openai_chat.setup_client(new_key)
                    debug_log("Using OpenAI API mode")
                    self._add_message_safe("OpenAI API mode activated.", False)
                else:
                    # No key provided but API mode selected
                    self._add_message_safe("Please provide an API key to use API mode.",
                                           False)
                    self.openai_chat.use_fallback_mode = True
    def setup_ui(self):
        """Create the chat UI components"""
        debug_log("Setting up UI components")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create chat button with modern styling
        self.chat_btn = QToolButton()
        self.chat_btn.setCursor(Qt.PointingHandCursor)
        self.chat_btn.setToolTip("Chat")
        self.chat_btn.clicked.connect(self.toggle_chat)

        # Add chat icon
        chat_icon_path = Path(__file__).resolve().parent.parent.parent / "resources/chatbot.png"
        if chat_icon_path.exists():
            debug_log(f"Using chat icon from: {chat_icon_path}")
            self.chat_btn.setIcon(QIcon(str(chat_icon_path)))
            self.chat_btn.setIconSize(QSize(26, 26))
        else:
            debug_log("Chat icon not found, using text emoji")
            self.chat_btn.setText("💬")
            self.chat_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)

        # Make button appropriately sized
        self.chat_btn.setMinimumSize(40, 40)

        # Create chat container with popup behavior
        self.chat_container = QFrame()
        self.chat_container.setObjectName("chatContainer")
        self.chat_container.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.chat_container.setAttribute(Qt.WA_TranslucentBackground)

        # Add shadow to the container
        container_shadow = QGraphicsDropShadowEffect()
        container_shadow.setBlurRadius(20)
        container_shadow.setOffset(0, 4)
        container_shadow.setColor(QColor(0, 0, 0, 40))
        self.chat_container.setGraphicsEffect(container_shadow)

        # Container layout
        container_layout = QVBoxLayout(self.chat_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Inner content frame
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")

        # Content layout
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Chat header with title and buttons
        header_container = QWidget()
        header_container.setObjectName("chatHeader")
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(15, 10, 15, 10)

        # Add avatar in header
        header_avatar = QLabel()
        if chat_icon_path.exists():
            avatar_pixmap = QPixmap(str(chat_icon_path)).scaled(22, 22,
                                                                Qt.KeepAspectRatio,
                                                                Qt.SmoothTransformation)
            header_avatar.setPixmap(avatar_pixmap)

        chat_title = QLabel("Car Assistant")
        font = QFont("Segoe UI", 11)
        font.setBold(True)
        chat_title.setFont(font)
        chat_title.setObjectName("chatTitle")

        # Expand button
        self.expand_btn = QToolButton()
        self.expand_btn.setText("⤢")  # Unicode expand symbol
        self.expand_btn.setObjectName("expandButton")
        self.expand_btn.setToolTip("Expand chat")
        self.expand_btn.setCursor(Qt.PointingHandCursor)
        self.expand_btn.clicked.connect(self.toggle_expand)

        # Close button
        close_btn = QToolButton()
        close_btn.setText("✕")
        close_btn.setObjectName("closeButton")
        close_btn.setToolTip("Close")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.toggle_chat)

        # Add header elements
        header_layout.addWidget(header_avatar)
        header_layout.addWidget(chat_title)
        header_layout.addStretch(1)
        header_layout.addWidget(self.expand_btn)
        header_layout.addWidget(close_btn)

        # Chat messages area with scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setObjectName("chatScroll")
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        # Container for chat messages
        self.messages_container = QWidget()
        self.messages_container.setObjectName("messagesContainer")
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setSpacing(12)
        self.messages_layout.setContentsMargins(15, 15, 15, 15)
        self.messages_layout.setAlignment(Qt.AlignTop)

        # Set the container as the widget for the scroll area
        self.scroll_area.setWidget(self.messages_container)

        # Message input area
        input_container = QWidget()
        input_container.setObjectName("inputContainer")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(15, 15, 15, 15)
        input_layout.setSpacing(10)

        self.message_input = QLineEdit()
        self.message_input.setObjectName("messageInput")
        self.message_input.setPlaceholderText("Ask me about car parts...")
        self.message_input.returnPressed.connect(self.send_message)
        self.message_input.setFixedHeight(38)

        send_btn = QPushButton("Send")
        send_btn.setObjectName("sendButton")
        send_btn.setFixedSize(70, 38)
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.clicked.connect(self.send_message)

        # Add input elements
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(send_btn)

        # Add everything to content layout
        content_layout.addWidget(header_container)
        content_layout.addWidget(self.scroll_area, 1)
        content_layout.addWidget(input_container)

        # Add content frame to container
        container_layout.addWidget(content_frame)

        # Set fixed size for the popup
        self.chat_container.setFixedWidth(320)
        self.chat_container.setFixedHeight(420)

        # Add button to main layout
        layout.addWidget(self.chat_btn)

        # Apply theme
        self.apply_theme()

        # Add welcome message
        welcome_message = f"Hello {self.username}! I'm your car assistant. Ask me about vehicle parts, maintenance, and common issues. I can help in English or Hebrew!"
        self._add_message_safe(welcome_message, False)

        debug_log("UI setup complete")

    def send_message(self):
        """Send a message and process response"""
        debug_log("send_message called")

        # Get message text
        message = self.message_input.text().strip()
        if not message:
            return

        debug_log(f"Message to process: {message}")

        # Add user message to UI
        self._add_message_safe(message, True)

        # Clear input field
        self.message_input.clear()

        # Show thinking indicator
        self._add_thinking_indicator()

        # Process in separate thread
        def process_message():
            try:
                # Get response using car knowledge base or OpenAI
                debug_log("Getting response")
                response = self.openai_chat.get_response(message)
                debug_log(f"Received response: {response}")

                # Remove thinking indicator and add response
                self.signal_bridge.remove_thinking_signal.emit()
                time.sleep(0.1)  # Small delay for UI update
                self.signal_bridge.update_signal.emit(response, False)

            except Exception as e:
                debug_log(f"Error generating response: {e}")
                error_message = str(e)

                # Remove thinking indicator
                self.signal_bridge.remove_thinking_signal.emit()
                time.sleep(0.1)

                # Check for API-related errors
                if any(term in error_message.lower() for term in ['quota', 'rate limit', 'capacity', 'exceeded']):
                    error_type = 'api_issue'
                    # Switch to fallback mode
                    self.openai_chat.use_fallback_mode = True

                    # Get fallback response
                    fallback = self.openai_chat.fallback.get_response(message)

                    # Show dialog about API issue (only once)
                    self.signal_bridge.api_error_signal.emit(error_message, error_type)

                    # Add explanatory message first, then the response
                    self.signal_bridge.update_signal.emit(
                        "I've switched to using the built-in car knowledge base due to API issues:", False
                    )
                    time.sleep(0.1)
                    self.signal_bridge.update_signal.emit(fallback, False)

                else:
                    # General error
                    self.signal_bridge.api_error_signal.emit(error_message, "general_error")

                    # Add fallback response to chat
                    fallback = self.openai_chat.fallback.get_response(message)
                    self.signal_bridge.update_signal.emit(fallback, False)

        # Start processing thread
        threading.Thread(target=process_message, daemon=True).start()
        debug_log("Started processing thread")

    def _show_api_error(self, error_message, error_type):
        """Show API error message and handle based on type"""
        debug_log(f"API error: {error_message} (type: {error_type})")

        # For API quota/rate limit issues
        if error_type == 'api_issue':
            # Only show the settings dialog once per session for API issues
            if not self.openai_chat.use_fallback_mode:
                self.show_settings(api_issue=True)
        else:
            # For other errors, just show a simple message box
            QMessageBox.warning(
                self,
                "Chat Error",
                f"Error: {error_message}\n\nUsing built-in responses instead."
            )

    def _add_thinking_indicator(self):
        """Add a thinking indicator to the chat"""
        debug_log("Adding thinking indicator")
        self.signal_bridge.update_signal.emit("Thinking...", False)

    def _add_message_safe(self, message, is_user):
        """Add a message to the chat from the main UI thread"""
        debug_log(f"Adding {'user' if is_user else 'bot'} message safely: {message}")

        # Create message container
        message_frame = QFrame(self.messages_container)
        message_frame.setObjectName("userBubble" if is_user else "botBubble")

        # Layout for the message
        message_layout = QHBoxLayout(message_frame)
        message_layout.setContentsMargins(8, 6, 8, 6)
        message_layout.setSpacing(10)

        # Create label for the message text
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # Set font
        font = QFont("Segoe UI", 10)
        message_label.setFont(font)
        message_label.setMinimumWidth(150)

        # If this is a thinking bubble, store a reference
        if not is_user and message == "Thinking...":
            self.thinking_label = message_frame

        # Layout arrangement based on user/bot
        if is_user:
            message_layout.addStretch(1)
            message_layout.addWidget(message_label)
        else:
            # Avatar for bot
            avatar_label = QLabel()
            avatar_path = Path(__file__).resolve().parent.parent.parent / "resources/chatbot.png"
            if avatar_path.exists():
                avatar_pixmap = QPixmap(str(avatar_path)).scaled(22, 22,
                                                             Qt.KeepAspectRatio,
                                                             Qt.SmoothTransformation)
                avatar_label.setPixmap(avatar_pixmap)
            else:
                avatar_label.setText("🤖")
            avatar_label.setFixedSize(22, 22)

            message_layout.addWidget(avatar_label)
            message_layout.addWidget(message_label)
            message_layout.addStretch(1)

        # Apply theme colors
        dark_mode = is_dark_theme()
        if is_user:
            bubble_color = "#2979FF" if dark_mode else "#2962FF"  # Blue
            text_color = "#FFFFFF"  # White
        else:
            bubble_color = "#1E2334" if dark_mode else "#F4F6F8"  # Dark/Light gray
            text_color = "#E0E0FF" if dark_mode else "#36454F"  # Blue-white/Charcoal

        # Apply styles
        message_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bubble_color};
                border-radius: 18px;
            }}
            QLabel {{
                color: {text_color};
                background-color: transparent;
                padding: 4px;
            }}
        """)

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 30))
        message_frame.setGraphicsEffect(shadow)

        # Add to layout
        self.messages_layout.addWidget(message_frame)

        # Make the message visible immediately
        message_frame.show()

        # Force update
        self.messages_container.updateGeometry()
        self.messages_container.update()
        QApplication.processEvents()

        # Scroll to bottom
        self.scroll_to_bottom()

        debug_log(f"Added {'user' if is_user else 'bot'} message to UI")

    def _remove_thinking_safe(self):
        """Remove the thinking indicator from the main UI thread"""
        debug_log("Removing thinking indicator safely")
        if self.thinking_label:
            self.thinking_label.hide()
            self.thinking_label.deleteLater()
            self.thinking_label = None
            QApplication.processEvents()
            debug_log("Thinking indicator removed")

    def scroll_to_bottom(self):
        """Scroll to the bottom of the chat"""
        try:
            scrollbar = self.scroll_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            debug_log("Scrolled to bottom")
        except Exception as e:
            debug_log(f"Error scrolling: {e}")

    def toggle_chat(self):
        """Toggle chat visibility"""
        debug_log("toggle_chat called")

        self.chat_visible = not self.chat_visible

        if self.chat_visible:
            debug_log("Showing chat window")

            # Position the popup near the button
            btn_global_pos = self.chat_btn.mapToGlobal(QPoint(0, self.chat_btn.height()))

            # Calculate position to make sure it's visible
            screen = QApplication.desktop().screenGeometry()
            x = min(btn_global_pos.x(), screen.width() - self.chat_container.width() - 20)
            x = max(20, x)

            self.chat_container.move(x, btn_global_pos.y() + 5)
            self.chat_container.show()
            self.message_input.setFocus()

            # Ensure we scroll to bottom
            QTimer.singleShot(100, self.scroll_to_bottom)
        else:
            debug_log("Hiding chat window")
            self.chat_container.hide()

    def toggle_expand(self):
        """Toggle between normal and expanded chat size"""
        self.is_expanded = not self.is_expanded

        if self.is_expanded:
            self.chat_container.setFixedWidth(400)
            self.chat_container.setFixedHeight(500)
            self.expand_btn.setText("⤡")  # Unicode collapse symbol
            self.expand_btn.setToolTip("Collapse chat")
        else:
            self.chat_container.setFixedWidth(320)
            self.chat_container.setFixedHeight(420)
            self.expand_btn.setText("⤢")  # Unicode expand symbol
            self.expand_btn.setToolTip("Expand chat")

        # Ensure we scroll to bottom after resize
        QTimer.singleShot(100, self.scroll_to_bottom)

    def apply_theme(self):
        """Apply modern theme styling"""
        # Determine if we're in dark mode
        dark_mode = is_dark_theme()

        # Define colors
        if dark_mode:
            accent_color = "#2A4B8D"  # Slightly lighter blue for dark theme
            accent_hover = "#5C6BC0"  # Lighter indigo for hover
            button_text = "#FFFFFF"
        else:
            accent_color = "#2A4B8D"  # Slightly lighter blue for light theme
            accent_hover = "#5C6BC0"  # Lighter indigo for hover
            button_text = "#FFFFFF"

        # Get theme colors
        try:
            bg_color = themes.get_color('card_bg')
            text_color = themes.get_color('text')
            input_bg = themes.get_color('input_bg')
        except Exception as e:
            debug_log(f"Error getting theme colors: {e}")
            # Fallback colors
            bg_color = "#1E1E1E" if dark_mode else "#FFFFFF"
            text_color = "#FFFFFF" if dark_mode else "#000000"
            input_bg = "#2D2D2D" if dark_mode else "#F0F0F0"

        # Button style
        self.chat_btn.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                border: none;
                padding: 6px;
            }}
            QToolButton:hover {{
                background-color: {accent_color}40;
                border-radius: 20px;
            }}
            QToolButton:pressed {{
                background-color: {accent_color}70;
                border-radius: 20px;
            }}
        """)

        # Container style with additional config button styling
        self.chat_container.setStyleSheet(f"""
            QFrame#chatContainer {{
                background-color: transparent;
                border: none;
            }}

            QFrame#contentFrame {{
                background-color: {bg_color};
                border-radius: 10px;
                border: none;
            }}

            #chatHeader {{
                background-color: {accent_color};
                color: {button_text};
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }}

            #chatTitle {{
                color: {button_text};
                font-weight: bold;
            }}

            #expandButton, #closeButton, #configButton {{
                background-color: transparent;
                color: {button_text};
                border: none;
                padding: 3px;
                border-radius: 4px;
            }}

            #expandButton:hover, #closeButton:hover, #configButton:hover {{
                background-color: {accent_hover};
            }}

            #chatScroll {{
                border: none;
                background-color: transparent;
            }}

            QScrollBar:vertical {{
                background-color: transparent;
                width: 8px;
                margin: 0px;
            }}

            QScrollBar::handle:vertical {{
                background-color: {accent_color}50;
                min-height: 20px;
                border-radius: 4px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {accent_color}80;
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            #messagesContainer {{
                background-color: transparent;
            }}

            #inputContainer {{
                background-color: {bg_color};
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }}

            #messageInput {{
                background-color: {input_bg};
                color: {text_color};
                border: none;
                border-radius: 19px;
                padding: 8px 15px;
                font-size: 10pt;
            }}

            #messageInput:focus {{
                border: 1px solid {accent_color};
            }}

            #sendButton {{
                background-color: {accent_color};
                color: white;
                border: none;
                border-radius: 19px;
                padding: 5px 10px;
                font-size: 10pt;
                font-weight: bold;
            }}

            #sendButton:hover {{
                background-color: {accent_hover};
            }}
        """)

    # Compatibility methods
    def pop_out_chat(self):
        pass

    @property
    def chat_submitted(self):
        return self.dummy_signal

    def update_translations(self):
        pass