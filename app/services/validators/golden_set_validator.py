"""
Golden Set Validator for quality assurance.

This validator compares submitted responses against known golden set examples
with expected answers, providing high-confidence validation.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
import json
from datetime import datetime

from app.db.repositories.golden_set_repository import GoldenSetRepository

logger = logging.getLogger(__name__)

class GoldenSetValidator:
    """
    Validator that compares responses against golden set examples.
    
    Golden sets are curated examples with known correct answers that serve as
    a high-confidence validation method and training tool for quality assurance.
    """
    
    def __init__(self, golden_set_repository: GoldenSetRepository):
        """
        Initialize the golden set validator.
        
        Args:
            golden_set_repository: Repository for golden set data access
        """
        self.golden_set_repository = golden_set_repository
    
    async def validate(
        self, task_id: str, response: Dict[str, Any], session_id: str, **kwargs
    ) -> Tuple[float, float, List[Dict[str, Any]], Optional[str]]:
        """
        Validate a response against a golden set example.
        
        Args:
            task_id: ID of the task being validated
            response: The user's response to validate
            session_id: Session ID of the user
            **kwargs: Additional validation context
            
        Returns:
            Tuple containing:
            - quality_score (float): 0-1 score indicating response quality
            - confidence (float): 0-1 score indicating confidence in the validation
            - issues (list): List of detected issues
            - feedback (str): Optional feedback for the user
        """
        # Retrieve the golden set for this task
        golden_set = self.golden_set_repository.get_by_task_id(task_id)
        
        if not golden_set:
            logger.warning(f"No golden set found for task {task_id}")
            return 0.0, 0.0, [], None
        
        # Get the expected response and allowed variation
        expected_response = golden_set.expected_response
        allowed_variation = golden_set.allowed_variation
        
        # Initialize variables
        quality_score = 0.0
        confidence = 1.0  # Golden sets provide high confidence
        issues = []
        feedback = None
        
        # Compare response with expected response
        match_score = self._calculate_match_score(response, expected_response)
        
        # Apply quality score based on match and allowed variation
        if match_score >= (1.0 - allowed_variation):
            # Response is within acceptable variation
            quality_score = match_score
            feedback = "Response matches the expected answer."
        else:
            # Response differs too much from expected
            quality_score = match_score
            issues.append({
                "type": "golden_set_mismatch",
                "severity": "high",
                "description": "Response does not match expected answer",
                "score_impact": 1.0 - match_score
            })
            
            # Provide feedback based on hints if available
            if golden_set.hints and len(golden_set.hints) > 0:
                feedback = golden_set.hints[0]  # Use first hint as feedback
            else:
                feedback = "Response does not match the expected answer."
        
        # Link validation to golden set for feedback loop
        if kwargs.get("validation_id"):
            self.golden_set_repository.link_validation(
                golden_set.id, kwargs.get("validation_id")
            )
        
        logger.info(
            f"Golden set validation for task {task_id}: "
            f"quality_score={quality_score}, confidence={confidence}"
        )
        
        return quality_score, confidence, issues, feedback
    
    def _calculate_match_score(
        self, response: Dict[str, Any], expected_response: Dict[str, Any]
    ) -> float:
        """
        Calculate how closely the response matches the expected response.
        
        This implementation handles different response types:
        - For text responses: uses similarity metrics
        - For multiple choice: exact matching
        - For structured data: field-by-field comparison
        
        Args:
            response: The actual response
            expected_response: The expected golden set response
            
        Returns:
            float: 0-1 score indicating match quality
        """
        # Handle different response types
        if isinstance(response, str) and isinstance(expected_response, str):
            # Text response: use simple string matching for now
            # In a real implementation, this would use more sophisticated text similarity metrics
            return self._calculate_text_similarity(response, expected_response)
            
        elif isinstance(response, (int, float)) and isinstance(expected_response, (int, float)):
            # Numeric response
            return self._calculate_numeric_similarity(response, expected_response)
            
        elif isinstance(response, list) and isinstance(expected_response, list):
            # List response (e.g., multiple choice)
            return self._calculate_list_similarity(response, expected_response)
            
        elif isinstance(response, dict) and isinstance(expected_response, dict):
            # Structured response
            return self._calculate_dict_similarity(response, expected_response)
            
        else:
            # Unknown format, use string representation
            return self._calculate_text_similarity(str(response), str(expected_response))
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings.
        
        In a production system, this would use more sophisticated NLP techniques.
        This simple implementation uses character-level similarity.
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            float: 0-1 similarity score
        """
        # Normalize texts
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        if not text1 and not text2:
            return 1.0
        if not text1 or not text2:
            return 0.0
            
        # Simple similarity based on Levenshtein distance
        try:
            import Levenshtein
            distance = Levenshtein.distance(text1, text2)
            max_len = max(len(text1), len(text2))
            return 1.0 - (distance / max_len)
        except ImportError:
            # Fallback if Levenshtein is not available
            # Simple exact match
            return 1.0 if text1 == text2 else 0.0
    
    def _calculate_numeric_similarity(self, num1: float, num2: float) -> float:
        """
        Calculate similarity between two numbers.
        
        Args:
            num1: First number
            num2: Second number
            
        Returns:
            float: 0-1 similarity score
        """
        # Handle edge cases
        if num1 == num2:
            return 1.0
            
        # Calculate difference percentage
        max_val = max(abs(num1), abs(num2))
        if max_val == 0:
            return 1.0  # Both are zero
            
        diff_percentage = abs(num1 - num2) / max_val
        
        # Convert to similarity score (1.0 means identical)
        similarity = max(0.0, 1.0 - diff_percentage)
        
        return similarity
    
    def _calculate_list_similarity(self, list1: list, list2: list) -> float:
        """
        Calculate similarity between two lists.
        
        For multiple choice answers, order may or may not matter.
        
        Args:
            list1: First list
            list2: Second list
            
        Returns:
            float: 0-1 similarity score
        """
        if not list1 and not list2:
            return 1.0
        if not list1 or not list2:
            return 0.0
            
        # For simplicity, we'll check if lists contain the same elements
        # (order doesn't matter for this implementation)
        set1 = set(str(item) for item in list1)
        set2 = set(str(item) for item in list2)
        
        # Jaccard similarity
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_dict_similarity(self, dict1: dict, dict2: dict) -> float:
        """
        Calculate similarity between two dictionaries.
        
        Compares keys and values recursively.
        
        Args:
            dict1: First dictionary
            dict2: Second dictionary
            
        Returns:
            float: 0-1 similarity score
        """
        if not dict1 and not dict2:
            return 1.0
        if not dict1 or not dict2:
            return 0.0
            
        # Get all unique keys
        all_keys = set(dict1.keys()).union(set(dict2.keys()))
        
        if not all_keys:
            return 1.0
            
        # Calculate similarity for each key
        total_similarity = 0.0
        
        for key in all_keys:
            # If key is missing in either dict, similarity for this key is 0
            if key not in dict1 or key not in dict2:
                continue
                
            # Get values
            val1 = dict1[key]
            val2 = dict2[key]
            
            # Calculate similarity based on value type
            if isinstance(val1, str) and isinstance(val2, str):
                key_similarity = self._calculate_text_similarity(val1, val2)
            elif isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                key_similarity = self._calculate_numeric_similarity(val1, val2)
            elif isinstance(val1, list) and isinstance(val2, list):
                key_similarity = self._calculate_list_similarity(val1, val2)
            elif isinstance(val1, dict) and isinstance(val2, dict):
                key_similarity = self._calculate_dict_similarity(val1, val2)
            else:
                # Different types, use string representation
                key_similarity = self._calculate_text_similarity(str(val1), str(val2))
                
            total_similarity += key_similarity
        
        # Average similarity across all keys
        present_keys = sum(1 for k in all_keys if k in dict1 and k in dict2)
        return total_similarity / present_keys if present_keys > 0 else 0.0
