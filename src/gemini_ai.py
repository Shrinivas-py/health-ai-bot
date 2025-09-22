"""
Enhanced AI Assistant with Google Gemini integration
Combines health-specific analysis with general AI capabilities
"""
import os
import logging
import google.generativeai as genai
from typing import Optional, Dict, Any
from .health_ai import HealthAI, SymptomAnalysis

logger = logging.getLogger(__name__)

class EnhancedAI:
    """Enhanced AI that combines health analysis with Gemini for general questions"""
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """Initialize the enhanced AI with health analysis and Gemini"""
        self.health_ai = HealthAI()
        self.gemini_api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        
        # Initialize Gemini
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                self.gemini_available = True
                logger.info("Gemini AI initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
                self.gemini_available = False
        else:
            self.gemini_available = False
            logger.warning("No Gemini API key provided - using health analysis only")
    
    def is_health_related(self, message: str) -> bool:
        """Determine if a message is health-related"""
        health_keywords = [
            'pain', 'hurt', 'ache', 'fever', 'sick', 'ill', 'nausea', 'vomit',
            'headache', 'stomach', 'cough', 'cold', 'flu', 'dizzy', 'tired',
            'fatigue', 'symptom', 'doctor', 'medicine', 'treatment', 'health',
            'medical', 'hospital', 'injury', 'wound', 'bleeding', 'infection',
            'allergy', 'rash', 'breathing', 'chest', 'heart', 'temperature',
            'swollen', 'sore', 'cramp', 'sprain', 'broken', 'burn', 'cut'
        ]
        
        message_lower = message.lower()
        
        # Check for health keywords
        for keyword in health_keywords:
            if keyword in message_lower:
                return True
        
        # Check for health-related patterns
        health_patterns = [
            'i feel', 'i have', 'my body', 'experiencing', 'suffering from',
            'what should i do for', 'how to treat', 'is it normal',
            'should i see a doctor', 'medical advice'
        ]
        
        for pattern in health_patterns:
            if pattern in message_lower:
                return True
        
        return False
    
    def analyze_message(self, message: str, user_name: str = "there") -> str:
        """Analyze message and provide appropriate response"""
        
        # Check if it's health-related
        if self.is_health_related(message):
            return self._handle_health_question(message, user_name)
        else:
            return self._handle_general_question(message, user_name)
    
    def _handle_health_question(self, message: str, user_name: str) -> str:
        """Handle health-related questions using specialized health AI"""
        try:
            analysis = self.health_ai.analyze_message(message)
            response = self.health_ai.format_response(analysis, user_name)
            
            # Add a note that we can help with other questions too
            if self.gemini_available:
                response += "\n\n💡 I can also help with general questions, advice, or any other topics!"
            
            return response
            
        except Exception as e:
            logger.error(f"Health analysis error: {e}")
            return self._get_fallback_health_response(user_name)
    
    def _handle_general_question(self, message: str, user_name: str) -> str:
        """Handle general questions using Gemini AI"""
        
        if not self.gemini_available:
            return self._get_fallback_general_response(user_name)
        
        try:
            # Create a prompt that makes the AI helpful and concise for WhatsApp
            prompt = f"""You are a helpful AI assistant responding to a WhatsApp message. 
            Keep your response concise (under 300 words), friendly, and helpful.
            
            User's message: {message}
            
            Provide a helpful response. If it's a question, answer it clearly. 
            If it's a request for advice, provide practical suggestions.
            Use emojis sparingly but appropriately to make it friendly for messaging."""
            
            response = self.gemini_model.generate_content(prompt)
            
            # Add a friendly greeting with the user's name
            ai_response = f"Hi {user_name}! {response.text}"
            
            # Add a note about health capabilities
            ai_response += "\n\n🏥 Need health advice? I can also analyze symptoms and provide medical guidance!"
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._get_fallback_general_response(user_name)
    
    def _get_fallback_health_response(self, user_name: str) -> str:
        """Fallback response for health questions when AI fails"""
        return f"""Hi {user_name}! I'm having trouble analyzing your symptoms right now.
        
🏥 For health concerns, I recommend:
• Consulting with a healthcare professional
• Calling your doctor if symptoms are concerning
• Visiting urgent care for serious issues
• Calling 911 for emergencies

💡 You can also try rephrasing your question and I'll do my best to help!"""
    
    def _get_fallback_general_response(self, user_name: str) -> str:
        """Fallback response for general questions when Gemini is unavailable"""
        return f"""Hi {user_name}! I'm currently optimized for health and medical questions.
        
🏥 I can help you with:
• Symptom analysis
• Health recommendations  
• Medical advice and guidance
• Emergency situation assessment

💡 Try asking me about any health concerns you might have!

⚠️ For other topics, I'm still learning. My AI capabilities are expanding soon!"""
    
    def get_health_tips(self) -> str:
        """Get health tips from the health AI"""
        tips = self.health_ai.get_health_tips()
        return "\n".join(tips)
    
    def test_gemini_connection(self) -> Dict[str, Any]:
        """Test the Gemini API connection"""
        if not self.gemini_available:
            return {
                "status": "error",
                "message": "Gemini API not available",
                "gemini_configured": False
            }
        
        try:
            test_response = self.gemini_model.generate_content("Hello! Please respond with 'Gemini is working!'")
            return {
                "status": "success",
                "message": test_response.text,
                "gemini_configured": True
            }
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Gemini test failed: {str(e)}",
                "gemini_configured": False
            }