# HotLabel Quality Assurance Service

This microservice handles quality validation, verification, and assessment of task results for the HotLabel platform.

## Features

- Real-time quality validation of task submissions
- Multiple validation strategies (golden set, consensus, statistical)
- Quality scoring and confidence assessment
- Result aggregation and dataset preparation
- Quality metrics and reporting

## Getting Started

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- PostgreSQL
- Redis

### Running the Service

```bash
# Using Docker
docker-compose up -d

# Without Docker
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API Documentation

Once the service is running, you can access the API documentation at:

- Swagger UI: http://localhost:8002/api/v1/docs
- ReDoc: http://localhost:8002/api/v1/redoc
