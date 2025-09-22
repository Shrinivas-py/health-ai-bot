"""
Health AI Assistant - Core AI logic for analyzing symptoms and providing health advice.
"""
import re
import json
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SymptomAnalysis:
    """Data class for symptom analysis results"""
    symptoms: List[str]
    severity: str  # mild, moderate, severe
    urgency: str   # low, medium, high, emergency
    confidence: float
    recommendations: List[str]
    potential_conditions: List[str]
    is_emergency: bool = False
    response: str = ""

class HealthAI:
    """Main AI health assistant class"""
    
    def __init__(self):
        self.symptom_keywords = self._load_symptom_keywords()
        self.medical_knowledge = self._load_medical_knowledge()
        self.emergency_keywords = [
            'chest pain', 'heart attack', 'stroke', 'seizure', 'unconscious',
            'difficulty breathing', 'severe bleeding', 'poisoning', 'overdose',
            'severe allergic reaction', 'broken bone', 'head injury'
        ]
        
    def _load_symptom_keywords(self) -> Dict:
        """Load symptom keywords and their categories"""
        return {
            'pain': {
                'keywords': ['pain', 'ache', 'hurt', 'sore', 'tender', 'throbbing', 'stabbing'],
                'severity_indicators': {
                    'mild': ['slight', 'minor', 'little'],
                    'moderate': ['moderate', 'noticeable'],
                    'severe': ['severe', 'intense', 'unbearable', 'excruciating']
                }
            },
            'fever': {
                'keywords': ['fever', 'temperature', 'hot', 'chills', 'sweating'],
                'severity_indicators': {
                    'mild': ['low grade', 'slight fever'],
                    'moderate': ['fever', 'high temperature'],
                    'severe': ['high fever', 'burning up']
                }
            },
            'respiratory': {
                'keywords': ['cough', 'breathing', 'shortness of breath', 'wheezing', 'congestion'],
                'severity_indicators': {
                    'mild': ['slight cough', 'light congestion'],
                    'moderate': ['persistent cough', 'difficulty breathing'],
                    'severe': ['severe breathing problems', 'can\'t breathe']
                }
            },
            'digestive': {
                'keywords': ['nausea', 'vomiting', 'diarrhea', 'stomach pain', 'constipation'],
                'severity_indicators': {
                    'mild': ['slight nausea', 'mild stomach upset'],
                    'moderate': ['vomiting', 'stomach pain'],
                    'severe': ['severe vomiting', 'intense stomach pain']
                }
            },
            'neurological': {
                'keywords': ['headache', 'dizziness', 'confusion', 'memory problems'],
                'severity_indicators': {
                    'mild': ['mild headache', 'slight dizziness'],
                    'moderate': ['headache', 'dizzy'],
                    'severe': ['severe headache', 'extreme dizziness', 'confusion']
                }
            }
        }
    
    def _load_medical_knowledge(self) -> Dict:
        """Load medical knowledge base"""
        return {
            'common_conditions': {
                'cold': {
                    'symptoms': ['runny nose', 'sneezing', 'mild cough', 'sore throat'],
                    'recommendations': [
                        'Get plenty of rest',
                        'Drink fluids',
                        'Consider over-the-counter medications',
                        'Monitor symptoms for 7-10 days'
                    ]
                },
                'flu': {
                    'symptoms': ['fever', 'body aches', 'fatigue', 'cough'],
                    'recommendations': [
                        'Rest and isolation',
                        'Increase fluid intake',
                        'Consider antiviral medication if within 48 hours',
                        'Seek medical care if symptoms worsen'
                    ]
                },
                'headache': {
                    'symptoms': ['head pain', 'pressure', 'tension'],
                    'recommendations': [
                        'Rest in a quiet, dark room',
                        'Apply cold or warm compress',
                        'Stay hydrated',
                        'Consider over-the-counter pain relievers'
                    ]
                },
                'stomach_bug': {
                    'symptoms': ['nausea', 'vomiting', 'diarrhea', 'stomach cramps'],
                    'recommendations': [
                        'Stay hydrated with clear fluids',
                        'BRAT diet (bananas, rice, applesauce, toast)',
                        'Rest',
                        'Avoid dairy and fatty foods'
                    ]
                }
            },
            'general_advice': [
                'This is not a substitute for professional medical advice',
                'Consult a healthcare provider for persistent or severe symptoms',
                'Call emergency services for life-threatening situations',
                'Keep track of your symptoms and their progression'
            ]
        }
    
    def analyze_message(self, message: str) -> SymptomAnalysis:
        """Analyze user message for symptoms and provide recommendations"""
        message = message.lower().strip()
        
        # Check for emergency keywords first
        if self._is_emergency(message):
            return self._create_emergency_response(message)
        
        # Extract symptoms
        symptoms = self._extract_symptoms(message)
        
        # Determine severity and urgency
        severity = self._assess_severity(message, symptoms)
        urgency = self._assess_urgency(severity, symptoms)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(symptoms, severity)
        
        # Identify potential conditions
        potential_conditions = self._identify_conditions(symptoms)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(symptoms, message)
        
        return SymptomAnalysis(
            symptoms=symptoms,
            severity=severity,
            urgency=urgency,
            confidence=confidence,
            recommendations=recommendations,
            potential_conditions=potential_conditions
        )
    
    def _is_emergency(self, message: str) -> bool:
        """Check if message indicates an emergency situation"""
        for keyword in self.emergency_keywords:
            if keyword in message:
                return True
        return False
    
    def _create_emergency_response(self, message: str) -> SymptomAnalysis:
        """Create response for emergency situations"""
        return SymptomAnalysis(
            symptoms=['emergency situation detected'],
            severity='severe',
            urgency='emergency',
            confidence=0.9,
            recommendations=[
                '🚨 EMERGENCY: Call emergency services immediately (911)',
                'If possible, go to the nearest emergency room',
                'Do not drive yourself if experiencing severe symptoms',
                'Stay calm and follow emergency operator instructions'
            ],
            potential_conditions=['medical emergency']
        )
    
    def _extract_symptoms(self, message: str) -> List[str]:
        """Extract symptoms from user message"""
        symptoms = []
        
        for category, data in self.symptom_keywords.items():
            for keyword in data['keywords']:
                if keyword in message:
                    symptoms.append(keyword)
        
        # Additional pattern matching for symptoms
        symptom_patterns = [
            r'i have (.*?)(?:\.|$)',
            r'experiencing (.*?)(?:\.|$)',
            r'feeling (.*?)(?:\.|$)',
            r'my (.*?) hurts?',
            r'(.*?) is bothering me'
        ]
        
        for pattern in symptom_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                clean_symptom = match.strip()
                if len(clean_symptom) > 2 and clean_symptom not in symptoms:
                    symptoms.append(clean_symptom)
        
        return symptoms[:10]  # Limit to 10 symptoms
    
    def _assess_severity(self, message: str, symptoms: List[str]) -> str:
        """Assess the severity of symptoms"""
        severity_score = 0
        
        # Check for severity indicators in message
        for category, data in self.symptom_keywords.items():
            for severity, indicators in data['severity_indicators'].items():
                for indicator in indicators:
                    if indicator in message:
                        if severity == 'mild':
                            severity_score += 1
                        elif severity == 'moderate':
                            severity_score += 3
                        elif severity == 'severe':
                            severity_score += 5
        
        # Assess based on number of symptoms
        severity_score += len(symptoms)
        
        if severity_score >= 8:
            return 'severe'
        elif severity_score >= 4:
            return 'moderate'
        else:
            return 'mild'
    
    def _assess_urgency(self, severity: str, symptoms: List[str]) -> str:
        """Assess urgency based on severity and symptoms"""
        if severity == 'severe':
            return 'high'
        elif severity == 'moderate':
            return 'medium'
        else:
            return 'low'
    
    def _generate_recommendations(self, symptoms: List[str], severity: str) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        # Add severity-based recommendations
        if severity == 'severe':
            recommendations.extend([
                'Seek immediate medical attention',
                'Consider visiting an urgent care center or emergency room',
                'Monitor symptoms closely'
            ])
        elif severity == 'moderate':
            recommendations.extend([
                'Consider consulting with a healthcare provider',
                'Monitor symptoms for changes',
                'Rest and self-care measures may help'
            ])
        else:
            recommendations.extend([
                'Try home remedies and self-care',
                'Monitor symptoms for any worsening',
                'Consider over-the-counter treatments if appropriate'
            ])
        
        # Add symptom-specific recommendations
        for symptom in symptoms:
            if 'fever' in symptom:
                recommendations.append('Stay hydrated and consider fever reducers')
            elif 'pain' in symptom:
                recommendations.append('Apply appropriate hot/cold therapy')
            elif 'cough' in symptom:
                recommendations.append('Try throat lozenges or warm liquids')
        
        # Add general advice
        recommendations.extend(self.medical_knowledge['general_advice'])
        
        return list(set(recommendations))  # Remove duplicates
    
    def _identify_conditions(self, symptoms: List[str]) -> List[str]:
        """Identify potential conditions based on symptoms"""
        potential_conditions = []
        
        for condition, data in self.medical_knowledge['common_conditions'].items():
            match_count = 0
            for condition_symptom in data['symptoms']:
                for user_symptom in symptoms:
                    if condition_symptom.lower() in user_symptom.lower():
                        match_count += 1
            
            if match_count >= 2:  # Require at least 2 matching symptoms
                potential_conditions.append(condition.replace('_', ' ').title())
        
        return potential_conditions
    
    def _calculate_confidence(self, symptoms: List[str], message: str) -> float:
        """Calculate confidence score for the analysis"""
        base_confidence = 0.6
        
        # Increase confidence based on number of recognized symptoms
        symptom_bonus = min(len(symptoms) * 0.1, 0.3)
        
        # Increase confidence based on message length and detail
        message_length_bonus = min(len(message.split()) * 0.01, 0.1)
        
        return min(base_confidence + symptom_bonus + message_length_bonus, 0.95)
    
    def format_response(self, analysis: SymptomAnalysis, user_name: str = "there") -> str:
        """Format the analysis into a user-friendly response"""
        
        if analysis.urgency == 'emergency':
            return self._format_emergency_response()
        
        response_parts = []
        
        # Greeting and acknowledgment
        response_parts.append(f"Hi {user_name}! I've analyzed your symptoms.")
        
        # Symptoms summary
        if analysis.symptoms:
            symptoms_text = ", ".join(analysis.symptoms[:5])  # Limit to 5 symptoms
            response_parts.append(f"📋 Symptoms identified: {symptoms_text}")
        
        # Severity and urgency
        response_parts.append(f"📊 Severity: {analysis.severity.title()}")
        
        # Potential conditions
        if analysis.potential_conditions:
            conditions_text = ", ".join(analysis.potential_conditions)
            response_parts.append(f"🔍 This might be related to: {conditions_text}")
        
        # Recommendations
        response_parts.append("💡 Recommendations:")
        for i, rec in enumerate(analysis.recommendations[:6], 1):  # Limit to 6 recommendations
            response_parts.append(f"{i}. {rec}")
        
        # Confidence and disclaimer
        response_parts.append(f"ℹ️ Confidence: {analysis.confidence:.0%}")
        response_parts.append("⚠️ This is AI-generated advice. Always consult healthcare professionals for serious concerns.")
        
        return "\n\n".join(response_parts)
    
    def _format_emergency_response(self) -> str:
        """Format emergency response"""
        return """🚨 EMERGENCY DETECTED 🚨

This appears to be a medical emergency!

IMMEDIATE ACTIONS:
1. Call emergency services (911) NOW
2. If possible, go to the nearest emergency room
3. Do not drive yourself
4. Stay calm and follow emergency operator instructions

This AI cannot provide emergency medical care. Please seek immediate professional help.

Stay safe! 🙏"""

    def get_health_tips(self) -> List[str]:
        """Get general health tips"""
        return [
            "💧 Stay hydrated - drink 8 glasses of water daily",
            "🏃‍♂️ Get regular exercise - at least 30 minutes daily",
            "😴 Maintain good sleep hygiene - 7-9 hours per night",
            "🥗 Eat a balanced diet with plenty of fruits and vegetables",
            "🧼 Wash your hands regularly to prevent infections",
            "😌 Manage stress through relaxation techniques",
            "🩺 Schedule regular check-ups with your healthcare provider"
        ]