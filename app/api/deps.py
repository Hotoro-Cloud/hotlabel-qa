from typing import Generator
from fastapi import Depends

from app.db.session import get_db
from app.db.repositories.validation_repository import ValidationRepository
from app.db.repositories.golden_set_repository import GoldenSetRepository
from app.db.repositories.consensus_repository import ConsensusRepository
from app.services.validation_service import ValidationService
from app.services.metrics_service import MetricsService
from app.services.report_service import ReportService
from app.services.golden_set_service import GoldenSetService

# Repository dependencies
def get_validation_repository(db = Depends(get_db)) -> ValidationRepository:
    return ValidationRepository(db)

def get_golden_set_repository(db = Depends(get_db)) -> GoldenSetRepository:
    return GoldenSetRepository(db)

def get_consensus_repository(db = Depends(get_db)) -> ConsensusRepository:
    return ConsensusRepository(db)

# Service dependencies
def get_validation_service(
    validation_repository = Depends(get_validation_repository),
    golden_set_repository = Depends(get_golden_set_repository),
    consensus_repository = Depends(get_consensus_repository)
) -> ValidationService:
    return ValidationService(validation_repository, golden_set_repository, consensus_repository)

def get_metrics_service(
    validation_repository = Depends(get_validation_repository)
) -> MetricsService:
    return MetricsService(validation_repository)

def get_report_service(
    validation_repository = Depends(get_validation_repository)
) -> ReportService:
    return ReportService(validation_repository)

def get_golden_set_service(
    golden_set_repository = Depends(get_golden_set_repository),
    validation_repository = Depends(get_validation_repository)
) -> GoldenSetService:
    return GoldenSetService(golden_set_repository, validation_repository)
