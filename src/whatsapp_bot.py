"""
WhatsApp Bot Integration using Twilio
Handles incoming WhatsApp messages and sends AI-generated responses
"""
import os
import sys
import logging

# Add the project root to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from twilio.base.exceptions import TwilioException
from src.gemini_ai import EnhancedAI
from src.database import DatabaseManager
from src.utils import setup_logging
from datetime import datetime
import json

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

class WhatsAppBot:
    """WhatsApp bot using Twilio API"""
    
    def __init__(self):
        # Load environment variables
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([self.account_sid, self.auth_token, self.twilio_number]):
            raise ValueError("Missing required Twilio environment variables")
        
        # Initialize Twilio client
        self.client = Client(self.account_sid, self.auth_token)
        
        # Initialize AI and database
        self.enhanced_ai = EnhancedAI()
        self.db = DatabaseManager()
        
        # User session management
        self.user_sessions = {}
        
        logger.info("WhatsApp Bot initialized successfully")
    
    def process_incoming_message(self, from_number: str, message_body: str) -> str:
        """Process incoming WhatsApp message and generate response"""
        try:
            # Clean phone number
            clean_number = self._clean_phone_number(from_number)
            
            # Log incoming message
            logger.info(f"Received message from {clean_number}: {message_body[:100]}...")
            
            # Store message in database
            self.db.store_message(clean_number, message_body, 'incoming')
            
            # Handle different message types
            response = self._handle_message(clean_number, message_body)
            
            # Store response in database
            self.db.store_message(clean_number, response, 'outgoing')
            
            logger.info(f"Generated response for {clean_number}: {response[:100]}...")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return "I'm sorry, I encountered an error processing your message. Please try again later."
    
    def _handle_message(self, phone_number: str, message: str) -> str:
        """Handle different types of messages"""
        message_lower = message.lower().strip()
        
        # Handle greeting messages
        if any(greeting in message_lower for greeting in ['hi', 'hello', 'hey', 'start']):
            return self._get_welcome_message()
        
        # Handle help requests
        if any(help_word in message_lower for help_word in ['help', 'menu', 'options']):
            return self._get_help_message()
        
        # Handle health tips request
        if 'tips' in message_lower or 'advice' in message_lower:
            return self._get_health_tips()
        
        # Handle emergency keywords
        if any(emergency in message_lower for emergency in ['emergency', '911', 'urgent']):
            return self._get_emergency_message()
        
        # Handle symptom analysis and general questions (default)
        return self._analyze_message(phone_number, message)
    
    def _analyze_message(self, phone_number: str, message: str) -> str:
        """Analyze message using enhanced AI (health + general)"""
        try:
            # Get user info
            user_info = self.db.get_user_info(phone_number)
            user_name = user_info.get('name', 'there') if user_info else 'there'
            
            # Debug: Check if enhanced_ai is available
            if not hasattr(self, 'enhanced_ai'):
                return f"Error: Enhanced AI not initialized. Available attributes: {list(self.__dict__.keys())}"
            
            # Use enhanced AI to analyze any type of message
            response = self.enhanced_ai.analyze_message(message, user_name)
            
            # Store interaction in database (for both health and general)
            self.db.store_message(phone_number, f"AI Response: {response[:100]}...", 'analysis')
            
            return response
            
        except Exception as e:
            logger.error(f"Error in message analysis: {str(e)}", exc_info=True)
            return f"Debug Error: {str(e)}"
    
    def _get_welcome_message(self) -> str:
        """Get welcome message for new users"""
        return """👋 Welcome to your AI Assistant!

I'm here to help you with:
🩺 Health questions and symptom analysis
🤖 General questions and advice
💡 Tips and guidance on any topic

🔹 Ask me about your health concerns
🔹 Ask me general questions (weather, advice, etc.)
🔹 Type 'help' for more options

⚠️ IMPORTANT: For medical emergencies, call 911 immediately.

How can I help you today?"""
    
    def _get_help_message(self) -> str:
        """Get help message with available options"""
        return """🆘 How I can help you:

1. 🩺 **Health & Medical Questions**
   Describe your symptoms for personalized health guidance

2. 🤖 **General AI Assistant**
   Ask me anything! I can help with advice, questions, explanations, and more

3. 💡 **Health Tips**
   Type 'tips' for general health advice

4. 🚨 **Emergencies**
   For medical emergencies, call 911 immediately

**Example messages:**
• "I have a headache and feel nauseous"
• "What's the weather like today?"
• "Tell me a joke"
• "How do I cook pasta?"
• "Give me some health tips"

I'm powered by advanced AI and can help with both medical and general questions!"""
    
    def _get_health_tips(self) -> str:
        """Get general health tips"""
        tips = self.enhanced_ai.get_health_tips()
        
        return f"""💡 Daily Health Tips:

{tips}

Remember: Small daily habits make a big difference in your overall health! 

Need help with specific symptoms or have other questions? Just ask me anything!"""
    
    def _get_emergency_message(self) -> str:
        """Get emergency response message"""
        return """🚨 EMERGENCY RESPONSE 🚨

If this is a medical emergency:
📞 Call 911 immediately
🏥 Go to the nearest emergency room

For urgent but non-emergency care:
📞 Call your doctor
🏥 Visit an urgent care center

I'm an AI assistant and cannot provide emergency medical care. Please seek immediate professional help for serious medical situations.

Stay safe! 🙏"""
    
    def _clean_phone_number(self, phone_number: str) -> str:
        """Clean and format phone number"""
        # Remove 'whatsapp:' prefix if present
        clean_number = phone_number.replace('whatsapp:', '')
        # Remove any non-numeric characters except +
        clean_number = ''.join(c for c in clean_number if c.isdigit() or c == '+')
        return clean_number
    
    def send_message(self, to_number: str, message_body: str) -> bool:
        """Send message via Twilio WhatsApp"""
        try:
            # Ensure number has whatsapp: prefix for Twilio
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'
            
            # Ensure Twilio number has whatsapp: prefix
            from_number = self.twilio_number
            if not from_number.startswith('whatsapp:'):
                from_number = f'whatsapp:{from_number}'
            
            message = self.client.messages.create(
                body=message_body,
                from_=from_number,
                to=to_number
            )
            
            logger.info(f"Message sent successfully. SID: {message.sid}")
            return True
            
        except TwilioException as e:
            logger.error(f"Twilio error sending message: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {str(e)}")
            return False

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Initialize bot
try:
    bot = WhatsAppBot()
except Exception as e:
    logger.error(f"Failed to initialize WhatsApp bot: {str(e)}")
    bot = None

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "WhatsApp AI Bot",
        "version": "2.0 with Gemini",
        "endpoints": ["/webhook", "/test"]
    })

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint to verify bot functionality"""
    try:
        # Test health question
        health_response = bot.enhanced_ai.analyze_message("I have a headache", "TestUser")
        
        # Test general question  
        general_response = bot.enhanced_ai.analyze_message("Tell me a joke", "TestUser")
        
        # Test Gemini connection
        gemini_test = bot.enhanced_ai.test_gemini_connection()
        
        return jsonify({
            "status": "success",
            "health_test": health_response[:100] + "..." if len(health_response) > 100 else health_response,
            "general_test": general_response[:100] + "..." if len(general_response) > 100 else general_response,
            "gemini_status": gemini_test,
            "environment": {
                "gemini_key_present": bool(os.getenv('GEMINI_API_KEY')),
                "gemini_available": bot.enhanced_ai.gemini_available
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "environment": {
                "gemini_key_present": bool(os.getenv('GEMINI_API_KEY'))
            }
        }), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint for Twilio WhatsApp messages"""
    if not bot:
        return jsonify({'error': 'Bot not initialized'}), 500
    
    try:
        # Get message data from Twilio
        from_number = request.form.get('From', '')
        message_body = request.form.get('Body', '')
        
        if not from_number or not message_body:
            logger.warning("Received webhook with missing data")
            return jsonify({'error': 'Missing required data'}), 400
        
        # Process message and get response
        response_message = bot.process_incoming_message(from_number, message_body)
        
        # Create Twilio response
        resp = MessagingResponse()
        resp.message(response_message)
        
        return str(resp)
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        # Return a generic error message
        resp = MessagingResponse()
        resp.message("I'm sorry, I'm experiencing technical difficulties. Please try again later.")
        return str(resp)

@app.route('/send', methods=['POST'])
def send_message():
    """Endpoint to send messages (for testing)"""
    if not bot:
        return jsonify({'error': 'Bot not initialized'}), 500
    
    try:
        data = request.get_json()
        to_number = data.get('to')
        message = data.get('message')
        
        if not to_number or not message:
            return jsonify({'error': 'Missing to or message parameter'}), 400
        
        success = bot.send_message(to_number, message)
        
        if success:
            return jsonify({'status': 'Message sent successfully'})
        else:
            return jsonify({'error': 'Failed to send message'}), 500
            
    except Exception as e:
        logger.error(f"Send message error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'bot_initialized': bot is not None
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get bot statistics"""
    if not bot:
        return jsonify({'error': 'Bot not initialized'}), 500
    
    try:
        stats = bot.db.get_statistics()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting WhatsApp bot on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)