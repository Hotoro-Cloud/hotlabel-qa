# HotLabel Quality Assurance Service

## Overview

The HotLabel Quality Assurance (QA) Service is a critical component of the HotLabel platform, responsible for validating, verifying, and assessing the quality of task results submitted by users. This service implements sophisticated validation strategies and quality control mechanisms to ensure high-quality data labels while identifying and handling potential issues.

## Features

### Multi-Layer Validation

- **Golden Set Validation**: Compares submitted responses against known golden set examples
- **Bot Detection**: Identifies automated or suspicious submission patterns
- **Statistical Validation**: Uses statistical methods to assess response quality relative to historical data
- **Threshold-Based Validation**: Applies configurable thresholds for validation criteria

### Quality Control

- **Confidence Scoring**: Each validation receives a confidence score indicating reliability
- **Quality Routing**: Routes submissions to appropriate validation paths based on confidence levels
- **Consensus Verification**: Implements consensus-based verification for medium-confidence submissions

### Data Management

- **Quality Metrics**: Comprehensive metrics for monitoring label quality
- **Issue Reporting**: System for reporting and tracking quality issues
- **Dataset Preparation**: Tools for preparing validated data for model training

## Architecture

The QA service follows a clean architecture pattern with proper separation of concerns:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  API Layer      │────▶│  Service Layer  │────▶│  Data Layer     │
│  (FastAPI)      │◀────│  (Business      │◀────│  (Repositories, │
└─────────────────┘     │   Logic)        │     │   Models)       │
                         └─────────────────┘     └─────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │  Validators     │
                         │  (Strategy      │
                         │   Pattern)      │
                         └─────────────────┘
```

## Getting Started

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- PostgreSQL
- Redis

### Installation

1. Clone the repository:

```bash
git clone https://github.com/Hotoro-Cloud/hotlabel-qa.git
cd hotlabel-qa
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy the example environment file and update it with your settings:

```bash
cp .env.example .env
# Edit .env with your configuration
```

### Running with Docker

The easiest way to run the service is using Docker Compose:

```bash
docker-compose up -d
```

This will start the QA service along with PostgreSQL and Redis.

### Running Locally

Alternatively, you can run the service directly:

```bash
# Apply database migrations
alembic upgrade head

# Start the service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

### Database Migrations

The service uses Alembic for database migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "Migration description"

# Apply migrations
alembic upgrade head

# Revert migrations
alembic downgrade -1
```

## API Documentation

Once the service is running, you can access the API documentation at:

- Swagger UI: http://localhost:8002/api/v1/docs
- ReDoc: http://localhost:8002/api/v1/redoc

## Key Endpoints

### Validation

- `POST /api/v1/quality/validate` - Validate a submission
- `GET /api/v1/quality/validations/{validation_id}` - Get validation details

### Metrics

- `POST /api/v1/quality/metrics` - Get quality metrics

### Reports

- `POST /api/v1/quality/reports` - Submit a quality report
- `GET /api/v1/quality/reports` - List quality reports

### Admin

- `POST /api/v1/admin/golden-sets` - Create a golden set
- `GET /api/v1/admin/consensus-groups/{consensus_id}` - Get consensus group details

## Integration with Other Services

The QA service integrates with other HotLabel services:

- **Task Management Service** - Receives task submissions for validation
- **User Profiling Service** - Uses user profiles for context-aware validation
- **Dataset Service** - Provides validated data for model training

## Development

### Project Structure

```
hotlabel-qa/
├── alembic/              # Database migrations
├── app/                  # Application code
│   ├── api/              # API layer (routes, endpoints)
│   ├── core/             # Core modules (config, exceptions)
│   ├── db/               # Database layer (session, repositories)
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   └── main.py           # Application entry point
├── migrations/           # Alembic migrations
├── .env.example          # Example environment variables
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile            # Docker configuration
└── requirements.txt      # Python dependencies
```

### Testing

The HotLabel QA Service uses a comprehensive testing suite to ensure code quality and functionality. The tests are organized by component type and cover all layers of the application.

#### Testing Framework

- **Pytest**: The project uses pytest as the main testing framework
- **Coverage Reporting**: Test coverage is tracked and reported
- **Async Support**: Tests support asynchronous code execution
- **In-memory Database**: Tests use SQLite in-memory database for isolation

#### Test Categories

The test suite is organized into several categories, each with a specific focus:

- **API Tests** (`tests/api/`): Test HTTP endpoints, request validation, and response formatting
  - Validate endpoint behavior for validation creation, retrieval, updates, and listing
  - Test error handling and edge cases (e.g., resource not found)
  - Ensure proper status codes and response formats

- **Service Tests** (`tests/services/`): Test business logic and service layer functionality
  - Validate core validation service operations
  - Test consensus service for agreement calculation
  - Verify golden set service for reference data management
  - Test metrics service for quality measurement

- **Model Tests** (`tests/models/`): Test data models and database interactions
  - Validate model relationships and constraints
  - Test enum values and conversions
  - Ensure proper data persistence

- **Validator Tests** (`tests/services/validators/`): Test validation strategies
  - Test threshold-based validation with different confidence levels
  - Validate golden set comparison logic
  - Test statistical validation methods
  - Verify bot detection algorithms

#### Test Fixtures

The project uses fixtures (defined in `conftest.py`) to set up test environments:

- Database session fixtures for transaction isolation
- API client fixtures for endpoint testing
- Redis client fixtures for caching tests
- Service fixtures for dependency injection

#### Running Tests

Basic test execution:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run tests with coverage report
pytest --cov=app
```

Running specific test categories:

```bash
# Run only API tests
pytest tests/api/

# Run only service tests
pytest tests/services/

# Run tests for a specific file
pytest tests/services/test_validation_service.py

# Run a specific test
pytest tests/api/test_validation_routes.py::test_create_validation
```

Test markers can be used to run specific types of tests:

```bash
# Run unit tests
pytest -m unit

# Run integration tests
pytest -m integration

# Run API tests
pytest -m api
```

#### Coverage Reports

The test suite generates coverage reports to identify untested code:

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# View missing coverage
pytest --cov=app --cov-report=term-missing
```

After running tests with coverage, you can view the HTML report in the `htmlcov/` directory.

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

[MIT](LICENSE)
