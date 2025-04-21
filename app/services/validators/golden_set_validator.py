from typing import Dict, Any, List, Optional, Tuple
import logging
import json
from datetime import datetime

from app.db.repositories.golden_set_repository import GoldenSetRepository

logger = logging.getLogger(__name__)

class GoldenSetValidator:
    """
    Validator for comparing task responses against golden set examples.
    
    This validator checks if a submitted response matches the expected response
    in a golden set item within the allowed variation.
    """
    
    def __init__(self, golden_set_repository: GoldenSetRepository):
        self.golden_set_repository = golden_set_repository
    
    async def validate(
        self, task_id: str, response: Any, session_id: str, **kwargs
    ) -> Tuple[float, float, List[Dict[str, Any]], Optional[str]]:
        """
        Validate a response against a golden set item.
        
        Args:
            task_id: Task ID being validated
            response: User's response to validate
            session_id: Session ID of the user
            **kwargs: Additional validation parameters
            
        Returns:
            Tuple containing:
            - quality_score (float): 0.0-1.0 score representing response quality
            - confidence (float): 0.0-1.0 confidence in the validation result
            - issues (List[Dict]): Any issues detected during validation
            - feedback (Optional[str]): Optional feedback message for the user
        """
        logger.info(f"Validating task {task_id} using golden set method")
        
        # Try to find the golden set for this task
        golden_set = self.golden_set_repository.get_by_task_id(task_id)
        if not golden_set:
            logger.warning(f"No golden set found for task {task_id}")
            return 0.0, 0.0, [{"type": "error", "message": "No golden set found"}], None
        
        # Log golden set details for debugging
        logger.debug(f"Found golden set {golden_set.id} for task {task_id}")
        
        # Compare response with expected response based on the response type
        quality_score, issues = self._compare_responses(response, golden_set.expected_response, golden_set.allowed_variation)
        
        # High confidence since we're comparing against a known correct answer
        confidence = 1.0
        
        # Generate feedback based on quality score
        feedback = self._generate_feedback(quality_score, golden_set.hints, issues)
        
        # Record validation result in the golden set's performance history
        self._record_validation_result(golden_set.id, quality_score, session_id)
        
        return quality_score, confidence, issues, feedback
    
    def _compare_responses(self, user_response: Any, expected_response: Any, allowed_variation: float) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Compare user response with expected response.
        
        Different comparison methods are used based on the type of response:
        - Exact match for strings, booleans, and numbers (within variation)
        - Fuzzy matching for text responses
        - Semantic matching for complex responses
        
        Args:
            user_response: User's submitted response
            expected_response: Expected response from golden set
            allowed_variation: Allowed deviation from expected response
            
        Returns:
            Tuple containing:
            - quality_score (float): 0.0-1.0 score representing match quality
            - issues (List[Dict]): Any issues detected during comparison
        """
        issues = []
        
        # Handle different response types
        if isinstance(expected_response, (str, int, float, bool)):
            return self._compare_simple_response(user_response, expected_response, allowed_variation, issues)
        elif isinstance(expected_response, dict):
            return self._compare_dict_response(user_response, expected_response, allowed_variation, issues)
        elif isinstance(expected_response, list):
            return self._compare_list_response(user_response, expected_response, allowed_variation, issues)
        else:
            issues.append({"type": "error", "message": f"Unsupported response type: {type(expected_response)}"})
            return 0.0, issues
    
    def _compare_simple_response(self, user_response: Any, expected_response: Any, allowed_variation: float, issues: List[Dict[str, Any]]) -> Tuple[float, List[Dict[str, Any]]]:
        """Compare simple response types (string, number, boolean)."""
        # Handle string comparison (case-insensitive for text)
        if isinstance(expected_response, str):
            if isinstance(user_response, str):
                # For longer text, use fuzzy matching
                if len(expected_response) > 20:
                    return self._fuzzy_text_compare(user_response, expected_response, issues)
                # For shorter text, use case-insensitive exact matching
                elif user_response.lower() == expected_response.lower():
                    return 1.0, issues
                else:
                    issues.append({
                        "type": "mismatch", 
                        "message": "Response doesn't match expected value",
                        "expected": expected_response,
                        "actual": user_response
                    })
                    return 0.0, issues
            else:
                issues.append({
                    "type": "type_error", 
                    "message": f"Expected string but got {type(user_response).__name__}"
                })
                return 0.0, issues
                
        # Handle numeric comparison with allowed variation
        elif isinstance(expected_response, (int, float)):
            if isinstance(user_response, (int, float)):
                if expected_response == 0:
                    # Avoid division by zero
                    if abs(user_response) <= allowed_variation:
                        return 1.0, issues
                else:
                    # Calculate relative error
                    relative_error = abs(user_response - expected_response) / abs(expected_response)
                    if relative_error <= allowed_variation:
                        return 1.0, issues
                    else:
                        # Partial credit based on how close the answer is
                        quality_score = max(0, 1.0 - (relative_error / (allowed_variation * 3)))
                        issues.append({
                            "type": "variation", 
                            "message": f"Response outside allowed variation of {allowed_variation}",
                            "expected": expected_response,
                            "actual": user_response
                        })
                        return quality_score, issues
            else:
                issues.append({
                    "type": "type_error", 
                    "message": f"Expected number but got {type(user_response).__name__}"
                })
                return 0.0, issues
                
        # Handle boolean comparison
        elif isinstance(expected_response, bool):
            if isinstance(user_response, bool):
                if user_response == expected_response:
                    return 1.0, issues
                else:
                    issues.append({
                        "type": "mismatch", 
                        "message": "Response doesn't match expected value",
                        "expected": expected_response,
                        "actual": user_response
                    })
                    return 0.0, issues
            else:
                issues.append({
                    "type": "type_error", 
                    "message": f"Expected boolean but got {type(user_response).__name__}"
                })
                return 0.0, issues
        
        # Fallback for unhandled types
        issues.append({
            "type": "error", 
            "message": f"Unsupported response type for simple comparison: {type(expected_response)}"
        })
        return 0.0, issues
    
    def _fuzzy_text_compare(self, user_text: str, expected_text: str, issues: List[Dict[str, Any]]) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Compare text responses using fuzzy matching.
        
        This is useful for free-form text responses where exact matching would be too strict.
        """
        try:
            # Simple approach: check keyword presence and similarity
            user_text_lower = user_text.lower()
            expected_text_lower = expected_text.lower()
            
            # Extract key words (words longer than 3 chars, excluding common stop words)
            # This is a simplified approach - in production would use NLP techniques
            stop_words = {"the", "and", "are", "for", "was", "not", "with", "this", "that"}
            expected_keywords = [word for word in expected_text_lower.split() 
                                if len(word) > 3 and word not in stop_words]
            
            # Count how many expected keywords are present in user response
            keywords_found = sum(1 for kw in expected_keywords if kw in user_text_lower)
            
            if not expected_keywords:
                return 1.0, issues  # No keywords to match against
                
            # Calculate match quality based on keyword coverage
            quality_score = keywords_found / len(expected_keywords)
            
            # Add issues if quality is not perfect
            if quality_score < 1.0:
                missing_keywords = [kw for kw in expected_keywords if kw not in user_text_lower]
                issues.append({
                    "type": "partial_match",
                    "message": f"Response only partially matches expected content",
                    "missing_keywords": missing_keywords[:5],  # Limit to first 5 missing keywords
                    "match_quality": quality_score
                })
                
            return quality_score, issues
            
        except Exception as e:
            logger.error(f"Error in fuzzy text comparison: {str(e)}")
            issues.append({
                "type": "error",
                "message": f"Error comparing text responses: {str(e)}"
            })
            return 0.0, issues
    
    def _compare_dict_response(self, user_response: Any, expected_response: Dict, allowed_variation: float, issues: List[Dict[str, Any]]) -> Tuple[float, List[Dict[str, Any]]]:
        """Compare dictionary responses by matching keys and values."""
        if not isinstance(user_response, dict):
            issues.append({
                "type": "type_error",
                "message": f"Expected dictionary but got {type(user_response).__name__}"
            })
            return 0.0, issues
        
        # Check that all expected keys are present
        total_keys = len(expected_response)
        keys_matched = 0
        values_matched = 0
        
        for key, expected_value in expected_response.items():
            if key in user_response:
                keys_matched += 1
                # Recursively compare the values
                value_score, value_issues = self._compare_responses(
                    user_response[key], expected_value, allowed_variation
                )
                values_matched += value_score
                
                # Add any value issues to the main issues list
                for issue in value_issues:
                    issue["key"] = key  # Add key information to issue
                    issues.append(issue)
        
        # Calculate overall score based on keys present and value matches
        key_coverage = keys_matched / total_keys if total_keys > 0 else 0
        value_quality = values_matched / total_keys if total_keys > 0 else 0
        
        # Overall score weights key presence and value correctness
        quality_score = 0.4 * key_coverage + 0.6 * value_quality
        
        # Add summary issue if not perfect
        if quality_score < 1.0:
            missing_keys = [k for k in expected_response.keys() if k not in user_response]
            if missing_keys:
                issues.append({
                    "type": "missing_keys",
                    "message": f"Response missing expected keys",
                    "missing_keys": missing_keys
                })
        
        return quality_score, issues
    
    def _compare_list_response(self, user_response: Any, expected_response: List, allowed_variation: float, issues: List[Dict[str, Any]]) -> Tuple[float, List[Dict[str, Any]]]:
        """Compare list responses by matching items."""
        if not isinstance(user_response, list):
            issues.append({
                "type": "type_error",
                "message": f"Expected list but got {type(user_response).__name__}"
            })
            return 0.0, issues
        
        # Empty lists match perfectly
        if not expected_response:
            return 1.0 if not user_response else 0.0, issues
        
        # Check list lengths
        if len(user_response) != len(expected_response):
            issues.append({
                "type": "length_mismatch",
                "message": f"Expected list of length {len(expected_response)} but got {len(user_response)}",
                "expected_length": len(expected_response),
                "actual_length": len(user_response)
            })
            # Continue evaluation but note the mismatch
        
        # For simple item types, check for order-independent matching
        # This works well for lists of strings, numbers, etc.
        if all(isinstance(x, (str, int, float, bool)) for x in expected_response):
            return self._compare_simple_lists(user_response, expected_response, issues)
        
        # For complex types, try to match items in order
        total_items = len(expected_response)
        matched_quality = 0
        
        for i, expected_item in enumerate(expected_response):
            if i < len(user_response):
                item_score, item_issues = self._compare_responses(
                    user_response[i], expected_item, allowed_variation
                )
                matched_quality += item_score
                
                # Add index information to issues
                for issue in item_issues:
                    issue["index"] = i
                    issues.append(issue)
        
        # Calculate quality as ratio of matched quality to total items
        quality_score = matched_quality / total_items
        
        return quality_score, issues
    
    def _compare_simple_lists(self, user_list: List, expected_list: List, issues: List[Dict[str, Any]]) -> Tuple[float, List[Dict[str, Any]]]:
        """Compare lists of simple items (strings, numbers, booleans)."""
        # Convert both lists to sets for order-independent comparison
        # Note: This only works well for lists of simple, hashable items
        try:
            expected_set = set(expected_list)
            user_set = set(user_list)
            
            # Find intersection and calculate coverage
            common_items = expected_set.intersection(user_set)
            expected_coverage = len(common_items) / len(expected_set) if expected_set else 1.0
            
            # Penalize for extra items not in expected set
            extra_items = user_set - expected_set
            precision = len(common_items) / len(user_set) if user_set else 1.0
            
            # Combine as F1-like score (harmonic mean of recall and precision)
            if expected_coverage + precision > 0:
                quality_score = 2 * (expected_coverage * precision) / (expected_coverage + precision)
            else:
                quality_score = 0.0
            
            # Add issues if quality is not perfect
            if quality_score < 1.0:
                missing_items = expected_set - user_set
                if missing_items:
                    issues.append({
                        "type": "missing_items",
                        "message": f"Response missing expected items",
                        "missing_items": list(missing_items)[:5]  # Limit to 5 items
                    })
                
                if extra_items:
                    issues.append({
                        "type": "extra_items",
                        "message": f"Response contains unexpected items",
                        "extra_items": list(extra_items)[:5]  # Limit to 5 items
                    })
            
            return quality_score, issues
            
        except Exception as e:
            # Fallback to item-by-item comparison if sets don't work
            logger.warning(f"Error in set-based list comparison: {str(e)}, falling back to item comparison")
            
            # Count matching items regardless of order
            matches = 0
            for expected_item in expected_list:
                if expected_item in user_list:
                    matches += 1
            
            quality_score = matches / len(expected_list) if expected_list else 1.0
            
            if quality_score < 1.0:
                issues.append({
                    "type": "partial_match",
                    "message": f"List items only partially match",
                    "match_ratio": quality_score
                })
            
            return quality_score, issues
    
    def _generate_feedback(self, quality_score: float, hints: List[str], issues: List[Dict[str, Any]]) -> Optional[str]:
        """
        Generate feedback message based on quality score and detected issues.
        
        Args:
            quality_score: Quality score (0.0-1.0)
            hints: List of hints associated with the golden set
            issues: List of issues detected during validation
            
        Returns:
            Optional feedback message
        """
        # For perfect scores, minimal feedback
        if quality_score >= 0.95:
            return "Excellent! Your response matches the expected answer."
        
        # For good scores, light feedback
        if quality_score >= 0.8:
            return "Good response! It's very close to the expected answer."
        
        # For medium scores, provide a hint if available
        if quality_score >= 0.5 and hints:
            return f"Your answer is partially correct. Hint: {hints[0]}"
        
        # For poor scores, provide targeted feedback based on issues
        if issues:
            issue_types = {issue["type"] for issue in issues}
            
            if "type_error" in issue_types:
                return "Your answer has the wrong format. Please check the expected response type."
            
            if "missing_keys" in issue_types:
                return "Your answer is missing some required information. Please check all required fields."
            
            if "partial_match" in issue_types:
                if hints:
                    return f"Your answer is partially correct but missing key elements. Hint: {hints[0]}"
                else:
                    return "Your answer is partially correct but missing key elements."
            
            if "mismatch" in issue_types:
                if hints:
                    return f"Your answer doesn't match the expected value. Hint: {hints[0]}"
                else:
                    return "Your answer doesn't match the expected value."
        
        # Generic feedback for low scores
        if hints:
            return f"Your answer needs improvement. Hint: {hints[0]}"
        else:
            return "Your answer needs improvement. Please try again."
    
    def _record_validation_result(self, golden_set_id: str, quality_score: float, session_id: str) -> None:
        """
        Record validation result for analytics and improvement tracking.
        
        This helps build a performance history for each golden set item.
        
        Note: This is a stub method - in a production environment, this would
        write to a database table tracking golden set performance.
        """
        # In a real implementation, this would update a database table
        # For now, we just log the result
        logger.info(f"Golden set {golden_set_id} validation: score={quality_score}, session={session_id}")
        
        # This would be used to track golden set quality and user performance
        pass
