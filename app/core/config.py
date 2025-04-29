import os
import json
from typing import List, Union, Dict, Any, Optional
from pydantic_settings import BaseSettings
from pydantic import validator

class Settings(BaseSettings):
    # Base settings
    SERVICE_NAME: str = "hotlabel-qa"
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = "INFO"
    
    # Security
    SECRET_KEY: str
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [i.strip() for i in v.split(",") if i]
        return v
    
    # External Services
    TASK_SERVICE_URL: str = "http://localhost:8001/api/v1"
    USER_SERVICE_URL: Optional[str] = None
    
    # Quality Thresholds
    HIGH_CONFIDENCE_THRESHOLD: float = 0.85
    MEDIUM_CONFIDENCE_THRESHOLD: float = 0.60
    
    # Validation Parameters
    GOLDEN_SET_PERCENTAGE: float = 0.10
    CONSENSUS_REQUIRED_AGREEMENT: float = 0.75
    MINIMUM_CONSENSUS_VALIDATORS: int = 3
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
