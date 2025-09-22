"""
Utility functions for the Health AI Bot
"""
import os
import logging
import logging.handlers
from datetime import datetime
from typing import Any, Dict, List
import re
import json
import hashlib
from dotenv import load_dotenv

def setup_logging(log_level: str = None, log_file: str = None) -> None:
    """Setup logging configuration"""
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    if log_file is None:
        log_file = os.path.join('logs', 'health_bot.log')
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Suppress some noisy loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

def load_environment():
    """Load environment variables from .env file"""
    load_dotenv()
    
    # Validate required environment variables
    required_vars = [
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN', 
        'TWILIO_PHONE_NUMBER'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

def sanitize_phone_number(phone_number: str) -> str:
    """Sanitize and format phone number"""
    # Remove whatsapp: prefix
    clean_number = phone_number.replace('whatsapp:', '')
    
    # Remove all non-digit characters except +
    clean_number = re.sub(r'[^\d+]', '', clean_number)
    
    # Ensure it starts with + for international format
    if not clean_number.startswith('+'):
        # Assume US number if no country code
        if len(clean_number) == 10:
            clean_number = '+1' + clean_number
        elif len(clean_number) == 11 and clean_number.startswith('1'):
            clean_number = '+' + clean_number
    
    return clean_number

def sanitize_message(message: str) -> str:
    """Sanitize user message for processing"""
    if not message:
        return ""
    
    # Remove excessive whitespace
    message = re.sub(r'\s+', ' ', message.strip())
    
    # Remove potential harmful content
    message = re.sub(r'<[^>]*>', '', message)  # Remove HTML tags
    
    # Limit message length
    max_length = int(os.getenv('MAX_MESSAGE_LENGTH', 1000))
    if len(message) > max_length:
        message = message[:max_length] + "..."
    
    return message

def anonymize_phone_number(phone_number: str) -> str:
    """Create anonymous hash of phone number for logging"""
    return hashlib.sha256(phone_number.encode()).hexdigest()[:8]

def validate_webhook_signature(payload: str, signature: str, auth_token: str) -> bool:
    """Validate Twilio webhook signature for security"""
    try:
        from twilio.request_validator import RequestValidator
        validator = RequestValidator(auth_token)
        return validator.validate(
            os.getenv('WEBHOOK_URL', ''),
            payload,
            signature
        )
    except Exception:
        return False

def format_datetime(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def parse_datetime(dt_string: str) -> datetime:
    """Parse datetime string"""
    try:
        return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
    except:
        return datetime.now()

def chunk_message(message: str, max_length: int = 1600) -> List[str]:
    """Split long message into chunks for WhatsApp"""
    if len(message) <= max_length:
        return [message]
    
    chunks = []
    current_chunk = ""
    
    # Split by paragraphs first
    paragraphs = message.split('\n\n')
    
    for paragraph in paragraphs:
        if len(current_chunk + paragraph) <= max_length:
            if current_chunk:
                current_chunk += '\n\n' + paragraph
            else:
                current_chunk = paragraph
        else:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                # Paragraph itself is too long, split by sentences
                sentences = paragraph.split('. ')
                for sentence in sentences:
                    if len(current_chunk + sentence) <= max_length:
                        if current_chunk:
                            current_chunk += '. ' + sentence
                        else:
                            current_chunk = sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def extract_keywords(text: str) -> List[str]:
    """Extract keywords from text for analysis"""
    # Convert to lowercase and remove punctuation
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    
    # Split into words
    words = text.split()
    
    # Remove common stop words
    stop_words = {
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your',
        'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she',
        'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their',
        'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that',
        'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an',
        'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of',
        'at', 'by', 'for', 'with', 'through', 'during', 'before', 'after', 'above',
        'below', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
        'further', 'then', 'once'
    }
    
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    
    return keywords[:20]  # Limit to 20 keywords

def calculate_message_sentiment(text: str) -> float:
    """Simple sentiment analysis (-1 to 1, negative to positive)"""
    positive_words = {
        'good', 'better', 'great', 'excellent', 'fine', 'okay', 'well', 'healthy',
        'happy', 'relief', 'improved', 'recovering', 'healing'
    }
    
    negative_words = {
        'bad', 'worse', 'terrible', 'awful', 'sick', 'ill', 'pain', 'hurt',
        'ache', 'suffering', 'miserable', 'worried', 'scared', 'anxious'
    }
    
    words = re.findall(r'\b\w+\b', text.lower())
    
    positive_count = sum(1 for word in words if word in positive_words)
    negative_count = sum(1 for word in words if word in negative_words)
    
    total_sentiment_words = positive_count + negative_count
    
    if total_sentiment_words == 0:
        return 0.0  # Neutral
    
    return (positive_count - negative_count) / total_sentiment_words

def is_medical_emergency(text: str) -> bool:
    """Check if text indicates a medical emergency"""
    emergency_patterns = [
        r'\b(can\'?t breathe|difficulty breathing|shortness of breath)\b',
        r'\b(chest pain|heart attack|heart problem)\b',
        r'\b(stroke|paralyzed|can\'?t move)\b',
        r'\b(severe bleeding|blood loss)\b',
        r'\b(unconscious|passed out|fainted)\b',
        r'\b(poisoning|overdose)\b',
        r'\b(severe allergic reaction|anaphylaxis)\b',
        r'\b(broken bone|fracture)\b',
        r'\b(head injury|concussion)\b',
        r'\b(seizure|convulsion)\b',
        r'\b(emergency|911|urgent)\b'
    ]
    
    text_lower = text.lower()
    
    for pattern in emergency_patterns:
        if re.search(pattern, text_lower):
            return True
    
    return False

def get_time_greeting() -> str:
    """Get time-appropriate greeting"""
    hour = datetime.now().hour
    
    if 5 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 17:
        return "Good afternoon"
    elif 17 <= hour < 21:
        return "Good evening"
    else:
        return "Hello"

def create_response_metadata(analysis_result) -> Dict[str, Any]:
    """Create metadata for response tracking"""
    return {
        'timestamp': datetime.now().isoformat(),
        'confidence': getattr(analysis_result, 'confidence', 0.0),
        'severity': getattr(analysis_result, 'severity', 'unknown'),
        'urgency': getattr(analysis_result, 'urgency', 'unknown'),
        'num_symptoms': len(getattr(analysis_result, 'symptoms', [])),
        'num_recommendations': len(getattr(analysis_result, 'recommendations', []))
    }

def safe_json_loads(json_string: str, default=None):
    """Safely load JSON with fallback"""
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default or []

def safe_json_dumps(obj, default=None) -> str:
    """Safely dump JSON with fallback"""
    try:
        return json.dumps(obj)
    except (TypeError, ValueError):
        return json.dumps(default or [])

class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if call is allowed for identifier"""
        now = datetime.now().timestamp()
        
        # Clean old entries
        if identifier in self.calls:
            self.calls[identifier] = [
                call_time for call_time in self.calls[identifier]
                if now - call_time < self.time_window
            ]
        else:
            self.calls[identifier] = []
        
        # Check if under limit
        if len(self.calls[identifier]) < self.max_calls:
            self.calls[identifier].append(now)
            return True
        
        return False