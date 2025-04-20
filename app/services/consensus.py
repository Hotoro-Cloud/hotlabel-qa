from typing import Dict, Any, List, Tuple, Union
from app.models.validation import Validation
import logging

logger = logging.getLogger(__name__)

def calculate_consensus(
    validations: List[Validation]
) -> Tuple[Dict[str, Any], float]:
    """Calculate consensus from multiple validations
    
    Args:
        validations: List of validation models to analyze
        
    Returns:
        Tuple containing:
            - consensus_result: The agreed-upon result
            - agreement_level: The level of agreement (0.0 to 1.0)
    """
    if not validations:
        return {}, 0.0
    
    # Extract responses from validations
    responses = [v.response for v in validations if v.response is not None]
    
    if not responses:
        return {}, 0.0
    
    # The consensus approach depends on the type of responses
    sample_response = responses[0]
    
    if isinstance(sample_response, str):
        return _calculate_text_consensus(responses)
    elif isinstance(sample_response, dict):
        return _calculate_dict_consensus(responses)
    elif isinstance(sample_response, list):
        return _calculate_list_consensus(responses)
    else:
        # Simple consensus for basic types (int, bool, etc.)
        return _calculate_simple_consensus(responses)

def _calculate_text_consensus(responses: List[str]) -> Tuple[str, float]:
    """Calculate consensus for text responses"""
    # Normalize responses
    normalized_responses = [r.strip().lower() for r in responses if isinstance(r, str)]
    
    if not normalized_responses:
        return "", 0.0
    
    # Count frequency of each normalized response
    from collections import Counter
    response_counts = Counter(normalized_responses)
    
    # Find most common response and its count
    most_common = response_counts.most_common(1)[0]
    most_common_response, count = most_common
    
    # Calculate agreement level
    agreement_level = count / len(normalized_responses)
    
    return most_common_response, agreement_level

def _calculate_dict_consensus(responses: List[Dict]) -> Tuple[Dict[str, Any], float]:
    """Calculate consensus for dictionary responses"""
    # This would be a more sophisticated implementation in a real system
    # For now, we'll do a key-by-key majority vote
    
    if not responses:
        return {}, 0.0
    
    # Collect all keys from all responses
    all_keys = set()
    for response in responses:
        all_keys.update(response.keys())
    
    consensus_result = {}
    key_agreement_levels = []
    
    # For each key, find the most common value
    for key in all_keys:
        # Collect all values for this key
        key_values = []
        for response in responses:
            if key in response:
                key_values.append(str(response[key]))  # Convert to string for comparison
        
        if not key_values:
            continue
        
        # Find the most common value
        from collections import Counter
        value_counts = Counter(key_values)
        most_common = value_counts.most_common(1)[0]
        most_common_value, count = most_common
        
        # Calculate agreement level for this key
        key_agreement = count / len(responses)
        key_agreement_levels.append(key_agreement)
        
        # Add to consensus result if agreement is sufficient
        if key_agreement > 0.5:  # More than 50% agreement
            try:
                # Try to convert back to original type
                if most_common_value.lower() == 'true':
                    consensus_result[key] = True
                elif most_common_value.lower() == 'false':
                    consensus_result[key] = False
                elif most_common_value.isdigit():
                    consensus_result[key] = int(most_common_value)
                elif most_common_value.replace('.', '', 1).isdigit():
                    consensus_result[key] = float(most_common_value)
                else:
                    consensus_result[key] = most_common_value
            except:
                consensus_result[key] = most_common_value
    
    # Calculate overall agreement level as average of key agreements
    overall_agreement = sum(key_agreement_levels) / len(key_agreement_levels) if key_agreement_levels else 0.0
    
    return consensus_result, overall_agreement

def _calculate_list_consensus(responses: List[List]) -> Tuple[List, float]:
    """Calculate consensus for list responses"""
    # This is a simplified implementation
    # In a real system, this would need to handle more complex cases
    
    if not responses:
        return [], 0.0
    
    # Flatten all items from all lists
    all_items = []
    for response in responses:
        if isinstance(response, list):
            all_items.extend(str(item) for item in response)  # Convert to strings for comparison
    
    if not all_items:
        return [], 0.0
    
    # Count frequency of each item
    from collections import Counter
    item_counts = Counter(all_items)
    
    # Include items that appear in at least half of the responses
    consensus_items = []
    threshold = len(responses) / 2
    for item, count in item_counts.items():
        if count >= threshold:
            # Try to convert back to original type when adding to consensus
            try:
                if item.lower() == 'true':
                    consensus_items.append(True)
                elif item.lower() == 'false':
                    consensus_items.append(False)
                elif item.isdigit():
                    consensus_items.append(int(item))
                elif item.replace('.', '', 1).isdigit():
                    consensus_items.append(float(item))
                else:
                    consensus_items.append(item)
            except:
                consensus_items.append(item)
    
    # Calculate agreement level
    # This is a simplification - real implementation would be more sophisticated
    agreement_level = len(consensus_items) / len(item_counts) if item_counts else 0.0
    
    return consensus_items, agreement_level

def _calculate_simple_consensus(responses: List[Any]) -> Tuple[Any, float]:
    """Calculate consensus for simple types (int, bool, etc.)"""
    if not responses:
        return None, 0.0
    
    # Count frequency of each response
    from collections import Counter
    response_counts = Counter(str(r) for r in responses)  # Convert to strings for counting
    
    # Find most common response and its count
    most_common = response_counts.most_common(1)[0]
    most_common_response_str, count = most_common
    
    # Convert back to original type if possible
    try:
        if most_common_response_str.lower() == 'true':
            most_common_response = True
        elif most_common_response_str.lower() == 'false':
            most_common_response = False
        elif most_common_response_str.isdigit():
            most_common_response = int(most_common_response_str)
        elif most_common_response_str.replace('.', '', 1).isdigit():
            most_common_response = float(most_common_response_str)
        else:
            most_common_response = most_common_response_str
    except:
        most_common_response = most_common_response_str
    
    # Calculate agreement level
    agreement_level = count / len(responses)
    
    return most_common_response, agreement_level
