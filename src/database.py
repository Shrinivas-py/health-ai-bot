"""
Database management for the Health AI Bot
Handles user data, message history, and analytics
"""
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import os
from dataclasses import asdict

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database operations"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.getenv('DATABASE_URL', 'sqlite:///health_bot.db')
            # Remove sqlite:/// prefix if present
            if db_path.startswith('sqlite:///'):
                db_path = db_path[10:]
        
        self.db_path = db_path
        self.init_database()
        logger.info(f"Database initialized at {self.db_path}")
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number TEXT UNIQUE NOT NULL,
                    name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_messages INTEGER DEFAULT 0
                )
            ''')
            
            # Messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    phone_number TEXT NOT NULL,
                    message_body TEXT NOT NULL,
                    message_type TEXT NOT NULL CHECK(message_type IN ('incoming', 'outgoing')),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Symptom analyses table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    phone_number TEXT NOT NULL,
                    original_message TEXT NOT NULL,
                    symptoms TEXT,
                    severity TEXT,
                    urgency TEXT,
                    confidence REAL,
                    recommendations TEXT,
                    potential_conditions TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_phone ON messages(phone_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analyses_phone ON analyses(phone_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analyses_timestamp ON analyses(timestamp)')
            
            conn.commit()
            logger.info("Database tables initialized successfully")
    
    def get_or_create_user(self, phone_number: str, name: str = None) -> int:
        """Get existing user or create new one"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Try to get existing user
            cursor.execute('SELECT id FROM users WHERE phone_number = ?', (phone_number,))
            user = cursor.fetchone()
            
            if user:
                user_id = user[0]
                # Update last active
                cursor.execute(
                    'UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE id = ?',
                    (user_id,)
                )
            else:
                # Create new user
                cursor.execute(
                    'INSERT INTO users (phone_number, name) VALUES (?, ?)',
                    (phone_number, name)
                )
                user_id = cursor.lastrowid
                logger.info(f"Created new user {user_id} for phone {phone_number}")
            
            conn.commit()
            return user_id
    
    def store_message(self, phone_number: str, message_body: str, message_type: str):
        """Store a message in the database"""
        user_id = self.get_or_create_user(phone_number)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO messages (user_id, phone_number, message_body, message_type)
                VALUES (?, ?, ?, ?)
            ''', (user_id, phone_number, message_body, message_type))
            
            # Update user's total message count
            cursor.execute(
                'UPDATE users SET total_messages = total_messages + 1 WHERE id = ?',
                (user_id,)
            )
            
            conn.commit()
    
    def store_analysis(self, phone_number: str, original_message: str, analysis):
        """Store symptom analysis results"""
        user_id = self.get_or_create_user(phone_number)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO analyses (
                    user_id, phone_number, original_message, symptoms, 
                    severity, urgency, confidence, recommendations, potential_conditions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                phone_number,
                original_message,
                json.dumps(analysis.symptoms),
                analysis.severity,
                analysis.urgency,
                analysis.confidence,
                json.dumps(analysis.recommendations),
                json.dumps(analysis.potential_conditions)
            ))
            
            conn.commit()
    
    def get_user_info(self, phone_number: str) -> Optional[Dict]:
        """Get user information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, phone_number, name, created_at, last_active, total_messages
                FROM users WHERE phone_number = ?
            ''', (phone_number,))
            
            user = cursor.fetchone()
            if user:
                return {
                    'id': user[0],
                    'phone_number': user[1],
                    'name': user[2],
                    'created_at': user[3],
                    'last_active': user[4],
                    'total_messages': user[5]
                }
            return None
    
    def get_user_message_history(self, phone_number: str, limit: int = 50) -> List[Dict]:
        """Get user's message history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT message_body, message_type, timestamp
                FROM messages
                WHERE phone_number = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (phone_number, limit))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'message_body': row[0],
                    'message_type': row[1],
                    'timestamp': row[2]
                })
            
            return messages
    
    def get_user_analyses(self, phone_number: str, limit: int = 10) -> List[Dict]:
        """Get user's analysis history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT original_message, symptoms, severity, urgency, 
                       confidence, recommendations, potential_conditions, timestamp
                FROM analyses
                WHERE phone_number = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (phone_number, limit))
            
            analyses = []
            for row in cursor.fetchall():
                analyses.append({
                    'original_message': row[0],
                    'symptoms': json.loads(row[1]) if row[1] else [],
                    'severity': row[2],
                    'urgency': row[3],
                    'confidence': row[4],
                    'recommendations': json.loads(row[5]) if row[5] else [],
                    'potential_conditions': json.loads(row[6]) if row[6] else [],
                    'timestamp': row[7]
                })
            
            return analyses
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total users
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            # Total messages
            cursor.execute('SELECT COUNT(*) FROM messages')
            total_messages = cursor.fetchone()[0]
            
            # Total analyses
            cursor.execute('SELECT COUNT(*) FROM analyses')
            total_analyses = cursor.fetchone()[0]
            
            # Active users (last 7 days)
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE last_active >= datetime('now', '-7 days')
            ''')
            active_users_7d = cursor.fetchone()[0]
            
            # Most common severities
            cursor.execute('''
                SELECT severity, COUNT(*) as count
                FROM analyses
                GROUP BY severity
                ORDER BY count DESC
            ''')
            severity_stats = dict(cursor.fetchall())
            
            # Most common urgency levels
            cursor.execute('''
                SELECT urgency, COUNT(*) as count
                FROM analyses
                GROUP BY urgency
                ORDER BY count DESC
            ''')
            urgency_stats = dict(cursor.fetchall())
            
            return {
                'total_users': total_users,
                'total_messages': total_messages,
                'total_analyses': total_analyses,
                'active_users_7d': active_users_7d,
                'severity_distribution': severity_stats,
                'urgency_distribution': urgency_stats,
                'generated_at': datetime.now().isoformat()
            }
    
    def cleanup_old_data(self, days: int = 90):
        """Clean up old data older than specified days"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Delete old messages
            cursor.execute('''
                DELETE FROM messages 
                WHERE timestamp < datetime('now', '-{} days')
            '''.format(days))
            
            # Delete old analyses
            cursor.execute('''
                DELETE FROM analyses 
                WHERE timestamp < datetime('now', '-{} days')
            '''.format(days))
            
            conn.commit()
            logger.info(f"Cleaned up data older than {days} days")
    
    def export_user_data(self, phone_number: str) -> Dict[str, Any]:
        """Export all user data for GDPR compliance"""
        user_info = self.get_user_info(phone_number)
        if not user_info:
            return {}
        
        messages = self.get_user_message_history(phone_number, limit=1000)
        analyses = self.get_user_analyses(phone_number, limit=100)
        
        return {
            'user_info': user_info,
            'messages': messages,
            'analyses': analyses,
            'exported_at': datetime.now().isoformat()
        }
    
    def delete_user_data(self, phone_number: str) -> bool:
        """Delete all user data for GDPR compliance"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                # Delete messages
                cursor.execute('DELETE FROM messages WHERE phone_number = ?', (phone_number,))
                
                # Delete analyses
                cursor.execute('DELETE FROM analyses WHERE phone_number = ?', (phone_number,))
                
                # Delete user
                cursor.execute('DELETE FROM users WHERE phone_number = ?', (phone_number,))
                
                conn.commit()
                logger.info(f"Deleted all data for user {phone_number}")
                return True
                
            except Exception as e:
                logger.error(f"Error deleting user data: {str(e)}")
                conn.rollback()
                return False