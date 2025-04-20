from typing import Dict, Any, List, Tuple, Optional
import logging
import statistics
import time

from app.services.validators.base_validator import BaseValidator
from app.db.repositories.validation_repository import ValidationRepository

logger = logging.getLogger(__name__)

class BotDetector(BaseValidator):
    """Validator that detects bot-like behavior in responses"""
    
    def __init__(self, validation_repository: ValidationRepository):
        self.validation_repository = validation_repository
    
    async def validate(self, task_id: str, response: Any, session_id: str, **kwargs) -> Tuple[float, float, List[Dict[str, Any]], Optional[str]]:
        time_spent_ms = kwargs.get('time_spent_ms', 0)
        task_type = kwargs.get('task_type', '')
        
        issues = []
        suspicion_score = 0.0  # 0.0 = definitely human, 1.0 = definitely bot
        
        # Check for suspiciously fast responses
        time_suspicion = self._check_response_time(time_spent_ms, task_type)
        suspicion_score += time_suspicion * 0.4  # Weight: 40%
        
        if time_suspicion > 0.8:
            issues.append({
                "type": "suspiciously_fast_response",
                "message": "Response submitted unusually quickly",
                "time_spent_ms": time_spent_ms
            })
        
        # Check for pattern repetition
        pattern_suspicion = await self._check_pattern_repetition(session_id, response)
        suspicion_score += pattern_suspicion * 0.3  # Weight: 30%
        
        if pattern_suspicion > 0.8:
            issues.append({
                "type": "repetitive_pattern",
                "message": "Suspiciously similar response pattern to previous submissions"
            })
        
        # Check for random clicking
        random_suspicion = self._check_random_clicking(response)
        suspicion_score += random_suspicion * 0.3  # Weight: 30%
        
        if random_suspicion > 0.8:
            issues.append({
                "type": "random_clicking",
                "message": "Response pattern suggests random clicking or input"
            })
        
        # Calculate the final quality score (inverse of suspicion score)
        quality_score = 1.0 - suspicion_score
        
        # Confidence in our assessment
        # For bot detection, confidence increases with more extreme scores
        confidence = 0.5 + abs(suspicion_score - 0.5)
        
        feedback = None
        if suspicion_score > 0.8:
            feedback = "Your response appears automated. Please take more time to consider your answers."
        
        return quality_score, confidence, issues, feedback
    
    def _check_response_time(self, time_spent_ms: int, task_type: str) -> float:
        """Check if the response time is suspiciously fast
        
        Returns a suspicion score from 0.0 to 1.0
        """
        # Define expected minimum times for different task types (in milliseconds)
        min_expected_times = {
            "vqa": 2000,  # Visual Question Answering
            "text_classification": 1500,
            "multiple_choice": 1000,
            "open_text": 3000,
            "default": 1500  # Default minimum time
        }
        
        # Get the minimum expected time for this task type
        min_time = min_expected_times.get(task_type, min_expected_times["default"])
        
        # Calculate suspicion score based on time spent
        if time_spent_ms <= 0:  # Invalid time
            return 1.0
        elif time_spent_ms < min_time * 0.5:  # Less than half the expected minimum time
            return 1.0
        elif time_spent_ms < min_time:  # Less than the expected minimum time
            # Linear scale from 0.5 to 1.0 as time approaches min_time
            return 0.5 + 0.5 * (1 - (time_spent_ms / min_time))
        else:  # Reasonable time
            return 0.0
    
    async def _check_pattern_repetition(self, session_id: str, current_response: Any) -> float:
        """Check for repetitive patterns in user responses
        
        Returns a suspicion score from 0.0 to 1.0
        """
        # Get recent validations for this session
        recent_validations = self.validation_repository.get_recent_by_session(session_id, limit=5)
        
        if not recent_validations or len(recent_validations) < 2:
            return 0.0  # Not enough history to detect patterns
        
        # Extract previous responses
        previous_responses = [v.response for v in recent_validations]
        
        # Check for exact same response repeated
        if any(self._responses_equal(current_response, prev_response) for prev_response in previous_responses):
            return 1.0
        
        # Check for pattern in response times
        response_times = [v.time_spent_ms for v in recent_validations if v.time_spent_ms is not None]
        if response_times and len(response_times) >= 3:
            time_pattern_score = self._detect_time_pattern(response_times)
            if time_pattern_score > 0.8:
                return time_pattern_score
        
        # More sophisticated pattern detection would go here
        # This is a simplified implementation
        return 0.0
    
    def _responses_equal(self, response1: Any, response2: Any) -> bool:
        """Check if two responses are equal"""
        if isinstance(response1, dict) and isinstance(response2, dict):
            # Compare dictionaries
            return response1 == response2
        elif isinstance(response1, str) and isinstance(response2, str):
            # Case-insensitive string comparison
            return response1.lower().strip() == response2.lower().strip()
        else:
            # Direct comparison for other types
            return response1 == response2
    
    def _detect_time_pattern(self, times: List[int]) -> float:
        """Detect suspicious patterns in response times"""
        if len(times) < 3:
            return 0.0
        
        # Check if all times are nearly identical (bot-like behavior)
        mean_time = statistics.mean(times)
        stdev = statistics.stdev(times) if len(times) > 1 else 0
        
        if stdev == 0:  # All times exactly the same
            return 1.0
        
        # Calculate coefficient of variation (CV)
        cv = stdev / mean_time if mean_time > 0 else float('inf')
        
        # If CV is very low, times are suspiciously consistent
        if cv < 0.1:  # Less than 10% variation
            return 0.9
        elif cv < 0.2:  # Less than 20% variation
            return 0.7
        else:
            return 0.0  # Normal variation
    
    def _check_random_clicking(self, response: Any) -> float:
        """Check for signs of random clicking or input
        
        Returns a suspicion score from 0.0 to 1.0
        """
        # This would be a complex implementation in a real system
        # For now, we'll provide a simplified version
        
        if isinstance(response, str):
            # Check for keyboard mashing in text
            return self._detect_keyboard_mashing(response)
        elif isinstance(response, list) and len(response) > 0:
            # Check for random selection in multiple choice
            return self._detect_random_selection(response)
        elif isinstance(response, dict) and len(response) > 0:
            # Check for random input in structured data
            return self._detect_random_structured_input(response)
        else:
            return 0.0  # Can't detect randomness for this type
    
    def _detect_keyboard_mashing(self, text: str) -> float:
        """Detect keyboard mashing in text"""
        if not text or len(text.strip()) == 0:
            return 1.0  # Empty text is suspicious
        
        # Check for repetitive characters
        import re
        if re.search(r'(.)\1{4,}', text):  # Same character repeated 5+ times
            return 0.8
        
        # Check for random character sequences
        # This is a very simplified check - real implementation would be more sophisticated
        consonant_clusters = re.findall(r'[bcdfghjklmnpqrstvwxyz]{5,}', text.lower())
        if consonant_clusters and len(max(consonant_clusters, key=len)) > 6:
            return 0.7
        
        return 0.0
    
    def _detect_random_selection(self, selections: List) -> float:
        """Detect random selection in multiple choice"""
        # In a real implementation, this would analyze patterns across multiple submissions
        # For now, we'll return a default low suspicion score
        return 0.0
    
    def _detect_random_structured_input(self, data: Dict) -> float:
        """Detect random input in structured data"""
        # In a real implementation, this would check for unusual combinations or values
        # For now, we'll return a default low suspicion score
        return 0.0
