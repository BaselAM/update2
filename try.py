import os
import sqlite3
import re
import time
import unicodedata
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import json


class AdvancedCarPartExtractor:
    """Advanced car parts extractor specifically optimized for btw_filenames.txt"""

    def __init__(self):
        """Initialize knowledge base and patterns for Hebrew car part descriptions"""
        # Car makes mapping (Hebrew to English)
        self.car_makes = {
            "מזדה": "Mazda", "טויוטה": "Toyota", "יונדאי": "Hyundai",
            "קיה": "Kia", "סקודה": "Skoda", "פורד": "Ford",
            "סוזוקי": "Suzuki", "ניסאן": "Nissan", "הונדה": "Honda",
            "מיצובישי": "Mitsubishi", "ב.מ.וו": "BMW", "רנו": "Renault",
            "פיג'ו": "Peugeot", "סיטרואן": "Citroen", "אאודי": "Audi",
            "מרצדס": "Mercedes", "פולקסווגן": "Volkswagen", "סובארו": "Subaru",
            "דייהטסו": "Daihatsu", "שברולט": "Chevrolet", "אופל": "Opel",
            "איסוזו": "Isuzu", "לנדרובר": "Land Rover", "לקסוס": "Lexus",
            "וולוו": "Volvo", "פיאט": "Fiat", "אלפא רומאו": "Alfa Romeo",
            "דודג": "Dodge", "סאנגיונג": "SsangYong", "מאזדה": "Mazda"
        }

        # Car models mapping with their makes
        self.car_models = {
            "קורולה": {"english": "Corolla", "make": "Toyota"},
            "אוקטביה": {"english": "Octavia", "make": "Skoda"},
            "פביה": {"english": "Fabia", "make": "Skoda"},
            "פוקוס": {"english": "Focus", "make": "Ford"},
            "אקסנט": {"english": "Accent", "make": "Hyundai"},
            "לנסר": {"english": "Lancer", "make": "Mitsubishi"},
            "גולף": {"english": "Golf", "make": "Volkswagen"},
            "פולו": {"english": "Polo", "make": "Volkswagen"},
            "ראב 4": {"english": "RAV4", "make": "Toyota"},
            "קרוז": {"english": "Cruze", "make": "Chevrolet"},
            "לאון": {"english": "Leon", "make": "Seat"},
            "קודיאק": {"english": "Kodiaq", "make": "Skoda"},
            "סנטה פה": {"english": "Santa Fe", "make": "Hyundai"},
            "טוסון": {"english": "Tucson", "make": "Hyundai"},
            "סורנטו": {"english": "Sorento", "make": "Kia"},
            "ספורטאג": {"english": "Sportage", "make": "Kia"},
            "קנגו": {"english": "Kangoo", "make": "Renault"},
            "מגאן": {"english": "Megane", "make": "Renault"},
            "קליאו": {"english": "Clio", "make": "Renault"},
            "לוגן": {"english": "Logan", "make": "Dacia"},
            "ג'טה": {"english": "Jetta", "make": "Volkswagen"},
            "פסאט": {"english": "Passat", "make": "Volkswagen"},
            "קורסה": {"english": "Corsa", "make": "Opel"},
            "אסטרה": {"english": "Astra", "make": "Opel"},
            "איביזה": {"english": "Ibiza", "make": "Seat"},
            "טוארג": {"english": "Touareg", "make": "Volkswagen"},
            "טיגואן": {"english": "Tiguan", "make": "Volkswagen"},
            "סיויק": {"english": "Civic", "make": "Honda"},
            "מזדה 3": {"english": "Mazda3", "make": "Mazda"},
            "מזדה 6": {"english": "Mazda6", "make": "Mazda"},
            "מזדה 5": {"english": "Mazda5", "make": "Mazda"},
            "מזדה 2": {"english": "Mazda2", "make": "Mazda"},
            "CX5": {"english": "CX-5", "make": "Mazda"},
            "SX4": {"english": "SX4", "make": "Suzuki"},
            "יאריס": {"english": "Yaris", "make": "Toyota"},
            "אייגו": {"english": "Aygo", "make": "Toyota"},
            "קאמרי": {"english": "Camry", "make": "Toyota"},
            "אוונסיס": {"english": "Avensis", "make": "Toyota"},
            "סוויפט": {"english": "Swift", "make": "Suzuki"},
            "אלטו": {"english": "Alto", "make": "Suzuki"},
            "ספלאש": {"english": "Splash", "make": "Suzuki"},
            "ויטרה": {"english": "Vitara", "make": "Suzuki"},
            "מיקרה": {"english": "Micra", "make": "Nissan"},
            "קשקאי": {"english": "Qashqai", "make": "Nissan"},
            "גוק": {"english": "Juke", "make": "Nissan"},
            "נוט": {"english": "Note", "make": "Nissan"},
            "אקורד": {"english": "Accord", "make": "Honda"},
            "סיד": {"english": "Ceed", "make": "Kia"},
            "ריו": {"english": "Rio", "make": "Kia"},
            "פיקנטו": {"english": "Picanto", "make": "Kia"},
            "פורטה": {"english": "Forte", "make": "Kia"},
            "אופטימה": {"english": "Optima", "make": "Kia"},
            "קרניבל": {"english": "Carnival", "make": "Kia"},
            "I10": {"english": "i10", "make": "Hyundai"},
            "I20": {"english": "i20", "make": "Hyundai"},
            "I25": {"english": "i25", "make": "Hyundai"},
            "I30": {"english": "i30", "make": "Hyundai"},
            "I35": {"english": "i35", "make": "Hyundai"},
            "I800": {"english": "i800", "make": "Hyundai"},
            "IX35": {"english": "ix35", "make": "Hyundai"},
            "אלנטרה": {"english": "Elantra", "make": "Hyundai"},
            "גטס": {"english": "Getz", "make": "Hyundai"},
            "גרנדיס": {"english": "Grandis", "make": "Mitsubishi"},
            "אאוטלנדר": {"english": "Outlander", "make": "Mitsubishi"},
            "לנד קרוזר": {"english": "Land Cruiser", "make": "Toyota"},
            "היילקס": {"english": "Hilux", "make": "Toyota"},
            "ויגו": {"english": "Vigo", "make": "Toyota"},
            "קינג": {"english": "King", "make": "Isuzu"},
            "דימקס": {"english": "D-Max", "make": "Isuzu"},
            "טרייטון": {"english": "Triton", "make": "Mitsubishi"},
            "סיריון": {"english": "Sirion", "make": "Daihatsu"},
            "XV": {"english": "XV", "make": "Subaru"},
            "B4": {"english": "B4", "make": "Subaru"},
            "ברלינגו": {"english": "Berlingo", "make": "Citroen"},
            "טרנזיט": {"english": "Transit", "make": "Ford"},
            "קרפטר": {"english": "Crafter", "make": "Volkswagen"},
            "ספרינטר": {"english": "Sprinter", "make": "Mercedes"},
            "פלואנס": {"english": "Fluence", "make": "Renault"},
            "דובלו": {"english": "Doblo", "make": "Fiat"},
            "107": {"english": "107", "make": "Peugeot"},
            "207": {"english": "207", "make": "Peugeot"},
            "208": {"english": "208", "make": "Peugeot"},
            "307": {"english": "307", "make": "Peugeot"},
            "308": {"english": "308", "make": "Peugeot"},
            "3008": {"english": "3008", "make": "Peugeot"},
            "C1": {"english": "C1", "make": "Citroen"},
            "C3": {"english": "C3", "make": "Citroen"},
            "C4": {"english": "C4", "make": "Citroen"},
            "C5": {"english": "C5", "make": "Citroen"},
            "A3": {"english": "A3", "make": "Audi"},
            "A4": {"english": "A4", "make": "Audi"},
            "A5": {"english": "A5", "make": "Audi"},
            "A6": {"english": "A6", "make": "Audi"},
            "A7": {"english": "A7", "make": "Audi"},
            "Q3": {"english": "Q3", "make": "Audi"},
            "Q5": {"english": "Q5", "make": "Audi"},
            "Q7": {"english": "Q7", "make": "Audi"},
            "Q8": {"english": "Q8", "make": "Audi"},
            "רפיד": {"english": "Rapid", "make": "Skoda"},
            "סופרב": {"english": "Superb", "make": "Skoda"},
            "רומסטר": {"english": "Roomster", "make": "Skoda"}
        }

        # Known engine codes
        self.engine_codes = {
            "CBZ": {"make": "Volkswagen", "displacement": "1.2", "fuel_type": "Petrol"},
            "CDA": {"make": "Volkswagen", "displacement": "1.8", "fuel_type": "Petrol"},
            "CJS": {"make": "Volkswagen", "displacement": "1.8", "fuel_type": "Petrol"},
            "CAX": {"make": "Volkswagen", "displacement": "1.4", "fuel_type": "Petrol"},
            "CAV": {"make": "Volkswagen", "displacement": "1.4", "fuel_type": "Petrol"},
            "BSE": {"make": "Volkswagen", "displacement": "1.6", "fuel_type": "Petrol"},
            "BTS": {"make": "Volkswagen", "displacement": "1.6", "fuel_type": "Petrol"},
            "CJZ": {"make": "Volkswagen", "displacement": "1.2", "fuel_type": "Petrol"},
            "TDI": {"make": "Volkswagen", "displacement": "Various",
                    "fuel_type": "Diesel"},
            "BMY": {"make": "Volkswagen", "displacement": "1.4", "fuel_type": "Petrol"},
            "BLX": {"make": "Volkswagen", "displacement": "2.0", "fuel_type": "Petrol"},
            "BLY": {"make": "Volkswagen", "displacement": "2.0", "fuel_type": "Petrol"},
            "AXW": {"make": "Volkswagen", "displacement": "2.0", "fuel_type": "Petrol"},
            "BLR": {"make": "Volkswagen", "displacement": "2.0", "fuel_type": "Petrol"},
            "CRC": {"make": "Audi", "displacement": "3.0", "fuel_type": "Diesel"},
            "CJJ": {"make": "Volkswagen", "displacement": "1.4", "fuel_type": "Petrol"},
            "CNC": {"make": "Volkswagen", "displacement": "2.0", "fuel_type": "Petrol"},
            "CJX": {"make": "Volkswagen", "displacement": "2.0", "fuel_type": "Petrol"},
            "DADA": {"make": "Skoda", "displacement": "1.5", "fuel_type": "Petrol"}
        }

        # Part categories with variations
        self.part_categories = {
            "פילטר": {"english": "Filter", "aliases": ["מסנן", "פ."]},
            "פ.אויר": {"english": "Air Filter", "parent": "Filter"},
            "פ.שמן": {"english": "Oil Filter", "parent": "Filter"},
            "פ.דלק": {"english": "Fuel Filter", "parent": "Filter"},
            "פ.סולר": {"english": "Diesel Filter", "parent": "Filter"},
            "פ.מזגן": {"english": "AC Filter", "parent": "Filter"},
            "פ.גיר": {"english": "Transmission Filter", "parent": "Filter"},
            "דסקיות": {"english": "Brake Discs", "aliases": ["דיסקים", "צלחות"]},
            "צלחות": {"english": "Brake Discs", "aliases": ["דסקיות", "דיסקים"]},
            "בולם": {"english": "Shock Absorber", "aliases": ["אמורטיזר"]},
            "בולם קדמי": {"english": "Front Shock Absorber", "parent": "Shock Absorber"},
            "בולם אחורי": {"english": "Rear Shock Absorber", "parent": "Shock Absorber"},
            "רפידות": {"english": "Brake Pads", "aliases": ["רפידות בלם"]},
            "מ.מים": {"english": "Water Pump", "aliases": ["משאבת מים"]},
            "מ.דלק": {"english": "Fuel Pump", "aliases": ["משאבת דלק"]},
            "ח.קראנק": {"english": "Crankshaft Sensor", "aliases": ["חיישן קראנק"]},
            "ח.חמצן": {"english": "Oxygen Sensor",
                       "aliases": ["חיישן חמצן", "חיישן אוקסיגן"]},
            "ח.הצתה": {"english": "Ignition Coil", "aliases": ["סליל הצתה"]},
            "אטם": {"english": "Gasket", "aliases": ["אטמים"]},
            "אטם ראש": {"english": "Head Gasket", "parent": "Gasket"},
            "אטם מכסה שסטומים": {"english": "Valve Cover Gasket", "parent": "Gasket"},
            "גומי": {"english": "Rubber Mount", "aliases": ["תומך גומי"]},
            "כוהל": {"english": "Coolant", "aliases": ["נוזל קירור"]},
            "טרמוסטט": {"english": "Thermostat", "aliases": ["ט'רמוסטט"]},
            "פלגים": {"english": "Spark Plugs", "aliases": ["מצתים"]},
            "יוניט": {"english": "Sensor Unit", "aliases": ["יחידת חיישן"]},
            "יוניט חום": {"english": "Temperature Sensor", "parent": "Sensor Unit"},
            "יוניט שמן": {"english": "Oil Pressure Sensor", "parent": "Sensor Unit"},
            "יוניט בלם": {"english": "Brake Light Switch", "parent": "Sensor Unit"},
            "צינור": {"english": "Pipe", "aliases": ["צינורות"]},
            "צינור מים": {"english": "Water Pipe", "parent": "Pipe"},
            "קפיץ": {"english": "Spring", "aliases": ["קפיצים"]},
            "משולש": {"english": "Control Arm", "aliases": ["זרוע משולש"]},
            "משולש עליון": {"english": "Upper Control Arm", "parent": "Control Arm"},
            "משולש תחתון": {"english": "Lower Control Arm", "parent": "Control Arm"},
            "זרוע": {"english": "Arm", "aliases": ["זרועות"]},
            "זרוע הגה": {"english": "Steering Arm", "parent": "Arm"},
            "ת.מנוע": {"english": "Engine Mount", "aliases": ["תומך מנוע"]},
            "ת.משולש": {"english": "Control Arm Bushing", "aliases": ["תומך משולש"]},
            "מייצב": {"english": "Stabilizer", "aliases": ["מוט מייצב"]},
            "ג.מייצב": {"english": "Stabilizer Link", "aliases": ["גומי מייצב"]},
            "רדיאטור": {"english": "Radiator", "aliases": ["מקרן"]},
            "ציריה": {"english": "CV Axle", "aliases": ["גל הינע"]},
            "מצמד": {"english": "Clutch", "aliases": ["קלאץ'"]},
            "דרם": {"english": "Drum", "aliases": ["תוף"]},
            "חיווט": {"english": "Wiring", "aliases": ["כבלים"]},
            "בוקסה": {"english": "Bushing", "aliases": ["בוש"]},
            "פלנץ": {"english": "Flange", "aliases": ["אוגן"]},
            "מחזיר שמן": {"english": "Oil Seal", "aliases": ["סימר", "אטם שמן"]},
        }

        # Location and side information
        self.locations = {
            "קדמי": "Front",
            "אחורי": "Rear",
            "עליון": "Upper",
            "תחתון": "Lower",
            "ימין": "Right",
            "שמאל": "Left"
        }

        # Displacement and drive patterns
        self.displacements = [
            r'נפח\s*(\d+\.\d+)',
            r'(\d+\.\d+)(?:\s*ליטר)?',
            r'^(\d+\.\d+)',
        ]

        self.drive_patterns = [
            r'(4x4|4X4)',
            r'(4x2|4X2)',
            r'(2x4|2X4)',
            r'(AWD|FWD|RWD)'
        ]

        # Year extraction patterns
        self.year_patterns = [
            r'מ(\d{2})',
            r'עד\s*(\d{2})',
            r'(\d{2})-(\d{2})'
        ]

        # Prepare advanced regex patterns
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for faster matching"""
        # Make patterns
        self.make_patterns = {}
        for make_heb in self.car_makes:
            self.make_patterns[make_heb] = re.compile(fr'\b{re.escape(make_heb)}\b',
                                                      re.IGNORECASE)

        # Model patterns
        self.model_patterns = {}
        for model_heb, model_data in self.car_models.items():
            self.model_patterns[model_heb] = re.compile(fr'\b{re.escape(model_heb)}\b',
                                                        re.IGNORECASE)

        # Engine code patterns
        self.engine_code_patterns = {}
        for code in self.engine_codes:
            self.engine_code_patterns[code] = re.compile(fr'\b{re.escape(code)}\b',
                                                         re.IGNORECASE)

        # Part category patterns
        self.category_patterns = {}
        for cat_heb, cat_data in self.part_categories.items():
            self.category_patterns[cat_heb] = re.compile(fr'\b{re.escape(cat_heb)}\b',
                                                         re.IGNORECASE)
            if "aliases" in cat_data:
                for alias in cat_data["aliases"]:
                    self.category_patterns[alias] = re.compile(fr'\b{re.escape(alias)}\b',
                                                               re.IGNORECASE)

        # Location patterns
        self.location_patterns = {}
        for loc_heb, loc_eng in self.locations.items():
            self.location_patterns[loc_heb] = re.compile(fr'\b{re.escape(loc_heb)}\b',
                                                         re.IGNORECASE)

        # Compile other patterns
        self.displacement_patterns = [re.compile(p, re.IGNORECASE) for p in
                                      self.displacements]
        self.drive_type_patterns = [re.compile(p, re.IGNORECASE) for p in
                                    self.drive_patterns]
        self.year_extraction_patterns = [re.compile(p, re.IGNORECASE) for p in
                                         self.year_patterns]

        # Special patterns
        self.mazda3_pattern = re.compile(r'מזדה\s*3', re.IGNORECASE)
        self.i_series_pattern = re.compile(r'\b(I|i)(\d{1,2})\b')

    def extract_all_details(self, text: str) -> Dict:
        """Extract all details from a car part description"""
        # Base structure for part details
        details = {
            "original_text": text,
            "car_make": None,
            "car_model": None,
            "year_from": None,
            "year_to": None,
            "engine_code": None,
            "engine_displacement": None,
            "part_category": None,
            "part_subcategory": None,
            "location": None,
            "side": None,
            "drive_type": None,
            "confidence_score": 0.5,
            "extracted_info": []
        }

        # Extract car make
        make_info = self._extract_car_make(text)
        if make_info:
            details["car_make"] = make_info["make"]
            details["confidence_score"] += 0.05
            details["extracted_info"].append(make_info["matched_text"])

        # Extract car model (with make context if available)
        model_info = self._extract_car_model(text, details["car_make"])
        if model_info:
            details["car_model"] = model_info["model"]
            details["confidence_score"] += 0.05
            details["extracted_info"].append(model_info["matched_text"])

            # If we found a model but not a make, use the model's known make
            if not details["car_make"] and "inferred_make" in model_info:
                details["car_make"] = model_info["inferred_make"]
                details["confidence_score"] += 0.03

        # Extract engine code
        engine_code_info = self._extract_engine_code(text)
        if engine_code_info:
            details["engine_code"] = engine_code_info["code"]
            details["confidence_score"] += 0.04
            details["extracted_info"].append(engine_code_info["matched_text"])

            # If we have engine code info but not displacement, add it
            if not details.get(
                    "engine_displacement") and "displacement" in engine_code_info:
                details["engine_displacement"] = engine_code_info["displacement"]

        # Extract engine displacement
        displacement_info = self._extract_displacement(text)
        if displacement_info:
            details["engine_displacement"] = displacement_info["displacement"]
            details["confidence_score"] += 0.03
            details["extracted_info"].append(displacement_info["matched_text"])

        # Extract part category and subcategory
        category_info = self._extract_part_category(text)
        if category_info:
            details["part_category"] = category_info["category"]
            details["confidence_score"] += 0.05
            details["extracted_info"].append(category_info["matched_text"])

            # Add subcategory if available
            if "subcategory" in category_info:
                details["part_subcategory"] = category_info["subcategory"]
                details["confidence_score"] += 0.02

        # Extract location and side
        location_info = self._extract_location_and_side(text)
        if location_info:
            # Add location if found
            if "location" in location_info:
                details["location"] = location_info["location"]
                details["confidence_score"] += 0.02
                details["extracted_info"].append(location_info["location_text"])

            # Add side if found
            if "side" in location_info:
                details["side"] = location_info["side"]
                details["confidence_score"] += 0.02
                details["extracted_info"].append(location_info["side_text"])

        # Extract years
        year_info = self._extract_years(text)
        if year_info:
            # Add from year if found
            if "year_from" in year_info:
                details["year_from"] = year_info["year_from"]
                details["confidence_score"] += 0.03
                details["extracted_info"].append(year_info["from_text"])

            # Add to year if found
            if "year_to" in year_info:
                details["year_to"] = year_info["year_to"]
                details["confidence_score"] += 0.02
                details["extracted_info"].append(year_info["to_text"])

        # Extract drive type
        drive_info = self._extract_drive_type(text)
        if drive_info:
            details["drive_type"] = drive_info["drive_type"]
            details["confidence_score"] += 0.03
            details["extracted_info"].append(drive_info["matched_text"])

        # Cap confidence score at 1.0
        details["confidence_score"] = min(details["confidence_score"], 1.0)

        return details

    def _extract_car_make(self, text: str) -> Optional[Dict]:
        """Extract car make from text"""
        # Direct pattern matching
        for make_heb, pattern in self.make_patterns.items():
            match = pattern.search(text)
            if match:
                return {
                    "make": self.car_makes[make_heb],
                    "matched_text": match.group(0),
                    "confidence": 0.95
                }

        # Check for special case: "מזדה 3" (Mazda3)
        mazda_match = self.mazda3_pattern.search(text)
        if mazda_match:
            return {
                "make": "Mazda",
                "matched_text": mazda_match.group(0),
                "confidence": 0.9
            }

        # Look for models to infer make
        for model_heb, model_data in self.car_models.items():
            if model_heb in text and "make" in model_data:
                # Only return if the model is distinctive enough (not just a number or letter)
                if len(model_heb) > 2 or not model_heb.isalnum():
                    return {
                        "make": model_data["make"],
                        "matched_text": model_heb,
                        "confidence": 0.7,
                        "inferred_from": "model"
                    }

        return None

    def _extract_car_model(self, text: str, make: Optional[str] = None) -> Optional[Dict]:
        """Extract car model from text with optional make context"""
        # If we have a make, prioritize models from that make
        if make:
            make_models = [model_heb for model_heb, model_data in self.car_models.items()
                           if model_data.get("make") == make]

            # Check for these models first
            for model_heb in make_models:
                if model_heb in text:
                    return {
                        "model": self.car_models[model_heb]["english"],
                        "matched_text": model_heb,
                        "confidence": 0.9
                    }

        # Special case for Mazda 3
        mazda3_match = self.mazda3_pattern.search(text)
        if mazda3_match:
            return {
                "model": "3",
                "matched_text": mazda3_match.group(0),
                "confidence": 0.9,
                "inferred_make": "Mazda"
            }

        # Special case for i-series (i10, i20, etc.)
        i_match = self.i_series_pattern.search(text)
        if i_match:
            model_num = i_match.group(2)
            model_name = f"i{model_num}"
            return {
                "model": model_name,
                "matched_text": i_match.group(0),
                "confidence": 0.9,
                "inferred_make": "Hyundai"
            }

        # General model extraction
        for model_heb, pattern in self.model_patterns.items():
            match = pattern.search(text)
            if match:
                model_data = self.car_models[model_heb]
                result = {
                    "model": model_data["english"],
                    "matched_text": match.group(0),
                    "confidence": 0.85
                }

                # Add inferred make if not already known
                if not make and "make" in model_data:
                    result["inferred_make"] = model_data["make"]

                return result

        # Numeric model extraction for makes that use numbers as models
        if make == "Mazda":
            numeric_match = re.search(r'מזדה\s*(\d)', text)
            if numeric_match:
                return {
                    "model": numeric_match.group(1),
                    "matched_text": numeric_match.group(0),
                    "confidence": 0.8
                }

        return None

    def _extract_engine_code(self, text: str) -> Optional[Dict]:
        """Extract engine code from text"""
        for code, pattern in self.engine_code_patterns.items():
            match = pattern.search(text)
            if match:
                result = {
                    "code": code,
                    "matched_text": match.group(0),
                    "confidence": 0.9
                }

                # Add engine metadata if available
                if code in self.engine_codes:
                    engine_data = self.engine_codes[code]
                    if "displacement" in engine_data:
                        result["displacement"] = engine_data["displacement"]
                    if "fuel_type" in engine_data:
                        result["fuel_type"] = engine_data["fuel_type"]
                    if "make" in engine_data:
                        result["make"] = engine_data["make"]

                return result

        return None

    def _extract_displacement(self, text: str) -> Optional[Dict]:
        """Extract engine displacement from text"""
        for pattern in self.displacement_patterns:
            match = pattern.search(text)
            if match:
                displacement = match.group(1)
                # Validate displacement is reasonable (between 0.5 and 9.0)
                try:
                    disp_value = float(displacement)
                    if 0.5 <= disp_value <= 9.0:
                        return {
                            "displacement": displacement,
                            "matched_text": match.group(0),
                            "confidence": 0.85
                        }
                except ValueError:
                    continue

        return None

    def _extract_part_category(self, text: str) -> Optional[Dict]:
        """Extract part category from text"""
        # First check for specific filters (common pattern)
        filter_match = re.search(r'פ\.(אויר|שמן|דלק|מזגן|סולר|גיר)', text)
        if filter_match:
            filter_type = filter_match.group(1)
            # Map Hebrew filter types to English
            filter_types = {
                "אויר": "Air Filter",
                "שמן": "Oil Filter",
                "דלק": "Fuel Filter",
                "מזגן": "AC Filter",
                "סולר": "Diesel Filter",
                "גיר": "Transmission Filter"
            }

            if filter_type in filter_types:
                return {
                    "category": "Filter",
                    "subcategory": filter_types[filter_type],
                    "matched_text": filter_match.group(0),
                    "confidence": 0.95
                }

        # Check for categories with pattern matching
        for cat_heb, pattern in self.category_patterns.items():
            match = pattern.search(text)
            if match:
                # Get the base category data
                cat_data = None
                for original_cat, data in self.part_categories.items():
                    if cat_heb == original_cat or (
                            "aliases" in data and cat_heb in data["aliases"]):
                        cat_data = data
                        break

                if not cat_data:
                    continue

                result = {
                    "category": cat_data["english"],
                    "matched_text": match.group(0),
                    "confidence": 0.9
                }

                # Add subcategory if this is a parent category
                if "parent" in cat_data:
                    result["subcategory"] = cat_data["english"]
                    result["category"] = cat_data["parent"]

                # Check for specific brake disc types
                if cat_data["english"] == "Brake Discs":
                    if "קדמי" in text:
                        result["subcategory"] = "Front Brake Discs"
                    elif "אחורי" in text:
                        result["subcategory"] = "Rear Brake Discs"

                # Check for specific shock absorber types
                elif cat_data["english"] == "Shock Absorber":
                    if "קדמי" in text:
                        result["subcategory"] = "Front Shock Absorber"
                    elif "אחורי" in text:
                        result["subcategory"] = "Rear Shock Absorber"

                return result

        return None

    def _extract_location_and_side(self, text: str) -> Optional[Dict]:
        """Extract location and side information"""
        result = {}

        # Extract location
        for loc_heb, pattern in self.location_patterns.items():
            if loc_heb in ["ימין", "שמאל"]:  # Skip side locations here
                continue

            match = pattern.search(text)
            if match:
                result["location"] = self.locations[loc_heb]
                result["location_text"] = match.group(0)
                break

        # Extract side
        if "ימין" in text:
            result["side"] = "Right"
            result["side_text"] = "ימין"
        elif "שמאל" in text:
            result["side"] = "Left"
            result["side_text"] = "שמאל"

        return result if result else None

    def _extract_years(self, text: str) -> Optional[Dict]:
        """Extract year ranges from text"""
        result = {}

        # Check for year range pattern (e.g., 09-12)
        range_match = re.search(r'(\d{2})-(\d{2})', text)
        if range_match:
            from_year = int(range_match.group(1))
            to_year = int(range_match.group(2))

            # Convert to 4-digit years
            from_year = 2000 + from_year if from_year < 50 else 1900 + from_year
            to_year = 2000 + to_year if to_year < 50 else 1900 + to_year

            result["year_from"] = from_year
            result["year_to"] = to_year
            result["from_text"] = range_match.group(1)
            result["to_text"] = range_match.group(2)
            return result

        # Check for "מ" (from) year pattern
        from_match = re.search(r'מ(\d{2})', text)
        if from_match:
            year_from = int(from_match.group(1))
            # Convert to 4-digit year
            year_from = 2000 + year_from if year_from < 50 else 1900 + year_from
            result["year_from"] = year_from
            result["from_text"] = from_match.group(0)

        # Check for "עד" (until) year pattern
        to_match = re.search(r'עד\s*(\d{2})', text)
        if to_match:
            year_to = int(to_match.group(1))
            # Convert to 4-digit year
            year_to = 2000 + year_to if year_to < 50 else 1900 + year_to
            result["year_to"] = year_to
            result["to_text"] = to_match.group(0)

        return result if result else None

    def _extract_drive_type(self, text: str) -> Optional[Dict]:
        """Extract drive type information"""
        for pattern in self.drive_type_patterns:
            match = pattern.search(text)
            if match:
                return {
                    "drive_type": match.group(0).upper(),
                    "matched_text": match.group(0),
                    "confidence": 0.9
                }

        return None


def create_car_parts_database():
    """Create a database with detailed car part information from btw_filenames.txt"""
    print("=" * 80)
    print("Advanced One-Time Car Parts Database Creator")
    print("=" * 80)

    # Define paths
    db_path = 'advanced_car_parts.db'
    file_path = 'resources/btw_filenames.txt'

    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return False

    print(f"Found input file: {file_path}")
    file_size = os.path.getsize(file_path)
    print(f"File size: {file_size} bytes")

    # Create database connection and schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables with detailed schema
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS car_parts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_text TEXT NOT NULL,
        car_make TEXT,
        car_model TEXT,
        year_from INTEGER,
        year_to INTEGER,
        engine_code TEXT,
        engine_displacement TEXT,
        part_category TEXT,
        part_subcategory TEXT,
        location TEXT,
        side TEXT,
        drive_type TEXT,
        confidence_score REAL,
        extracted_info TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create indexes for efficient searching
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_parts_make ON car_parts(car_make)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_parts_model ON car_parts(car_model)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_parts_category ON car_parts(part_category)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_parts_year ON car_parts(year_from, year_to)")

    # Initialize extractor
    extractor = AdvancedCarPartExtractor()

    # Process the file
    print("Processing car parts data...")
    start_time = time.time()

    total_lines = 0
    processed_count = 0
    error_count = 0

    # Statistics collectors
    makes_count = defaultdict(int)
    models_count = defaultdict(int)
    categories_count = defaultdict(int)
    years_count = defaultdict(int)

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                total_lines += 1

                if not line.strip():
                    continue

                try:
                    # Extract details from the line
                    part_details = extractor.extract_all_details(line.strip())

                    # Convert extracted_info list to JSON string
                    extracted_info_json = json.dumps(part_details["extracted_info"],
                                                     ensure_ascii=False)

                    # Insert into database
                    cursor.execute('''
                    INSERT INTO car_parts (
                        original_text, car_make, car_model, year_from, year_to,
                        engine_code, engine_displacement, part_category, part_subcategory,
                        location, side, drive_type, confidence_score, extracted_info
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        part_details["original_text"],
                        part_details["car_make"],
                        part_details["car_model"],
                        part_details["year_from"],
                        part_details["year_to"],
                        part_details["engine_code"],
                        part_details["engine_displacement"],
                        part_details["part_category"],
                        part_details["part_subcategory"],
                        part_details["location"],
                        part_details["side"],
                        part_details["drive_type"],
                        part_details["confidence_score"],
                        extracted_info_json
                    ))

                    # Commit every 100 records to avoid large transactions
                    if line_num % 100 == 0:
                        conn.commit()

                    processed_count += 1

                    # Collect statistics
                    if part_details["car_make"]:
                        makes_count[part_details["car_make"]] += 1

                    if part_details["car_model"]:
                        model_key = f"{part_details['car_make'] or 'Unknown'} {part_details['car_model']}"
                        models_count[model_key] += 1

                    if part_details["part_category"]:
                        categories_count[part_details["part_category"]] += 1

                    if part_details["year_from"]:
                        year_decade = f"{part_details['year_from'] // 10 * 10}s"
                        years_count[year_decade] += 1

                    # Print progress every 500 lines
                    if line_num % 500 == 0:
                        elapsed = time.time() - start_time
                        print(
                            f"Processed {line_num} lines ({processed_count} parts) in {elapsed:.2f} seconds")

                except Exception as e:
                    error_count += 1
                    print(f"Error processing line {line_num}: {str(e)}")
                    # Continue with next line

        # Commit any remaining records
        conn.commit()

    except Exception as e:
        print(f"Error processing file: {str(e)}")
        conn.rollback()
        return False

    elapsed_time = time.time() - start_time

    # Print processing summary
    print("\n" + "=" * 40)
    print(f"Processing completed in {elapsed_time:.2f} seconds")
    print(f"Total lines: {total_lines}")
    print(f"Successfully processed: {processed_count}")
    print(f"Errors: {error_count}")

    # Print statistics
    print("\nTop Car Makes:")
    for make, count in sorted(makes_count.items(), key=lambda x: x[1], reverse=True)[:10]:
        if make:
            print(f"  - {make}: {count} parts")

    print("\nTop Car Models:")
    for model, count in sorted(models_count.items(), key=lambda x: x[1], reverse=True)[
                        :10]:
        print(f"  - {model}: {count} parts")

    print("\nTop Part Categories:")
    for category, count in sorted(categories_count.items(), key=lambda x: x[1],
                                  reverse=True)[:10]:
        print(f"  - {category}: {count} parts")

    print("\nYear Distribution:")
    for decade, count in sorted(years_count.items()):
        print(f"  - {decade}: {count} parts")

    # Verify the database count
    cursor.execute("SELECT COUNT(*) FROM car_parts")
    db_count = cursor.fetchone()[0]

    print(f"\nDatabase verification: {db_count} records in database")

    # Create a view for easier querying
    cursor.execute('''
    CREATE VIEW IF NOT EXISTS car_parts_view AS
    SELECT 
        id, original_text, car_make, car_model, 
        year_from, year_to,
        engine_code, engine_displacement, 
        part_category, part_subcategory,
        location, side, drive_type,
        confidence_score
    FROM car_parts
    ''')

    conn.commit()
    conn.close()

    print("\nDatabase created successfully at: advanced_car_parts.db")
    print("You can now view this database in PyCharm by:")
    print("1. View → Tool Windows → Database")
    print("2. Click the + icon")
    print("3. Select 'Data Source' → 'SQLite'")
    print("4. Browse to your 'advanced_car_parts.db' file")
    print("5. Test the connection and click 'OK'")

    return True


if __name__ == "__main__":
    create_car_parts_database()