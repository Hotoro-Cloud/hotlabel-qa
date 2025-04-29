#!/usr/bin/env python3
import requests
import uuid
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Configuration
QA_SERVICE_URL = "http://localhost:8003"  # Direct connection to QA service
BASE_URL = f"{QA_SERVICE_URL}/api/v1"
VALIDATION_URL = f"{BASE_URL}/validation"
METRICS_URL = f"{BASE_URL}/metrics"
REPORTS_URL = f"{BASE_URL}/reports"
ADMIN_URL = f"{BASE_URL}/admin"
CONSENSUS_URL = f"{BASE_URL}/consensus"

# Set API key for authentication - make sure this matches what's in your service config
API_KEY = "test_api_key_qa_service"  # Replace with actual API key
HEADERS = {"X-API-Key": API_KEY}

# Test data IDs - created using scripts/create_test_data.py
TASK_ID = '3d118c2d-f574-4275-baa5-857b86bfdb7c'
VALIDATOR_ID = '161678f1-f153-4e89-8e26-8d898cdb4a6d'
VALIDATION_ID = '2b3cce3a-7485-4939-8de4-39fc95c6ae7a'

def print_response(response: requests.Response, title: str) -> None:
    """Helper function to print API responses in a readable format"""
    print(f"\n=== {title} ===")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(f"Raw response text: {response.text}")
    print("=" * 50)

# Basic Service Health Endpoints
def test_health_check():
    """Test health check endpoint"""
    response = requests.get(f"{QA_SERVICE_URL}/health", headers=HEADERS)
    print_response(response, "Health Check")
    return response.json() if response.status_code < 300 else {}

def test_ready_check():
    """Test ready check endpoint"""
    response = requests.get(f"{QA_SERVICE_URL}/ready", headers=HEADERS)
    print_response(response, "Ready Check")
    return response.json() if response.status_code < 300 else {}

def test_root():
    """Test root endpoint"""
    response = requests.get(QA_SERVICE_URL, headers=HEADERS)
    print_response(response, "Root Endpoint")
    return response.json() if response.status_code < 300 else {}

# Validation Endpoints Tests
def test_create_validation() -> Dict[str, Any]:
    """Test creating a new validation"""
    validation_data = {
        "task_id": TASK_ID,  # Use our test task ID
        "result_id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "publisher_id": str(uuid.uuid4()),
        "validator_id": VALIDATOR_ID,  # Use our test validator ID
        "task_type": "image_classification",
        "response": {
            "class": "dog",
            "confidence": 0.95
        },
        "time_spent_ms": 5000
    }
    
    print(f"\nSending request to {VALIDATION_URL} with data: {json.dumps(validation_data, indent=2)}")
    response = requests.post(VALIDATION_URL, json=validation_data, headers=HEADERS)
    print_response(response, "Create Validation")
    return response.json() if response.status_code < 300 else {}

def test_get_validation(validation_id: str):
    """Test getting a validation by ID"""
    response = requests.get(f"{VALIDATION_URL}/{validation_id}", headers=HEADERS)
    print_response(response, "Get Validation by ID")
    return response.json() if response.status_code < 300 else {}

def test_list_validations():
    """Test listing validations with various filters"""
    # No filters
    response = requests.get(VALIDATION_URL, headers=HEADERS)
    print_response(response, "List All Validations")
    
    # With status filter
    response = requests.get(f"{VALIDATION_URL}?status=pending", headers=HEADERS)
    print_response(response, "List Validations by Status")
    
    # With validator filter
    response = requests.get(f"{VALIDATION_URL}?validator_id={VALIDATOR_ID}", headers=HEADERS)
    print_response(response, "List Validations by Validator")
    
    return response.json() if response.status_code < 300 else {}

def test_update_validation_status(validation_id: str):
    """Test updating a validation status"""
    statuses = ["validated", "rejected", "needs_review"]
    update_data = {
        "status": random.choice(statuses)
    }
    response = requests.patch(f"{VALIDATION_URL}/{validation_id}/status", json=update_data, headers=HEADERS)
    print_response(response, "Update Validation Status")
    return response.json() if response.status_code < 300 else {}

def test_get_validation_by_result(result_id: str):
    """Test getting validation by result ID"""
    response = requests.get(f"{VALIDATION_URL}/results/{result_id}", headers=HEADERS)
    print_response(response, "Get Validation by Result ID")
    return response.json() if response.status_code < 300 else {}

# Metrics Endpoints Tests
def test_get_metrics():
    """Test getting all metrics"""
    response = requests.get(METRICS_URL, headers=HEADERS)
    print_response(response, "Get All Metrics")
    return response.json() if response.status_code < 300 else {}

def test_get_metrics_by_validation(validation_id: str):
    """Test getting metrics for a specific validation"""
    response = requests.get(f"{METRICS_URL}/validation/{validation_id}", headers=HEADERS)
    print_response(response, "Get Metrics by Validation ID")
    return response.json() if response.status_code < 300 else {}

def test_get_metrics_by_task(task_id: str):
    """Test getting metrics for a specific task"""
    response = requests.get(f"{METRICS_URL}/task/{task_id}", headers=HEADERS)
    print_response(response, "Get Metrics by Task ID")
    return response.json() if response.status_code < 300 else {}

def test_create_metrics():
    """Test creating new metrics"""
    metrics_data = {
        "validation_id": str(uuid.uuid4()),
        "task_id": TASK_ID,  # Use our test task ID
        "accuracy": 0.95,
        "precision": 0.92,
        "recall": 0.90,
        "f1_score": 0.91,
        "latency_ms": 250,
        "custom_metrics": {
            "confidence": 0.88,
            "difficulty": 3
        }
    }
    response = requests.post(METRICS_URL, json=metrics_data, headers=HEADERS)
    print_response(response, "Create Metrics")
    return response.json() if response.status_code < 300 else {}

# Report Endpoints Tests
def test_get_reports():
    """Test getting all reports"""
    response = requests.get(REPORTS_URL, headers=HEADERS)
    print_response(response, "Get All Reports")
    return response.json() if response.status_code < 300 else {}

def test_get_report(report_id: str):
    """Test getting a specific report"""
    response = requests.get(f"{REPORTS_URL}/{report_id}", headers=HEADERS)
    print_response(response, "Get Report by ID")
    return response.json() if response.status_code < 300 else {}

def test_generate_report():
    """Test generating a new report"""
    report_data = {
        "name": "Test Quality Report",
        "report_type": "weekly",
        "start_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
        "end_date": datetime.utcnow().isoformat(),
        "filters": {
            "task_type": ["image_classification", "text_classification"],
            "validation_status": ["validated", "rejected"]
        },
        "grouping": ["task_type", "validation_status"]
    }
    response = requests.post(REPORTS_URL, json=report_data, headers=HEADERS)
    print_response(response, "Generate Report")
    return response.json() if response.status_code < 300 else {}

# Consensus Endpoints Tests
def test_get_consensus():
    """Test getting all consensus groups"""
    response = requests.get(CONSENSUS_URL, headers=HEADERS)
    print_response(response, "Get All Consensus Groups")
    return response.json() if response.status_code < 300 else {}

def test_get_consensus_by_id(consensus_id: str):
    """Test getting a specific consensus group"""
    response = requests.get(f"{CONSENSUS_URL}/{consensus_id}", headers=HEADERS)
    print_response(response, "Get Consensus by ID")
    return response.json() if response.status_code < 300 else {}

def test_create_consensus():
    """Test creating a new consensus group"""
    consensus_data = {
        "task_id": TASK_ID,  # Use our test task ID
        "required_validations": 3,
        "agreement_threshold": 0.7
    }
    response = requests.post(CONSENSUS_URL, json=consensus_data, headers=HEADERS)
    print_response(response, "Create Consensus Group")
    return response.json() if response.status_code < 300 else {}

def test_add_validation_to_consensus(consensus_id: str):
    """Test adding a validation to a consensus group"""
    validation_data = {
        "validation_id": str(uuid.uuid4())
    }
    response = requests.post(f"{CONSENSUS_URL}/{consensus_id}/validations", json=validation_data, headers=HEADERS)
    print_response(response, "Add Validation to Consensus")
    return response.json() if response.status_code < 300 else {}

def test_get_consensus_status(consensus_id: str):
    """Test getting consensus status"""
    response = requests.get(f"{CONSENSUS_URL}/{consensus_id}/status", headers=HEADERS)
    print_response(response, "Get Consensus Status")
    return response.json() if response.status_code < 300 else {}

# Admin Endpoints Tests
def test_get_validators():
    """Test getting all validators"""
    response = requests.get(f"{ADMIN_URL}/validators", headers=HEADERS)
    print_response(response, "Get All Validators")
    return response.json() if response.status_code < 300 else {}

def test_create_validator():
    """Test creating a new validator"""
    random_id = uuid.uuid4().hex[:8]
    validator_data = {
        "name": f"Test Validator {random_id}",
        "email": f"validator_{random_id}@example.com",
        "is_active": True
    }
    response = requests.post(f"{ADMIN_URL}/validators", json=validator_data, headers=HEADERS)
    print_response(response, "Create Validator")
    return response.json() if response.status_code < 300 else {}

def test_get_golden_sets():
    """Test getting all golden sets"""
    response = requests.get(f"{ADMIN_URL}/golden-sets", headers=HEADERS)
    print_response(response, "Get All Golden Sets")
    return response.json() if response.status_code < 300 else {}

def test_create_golden_set():
    """Test creating a new golden set"""
    golden_set_data = {
        "task_id": str(uuid.uuid4()),  # Use a random UUID to avoid unique constraint violations
        "expected_response": {
            "class": "cat",
            "confidence": 1.0
        },
        "allowed_variation": 0.1,
        "difficulty_level": 2,
        "category": "animal",
        "tags": ["cat", "pet", "animal"],
        "hints": ["Look closely at the ears and whiskers"]
    }
    response = requests.post(f"{ADMIN_URL}/golden-sets", json=golden_set_data, headers=HEADERS)
    print_response(response, "Create Golden Set")
    return response.json() if response.status_code < 300 else {}

def main():
    print("\n" + "="*50)
    print("STARTING QA SERVICE API TESTS")
    print("="*50 + "\n")
    
    # Track IDs for use in later tests
    ids = {
        "validation_id": VALIDATION_ID,  # Use the one from create_test_data
        "result_id": None,
        "task_id": TASK_ID,
        "consensus_id": None,
        "report_id": None
    }
    
    try:
        print("\n--- BASIC SERVICE ENDPOINTS ---\n")
        # Basic service endpoints
        test_root()
        test_health_check()
        test_ready_check()
        
        print("\n--- VALIDATION ENDPOINTS TESTS ---\n")
        # Test validation endpoints
        validation = test_create_validation()
        if validation and "id" in validation:
            ids["validation_id"] = validation["id"]
            ids["result_id"] = validation.get("result_id")
            
            test_get_validation(ids["validation_id"])
            test_update_validation_status(ids["validation_id"])
            
            if ids["result_id"]:
                test_get_validation_by_result(ids["result_id"])
        
        test_list_validations()
        
        print("\n--- METRICS ENDPOINTS TESTS ---\n")
        # Test metrics endpoints
        metrics = test_create_metrics()
        test_get_metrics()
        
        if ids["validation_id"]:
            test_get_metrics_by_validation(ids["validation_id"])
        
        if ids["task_id"]:
            test_get_metrics_by_task(ids["task_id"])
        
        print("\n--- REPORTS ENDPOINTS TESTS ---\n")
        # Test reports endpoints
        report = test_generate_report()
        if report and "id" in report:
            ids["report_id"] = report["id"]
            test_get_report(ids["report_id"])
        
        test_get_reports()
        
        print("\n--- CONSENSUS ENDPOINTS TESTS ---\n")
        # Test consensus endpoints
        consensus = test_create_consensus()
        if consensus and "id" in consensus:
            ids["consensus_id"] = consensus["id"]
            test_get_consensus_by_id(ids["consensus_id"])
            test_add_validation_to_consensus(ids["consensus_id"])
            test_get_consensus_status(ids["consensus_id"])
        
        test_get_consensus()
        
        print("\n--- ADMIN ENDPOINTS TESTS ---\n")
        # Test admin endpoints
        test_get_validators()
        test_create_validator()
        test_get_golden_sets()
        test_create_golden_set()
        
        print("\n" + "="*50)
        print("QA SERVICE API TESTS COMPLETED")
        print("="*50)
    
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    main() 