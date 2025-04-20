from typing import Dict, Any, List, Tuple, Optional
import logging

from app.services.validators.base_validator import BaseValidator

logger = logging.getLogger(__name__)

class ThresholdValidator(BaseValidator):
    """Validator that applies simple thresholds to responses"""
    
    async def validate(self, task_id: str, response: Any, session_id: str, **kwargs) -> Tuple[float, float, List[Dict[str, Any]], Optional[str]]:
        time_spent_ms = kwargs.get('time_spent_ms', 0)
        task_type = kwargs.get('task_type', '')
        
        issues = []
        quality_score = 1.0  # Start with perfect score and subtract based on issues
        
        # Check minimum time threshold
        min_time_quality, min_time_issues = self._check_minimum_time(time_spent_ms, task_type)
        quality_score *= min_time_quality
        issues.extend(min_time_issues)
        
        # Check response format and completeness
        format_quality, format_issues = self._check_response_format(response, task_type)
        quality_score *= format_quality
        issues.extend(format_issues)
        
        # Check response content quality
        content_quality, content_issues = self._check_response_content(response, task_type)
        quality_score *= content_quality
        issues.extend(content_issues)
        
        # For threshold validation, confidence is relatively high
        confidence = 0.8
        
        feedback = None
        if issues:
            feedback = "Please ensure your response meets our requirements."
        
        return quality_score, confidence, issues, feedback
    
    def _check_minimum_time(self, time_spent_ms: int, task_type: str) -> Tuple[float, List[Dict[str, Any]]]:
        """Check if the response meets minimum time requirements"""
        issues = []
        
        # Define minimum time thresholds for different task types (in milliseconds)
        min_times = {
            "vqa": 1500,  # Visual Question Answering
            "text_classification": 1000,
            "multiple_choice": 800,
            "open_text": 2000,
            "default": 1000  # Default minimum time
        }
        
        # Get the minimum time for this task type
        min_time = min_times.get(task_type, min_times["default"])
        
        if time_spent_ms < min_time:
            issues.append({
                "type": "insufficient_time",
                "message": f"Response time ({time_spent_ms}ms) is below the minimum expected time ({min_time}ms)"
            })
            
            # Calculate quality reduction based on how much below threshold
            if time_spent_ms <= 0:  # Invalid time
                return 0.3, issues
            else:
                # Scale quality from 0.5 to 0.9 based on how close to threshold
                quality = 0.5 + (0.4 * time_spent_ms / min_time)
                return min(0.9, quality), issues
        
        return 1.0, issues  # No issues, maintain quality score
    
    def _check_response_format(self, response: Any, task_type: str) -> Tuple[float, List[Dict[str, Any]]]:
        """Check if the response meets format requirements"""
        issues = []
        
        # Different format checks based on task type
        if task_type == "multiple_choice":
            if not isinstance(response, (str, int)) or not response:
                issues.append({
                    "type": "invalid_format",
                    "message": "Multiple choice response must be a non-empty string or integer"
                })
                return 0.5, issues
                
        elif task_type == "open_text":
            if not isinstance(response, str):
                issues.append({
                    "type": "invalid_format",
                    "message": "Open text response must be a string"
                })
                return 0.5, issues
            
            # Check minimum length
            if len(response.strip()) < 5:  # Arbitrary minimum length
                issues.append({
                    "type": "insufficient_content",
                    "message": "Response is too short"
                })
                return 0.7, issues
                
        elif task_type == "vqa":  # Visual Question Answering
            if not isinstance(response, str) or not response:
                issues.append({
                    "type": "invalid_format",
                    "message": "VQA response must be a non-empty string"
                })
                return 0.5, issues
        
        # Add more task types as needed
        
        return 1.0, issues  # No issues, maintain quality score
    
    def _check_response_content(self, response: Any, task_type: str) -> Tuple[float, List[Dict[str, Any]]]:
        """Check the content quality of the response"""
        issues = []
        
        if isinstance(response, str):
            # Check for very repetitive content
            repetition_score = self._check_repetition(response)
            if repetition_score < 0.7:
                issues.append({
                    "type": "repetitive_content",
                    "message": "Response contains excessive repetition"
                })
                return repetition_score, issues
            
            # Check for gibberish/random text
            if task_type == "open_text" and len(response) > 10:
                gibberish_score = self._check_gibberish(response)
                if gibberish_score < 0.7:
                    issues.append({
                        "type": "low_quality_text",
                        "message": "Response appears to be low-quality or random text"
                    })
                    return gibberish_score, issues
        
        return 1.0, issues  # No issues, maintain quality score
    
    def _check_repetition(self, text: str) -> float:
        """Check for repetitive patterns in text
        
        Returns a quality score from 0.0 to 1.0
        """
        if not text or len(text) < 5:
            return 1.0  # Too short to check
        
        import re
        
        # Check for repeated characters
        char_repeats = re.findall(r'(.)\1{3,}', text)  # Same character 4+ times in a row
        if char_repeats and len(char_repeats) > 2:
            return 0.6
        
        # Check for repeated words or phrases
        words = text.lower().split()
        if len(words) >= 6:
            word_set = set(words)
            unique_ratio = len(word_set) / len(words)
            
            if unique_ratio < 0.3:  # Less than 30% unique words
                return 0.5
            elif unique_ratio < 0.5:  # Less than 50% unique words
                return 0.7
        
        return 1.0
    
    def _check_gibberish(self, text: str) -> float:
        """Check if text appears to be gibberish or random input
        
        Returns a quality score from 0.0 to 1.0
        """
        # This would be a more sophisticated implementation in a real system
        # For now, we'll use some simple heuristics
        
        # Normalize text
        text = text.lower().strip()
        
        # Check for normal word patterns
        import re
        words = re.findall(r'\b[a-z]{1,20}\b', text)  # Find all words
        total_words = len(words) if words else 0
        
        if total_words == 0:
            return 0.5  # No recognizable words
        
        # Check typical word length distribution
        word_lengths = [len(w) for w in words]
        avg_length = sum(word_lengths) / len(word_lengths) if word_lengths else 0
        
        # Extremely short or long average word length is suspicious
        if avg_length < 2.5 or avg_length > 10:
            return 0.6
        
        # More sophisticated checks would analyze character frequency, n-grams,
        # language models, etc., but this is a simple starting point
        
        return 1.0  # Default to assuming content is fine
