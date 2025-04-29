#!/usr/bin/env python3
"""
Script to create test data in the QA database for testing purposes.
This script:
1. Creates a test task in the qa_tasks table
2. Creates a test validator in the validators table
3. Creates a test validation if not exists
4. Creates a test metrics record if not exists
"""

import os
import sys
import uuid
import json
import logging
from datetime import datetime
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Get database URL from environment or use a default for local testing
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/hotlabel_qa")

def create_test_task():
    """Create a test task in the qa_tasks table."""
    try:
        engine = create_engine(DB_URL)
        task_id = str(uuid.uuid4())
        
        with engine.connect() as conn:
            # Check if the task already exists
            result = conn.execute(
                text("SELECT id FROM qa_tasks WHERE id = :task_id"),
                {"task_id": task_id}
            )
            if result.fetchone():
                logger.info(f"Task with ID {task_id} already exists.")
                return task_id
            
            # Create the task
            content = {
                "image_url": "https://example.com/test-image.jpg",
                "question": "What is in this image?"
            }
            
            conn.execute(
                text("""
                INSERT INTO qa_tasks (id, type, content, status, created_at, updated_at)
                VALUES (:id, :type, :content, :status, :created_at, :updated_at)
                """),
                {
                    "id": task_id,
                    "type": "image_classification",
                    "content": json.dumps(content),
                    "status": "pending",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            )
            conn.commit()
            
            logger.info(f"Created test task with ID: {task_id}")
            return task_id
    except Exception as e:
        logger.error(f"Failed to create test task: {str(e)}")
        return None

def create_test_validator():
    """Create a test validator in the validators table."""
    try:
        engine = create_engine(DB_URL)
        validator_id = str(uuid.uuid4())
        
        with engine.connect() as conn:
            # Check if a validator with the test email already exists
            result = conn.execute(
                text("SELECT id FROM validators WHERE email = :email"),
                {"email": "test_validator@example.com"}
            )
            existing = result.fetchone()
            if existing:
                logger.info(f"Validator with email test_validator@example.com already exists with ID {existing[0]}.")
                return existing[0]
            
            # Create the validator
            conn.execute(
                text("""
                INSERT INTO validators (id, name, email, is_active, created_at, updated_at)
                VALUES (:id, :name, :email, :is_active, :created_at, :updated_at)
                """),
                {
                    "id": validator_id,
                    "name": "Test Validator",
                    "email": "test_validator@example.com",
                    "is_active": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            )
            conn.commit()
            
            logger.info(f"Created test validator with ID: {validator_id}")
            return validator_id
    except Exception as e:
        logger.error(f"Failed to create test validator: {str(e)}")
        return None

def create_test_validation(task_id, validator_id):
    """Create a test validation record if it doesn't already exist."""
    try:
        engine = create_engine(DB_URL)
        validation_id = str(uuid.uuid4())
        
        with engine.connect() as conn:
            # Check if a validation for this task already exists
            result = conn.execute(
                text("SELECT id FROM validations WHERE task_id = :task_id AND validator_id = :validator_id"),
                {"task_id": task_id, "validator_id": validator_id}
            )
            existing = result.fetchone()
            if existing:
                logger.info(f"Validation for task {task_id} already exists with ID {existing[0]}.")
                return existing[0]
            
            # Create the validation
            conn.execute(
                text("""
                INSERT INTO validations (id, task_id, validator_id, status, created_at, updated_at)
                VALUES (:id, :task_id, :validator_id, :status, :created_at, :updated_at)
                """),
                {
                    "id": validation_id,
                    "task_id": task_id,
                    "validator_id": validator_id,
                    "status": "VALIDATED",  # Using validated status
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            )
            conn.commit()
            
            logger.info(f"Created test validation with ID: {validation_id}")
            return validation_id
    except Exception as e:
        logger.error(f"Failed to create test validation: {str(e)}")
        return None

def create_test_metrics(validation_id, task_id):
    """Create a test metrics record if it doesn't already exist."""
    try:
        engine = create_engine(DB_URL)
        metrics_id = str(uuid.uuid4())
        
        with engine.connect() as conn:
            # Check if metrics for this validation already exists
            result = conn.execute(
                text("SELECT id FROM metrics WHERE validation_id = :validation_id"),
                {"validation_id": validation_id}
            )
            existing = result.fetchone()
            if existing:
                logger.info(f"Metrics for validation {validation_id} already exists with ID {existing[0]}.")
                return existing[0]
            
            # Create the metrics
            conn.execute(
                text("""
                INSERT INTO metrics (id, validation_id, task_id, accuracy, precision, recall, f1_score, latency_ms, created_at, updated_at)
                VALUES (:id, :validation_id, :task_id, :accuracy, :precision, :recall, :f1_score, :latency_ms, :created_at, :updated_at)
                """),
                {
                    "id": metrics_id,
                    "validation_id": validation_id,
                    "task_id": task_id,
                    "accuracy": 0.95,
                    "precision": 0.92,
                    "recall": 0.90,
                    "f1_score": 0.91,
                    "latency_ms": 250,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            )
            conn.commit()
            
            logger.info(f"Created test metrics with ID: {metrics_id}")
            return metrics_id
    except Exception as e:
        logger.error(f"Failed to create test metrics: {str(e)}")
        return None

def main():
    """Run the script to create test data."""
    logger.info("Creating test data in the QA database...")
    
    # Create a test task
    task_id = create_test_task()
    
    # Create a test validator
    validator_id = create_test_validator()
    
    if task_id and validator_id:
        # Create a test validation
        validation_id = create_test_validation(task_id, validator_id)
        
        # Create a test metrics record
        if validation_id:
            metrics_id = create_test_metrics(validation_id, task_id)
            logger.info(f"Created test metrics with ID: {metrics_id}")
        
        logger.info(f"Successfully created test data.")
        logger.info(f"Task ID: {task_id}")
        logger.info(f"Validator ID: {validator_id}")
        logger.info(f"Validation ID: {validation_id}")
        
        # Print in a format that can be copied directly
        print("\nUse these IDs in your tests:")
        print(f"TASK_ID = '{task_id}'")
        print(f"VALIDATOR_ID = '{validator_id}'")
        print(f"VALIDATION_ID = '{validation_id}'")
    else:
        logger.error("Failed to create some test data.")
        sys.exit(1)

if __name__ == "__main__":
    main() 