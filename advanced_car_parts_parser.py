import sqlite3
import re
import os
import json
import logging
from datetime import datetime
import unicodedata
from typing import Dict, List, Tuple, Optional, Any, Union
from collections import defaultdict
import importlib.util

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("enhanced_parser.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("EnhancedCarPartsParser")

# Check for optional advanced libraries
HAVE_NUMPY = importlib.util.find_spec("numpy") is not None
HAVE_SKLEARN = importlib.util.find_spec("sklearn") is not None
HAVE_SPACY = importlib.util.find_spec("spacy") is not None

# Import optional libraries if available
if HAVE_NUMPY:
    import numpy as np

if HAVE_SKLEARN and HAVE_NUMPY:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import DBSCAN

    try:
        from sklearn.ensemble import RandomForestClassifier
        HAVE_NUMPY = importlib.util.find_spec("numpy") is not None
        HAVE_SKLEARN = importlib.util.find_spec("sklearn") is not None
        HAVE_SPACY = importlib.util.find_spec("spacy") is not None
        HAVE_HEBREW_NLP = False  # Initialize to False by default
        HAVE_ML_MODELS = True
    except ImportError:
        HAVE_ML_MODELS = False
else:
    HAVE_ML_MODELS = False

# Initialize Hebrew NLP flag before checking for spaCy model
HAVE_HEBREW_NLP = False  # Initialize to False by default

if HAVE_SPACY:
    try:
        import spacy
        # Try to load Hebrew model
        spacy_nlp = spacy.load("he_core_news_sm")
        HAVE_HEBREW_NLP = True  # Set to True if Hebrew model loaded successfully
    except Exception as e:
        # If loading Hebrew model fails, use blank model and keep HAVE_HEBREW_NLP as False
        spacy_nlp = spacy.blank("he")
        # Optionally log the error (if you want to know why it failed)
        logger.warning(f"Failed to load Hebrew model: {e}")


# Try to import word embedding capabilities
try:
    from gensim.models import Word2Vec

    HAVE_WORD2VEC = True
except ImportError:
    HAVE_WORD2VEC = False


class PartPattern:
    """Enhanced class to define and store complex part naming patterns with validation"""

    def __init__(self, name: str, regex: str, priority: int = 5, validation_func=None):
        self.name = name
        self.regex = regex
        self.priority = priority  # Higher means more specific/reliable
        self._compiled_regex = re.compile(regex, re.UNICODE)
        self.validation_func = validation_func  # Function to validate matches
        self.match_count = 0  # Track how often this pattern matches successfully
        self.false_positive_count = 0  # Track incorrect matches (from feedback)

    def match(self, text: str) -> Optional[re.Match]:
        match = self._compiled_regex.search(text)
        if match and (not self.validation_func or self.validation_func(match)):
            self.match_count += 1
            return match
        return None

    @property
    def precision(self):
        """Calculate precision of this pattern based on usage statistics"""
        if self.match_count == 0:
            return 0.5  # Default precision
        return (self.match_count - self.false_positive_count) / self.match_count


class EnhancedCarPartParser:
    """Advanced car parts parser with machine learning and expert system capabilities"""

    def __init__(self, db_path: str = 'car_parts.db',
                 knowledge_base_path: str = 'enhanced_knowledge_base.json',
                 model_dir: str = 'models'):
        """Initialize the enhanced parser with databases, knowledge bases and ML models"""
        self.db_path = db_path
        self.knowledge_base_path = knowledge_base_path
        self.model_dir = model_dir

        # Create model directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)

        # Load or create knowledge base
        if os.path.exists(knowledge_base_path):
            with open(knowledge_base_path, 'r', encoding='utf-8') as f:
                self.knowledge_base = json.load(f)
        else:
            self.knowledge_base = self._create_initial_knowledge_base()
            self._save_knowledge_base()

        # Initialize key components in the right order
        self.known_abbreviations = self._build_abbreviations_map()
        self.common_mistakes = self._build_common_mistakes_map()

        # Initialize NLP components if available
        self.nlp = spacy_nlp if HAVE_SPACY else None

        # Initialize statistical models
        self.car_makes_dict = self._build_lookup_dict(self.knowledge_base['car_makes'])
        self.car_models_dict = self._build_lookup_dict(self.knowledge_base['car_models'])
        self.part_categories_dict = self._build_lookup_dict(
            self.knowledge_base['part_categories'])

        # Build enhanced mapping structures
        self.car_make_to_models = self._build_make_to_models_map()
        self.part_compatibility = self._build_compatibility_map()
        self.part_patterns = self._compile_part_patterns()

        # Hebrew-specific handling
        self.heb_to_eng_chars = {
            'א': 'a', 'ב': 'b', 'ג': 'g', 'ד': 'd', 'ה': 'h', 'ו': 'v', 'ז': 'z',
            'ח': 'ch', 'ט': 't', 'י': 'y', 'כ': 'k', 'ל': 'l', 'מ': 'm', 'נ': 'n',
            'ס': 's', 'ע': 'a', 'פ': 'p', 'צ': 'ts', 'ק': 'k', 'ר': 'r', 'ש': 'sh',
            'ת': 't'
        }

        # Create database if needed
        self._ensure_database_exists()

        # Load or initialize ML models if available
        self.vectorizer = None
        self.word2vec = None
        self.category_classifier = None
        if HAVE_ML_MODELS:
            self._load_or_train_models()

        # Statistical data for validation
        self.valid_year_range = (
        1980, datetime.now().year + 5)  # Allow up to 5 years in future

        # Cache for performance
        self.extraction_cache = {}
        self.embedding_cache = {}

        # Track feedback for continuous improvement
        self.feedback_history = []

        logger.info(
            f"Initialized EnhancedCarPartsParser with {len(self.knowledge_base['car_makes'])} car makes, "
            f"{len(self.knowledge_base['car_models'])} car models, and "
            f"{len(self.knowledge_base['part_categories'])} part categories")

        # Log available advanced features
        logger.info(
            f"Advanced features available: NumPy={HAVE_NUMPY}, scikit-learn={HAVE_SKLEARN}, "
            f"spaCy={HAVE_SPACY}, Hebrew NLP={HAVE_HEBREW_NLP}, Word2Vec={HAVE_WORD2VEC}, "
            f"ML Models={HAVE_ML_MODELS}")

    def _load_or_train_models(self):
        """Load existing ML models or initialize new ones if they don't exist"""
        if not HAVE_ML_MODELS:
            return

        # Word2Vec model for term similarity
        if HAVE_WORD2VEC:
            word2vec_path = os.path.join(self.model_dir, 'word2vec.model')
            if os.path.exists(word2vec_path):
                try:
                    self.word2vec = Word2Vec.load(word2vec_path)
                    logger.info("Loaded existing Word2Vec model")
                except Exception as e:
                    logger.warning(f"Failed to load Word2Vec model: {e}")
                    self.word2vec = None
            else:
                self.word2vec = None
                logger.info("No Word2Vec model yet. Will be trained on first import")

        # TF-IDF vectorizer for part descriptions
        vectorizer_path = os.path.join(self.model_dir, 'tfidf_vectorizer.pkl')
        if os.path.exists(vectorizer_path):
            try:
                import pickle
                with open(vectorizer_path, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                logger.info("Loaded existing TF-IDF vectorizer")
            except Exception as e:
                logger.warning(f"Failed to load vectorizer: {e}")
                self.vectorizer = self._create_new_vectorizer()
        else:
            self.vectorizer = self._create_new_vectorizer()
            logger.info("Initialized new TF-IDF vectorizer")

        # Part category classifier
        classifier_path = os.path.join(self.model_dir, 'category_classifier.pkl')
        if os.path.exists(classifier_path):
            try:
                import pickle
                with open(classifier_path, 'rb') as f:
                    self.category_classifier = pickle.load(f)
                logger.info("Loaded existing category classifier")
            except Exception as e:
                logger.warning(f"Failed to load classifier: {e}")
                self.category_classifier = None
        else:
            self.category_classifier = None
            logger.info("No category classifier yet. Will be trained on first import")

    def _create_new_vectorizer(self):
        """Create a new TF-IDF vectorizer"""
        if HAVE_SKLEARN and HAVE_NUMPY:
            return TfidfVectorizer(
                analyzer='word',
                ngram_range=(1, 3),
                min_df=2,
                max_df=0.95,
                token_pattern=r'[א-ת\w]+'
            )
        return None

    def _create_initial_knowledge_base(self) -> Dict:
        """Create an expanded knowledge base with automotive domain knowledge"""
        # Load the basic knowledge base from the previous implementation
        # This is just a starter - the enhanced version will have much more data

        base_kb = {
            "car_makes": {
                # Hebrew names mapped to English with confidence scores and expanded info
                "מזדה": {
                    "english": "Mazda",
                    "confidence": 0.95,
                    "aliases": ["מאזדה", "מאזדא", "מאזדה", "mazda"],
                    "parent_company": "Independent",
                    "country": "Japan"
                },
                "טויוטה": {
                    "english": "Toyota",
                    "confidence": 0.95,
                    "aliases": ["טויוטא", "toyota"],
                    "parent_company": "Toyota Motor Corporation",
                    "country": "Japan"
                },
                "יונדאי": {
                    "english": "Hyundai",
                    "confidence": 0.95,
                    "aliases": ["יונדאי", "hyundai"],
                    "parent_company": "Hyundai Motor Group",
                    "country": "South Korea"
                },
                "קיה": {
                    "english": "Kia",
                    "confidence": 0.95,
                    "aliases": ["קיאה", "kia"],
                    "parent_company": "Hyundai Motor Group",
                    "country": "South Korea"
                },
                "סקודה": {
                    "english": "Skoda",
                    "confidence": 0.95,
                    "aliases": ["סקודא", "škoda", "skoda"],
                    "parent_company": "Volkswagen Group",
                    "country": "Czech Republic"
                },
                "פורד": {"english": "Ford", "confidence": 0.95, "aliases": ["ford"]},
                "סוזוקי": {"english": "Suzuki", "confidence": 0.95,
                           "aliases": ["סוזוקי", "suzuki"]},
                "ניסאן": {"english": "Nissan", "confidence": 0.95,
                          "aliases": ["ניסן", "nissan"]},
                "הונדה": {"english": "Honda", "confidence": 0.95, "aliases": ["honda"]},
                "מיצובישי": {"english": "Mitsubishi", "confidence": 0.95,
                             "aliases": ["מיצובישי", "mitsubishi"]},
                "ב.מ.וו": {"english": "BMW", "confidence": 0.95,
                           "aliases": ["ב.מ.וו", "במוו", "bmw"]},
                "רנו": {"english": "Renault", "confidence": 0.95,
                        "aliases": ["רנו", "renault"]},
                "פיג'ו": {"english": "Peugeot", "confidence": 0.95,
                          "aliases": ["פיג'ו", "פגו", "פיגו", "peugeot"]},
                "סיטרואן": {"english": "Citroen", "confidence": 0.95,
                            "aliases": ["סיטרואן", "citroen", "citroën"]},
                "אאודי": {"english": "Audi", "confidence": 0.95,
                          "aliases": ["אאודי", "אודי", "audi"]},
                "מרצדס": {"english": "Mercedes", "confidence": 0.95,
                          "aliases": ["מרצדס בנץ", "mercedes", "mercedes-benz"]},
                "פולקסווגן": {"english": "Volkswagen", "confidence": 0.95,
                              "aliases": ["פולקסוואגן", "וולקסווגן", "volkswagen", "vw"]},
                "סובארו": {"english": "Subaru", "confidence": 0.95,
                           "aliases": ["סובארו", "subaru"]},
                "דייהטסו": {"english": "Daihatsu", "confidence": 0.95,
                            "aliases": ["דייהטסו", "daihatsu"]},
                "שברולט": {"english": "Chevrolet", "confidence": 0.95,
                           "aliases": ["שבראולט", "שברולט", "chevrolet", "chevy"]},
                "אופל": {"english": "Opel", "confidence": 0.95,
                         "aliases": ["אופל", "opel"]},
                "איסוזו": {"english": "Isuzu", "confidence": 0.95,
                           "aliases": ["איסוזו", "isuzu"]},
                "לנדרובר": {"english": "Land Rover", "confidence": 0.95,
                            "aliases": ["לנד רובר", "land rover"]},
                "לקסוס": {"english": "Lexus", "confidence": 0.95,
                          "aliases": ["לקסוס", "lexus"]},
                "וולוו": {"english": "Volvo", "confidence": 0.95,
                          "aliases": ["וולוו", "volvo"]},
                "פיאט": {"english": "Fiat", "confidence": 0.95,
                         "aliases": ["פיאט", "fiat"]},
                "אלפא רומאו": {"english": "Alfa Romeo", "confidence": 0.95,
                               "aliases": ["אלפא", "alfa", "alfa romeo"]},
            },

            "car_models": {
                # Models with detailed information
                "קורולה": {
                    "english": "Corolla",
                    "confidence": 0.95,
                    "make": "Toyota",
                    "aliases": ["corolla"],
                    "body_styles": ["sedan", "hatchback", "wagon"],
                    "popular_years": [1990, 2020],
                    "common_engines": ["1.6", "1.8", "2.0"]
                },
                "אוקטביה": {
                    "english": "Octavia",
                    "confidence": 0.95,
                    "make": "Skoda",
                    "aliases": ["octavia"],
                    "body_styles": ["sedan", "wagon"],
                    "popular_years": [2000, 2022],
                    "common_engines": ["1.4", "1.8", "2.0"]
                },
                "פביה": {"english": "Fabia", "confidence": 0.95, "make": "Skoda",
                         "aliases": ["fabia"]},
                "פוקוס": {"english": "Focus", "confidence": 0.95, "make": "Ford",
                          "aliases": ["focus"]},
                "אקסנט": {"english": "Accent", "confidence": 0.95, "make": "Hyundai",
                          "aliases": ["accent"]},
                "לנסר": {"english": "Lancer", "confidence": 0.95, "make": "Mitsubishi",
                         "aliases": ["lancer"]},
                "גולף": {"english": "Golf", "confidence": 0.95, "make": "Volkswagen",
                         "aliases": ["golf"]},
                "פולו": {"english": "Polo", "confidence": 0.95, "make": "Volkswagen",
                         "aliases": ["polo"]},
                "ראב 4": {"english": "RAV4", "confidence": 0.95, "make": "Toyota",
                          "aliases": ["rav4", "rav 4"]},
                "קרוז": {"english": "Cruze", "confidence": 0.95, "make": "Chevrolet",
                         "aliases": ["cruze"]},
                "לאון": {"english": "Leon", "confidence": 0.95, "make": "Seat",
                         "aliases": ["leon"]},
                "קודיאק": {"english": "Kodiaq", "confidence": 0.95, "make": "Skoda",
                           "aliases": ["kodiaq"]},
                "סנטה פה": {"english": "Santa Fe", "confidence": 0.95, "make": "Hyundai",
                            "aliases": ["santa fe"]},
                "טוסון": {"english": "Tucson", "confidence": 0.95, "make": "Hyundai",
                          "aliases": ["tucson"]},
                "סורנטו": {"english": "Sorento", "confidence": 0.95, "make": "Kia",
                           "aliases": ["sorento"]},
                "ספורטאג": {"english": "Sportage", "confidence": 0.95, "make": "Kia",
                            "aliases": ["sportage"]},
                "קנגו": {"english": "Kangoo", "confidence": 0.95, "make": "Renault",
                         "aliases": ["kangoo"]},
                "מגאן": {"english": "Megane", "confidence": 0.95, "make": "Renault",
                         "aliases": ["megane"]},
                "קליאו": {"english": "Clio", "confidence": 0.95, "make": "Renault",
                          "aliases": ["clio"]},
                "לוגן": {"english": "Logan", "confidence": 0.95, "make": "Dacia",
                         "aliases": ["logan"]},
                "ג'טה": {"english": "Jetta", "confidence": 0.95, "make": "Volkswagen",
                         "aliases": ["jetta", "g'eta"]},
                "פסאט": {"english": "Passat", "confidence": 0.95, "make": "Volkswagen",
                         "aliases": ["passat"]},
                "גרנד צ'רוקי": {"english": "Grand Cherokee", "confidence": 0.95,
                                "make": "Jeep", "aliases": ["grand cherokee"]},
                "קורסה": {"english": "Corsa", "confidence": 0.95, "make": "Opel",
                          "aliases": ["corsa"]},
                "אסטרה": {"english": "Astra", "confidence": 0.95, "make": "Opel",
                          "aliases": ["astra"]},
                "רפיד": {"english": "Rapid", "confidence": 0.95, "make": "Skoda",
                         "aliases": ["rapid"]},
                "סופרב": {"english": "Superb", "confidence": 0.95, "make": "Skoda",
                          "aliases": ["superb"]},
                "איביזה": {"english": "Ibiza", "confidence": 0.95, "make": "Seat",
                           "aliases": ["ibiza"]},
                "טוארג": {"english": "Touareg", "confidence": 0.95, "make": "Volkswagen",
                          "aliases": ["touareg"]},
                "טיגואן": {"english": "Tiguan", "confidence": 0.95, "make": "Volkswagen",
                           "aliases": ["tiguan"]},
                "I10": {"english": "i10", "confidence": 0.95, "make": "Hyundai",
                        "aliases": ["i10"]},
                "I20": {"english": "i20", "confidence": 0.95, "make": "Hyundai",
                        "aliases": ["i20"]},
                "I30": {"english": "i30", "confidence": 0.95, "make": "Hyundai",
                        "aliases": ["i30"]},
                "I35": {"english": "i35", "confidence": 0.95, "make": "Hyundai",
                        "aliases": ["i35"]},
                "I25": {"english": "i25", "confidence": 0.95, "make": "Hyundai",
                        "aliases": ["i25"]},
                "IX35": {"english": "ix35", "confidence": 0.95, "make": "Hyundai",
                         "aliases": ["ix35"]},
                "SX4": {"english": "SX4", "confidence": 0.95, "make": "Suzuki",
                        "aliases": ["sx4"]},
                "CX5": {"english": "CX-5", "confidence": 0.95, "make": "Mazda",
                        "aliases": ["cx5", "cx-5"]},
                "סיויק": {"english": "Civic", "confidence": 0.95, "make": "Honda",
                          "aliases": ["civic"]},
            },

            "part_categories": {
                # Part categories with detailed mapping and hierarchy
                "פילטר": {
                    "english": "Filter",
                    "confidence": 0.95,
                    "aliases": ["מסנן", "filter"],
                    "subcategories": ["אויר", "שמן", "דלק", "מזגן", "סולר"],
                    "related_systems": ["Engine", "Fuel System", "HVAC"]
                },
                "פ.": {
                    "english": "Filter",
                    "confidence": 0.95,
                    "aliases": ["פילטר", "מסנן", "filter"],
                    "is_abbreviation": True
                },
                "פ.אויר": {
                    "english": "Air Filter",
                    "confidence": 0.95,
                    "aliases": ["פילטר אויר", "מסנן אויר", "air filter"],
                    "parent_category": "Filter",
                    "related_systems": ["Engine", "Intake"]
                },
                "בולם": {
                    "english": "Shock Absorber",
                    "confidence": 0.95,
                    "aliases": ["shock", "shock absorber", "strut"],
                    "related_systems": ["Suspension"],
                    "common_locations": ["Front", "Rear"]
                },
                "שמן": {"english": "Oil", "confidence": 0.95, "aliases": ["oil"]},
                "בולם קדמי": {"english": "Front Shock Absorber", "confidence": 0.95,
                              "aliases": ["front shock", "front shock absorber"]},
                "בולם אחורי": {"english": "Rear Shock Absorber", "confidence": 0.95,
                               "aliases": ["rear shock", "rear shock absorber"]},
                "רפידות": {"english": "Brake Pads", "confidence": 0.95,
                           "aliases": ["רפידות בלם", "brake pads"]},
                "דיסק": {"english": "Disc", "confidence": 0.95,
                         "aliases": ["disc", "disk"]},
                "דסקיות": {"english": "Discs", "confidence": 0.95,
                           "aliases": ["דיסקים", "discs", "disks"]},
                "דסקיות קדמי": {"english": "Front Discs", "confidence": 0.95,
                                "aliases": ["דיסקים קדמיים", "front discs"]},
                "דסקיות אחורי": {"english": "Rear Discs", "confidence": 0.95,
                                 "aliases": ["דיסקים אחוריים", "rear discs"]},
                "צלחת": {"english": "Plate", "confidence": 0.95, "aliases": ["plate"]},
                "צלחות": {"english": "Plates", "confidence": 0.95, "aliases": ["plates"]},
                "אטם": {"english": "Gasket", "confidence": 0.95,
                        "aliases": ["gasket", "seal"]},
                "אטם ראש": {"english": "Head Gasket", "confidence": 0.95,
                            "aliases": ["head gasket"]},
                "אטם מכסה שסטומים": {"english": "Valve Cover Gasket", "confidence": 0.95,
                                     "aliases": ["valve cover gasket"]},
                "מצמד": {"english": "Clutch", "confidence": 0.95, "aliases": ["clutch"]},
                "טרמוסטט": {"english": "Thermostat", "confidence": 0.95,
                            "aliases": ["thermostat"]},
                "משולש": {"english": "Triangle Arm", "confidence": 0.95,
                          "aliases": ["control arm", "triangle arm"]},
                "משולש עליון": {"english": "Upper Control Arm", "confidence": 0.95,
                                "aliases": ["upper control arm"]},
                "משולש תחתון": {"english": "Lower Control Arm", "confidence": 0.95,
                                "aliases": ["lower control arm"]},
                "זרוע": {"english": "Arm", "confidence": 0.95, "aliases": ["arm"]},
                "זרוע הגה": {"english": "Steering Arm", "confidence": 0.95,
                             "aliases": ["steering arm", "tie rod"]},
                "מייצב": {"english": "Stabilizer", "confidence": 0.95,
                          "aliases": ["stabilizer", "sway bar"]},
                "ג.מייצב": {"english": "Stabilizer Link", "confidence": 0.95,
                            "aliases": ["stabilizer link", "sway bar link"]},
                "גלגלת": {"english": "Pulley", "confidence": 0.95, "aliases": ["pulley"]},
                "כוהל": {"english": "Coolant", "confidence": 0.95,
                         "aliases": ["coolant", "antifreeze"]},
                "חיישן": {"english": "Sensor", "confidence": 0.95, "aliases": ["sensor"]},
                "ח.חמצן": {"english": "Oxygen Sensor", "confidence": 0.95,
                           "aliases": ["oxygen sensor", "o2 sensor"]},
                "ח.קראנק": {"english": "Crankshaft Sensor", "confidence": 0.95,
                            "aliases": ["crankshaft position sensor", "crank sensor"]},
                "מיסב": {"english": "Bearing", "confidence": 0.95,
                         "aliases": ["bearing"]},
                "אנטרקולר": {"english": "Intercooler", "confidence": 0.95,
                             "aliases": ["intercooler"]},
                "רדיאטור": {"english": "Radiator", "confidence": 0.95,
                            "aliases": ["radiator"]},
                "תומך": {"english": "Support", "confidence": 0.95,
                         "aliases": ["support", "mount"]},
                "ת.מנוע": {"english": "Engine Mount", "confidence": 0.95,
                           "aliases": ["engine mount", "motor mount"]},
                "ת.משולש": {"english": "Control Arm Bushing", "confidence": 0.95,
                            "aliases": ["control arm bushing"]},
                "גומי": {"english": "Rubber", "confidence": 0.95, "aliases": ["rubber"]},
                "קפיץ": {"english": "Spring", "confidence": 0.95, "aliases": ["spring"]},
                "מ.מים": {"english": "Water Pump", "confidence": 0.95,
                          "aliases": ["water pump"]},
                "קולר": {"english": "Cooler", "confidence": 0.95, "aliases": ["cooler"]},
                "מ.דלק": {"english": "Fuel Pump", "confidence": 0.95,
                          "aliases": ["fuel pump"]},
                "מ.מייצב": {"english": "Stabilizer Link", "confidence": 0.95,
                            "aliases": ["stabilizer link"]},
                "צינור": {"english": "Pipe", "confidence": 0.95,
                          "aliases": ["pipe", "hose"]},
                "צינור מים": {"english": "Water Pipe", "confidence": 0.95,
                              "aliases": ["water pipe", "water hose"]},
                "צלב": {"english": "Universal Joint", "confidence": 0.95,
                        "aliases": ["universal joint", "u-joint"]},
                "יוניט": {"english": "Unit", "confidence": 0.95,
                          "aliases": ["unit", "sensor"]},
                "יוניט חום": {"english": "Temperature Sensor", "confidence": 0.95,
                              "aliases": ["temperature sensor", "temp sensor"]},
                "יוניט שמן": {"english": "Oil Pressure Sensor", "confidence": 0.95,
                              "aliases": ["oil pressure sensor"]},
                "יוניט בלם": {"english": "Brake Switch", "confidence": 0.95,
                              "aliases": ["brake light switch"]},
                "ציריה": {"english": "CV Axle", "confidence": 0.95,
                          "aliases": ["cv axle", "drive shaft"]},
                "פעמון צריה": {"english": "CV Boot", "confidence": 0.95,
                               "aliases": ["cv boot"]},
                "בוקסה": {"english": "Bushing", "confidence": 0.95,
                          "aliases": ["bushing"]},
                "גל": {"english": "Shaft", "confidence": 0.95, "aliases": ["shaft"]},
                "פ.שמן": {"english": "Oil Filter", "confidence": 0.95,
                          "aliases": ["פילטר שמן", "מסנן שמן", "oil filter"]},
                "פ.דלק": {"english": "Fuel Filter", "confidence": 0.95,
                          "aliases": ["פילטר דלק", "מסנן דלק", "fuel filter"]},
                "פ.מזגן": {"english": "AC Filter", "confidence": 0.95,
                           "aliases": ["פילטר מזגן", "מסנן מזגן", "ac filter",
                                       "cabin filter"]},
                "פ.סולר": {"english": "Diesel Filter", "confidence": 0.95,
                           "aliases": ["פילטר סולר", "מסנן סולר", "diesel filter"]},
            },

            # Expert system rules for consistency checking
            "compatibility_rules": [
                {
                    "rule_name": "engine_displacement_validation",
                    "description": "Validates that engine displacement matches the model",
                    "condition": "engine_displacement AND car_model",
                    "validation_script": "validate_displacement_model_match"
                },
                {
                    "rule_name": "year_model_validation",
                    "description": "Validates that year range makes sense for the model",
                    "condition": "year_from AND car_model",
                    "validation_script": "validate_year_model_match"
                },
            ],

            "special_patterns": [
                # Complex patterns with regex
                {"name": "year_range",
                 "regex": r"(?:מ|מודל\s*|משנת\s*)(\d{2})[-\s]?(?:עד|ו|-)?\s*(?:שנת\s*)?(\d{2})?",
                 "description": "Year range with מ (from) and עד (to)"},
                {"name": "single_year", "regex": r"(?:שנת|מודל)\s*(\d{4}|\d{2})",
                 "description": "Single year specification"},
                {"name": "displacement", "regex": r"נפח\s*(\d+\.\d+|\d+)",
                 "description": "Engine displacement"},
                {"name": "specific_model", "regex": r"(?:דגם|מודל)\s*([A-Za-z0-9]+)",
                 "description": "Specific model code"},
                {"name": "wheel_drive", "regex": r"(4x4|4x2|2x4|AWD|RWD|FWD)",
                 "description": "Type of wheel drive"},
                # Additional patterns for complex automotive part descriptions
                {"name": "brake_disc_size", "regex": r"(\d{3})(?:\s*(?:מ\"מ|mm))",
                 "description": "Brake disc diameter in mm"},
                {"name": "thread_size", "regex": r"M(\d+)x(\d+\.?\d*)",
                 "description": "Thread size (e.g., M8x1.25)"},
                {"name": "part_dimensions",
                 "regex": r"(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*(?:[xX×]\s*(\d+(?:\.\d+)?))?",
                 "description": "Part dimensions"},
            ],

            "abbreviations": {
                "פ.": "פילטר",
                "ח.": "חיישן",
                "ת.": "תומך",
                "ג.": "גומי",
                "מ.": "משאבת",
            },

            "component_locations": {
                "קדמי": "Front",
                "אחורי": "Rear",
                "ימין": "Right",
                "שמאל": "Left",
                "עליון": "Upper",
                "תחתון": "Lower",
            },

            "engine_codes": {
                "CBZ": {"make": "Volkswagen", "displacement": "1.2",
                        "fuel_type": "Petrol", "years": [2009, 2015]},
                "CDA": {"make": "Volkswagen", "displacement": "1.8",
                        "fuel_type": "Petrol", "years": [2007, 2014]},
                "CJS": {"make": "Volkswagen", "displacement": "1.8",
                        "fuel_type": "Petrol", "years": [2013, 2020]},
                "CAX": {"make": "Volkswagen", "displacement": "1.4",
                        "fuel_type": "Petrol", "years": [2008, 2014]},
                "CAV": {"make": "Volkswagen", "displacement": "1.4",
                        "fuel_type": "Petrol", "years": [2007, 2012]},
                "BSE": {"make": "Volkswagen", "displacement": "1.6",
                        "fuel_type": "Petrol", "years": [2004, 2012]},
                "BTS": {"make": "Volkswagen", "displacement": "1.6",
                        "fuel_type": "Petrol", "years": [2004, 2010]},
                "CJZ": {"make": "Volkswagen", "displacement": "1.2",
                        "fuel_type": "Petrol", "years": [2013, 2018]},
                "TDI": {"make": "Volkswagen", "displacement": "Various",
                        "fuel_type": "Diesel", "years": [1995, 2023]},
            },

            # Part systems hierarchy for better categorization
            "systems_hierarchy": {
                "Engine": ["Air Intake", "Fuel System", "Cooling", "Lubrication",
                           "Exhaust", "Electrical"],
                "Transmission": ["Manual", "Automatic", "Clutch", "Driveshaft"],
                "Suspension": ["Shocks", "Springs", "Control Arms", "Stabilizers",
                               "Bushings"],
                "Brakes": ["Discs", "Pads", "Calipers", "Brake Lines", "ABS"],
                "Electrical": ["Battery", "Alternator", "Starter", "Lighting", "Sensors"],
                "Body": ["Exterior", "Interior", "Chassis", "Glass"],
                "HVAC": ["Heating", "Air Conditioning", "Ventilation"]
            },

            # Common error patterns and corrections
            "error_patterns": {
                "swapped_letters": ["פליטר/פילטר", "רדיטאור/רדיאטור"],
                "forgotten_spaces": ["מזדה3/מזדה 3", "פולו1.4/פולו 1.4"],
                "typos": ["סקדוה/סקודה", "קרולה/קורולה"]
            }
        }

        return base_kb

    def _build_lookup_dict(self, data_dict: Dict) -> Dict:
        """Build a lookup dictionary for efficient matching"""
        lookup = {}
        for key, value in data_dict.items():
            # Add the main key (normalized)
            lookup[self._normalize_text(key)] = value["english"]

            # Add all aliases (normalized)
            for alias in value.get("aliases", []):
                lookup[self._normalize_text(alias)] = value["english"]

        return lookup

    def _build_make_to_models_map(self) -> Dict[str, List[Dict]]:
        """Build a mapping from car makes to their models with additional details"""
        make_to_models = defaultdict(list)

        for model_name, model_data in self.knowledge_base["car_models"].items():
            if "make" in model_data:
                make = model_data["make"]
                english_model = model_data["english"]
                model_info = {
                    "name": english_model,
                    "hebrew_name": model_name,
                    "body_styles": model_data.get("body_styles", []),
                    "popular_years": model_data.get("popular_years", []),
                    "common_engines": model_data.get("common_engines", [])
                }
                make_to_models[make].append(model_info)

        return dict(make_to_models)

    def _build_abbreviations_map(self) -> Dict[str, str]:
        """Build a map of known abbreviations"""
        return self.knowledge_base["abbreviations"]

    def _build_common_mistakes_map(self) -> Dict[str, str]:
        """Build a map of common mistakes and their corrections"""
        mistakes_map = {}

        # Add direct mappings from knowledge base
        for error_type, error_pairs in self.knowledge_base.get("error_patterns",
                                                               {}).items():
            for pair in error_pairs:
                if "/" in pair:
                    mistake, correction = pair.split("/")
                    mistakes_map[mistake] = correction

        # Add common typos based on keyboard proximity and phonetic similarity
        mistakes_map.update({
            "פילתר": "פילטר",
            "פליטר": "פילטר",
            "רדיטאור": "רדיאטור",
            "דיסקות": "דסקיות",
            "דיסקים": "דסקיות",
            "בולים": "בולם",
            "היונדאי": "יונדאי"
        })

        return mistakes_map

    def _build_compatibility_map(self) -> Dict:
        """Build a compatibility map for validating part-vehicle relationships"""
        compatibility = {}

        # Extract compatibility rules from knowledge base
        for rule in self.knowledge_base.get("compatibility_rules", []):
            compatibility[rule["rule_name"]] = rule

        # Build model year ranges
        compatibility["model_years"] = {}
        for model_name, model_data in self.knowledge_base["car_models"].items():
            if "make" in model_data and "popular_years" in model_data and len(
                    model_data["popular_years"]) >= 2:
                make = model_data["make"]
                model = model_data["english"]
                year_range = model_data["popular_years"]
                compatibility["model_years"][(make, model)] = (
                min(year_range), max(year_range))

        # Build engine displacement by model
        compatibility["model_engines"] = {}
        for model_name, model_data in self.knowledge_base["car_models"].items():
            if "make" in model_data and "common_engines" in model_data:
                make = model_data["make"]
                model = model_data["english"]
                engines = model_data["common_engines"]
                compatibility["model_engines"][(make, model)] = engines

        return compatibility

    def _compile_part_patterns(self) -> List[PartPattern]:
        """Compile regex patterns for part identification with validation functions"""
        patterns = []

        # Add patterns for special cases from knowledge base
        for pattern_data in self.knowledge_base.get("special_patterns", []):
            patterns.append(PartPattern(
                name=pattern_data["name"],
                regex=pattern_data["regex"],
                priority=7,  # Higher priority for special patterns
                validation_func=self._get_validation_func(pattern_data["name"])
            ))

        # Year patterns (high priority)
        patterns.append(PartPattern(
            name="year_from_to",
            regex=r"(?:מ|מודל|משנת)[-\s]?(\d{2,4})[-\s]?(?:עד|ו|-)[-\s]?(?:שנת)?(\d{2,4})?",
            priority=8,
            validation_func=self._validate_year_range
        ))
        patterns.append(PartPattern(
            name="year_from",
            regex=r"(?:מ)(\d{2})",
            priority=8,
            validation_func=self._validate_year
        ))
        patterns.append(PartPattern(
            name="year_to",
            regex=r"(?:עד)[-\s]?(\d{2})",
            priority=8,
            validation_func=self._validate_year
        ))

        # Engine displacement (high priority)
        patterns.append(PartPattern(
            name="engine_displacement",
            regex=r"(?:נפח\s*)?(\d+\.\d+)(?:\s*ליטר)?",
            priority=7,
            validation_func=self._validate_displacement
        ))

        # Car make + model patterns (medium-high priority)
        for make_heb, make_data in self.knowledge_base["car_makes"].items():
            eng_make = make_data["english"]
            patterns.append(PartPattern(
                name=f"make_{eng_make}",
                regex=fr"\b{re.escape(make_heb)}\b",
                priority=6
            ))

            # Also look for English make names
            patterns.append(PartPattern(
                name=f"make_eng_{eng_make}",
                regex=fr"\b{re.escape(eng_make.lower())}\b",
                priority=6
            ))

            # For each make, add its models with more context
            for model_heb, model_data in self.knowledge_base["car_models"].items():
                if model_data.get("make") == eng_make:
                    eng_model = model_data["english"]
                    # Pattern for "make model" like "מזדה 3"
                    patterns.append(PartPattern(
                        name=f"model_{eng_make}_{eng_model}",
                        regex=fr"\b{re.escape(make_heb)}\s*\d*\s*{re.escape(model_heb)}\b",
                        priority=7,
                        validation_func=lambda m, make=eng_make,
                                               model=eng_model: self._validate_make_model_pair(
                            m, make, model)
                    ))
                    # Pattern for standalone model
                    patterns.append(PartPattern(
                        name=f"model_{eng_model}",
                        regex=fr"\b{re.escape(model_heb)}\b",
                        priority=5
                    ))

        # Look for engine codes (high priority)
        for code, code_data in self.knowledge_base["engine_codes"].items():
            patterns.append(PartPattern(
                name=f"engine_code_{code}",
                regex=fr"\b{re.escape(code)}\b",
                priority=7,
                validation_func=lambda m, engine_code=code: self._validate_engine_code(m,
                                                                                       engine_code)
            ))
        # Part category patterns (medium priority)
        for category_heb, category_data in self.knowledge_base["part_categories"].items():
            eng_category = category_data["english"]
            patterns.append(PartPattern(
                name=f"category_{eng_category}",
                regex=fr"\b{re.escape(category_heb)}\b",
                priority=6
            ))

            # Add subcategory patterns if applicable
            if "subcategories" in category_data:
                for subcategory in category_data["subcategories"]:
                    subcat_pattern = fr"\b{re.escape(category_heb)}\s+{re.escape(subcategory)}\b"
                    patterns.append(PartPattern(
                        name=f"category_{eng_category}_{subcategory}",
                        regex=subcat_pattern,
                        priority=7
                    ))

        # Add common 4x4, 4x2 patterns (medium priority)
        patterns.append(PartPattern(
            name="drive_type",
            regex=r"\b(4x4|4x2|2x4|AWD|RWD|FWD)\b",
            priority=6
        ))

        # Add location patterns (front, rear, etc.)
        for loc_heb, loc_eng in self.knowledge_base["component_locations"].items():
            patterns.append(PartPattern(
                name=f"location_{loc_eng}",
                regex=fr"\b{re.escape(loc_heb)}\b",
                priority=5
            ))

        # I-model patterns for Hyundai (high priority)
        patterns.append(PartPattern(
            name="hyundai_i_models",
            regex=r"\b(I|i)(\d{1,2})\b",
            priority=7,
            validation_func=self._validate_hyundai_i_model
        ))

        # Special part patterns
        patterns.append(PartPattern(
            name="filter_abbreviation",
            regex=r"\bפ\.(אויר|שמן|דלק|מזגן|סולר)\b",
            priority=7
        ))

        # Complex part type identification patterns
        patterns.append(PartPattern(
            name="brake_components",
            regex=r"\b(רפידות|דסקיות|צלחות|בלמים)\b",
            priority=5
        ))

        patterns.append(PartPattern(
            name="engine_components",
            regex=r"\b(אטם ראש|טיימינג|שרשרת|רצועת|מסנן שמן|מנוע)\b",
            priority=5
        ))

        patterns.append(PartPattern(
            name="suspension_components",
            regex=r"\b(בולם|קפיץ|משולש|זרוע|מייצב|תומך)\b",
            priority=5
        ))

        # Add technical specifications patterns
        patterns.append(PartPattern(
            name="dimensions",
            regex=r"(\d+(?:\.\d+)?)[\s]*[xX×][\s]*(\d+(?:\.\d+)?)(?:[\s]*[xX×][\s]*(\d+(?:\.\d+)?))?",
            priority=6
        ))

        patterns.append(PartPattern(
            name="part_number",
            regex=r"\b([A-Z0-9]{3,}[-]?[A-Z0-9]{3,})\b",
            priority=6
        ))

        return patterns

    def _get_validation_func(self, pattern_name):
        """Get the appropriate validation function for a pattern"""
        validation_funcs = {
            "year_range": self._validate_year_range,
            "single_year": self._validate_year,
            "displacement": self._validate_displacement,
            "specific_model": self._validate_model_code,
            "wheel_drive": self._validate_drive_type,
            "brake_disc_size": self._validate_brake_disc_size,
            "thread_size": None,  # No specific validation needed
            "part_dimensions": None  # No specific validation needed
        }

        return validation_funcs.get(pattern_name)

    def _validate_year_range(self, match):
        """Validate that a year range is reasonable"""
        try:
            year1 = int(match.group(1))
            year2 = match.group(2)
            year2 = int(year2) if year2 else None

            # Convert 2-digit years to 4-digit
            if year1 < 100:
                year1 = 2000 + year1 if year1 < 50 else 1900 + year1

            if year2 and year2 < 100:
                year2 = 2000 + year2 if year2 < 50 else 1900 + year2

            # Basic validation
            current_year = datetime.now().year
            if year1 < 1930 or year1 > current_year + 5:
                return False

            if year2 and (year2 < year1 or year2 > current_year + 5):
                return False

            return True
        except:
            return False

    def _validate_year(self, match):
        """Validate that a year is reasonable"""
        try:
            year = int(match.group(1))
            if year < 100:
                year = 2000 + year if year < 50 else 1900 + year

            current_year = datetime.now().year
            return 1930 <= year <= current_year + 5
        except:
            return False

    def _validate_displacement(self, match):
        """Validate that an engine displacement is reasonable"""
        try:
            displacement = float(match.group(1))
            # Most car engines are between 0.6 and 8.0 liters
            return 0.6 <= displacement <= 8.0
        except:
            return False

    def _validate_model_code(self, match):
        """Validate that a model code follows typical patterns"""
        code = match.group(1)
        # Most model codes are 3-10 characters with letters and numbers
        return 3 <= len(code) <= 10 and re.match(r'^[A-Z0-9]+$', code)

    def _validate_drive_type(self, match):
        """Validate that a drive type is one of the known types"""
        drive_type = match.group(1).upper()
        return drive_type in ["4X4", "4X2", "2X4", "AWD", "RWD", "FWD"]

    def _validate_make_model_pair(self, match, make, model):
        """Validate that a make-model pair is valid"""
        for model_info in self.car_make_to_models.get(make, []):
            if model_info['name'] == model:
                return True
        return False

    def _validate_engine_code(self, match, code):
        """Validate that an engine code is known"""
        return code in self.knowledge_base["engine_codes"]

    def _validate_hyundai_i_model(self, match):
        """Validate that a Hyundai i-model is legitimate"""
        model_num = int(match.group(2))
        # Hyundai has models from i10 to i40
        return 10 <= model_num <= 40

    def _validate_brake_disc_size(self, match):
        """Validate that a brake disc size is reasonable"""
        try:
            size = int(match.group(1))
            # Most brake discs are between 220mm and 405mm
            return 220 <= size <= 405
        except:
            return False

    def _ensure_database_exists(self):
        """Ensure the SQLite database exists and has the correct schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if parts table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='parts'")
        if not cursor.fetchone():
            # Create parts table with enhanced schema
            cursor.execute('''
            CREATE TABLE parts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                part_name TEXT NOT NULL,
                part_name_normalized TEXT,
                car_make TEXT,
                car_model TEXT,
                year_from INTEGER,
                year_to INTEGER,
                category TEXT,
                category_specific TEXT,
                engine_code TEXT,
                engine_displacement TEXT,
                location TEXT,
                side TEXT,
                drive_type TEXT,
                dimensions TEXT,
                part_number TEXT,
                technical_specs TEXT,
                compatibility TEXT,
                additional_info TEXT,
                confidence_score REAL,
                confidence_factors TEXT,
                extraction_method TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # Create indexes for efficient searching
            cursor.execute(
                "CREATE INDEX idx_parts_make_model ON parts(car_make, car_model)")
            cursor.execute("CREATE INDEX idx_parts_category ON parts(category)")
            cursor.execute("CREATE INDEX idx_parts_years ON parts(year_from, year_to)")
            cursor.execute("CREATE INDEX idx_parts_part_number ON parts(part_number)")

            # Create feedback table for tracking user corrections
            cursor.execute('''
            CREATE TABLE feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                part_id INTEGER,
                field_name TEXT,
                original_value TEXT,
                corrected_value TEXT,
                feedback_type TEXT,
                confidence_impact REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (part_id) REFERENCES parts(id)
            )
            ''')

            logger.info("Created new parts database with enhanced schema")

        conn.commit()
        conn.close()

    def _normalize_text(self, text: str) -> str:
        """Advanced text normalization for better matching"""
        if not text:
            return ""

        # Convert to lowercase
        normalized = text.lower()

        # Remove accents and diacritics
        normalized = ''.join(c for c in unicodedata.normalize('NFD', normalized)
                             if unicodedata.category(c) != 'Mn')

        # Normalize spaces and punctuation
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = re.sub(r'[^\w\s.]', ' ', normalized)

        # Expand abbreviations
        for abbr, full in self.known_abbreviations.items():
            normalized = re.sub(fr'\b{re.escape(abbr)}\b', full, normalized)

        # Correct common mistakes
        for mistake, correction in self.common_mistakes.items():
            normalized = normalized.replace(mistake, correction)

        # Handle number formats
        normalized = re.sub(r'(\d),(\d)', r'\1\2',
                            normalized)  # Remove thousand separators

        # Process with NLP for tokenization if available
        if self.nlp:
            try:
                doc = self.nlp(normalized)
                tokens = [token.text for token in doc]
                normalized = ' '.join(tokens)
            except:
                pass

        return normalized.strip()

    def _extract_year(self, text: str) -> Tuple[Optional[int], Optional[int]]:
        """Extract years from the part description with advanced validation"""
        year_from = None
        year_to = None

        # Look for year range pattern "מYY-עדYY"
        range_match = re.search(r'מ(\d{2,4})(?:\s*-\s*|\s*עד\s*)(\d{2,4})', text)
        if range_match:
            year_from_raw = range_match.group(1)
            year_to_raw = range_match.group(2)

            year_from = int(year_from_raw)
            year_to = int(year_to_raw)

            # Convert 2-digit years to 4-digit
            if year_from < 100:
                year_from = 2000 + year_from if year_from < 50 else 1900 + year_from

            if year_to < 100:
                year_to = 2000 + year_to if year_to < 50 else 1900 + year_to
        else:
            # Look for "מ" (from) year pattern
            from_match = re.search(r'מ(\d{2})', text)
            if from_match:
                year_from_short = int(from_match.group(1))
                # Decide if it's 19xx or 20xx
                year_from = 2000 + year_from_short if year_from_short < 50 else 1900 + year_from_short

            # Look for "עד" (until) year pattern
            to_match = re.search(r'עד\s*(\d{2})', text)
            if to_match:
                year_to_short = int(to_match.group(1))
                # Decide if it's 19xx or 20xx
                year_to = 2000 + year_to_short if year_to_short < 50 else 1900 + year_to_short

        # Validate years
        current_year = datetime.now().year
        if year_from and (year_from < 1950 or year_from > current_year + 5):
            year_from = None
        if year_to and (year_to < 1950 or year_to > current_year + 5):
            year_to = None

        # If only to_year is specified, assume from_year is some reasonable past
        if year_to and not year_from:
            year_from = year_to - 15

        # Ensure year_from < year_to
        if year_from and year_to and year_from > year_to:
            year_from, year_to = year_to, year_from

        return year_from, year_to

    def _extract_car_make(self, text: str) -> Tuple[Optional[str], float, str]:
        """Extract car make with confidence score and extraction method"""
        normalized_text = self._normalize_text(text)

        # First try exact matches with higher confidence
        for term in normalized_text.split():
            if term in self.car_makes_dict:
                return self.car_makes_dict[term], 0.95, "exact_match"

        # Try the text as a whole (for multi-word makes)
        if normalized_text in self.car_makes_dict:
            return self.car_makes_dict[normalized_text], 0.9, "exact_match"

        # Try window-based approach
        words = normalized_text.split()
        for i in range(len(words)):
            for j in range(i + 1, min(i + 4, len(words) + 1)):
                phrase = " ".join(words[i:j])
                if phrase in self.car_makes_dict:
                    return self.car_makes_dict[phrase], 0.85, "phrase_match"

        # NLP-based extraction if spaCy is available
        if HAVE_SPACY and self.nlp and HAVE_HEBREW_NLP:
            try:
                doc = self.nlp(normalized_text)
                for ent in doc.ents:
                    if ent.label_ in ["ORG",
                                      "PRODUCT"]:  # Organizations or products in spaCy often include car manufacturers
                        ent_text = ent.text.lower()
                        # Check if this entity matches any known make
                        for make_term, make in self.car_makes_dict.items():
                            if make_term in ent_text or ent_text in make_term:
                                return make, 0.8, "nlp_entity"
            except:
                pass

        # Next try pattern-based extraction for makes
        for pattern in self.part_patterns:
            if pattern.name.startswith("make_"):
                match = pattern.match(text)
                if match:
                    make_name = pattern.name.replace("make_", "").replace("eng_", "")
                    return make_name, 0.9, "pattern_match"

        # Check for models to infer makes
        for pattern in self.part_patterns:
            if pattern.name.startswith("model_") and len(pattern.name.split("_")) > 2:
                match = pattern.match(text)
                if match:
                    parts = pattern.name.split("_")
                    make = parts[1]
                    return make, 0.8, "inferred_from_model"

        # Try fuzzy matching based on model if we have one
        for model_term, model in self.car_models_dict.items():
            if model_term in normalized_text:
                # Find the make for this model
                for model_data in self.knowledge_base["car_models"].values():
                    if model_data["english"] == model and "make" in model_data:
                        return model_data["make"], 0.75, "inferred_from_model_match"

        # Word embedding similarity if Word2Vec is available
        if HAVE_WORD2VEC and self.word2vec is not None:
            try:
                # Calculate average embedding for the text
                words = normalized_text.split()
                if words:
                    vectors = []
                    for word in words:
                        if word in self.word2vec.wv:
                            vectors.append(self.word2vec.wv[word])

                    if vectors and HAVE_NUMPY:
                        import numpy as np
                        avg_vector = np.mean(vectors, axis=0)

                        # Find the most similar car make
                        best_similarity = -1
                        best_make = None

                        for make_term, make in self.car_makes_dict.items():
                            if make_term in self.word2vec.wv:
                                similarity = np.dot(avg_vector,
                                                    self.word2vec.wv[make_term]) / (
                                                     np.linalg.norm(
                                                         avg_vector) * np.linalg.norm(
                                                 self.word2vec.wv[make_term])
                                             )
                                if similarity > best_similarity and similarity > 0.7:  # Threshold
                                    best_similarity = similarity
                                    best_make = make

                        if best_make:
                            return best_make, best_similarity * 0.8, "word_embedding"
            except Exception as e:
                logger.debug(f"Word embedding extraction failed: {e}")

        return None, 0.0, "no_match"

    def _extract_car_model(self, text: str, car_make: Optional[str] = None) -> Tuple[
        Optional[str], float, str]:
        """Extract car model with confidence score and extraction method"""
        normalized_text = self._normalize_text(text)

        # First try pattern-based extraction
        for pattern in self.part_patterns:
            if pattern.name.startswith("model_"):
                match = pattern.match(text)
                if match:
                    parts = pattern.name.split("_")
                    if len(parts) > 2 and (not car_make or parts[1] == car_make):
                        return parts[2], 0.9, "pattern_match_with_make"
                    elif len(parts) == 2:
                        # For single model patterns, check if it matches the make if provided
                        model = parts[1]
                        if not car_make:
                            return model, 0.85, "pattern_match"
                        else:
                            # Verify this model belongs to the make
                            for model_info in self.car_make_to_models.get(car_make, []):
                                if model_info["name"] == model:
                                    return model, 0.9, "pattern_match_verified"

        # Check for Hyundai I/i models (very specific pattern)
        i_model_match = re.search(r'\b[Ii](\d{1,2})\b', text)
        if i_model_match and (not car_make or car_make == "Hyundai"):
            model_number = i_model_match.group(1)
            return f"i{model_number}", 0.95, "i_model_pattern"

        # Try direct lookup in the models dictionary filtered by make if provided
        for term in normalized_text.split():
            if term in self.car_models_dict:
                model = self.car_models_dict[term]
                # If make is provided, ensure the model belongs to that make
                if not car_make:
                    return model, 0.8, "direct_lookup"

                for model_info in self.car_make_to_models.get(car_make, []):
                    if model_info["name"] == model:
                        return model, 0.9, "direct_lookup_verified"

        # Try numeric model extraction if make is provided
        if car_make:
            # Find Hebrew representation of make
            heb_make = None
            for key, value in self.knowledge_base["car_makes"].items():
                if value["english"] == car_make:
                    heb_make = key
                    break

            if heb_make:
                # Look for patterns like "מזדה 3"
                model_match = re.search(fr"{re.escape(heb_make)}\s*(\d+)", text)
                if model_match:
                    return model_match.group(1), 0.85, "numeric_model_match"

        # Try window-based approach for multi-word models
        words = normalized_text.split()
        for i in range(len(words)):
            for j in range(i + 1, min(i + 4, len(words) + 1)):
                phrase = " ".join(words[i:j])
                if phrase in self.car_models_dict:
                    model = self.car_models_dict[phrase]
                    if not car_make:
                        return model, 0.8, "phrase_match"

                    for model_info in self.car_make_to_models.get(car_make, []):
                        if model_info["name"] == model:
                            return model, 0.9, "phrase_match_verified"

        # NLP-based extraction if spaCy is available
        if HAVE_SPACY and self.nlp and HAVE_HEBREW_NLP and car_make:
            try:
                doc = self.nlp(normalized_text)
                for ent in doc.ents:
                    if ent.label_ in [
                        "PRODUCT"]:  # Products in spaCy could include car models
                        ent_text = ent.text.lower()
                        # Check all models for this make
                        for model_info in self.car_make_to_models.get(car_make, []):
                            model_name = model_info["name"].lower()
                            hebrew_name = self._normalize_text(
                                model_info.get("hebrew_name", ""))

                            if model_name in ent_text or hebrew_name in ent_text:
                                return model_info["name"], 0.8, "nlp_entity"
            except:
                pass

        # Word embedding similarity if Word2Vec is available
        if car_make and HAVE_WORD2VEC and self.word2vec is not None and HAVE_NUMPY:
            try:
                import numpy as np
                # Get models for this make
                models_for_make = [info["name"].lower() for info in
                                   self.car_make_to_models.get(car_make, [])]
                hebrew_models = []

                for model_heb, model_data in self.knowledge_base["car_models"].items():
                    if model_data.get("make") == car_make:
                        hebrew_models.append(model_heb.lower())

                # Calculate average embedding for the text
                words = normalized_text.split()
                if words:
                    vectors = []
                    for word in words:
                        if word in self.word2vec.wv:
                            vectors.append(self.word2vec.wv[word])

                    if vectors:
                        avg_vector = np.mean(vectors, axis=0)

                        # Find the most similar model for this make
                        best_similarity = -1
                        best_model = None

                        # Check English model names
                        for model in models_for_make:
                            if model in self.word2vec.wv:
                                similarity = np.dot(avg_vector,
                                                    self.word2vec.wv[model]) / (
                                                     np.linalg.norm(
                                                         avg_vector) * np.linalg.norm(
                                                 self.word2vec.wv[model])
                                             )
                                if similarity > best_similarity and similarity > 0.7:
                                    best_similarity = similarity
                                    best_model = model

                        # Check Hebrew model names
                        for model_heb in hebrew_models:
                            if model_heb in self.word2vec.wv:
                                similarity = np.dot(avg_vector,
                                                    self.word2vec.wv[model_heb]) / (
                                                     np.linalg.norm(
                                                         avg_vector) * np.linalg.norm(
                                                 self.word2vec.wv[model_heb])
                                             )
                                if similarity > best_similarity and similarity > 0.7:
                                    best_similarity = similarity
                                    # Find the English name
                                    for m_heb, m_data in self.knowledge_base[
                                        "car_models"].items():
                                        if m_heb.lower() == model_heb and m_data.get(
                                                "make") == car_make:
                                            best_model = m_data["english"]
                                            break

                        if best_model:
                            return best_model, best_similarity * 0.8, "word_embedding"
            except Exception as e:
                logger.debug(f"Word embedding extraction failed: {e}")

        # If we have a make and haven't found a model yet, try most common models for this make
        if car_make:
            models = self.car_make_to_models.get(car_make, [])
            if models:
                # For now, return the first model with low confidence
                # In a real implementation, we'd use statistics to return the most common model
                return models[0]["name"], 0.3, "default_for_make"

        return None, 0.0, "no_match"

    def _extract_part_category(self, text: str) -> Tuple[
        Optional[str], Optional[str], float, str]:
        """Extract part category and specific subcategory with confidence score and method"""
        normalized_text = self._normalize_text(text)

        # Check for common abbreviations first - highest confidence
        for abbr_pattern, category in [
            (r'פ\.אויר', "Air Filter"),
            (r'פ\.שמן', "Oil Filter"),
            (r'פ\.דלק', "Fuel Filter"),
            (r'פ\.מזגן', "AC Filter"),
            (r'פ\.סולר', "Diesel Filter"),
        ]:
            if re.search(abbr_pattern, text):
                return "Filter", category, 0.95, "abbreviation_pattern"

        # Try direct lookup in categories dictionary
        for term in normalized_text.split():
            if term in self.part_categories_dict:
                category = self.part_categories_dict[term]
                # Check if there is a specific subcategory
                for cat_heb, cat_data in self.knowledge_base["part_categories"].items():
                    if cat_data["english"] == category and "subcategories" in cat_data:
                        for subcategory in cat_data["subcategories"]:
                            if subcategory.lower() in normalized_text:
                                return category, subcategory, 0.9, "direct_lookup_with_subcategory"
                return category, None, 0.9, "direct_lookup"

        # Try pattern-based category extraction
        for pattern in self.part_patterns:
            if pattern.name.startswith("category_"):
                match = pattern.match(text)
                if match:
                    category_parts = pattern.name.replace("category_", "").split("_")
                    if len(category_parts) == 2:
                        return category_parts[0], category_parts[
                            1], 0.9 * pattern.precision, "pattern_match_with_specific"
                    else:
                        return category_parts[
                            0], None, 0.9 * pattern.precision, "pattern_match"

        # Check specific component groups
        if re.search(r'\b(בולם|קפיץ|משולש|זרוע|מייצב)\b', normalized_text):
            return "Suspension", None, 0.85, "component_group_match"

        if re.search(r'\b(רפידות|דסקיות|צלחות|קליפר)\b', normalized_text):
            return "Brakes", None, 0.85, "component_group_match"

        if re.search(r'\b(אטם|טיימינג|שרשרת|רצועת|מסנן שמן|מנוע)\b', normalized_text):
            return "Engine", None, 0.85, "component_group_match"

        if re.search(r'\b(מזגן|מעבה|מאייד|מפוח)\b', normalized_text):
            return "Air Conditioning", None, 0.85, "component_group_match"

        # Try window-based approach for multi-word categories
        words = normalized_text.split()
        for i in range(len(words)):
            for j in range(i + 1, min(i + 4, len(words) + 1)):
                phrase = " ".join(words[i:j])
                if phrase in self.part_categories_dict:
                    return self.part_categories_dict[phrase], None, 0.8, "phrase_match"

        # Machine learning classification if available
        if HAVE_ML_MODELS and self.category_classifier and self.vectorizer:
            try:
                # Transform text to feature vector
                text_vector = self.vectorizer.transform([normalized_text])
                # Predict category
                category_probas = self.category_classifier.predict_proba(text_vector)[0]
                if max(category_probas) > 0.6:  # Minimum confidence threshold
                    category_idx = category_probas.argmax()
                    category = self.category_classifier.classes_[category_idx]
                    return category, None, max(category_probas), "ml_classification"
            except Exception as e:
                logger.debug(f"ML classification failed: {e}")

        # Word embedding similarity if Word2Vec is available
        if HAVE_WORD2VEC and self.word2vec is not None and HAVE_NUMPY:
            try:
                import numpy as np
                # Calculate average embedding for the text
                words = normalized_text.split()
                if words:
                    vectors = []
                    for word in words:
                        if word in self.word2vec.wv:
                            vectors.append(self.word2vec.wv[word])

                    if vectors:
                        avg_vector = np.mean(vectors, axis=0)

                        # Find the most similar category
                        best_similarity = -1
                        best_category = None

                        for cat_term, category in self.part_categories_dict.items():
                            if cat_term in self.word2vec.wv:
                                similarity = np.dot(avg_vector,
                                                    self.word2vec.wv[cat_term]) / (
                                                     np.linalg.norm(
                                                         avg_vector) * np.linalg.norm(
                                                 self.word2vec.wv[cat_term])
                                             )
                                if similarity > best_similarity and similarity > 0.7:
                                    best_similarity = similarity
                                    best_category = category

                        if best_category:
                            return best_category, None, best_similarity * 0.8, "word_embedding"
            except Exception as e:
                logger.debug(f"Word embedding extraction failed: {e}")

        return None, None, 0.0, "no_match"

    def _extract_location_and_side(self, text: str) -> Tuple[
        Optional[str], Optional[str], str]:
        """Extract component location (front/rear) and side (left/right) with method"""
        normalized_text = self._normalize_text(text)

        location_mapping = {
            "קדמי": "Front",
            "אחורי": "Rear",
            "עליון": "Upper",
            "תחתון": "Lower",
            "front": "Front",
            "rear": "Rear",
            "upper": "Upper",
            "lower": "Lower"
        }

        side_mapping = {
            "ימין": "Right",
            "שמאל": "Left",
            "right": "Right",
            "left": "Left"
        }

        location = None
        side = None
        method = "no_match"

        # Check for pattern matches first (more reliable)
        for pattern in self.part_patterns:
            if pattern.name.startswith("location_"):
                match = pattern.match(normalized_text)
                if match:
                    location = pattern.name.replace("location_", "")
                    method = "pattern_match"
                    break

        # If no pattern match, try direct text search
        if not location:
            for heb, eng in location_mapping.items():
                if heb in normalized_text:
                    location = eng
                    method = "direct_text_match"
                    break

        # Check side with direct text search
        for heb, eng in side_mapping.items():
            if heb in normalized_text:
                side = eng
                if method == "no_match":
                    method = "direct_text_match"
                break

        return location, side, method

    def _extract_engine_info(self, text: str) -> Tuple[Optional[str], Optional[str], str]:
        """Extract engine code and displacement with method"""
        normalized_text = self._normalize_text(text)

        # Try to find engine code
        engine_code = None
        engine_method = "no_match"

        # First try pattern-based extraction
        for pattern in self.part_patterns:
            if pattern.name.startswith("engine_code_"):
                match = pattern.match(normalized_text)
                if match:
                    engine_code = pattern.name.replace("engine_code_", "")
                    engine_method = "pattern_match"
                    break

        # If no pattern match, try direct text search
        if not engine_code:
            for code in self.knowledge_base["engine_codes"].keys():
                if code in normalized_text:
                    engine_code = code
                    engine_method = "direct_text_match"
                    break

        # Try to find displacement
        displacement_match = re.search(r'(?:נפח\s*)?(\d+\.\d+)(?:\s*ליטר)?',
                                       normalized_text)
        displacement = displacement_match.group(1) if displacement_match else None

        # If we have an engine code but no displacement, get it from knowledge base
        if engine_code and not displacement and engine_code in self.knowledge_base[
            "engine_codes"]:
            displacement = self.knowledge_base["engine_codes"][engine_code].get(
                "displacement")
            if displacement:
                engine_method = "inferred_from_code"

        return engine_code, displacement, engine_method

    def _extract_drive_type(self, text: str) -> Tuple[Optional[str], str]:
        """Extract drive type (4x4, 4x2, etc.) with method"""
        drive_match = re.search(r'\b(4x4|4x2|2x4|AWD|FWD|RWD)\b', text, re.IGNORECASE)
        if drive_match:
            return drive_match.group(1).upper(), "direct_text_match"
        return None, "no_match"

    def _extract_dimensions(self, text: str) -> Tuple[Optional[str], str]:
        """Extract part dimensions if mentioned"""
        dim_match = re.search(
            r'(\d+(?:\.\d+)?)[\s]*[xX×][\s]*(\d+(?:\.\d+)?)(?:[\s]*[xX×][\s]*(\d+(?:\.\d+)?))?',
            text)
        if dim_match:
            if dim_match.group(3):  # 3D dimensions
                return f"{dim_match.group(1)}x{dim_match.group(2)}x{dim_match.group(3)}", "direct_text_match"
            else:  # 2D dimensions
                return f"{dim_match.group(1)}x{dim_match.group(2)}", "direct_text_match"
        return None, "no_match"

    def _extract_part_number(self, text: str) -> Tuple[Optional[str], str]:
        """Extract potential part number or reference code"""
        # Look for typical part number patterns (alphanumeric with possible dashes)
        part_match = re.search(r'\b([A-Z0-9]{3,}[-]?[A-Z0-9]{3,})\b', text)
        if part_match:
            return part_match.group(1), "pattern_match"
        return None, "no_match"

    def _compute_confidence_score(self, extraction_results: Dict) -> Tuple[float, Dict]:
        """Compute overall confidence score based on individual extractions with detailed factors"""
        # Start with a base score
        base_score = 0.7
        confidence_factors = {}

        # Add weighted scores for each successful extraction
        weights = {
            "car_make": 0.6,
            "car_model": 0.5,
            "year_from": 0.4,
            "year_to": 0.3,
            "category": 0.5,
            "category_specific": 0.4,
            "engine_code": 0.4,
            "engine_displacement": 0.3,
            "location": 0.3,
            "side": 0.2,
            "drive_type": 0.3,
            "part_number": 0.5,
            "dimensions": 0.3
        }

        # Adjust weights based on extraction methods
        method_multipliers = {
            "exact_match": 1.0,
            "alias_match": 0.95,
            "pattern_match": 0.9,
            "pattern_match_with_make": 0.95,
            "pattern_match_with_specific": 0.95,
            "direct_text_match": 0.9,
            "direct_lookup": 0.9,
            "direct_lookup_verified": 0.95,
            "direct_lookup_with_subcategory": 0.95,
            "i_model_pattern": 0.95,
            "numeric_model_match": 0.9,
            "numeric_model_guess": 0.8,
            "make_model_sequence": 0.95,
            "phrase_match": 0.85,
            "phrase_match_verified": 0.95,
            "component_group_match": 0.85,
            "ml_classification": 0.9,
            "word_embedding": 0.85,
            "default_for_make": 0.7,
            "inferred_from_model": 0.75,
            "inferred_from_code": 0.85,
            "inferred_from_model_match": 0.8,
            "nlp_entity": 0.85,
            "abbreviation_pattern": 0.95,
            "no_match": 0.0
        }

        total_weight = sum(weights.values())
        weighted_score = 0

        for field, weight in weights.items():
            # For fields with extraction method
            method_field = f"{field}_method"
            confidence_field = f"{field}_confidence"

            if method_field in extraction_results and extraction_results.get(field):
                method = extraction_results[method_field]
                method_multiplier = method_multipliers.get(method, 0.7)

                if confidence_field in extraction_results:
                    confidence = extraction_results[confidence_field]
                else:
                    confidence = 0.8  # Default confidence if not specified

                field_score = weight * confidence * method_multiplier
                weighted_score += field_score
                confidence_factors[field] = {
                    "value": extraction_results[field],
                    "extraction_method": method,
                    "confidence": confidence,
                    "weight": weight,
                    "score_contribution": field_score / total_weight
                }
            # For binary values (present/not present)
            elif extraction_results.get(field):
                weighted_score += weight
                confidence_factors[field] = {
                    "value": extraction_results[field],
                    "extraction_method": "direct",
                    "weight": weight,
                    "score_contribution": weight / total_weight
                }

        # Check compatibility between extracted data points
        compatibility_bonus = 0
        compatibility_checks = []

        # 1. Check if make and model are compatible
        if extraction_results.get("car_make") and extraction_results.get("car_model"):
            make = extraction_results["car_make"]
            model = extraction_results["car_model"]
            is_compatible = False

            # Check if this is a known make-model combination
            for model_info in self.car_make_to_models.get(make, []):
                if model_info["name"] == model:
                    is_compatible = True
                    compatibility_bonus += 0.1
                    compatibility_checks.append({
                        "check": "make_model_compatibility",
                        "result": True,
                        "bonus": 0.1
                    })
                    break

            if not is_compatible:
                compatibility_checks.append({
                    "check": "make_model_compatibility",
                    "result": False,
                    "penalty": 0.2
                })
                weighted_score -= 0.2  # Penalty for incompatible make-model

        # 2. Check if year range is compatible with model
        if extraction_results.get("car_model") and extraction_results.get("year_from"):
            model = extraction_results["car_model"]
            year = extraction_results["year_from"]
            make = extraction_results.get("car_make")

            if make and (make, model) in self.part_compatibility.get("model_years", {}):
                model_year_range = self.part_compatibility["model_years"][(make, model)]
                if model_year_range[0] <= year <= model_year_range[1]:
                    compatibility_bonus += 0.1
                    compatibility_checks.append({
                        "check": "year_model_compatibility",
                        "result": True,
                        "bonus": 0.1
                    })
                else:
                    compatibility_checks.append({
                        "check": "year_model_compatibility",
                        "result": False,
                        "penalty": 0.1
                    })
                    weighted_score -= 0.1  # Smaller penalty for year discrepancy

        # 3. Check if engine displacement is compatible with model
        if extraction_results.get("car_model") and extraction_results.get(
                "engine_displacement"):
            model = extraction_results["car_model"]
            displacement = extraction_results["engine_displacement"]
            make = extraction_results.get("car_make")

            if make and (make, model) in self.part_compatibility.get("model_engines", {}):
                compatible_engines = self.part_compatibility["model_engines"][
                    (make, model)]
                if displacement in compatible_engines:
                    compatibility_bonus += 0.1
                    compatibility_checks.append({
                        "check": "engine_model_compatibility",
                        "result": True,
                        "bonus": 0.1
                    })
                else:
                    compatibility_checks.append({
                        "check": "engine_model_compatibility",
                        "result": False,
                        "penalty": 0.1
                    })
                    weighted_score -= 0.1  # Penalty for engine displacement discrepancy

        # Add compatibility results to confidence factors
        confidence_factors["compatibility_checks"] = compatibility_checks

        # Normalize to 0-1 range for the weighted component
        normalized_score = min(weighted_score / total_weight, 1.0)

        # Apply compatibility bonus (capped)
        normalized_score = min(normalized_score + compatibility_bonus, 1.0)

        # Combine with base score
        final_score = (base_score + normalized_score) / 2

        return round(final_score, 2), confidence_factors

    def parse_part_line(self, line: str) -> Dict:
        """Parse a single car part description line with enhanced accuracy"""
        if not line or not line.strip():
            return None

        line = line.strip()

        # Check if already in cache
        if line in self.extraction_cache:
            return self.extraction_cache[line]

        # Start with base structure
        result = {
            "part_name": line,
            "part_name_normalized": self._normalize_text(line),
            "car_make": None,
            "car_model": None,
            "year_from": None,
            "year_to": None,
            "category": None,
            "category_specific": None,
            "engine_code": None,
            "engine_displacement": None,
            "location": None,
            "side": None,
            "drive_type": None,
            "dimensions": None,
            "part_number": None,
            "technical_specs": None,
            "additional_info": None,
            "extraction_method": "enhanced_pattern_matching"
        }

        # Extract year range
        result["year_from"], result["year_to"] = self._extract_year(line)

        # Extract car make with confidence and method
        result["car_make"], result["car_make_confidence"], result[
            "car_make_method"] = self._extract_car_make(line)

        # Extract car model with confidence and method
        result["car_model"], result["car_model_confidence"], result[
            "car_model_method"] = self._extract_car_model(line, result["car_make"])

        # Extract part category with confidence and method
        result["category"], result["category_specific"], result["category_confidence"], \
        result["category_method"] = self._extract_part_category(line)

        # Extract location and side with method
        result["location"], result["side"], result[
            "location_method"] = self._extract_location_and_side(line)

        # Extract engine information with method
        result["engine_code"], result["engine_displacement"], result[
            "engine_code_method"] = self._extract_engine_info(line)

        # Extract drive type with method
        result["drive_type"], result["drive_type_method"] = self._extract_drive_type(line)

        # Extract dimensions with method
        result["dimensions"], result["dimensions_method"] = self._extract_dimensions(line)

        # Extract part number with method
        result["part_number"], result["part_number_method"] = self._extract_part_number(
            line)

        # Add technical specifications if we have engine or dimension data
        tech_specs = {}
        if result["engine_displacement"]:
            tech_specs["displacement"] = f"{result['engine_displacement']}L"
        if result["dimensions"]:
            tech_specs["dimensions"] = result["dimensions"]
        if result["drive_type"]:
            tech_specs["drive_type"] = result["drive_type"]

        if tech_specs:
            result["technical_specs"] = json.dumps(tech_specs)

        # Calculate confidence score with detailed factors
        result["confidence_score"], confidence_factors = self._compute_confidence_score(
            result)
        result["confidence_factors"] = json.dumps(confidence_factors)

        # Extract additional information
        # This is what's left after removing all the identified components
        extracted_info = []
        for field in ["car_make", "car_model", "category", "location", "side",
                      "engine_code", "drive_type"]:
            if result[field]:
                # For each field, find all possible Hebrew representations
                for heb_term, term_data in self.knowledge_base.get(f"{field}s",
                                                                   {}).items():
                    if term_data.get("english") == result[field]:
                        extracted_info.append(heb_term)
                        for alias in term_data.get("aliases", []):
                            extracted_info.append(alias)

        # Add year patterns
        if result["year_from"]:
            extracted_info.append(f"מ{result['year_from'] % 100}")
        if result["year_to"]:
            extracted_info.append(f"עד {result['year_to'] % 100}")

        # Remove extracted info from original text
        additional_info = line
        for info in extracted_info:
            additional_info = additional_info.replace(info, "")

        # Clean up
        additional_info = re.sub(r'\s+', ' ', additional_info).strip()
        if additional_info:
            result["additional_info"] = additional_info

        # Cache the result
        self.extraction_cache[line] = result

        return result

    def _save_knowledge_base(self):
        """Save the knowledge base to disk with updated statistics"""
        with open(self.knowledge_base_path, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_base, f, ensure_ascii=False, indent=2)
        logger.info(f"Knowledge base saved to {self.knowledge_base_path}")

    def import_car_parts(self, file_path: str, batch_size: int = 100) -> int:
        """Import car parts from a file with batched processing and enhanced learning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        count = 0
        skipped = 0
        batch = []

        # Collect text for ML training
        all_texts = []
        all_categories = []

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        part_data = self.parse_part_line(line)
                        if part_data:
                            # Prepare data for database insertion
                            batch.append((
                                part_data["part_name"],
                                part_data["part_name_normalized"],
                                part_data["car_make"],
                                part_data["car_model"],
                                part_data["year_from"],
                                part_data["year_to"],
                                part_data["category"],
                                part_data["category_specific"],
                                part_data["engine_code"],
                                part_data["engine_displacement"],
                                part_data["location"],
                                part_data["side"],
                                part_data["drive_type"],
                                part_data["dimensions"],
                                part_data["part_number"],
                                part_data["technical_specs"],
                                part_data.get("compatibility", None),
                                part_data["additional_info"],
                                part_data["confidence_score"],
                                part_data.get("confidence_factors", None),
                                part_data["extraction_method"]
                            ))

                            count += 1

                            # Collect data for ML training
                            all_texts.append(part_data["part_name_normalized"])
                            if part_data["category"]:
                                all_categories.append(part_data["category"])
                        else:
                            skipped += 1

                    # Process in batches for better performance
                    if len(batch) >= batch_size:
                        cursor.executemany('''
                        INSERT INTO parts (
                            part_name, part_name_normalized, car_make, car_model, year_from, year_to, 
                            category, category_specific, engine_code, engine_displacement, 
                            location, side, drive_type, dimensions, part_number, technical_specs,
                            compatibility, additional_info, confidence_score, confidence_factors,
                            extraction_method
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', batch)
                        conn.commit()
                        batch = []

            # Process remaining items
            if batch:
                cursor.executemany('''
                INSERT INTO parts (
                    part_name, part_name_normalized, car_make, car_model, year_from, year_to, 
                    category, category_specific, engine_code, engine_displacement, 
                    location, side, drive_type, dimensions, part_number, technical_specs,
                    compatibility, additional_info, confidence_score, confidence_factors,
                    extraction_method
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', batch)
                conn.commit()

            # Train or update ML models if we have the necessary libraries
            if HAVE_ML_MODELS:
                self._update_ml_models(all_texts, all_categories)

            logger.info(
                f"Successfully imported {count} car parts into the database. Skipped {skipped} invalid entries.")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error during import: {e}")
            raise
        finally:
            conn.close()

        return count

    def _update_ml_models(self, texts, categories):
        """Update ML models with new data if possible"""
        if not HAVE_ML_MODELS or not texts:
            return

        # Update TF-IDF vectorizer
        if self.vectorizer is None:
            self.vectorizer = self._create_new_vectorizer()

        if not hasattr(self.vectorizer,
                       'vocabulary_') or self.vectorizer.vocabulary_ is None:
            # First time training
            try:
                self.vectorizer.fit(texts)
                logger.info("Trained TF-IDF vectorizer on the dataset")
            except Exception as e:
                logger.warning(f"Failed to train vectorizer: {e}")

        # Train category classifier if we have enough labeled data
        if len(categories) > 50 and len(set(categories)) > 1:
            try:
                from sklearn.ensemble import RandomForestClassifier

                # Transform texts to feature vectors
                X = self.vectorizer.transform(texts)
                y = categories

                # Train a classifier
                self.category_classifier = RandomForestClassifier(n_estimators=100,
                                                                  random_state=42)
                self.category_classifier.fit(X, y)
                logger.info(
                    f"Trained category classifier on {len(categories)} labeled examples")
            except Exception as e:
                logger.warning(f"Failed to train category classifier: {e}")

        # Train Word2Vec model if available and we have enough data
        if HAVE_WORD2VEC and len(texts) > 100:
            try:
                from gensim.models import Word2Vec

                # Process texts into sentences
                sentences = [text.split() for text in texts if text]

                if not sentences:
                    return

                if self.word2vec is None:
                    # Train new model
                    self.word2vec = Word2Vec(sentences, vector_size=100, window=5,
                                             min_count=1, workers=4)
                    logger.info("Trained new Word2Vec model")
                else:
                    # Update existing model
                    self.word2vec.build_vocab(sentences, update=True)
                    self.word2vec.train(sentences, total_examples=len(sentences),
                                        epochs=5)
                    logger.info("Updated existing Word2Vec model")
            except Exception as e:
                logger.warning(f"Failed to train Word2Vec model: {e}")

        # Save the updated models
        self._save_ml_models()

    def _save_ml_models(self):
        """Save the ML models to disk"""
        if not HAVE_ML_MODELS:
            return

        try:
            import pickle
            # Save TF-IDF vectorizer
            if self.vectorizer and hasattr(self.vectorizer, 'vocabulary_'):
                vectorizer_path = os.path.join(self.model_dir, 'tfidf_vectorizer.pkl')
                with open(vectorizer_path, 'wb') as f:
                    pickle.dump(self.vectorizer, f)
                logger.info("Saved TF-IDF vectorizer")

            # Save category classifier if available
            if self.category_classifier:
                classifier_path = os.path.join(self.model_dir, 'category_classifier.pkl')
                with open(classifier_path, 'wb') as f:
                    pickle.dump(self.category_classifier, f)
                logger.info("Saved category classifier")

            # Save Word2Vec model if available
            if HAVE_WORD2VEC and self.word2vec:
                word2vec_path = os.path.join(self.model_dir, 'word2vec.model')
                self.word2vec.save(word2vec_path)
                logger.info("Saved Word2Vec model")

        except Exception as e:
            logger.error(f"Error saving ML models: {e}")

    def learn_from_feedback(self, part_id: int, corrections: Dict):
        """Learn from user corrections to improve future parsing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get the original part data
            cursor.execute("SELECT part_name, confidence_factors FROM parts WHERE id = ?",
                           (part_id,))
            result = cursor.fetchone()

            if result:
                original_part_name, confidence_factors_json = result

                # Update the database entry with corrections
                update_fields = []
                update_values = []

                for field, value in corrections.items():
                    if field in ["car_make", "car_model", "category", "category_specific",
                                 "year_from", "year_to", "engine_code",
                                 "engine_displacement",
                                 "location", "side", "drive_type", "dimensions",
                                 "part_number"]:
                        update_fields.append(f"{field} = ?")
                        update_values.append(value)

                        # Record the feedback for learning
                        cursor.execute('''
                        INSERT INTO feedback (part_id, field_name, original_value, corrected_value, feedback_type)
                        VALUES (?, ?, (SELECT ? FROM parts WHERE id = ?), ?, 'correction')
                        ''', (part_id, field, field, part_id, value))

                if update_fields:
                    # Add updated_at timestamp
                    update_fields.append("updated_at = CURRENT_TIMESTAMP")
                    update_fields.append("confidence_score = ?")
                    update_values.append(1.0)  # Perfect confidence for manual corrections

                    # Add extraction_method to indicate manual correction
                    update_fields.append("extraction_method = ?")
                    update_values.append("manual_correction")

                    # Update the row
                    cursor.execute(f'''
                    UPDATE parts 
                    SET {", ".join(update_fields)}
                    WHERE id = ?
                    ''', update_values + [part_id])

                    conn.commit()

                    # Update our knowledge base for future parsing
                    self._update_knowledge_base_from_feedback(original_part_name,
                                                              corrections,
                                                              confidence_factors_json)

                    logger.info(
                        f"Applied corrections to part ID {part_id} and updated knowledge base")

                    # Clear cache since our knowledge has improved
                    self.extraction_cache = {}

                    return True

            return False
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating from feedback: {e}")
            return False
        finally:
            conn.close()

    def _update_knowledge_base_from_feedback(self, part_name: str, corrections: Dict,
                                             confidence_factors_json: str = None):
        """Update knowledge base with corrections for improved future pattern recognition"""
        try:
            confidence_factors = json.loads(
                confidence_factors_json) if confidence_factors_json else {}
        except:
            confidence_factors = {}

        updated = False

        # Process make corrections
        if "car_make" in corrections and corrections["car_make"]:
            # Check if we already know about this make
            make_found = False
            for make_heb, make_data in self.knowledge_base["car_makes"].items():
                if make_data["english"] == corrections["car_make"]:
                    make_found = True
                    # Update confidence based on feedback
                    make_data["confidence"] = min(1.0, make_data["confidence"] + 0.05)
                    updated = True
                    break

            # If we don't know this make, add it
            if not make_found:
                self.knowledge_base["car_makes"][corrections["car_make"]] = {
                    "english": corrections["car_make"],
                    "confidence": 0.9,
                    "aliases": [corrections["car_make"].lower()],
                    "added_from_feedback": True
                }
                updated = True
                logger.info(
                    f"Added new car make to knowledge base: {corrections['car_make']}")

        # Process model corrections
        if "car_model" in corrections and corrections[
            "car_model"] and "car_make" in corrections:
            make = corrections["car_make"]
            model = corrections["car_model"]

            # Check if we already know about this model
            model_found = False
            for model_heb, model_data in self.knowledge_base["car_models"].items():
                if model_data["english"] == model and model_data.get("make") == make:
                    model_found = True
                    # Update confidence based on feedback
                    model_data["confidence"] = min(1.0, model_data["confidence"] + 0.05)
                    updated = True
                    break

            # If we don't know this model, add it
            if not model_found:
                # Use a transliteration of model as Hebrew key if we don't have the original
                heb_key = f"{model}_feedback"
                self.knowledge_base["car_models"][heb_key] = {
                    "english": model,
                    "confidence": 0.9,
                    "make": make,
                    "aliases": [model.lower()],
                    "added_from_feedback": True
                }
                updated = True
                logger.info(f"Added new car model to knowledge base: {make} {model}")

                # Also update the make-to-models mapping
                new_model_info = {
                    "name": model,
                    "hebrew_name": heb_key,
                    "added_from_feedback": True
                }

                if make in self.car_make_to_models:
                    self.car_make_to_models[make].append(new_model_info)
                else:
                    self.car_make_to_models[make] = [new_model_info]

        # Process category corrections
        if "category" in corrections and corrections["category"]:
            category = corrections["category"]

            # Check if we already know about this category
            category_found = False
            for cat_heb, cat_data in self.knowledge_base["part_categories"].items():
                if cat_data["english"] == category:
                    category_found = True
                    # Update confidence based on feedback
                    cat_data["confidence"] = min(1.0, cat_data["confidence"] + 0.05)
                    updated = True

                    # Update subcategory information if provided
                    if "category_specific" in corrections and corrections[
                        "category_specific"]:
                        specific = corrections["category_specific"]
                        if "subcategories" not in cat_data:
                            cat_data["subcategories"] = []
                        if specific not in cat_data["subcategories"]:
                            cat_data["subcategories"].append(specific)
                            logger.info(
                                f"Added new subcategory {specific} to category {category}")
                    break

            # If we don't know this category, add it
            if not category_found:
                # Use a transliteration of category as Hebrew key if we don't have the original
                heb_key = f"{category}_feedback"
                subcategories = []
                if "category_specific" in corrections and corrections[
                    "category_specific"]:
                    subcategories = [corrections["category_specific"]]

                self.knowledge_base["part_categories"][heb_key] = {
                    "english": category,
                    "confidence": 0.9,
                    "aliases": [category.lower()],
                    "subcategories": subcategories,
                    "added_from_feedback": True
                }
                updated = True
                logger.info(f"Added new part category to knowledge base: {category}")

        # Update pattern statistics based on feedback
        for pattern in self.part_patterns:
            pattern_field = None
            if pattern.name.startswith("make_") and "car_make" in corrections:
                pattern_field = "car_make"
            elif pattern.name.startswith("model_") and "car_model" in corrections:
                pattern_field = "car_model"
            elif pattern.name.startswith("category_") and "category" in corrections:
                pattern_field = "category"

            if pattern_field:
                for field_info in confidence_factors.get(pattern_field, {}).values():
                    if field_info.get(
                            "extraction_method") == "pattern_match" and field_info.get(
                            "value") != corrections[pattern_field]:
                        pattern.false_positive_count += 1
                        updated = True

        # If we made updates, save the knowledge base and rebuild our lookups
        if updated:
            self._save_knowledge_base()

            # Rebuild lookups
            self.car_makes_dict = self._build_lookup_dict(
                self.knowledge_base["car_makes"])
            self.car_models_dict = self._build_lookup_dict(
                self.knowledge_base["car_models"])
            self.part_categories_dict = self._build_lookup_dict(
                self.knowledge_base["part_categories"])

    def get_statistics(self):
        """Get comprehensive statistics about the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {
            "total_parts": 0,
            "parts_by_make": {},
            "parts_by_model": {},
            "parts_by_category": {},
            "parts_by_year": {},
            "confidence_distribution": {
                "high": 0,  # 0.8-1.0
                "medium": 0,  # 0.5-0.79
                "low": 0  # <0.5
            },
            "extraction_methods": {},
            "common_combinations": {
                "make_model": [],
                "model_category": [],
                "make_category": []
            },
            "part_categories_hierarchy": {},
            "feedback_stats": {
                "total_corrections": 0,
                "corrections_by_field": {},
                "model_performance": {}
            }
        }

        # Total parts
        cursor.execute("SELECT COUNT(*) FROM parts")
        stats["total_parts"] = cursor.fetchone()[0]

        # Parts by make
        cursor.execute("""
        SELECT car_make, COUNT(*) as count 
        FROM parts 
        WHERE car_make IS NOT NULL 
        GROUP BY car_make 
        ORDER BY count DESC
        LIMIT 20
        """)
        stats["parts_by_make"] = {row[0]: row[1] for row in cursor.fetchall()}

        # Parts by model
        cursor.execute("""
        SELECT car_make, car_model, COUNT(*) as count 
        FROM parts 
        WHERE car_make IS NOT NULL AND car_model IS NOT NULL
        GROUP BY car_make, car_model 
        ORDER BY count DESC
        LIMIT 20
        """)
        stats["parts_by_model"] = {f"{row[0]} {row[1]}": row[2] for row in
                                   cursor.fetchall()}

        # Parts by category
        cursor.execute("""
        SELECT category, COUNT(*) as count 
        FROM parts 
        WHERE category IS NOT NULL 
        GROUP BY category 
        ORDER BY count DESC
        LIMIT 20
        """)
        stats["parts_by_category"] = {row[0]: row[1] for row in cursor.fetchall()}

        # Parts by decade
        cursor.execute("""
        SELECT 
            CASE 
                WHEN year_from IS NULL THEN 'Unknown'
                WHEN year_from < 1990 THEN 'Before 1990'
                WHEN year_from < 2000 THEN '1990s'
                WHEN year_from < 2010 THEN '2000s'
                WHEN year_from < 2020 THEN '2010s'
                ELSE '2020s and newer'
            END as decade,
            COUNT(*) as count
        FROM parts
        GROUP BY decade
        ORDER BY decade
        """)
        stats["parts_by_year"] = {row[0]: row[1] for row in cursor.fetchall()}

        # Confidence distribution
        cursor.execute("""
        SELECT 
            CASE 
                WHEN confidence_score >= 0.8 THEN 'high'
                WHEN confidence_score >= 0.5 THEN 'medium'
                ELSE 'low'
            END as confidence_level,
            COUNT(*) as count
        FROM parts
        GROUP BY confidence_level
        """)

        for row in cursor.fetchall():
            stats["confidence_distribution"][row[0]] = row[1]

        # Extraction methods
        cursor.execute("""
        SELECT extraction_method, COUNT(*) as count
        FROM parts
        GROUP BY extraction_method
        ORDER BY count DESC
        """)
        stats["extraction_methods"] = {row[0]: row[1] for row in cursor.fetchall()}

        # Check if feedback table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='feedback'")
        has_feedback_table = cursor.fetchone() is not None

        if has_feedback_table:
            # Feedback statistics
            cursor.execute("SELECT COUNT(*) FROM feedback")
            stats["feedback_stats"]["total_corrections"] = cursor.fetchone()[0]

            cursor.execute("""
            SELECT field_name, COUNT(*) as count
            FROM feedback
            WHERE feedback_type = 'correction'
            GROUP BY field_name
            ORDER BY count DESC
            """)
            stats["feedback_stats"]["corrections_by_field"] = {row[0]: row[1] for row in
                                                               cursor.fetchall()}

        conn.close()
        return stats