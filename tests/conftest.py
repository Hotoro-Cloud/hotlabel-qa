import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator

from app.db.base import Base
from app.db.base_class import *  # Import all models
from app.core.config import settings
import redis.asyncio as redis

# Create test database engine
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db() -> Generator:
    """Create test database tables."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(db) -> Generator[Session, None, None]:
    """Create a fresh database session for a test."""
    connection = db.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    """Create a test client with a database session."""
    from app.main import app
    from app.db.session import get_db
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="session")
async def redis_client():
    """Create a Redis client for testing."""
    redis_url = settings.REDIS_URL
    client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    yield client
    await client.close()

@pytest.fixture(scope="function")
async def clean_redis(redis_client):
    """Clean Redis before each test."""
    await redis_client.flushall()
    yield redis_client
    await redis_client.flushall()
