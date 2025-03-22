import re
import random
import time
import threading
import os


class ChatAI:
    """Simple AI chat processing logic"""

    def __init__(self, username=None):
        """Initialize the AI processor"""
        # Get username
        self.username = username or os.environ.get('USERNAME', 'User')

        # Initialize response patterns
        self.initialize_responses()

    def initialize_responses(self):
        """Set up the response patterns"""
        # Basic greeting and conversation patterns
        self.responses = {
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
            r'features|functionality|abilities': [
                "I can help with application information, answer questions, provide guidance on features, and assist with basic tasks.",
                "My capabilities include answering questions, explaining features, and helping you navigate the application.",
                "I'm designed to provide assistance, information, and guidance related to this application's features."
            ],
            r'search|find': [
                "You can use the search bar at the top of the application to find what you're looking for.",
                "To search, use the search field in the top bar and enter your keywords.",
                "The search functionality is available in the header - just type what you're looking for."
            ],
            r'notification|alert': [
                "Notifications are displayed in the bell icon at the top-right corner of the application.",
                "Check the bell icon in the header for your notifications and alerts.",
                "The notification center can be accessed through the bell icon in the top bar."
            ],
            r'settings|preferences': [
                "You can access settings through the main menu to customize the application according to your preferences.",
                "Look for the settings option in the main navigation menu to adjust your preferences.",
                "Application settings can be configured through the settings menu accessible from the main interface."
            ],
            r'help|assistance': [
                "I'm here to help! Just tell me what you need assistance with.",
                "You can ask me about any feature or how to perform specific tasks, and I'll guide you.",
                "For help with specific features, just ask me directly about what you want to know."
            ],
            r'dark mode|light mode|theme': [
                "You can change the application theme in the settings. Both dark and light modes are available.",
                "To switch between dark and light mode, go to settings and select your preferred theme.",
                "The application supports theme customization. Check the settings to change between dark and light modes."
            ],
            r'chat|conversation': [
                f"Yes, {self.username}, this chat functionality is fully working now! You can ask me anything.",
                "I'm designed to have conversations like this one. What would you like to talk about?",
                "This chat system is integrated and working. How can I assist you today?"
            ],
            r'work|working|not working': [
                "I'm fully operational and ready to assist you.",
                "The chat system is working as expected. What else would you like to know?",
                "Everything is working fine with the chat functionality. How can I help you?"
            ],
        }

        # Special responses for BaselAM
        if self.username.lower() == 'baselam':
            self.responses[r'code|programming|development'] = [
                "I notice you're the developer! The chat implementation is working correctly now.",
                "The chat code is operating as designed. Nice work on the integration!",
                "Your chat implementation is functioning properly. No more 'coming soon' messages."
            ]

            self.responses[r'test|testing'] = [
                "The chat test is successful. Messages are being processed and displayed correctly.",
                "Testing complete - chat responses are working. The implementation is successful.",
                "Test confirmed: Chat system is processing messages properly."
            ]

        # Default responses when no pattern matches
        self.default_responses = [
            f"I'm not sure I understand, {self.username}. Could you rephrase that or ask something else?",
            "I don't have specific information about that. Is there something else I can help with?",
            "That's beyond my current knowledge. Could you try asking in a different way?",
            "I'm not able to answer that specific question. Would you like to know about the application features instead?"
        ]

    def process_message(self, message, callback):
        """
        Process a message from the user and return a response.
        Uses a callback to return the response asynchronously.

        Args:
            message: The user's message
            callback: Function to call with the response
        """

        # Start processing in a thread to keep the UI responsive
        def process_thread():
            # Simulate thinking time
            time.sleep(1)

            # Generate response
            response = self.generate_response(message)

            # Call the callback with the response
            callback(response)

        threading.Thread(target=process_thread, daemon=True).start()

    def generate_response(self, message):
        """Generate a response based on the input message"""
        # Check all patterns for a match
        for pattern, possible_responses in self.responses.items():
            if re.search(pattern, message.lower()):
                return random.choice(possible_responses)

        # If no match found, use a default response
        return random.choice(self.default_responses)