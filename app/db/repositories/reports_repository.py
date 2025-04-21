from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.reports import Report, ReportType, ReportStatus
from app.schemas.reports import ReportCreate, ReportUpdate

class ReportsRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, report_data: ReportCreate) -> Report:
        """Create a new report."""
        db_report = Report(**report_data.model_dump())
        self.db.add(db_report)
        self.db.commit()
        self.db.refresh(db_report)
        return db_report
    
    def get_by_id(self, report_id: str) -> Optional[Report]:
        """Get report by ID."""
        return self.db.query(Report).filter(Report.id == report_id).first()
    
    def list_reports(
        self, 
        report_type: Optional[ReportType] = None,
        status: Optional[ReportStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Report]:
        """List reports with optional filters."""
        query = self.db.query(Report)
        
        if report_type:
            query = query.filter(Report.report_type == report_type)
        if status:
            query = query.filter(Report.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    def update(self, report_id: str, update_data: Dict[str, Any]) -> Optional[Report]:
        """Update report."""
        db_report = self.get_by_id(report_id)
        if not db_report:
            return None
        
        for key, value in update_data.items():
            setattr(db_report, key, value)
        
        self.db.commit()
        self.db.refresh(db_report)
        return db_report
    
    def delete(self, report_id: str) -> bool:
        """Delete report."""
        db_report = self.get_by_id(report_id)
        if not db_report:
            return False
        
        self.db.delete(db_report)
        self.db.commit()
        return True
    
    def get_reports_by_date_range(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        report_type: Optional[ReportType] = None
    ) -> List[Report]:
        """Get reports within a date range."""
        query = self.db.query(Report)
        
        if start_date:
            query = query.filter(Report.start_date >= start_date)
        if end_date:
            query = query.filter(Report.end_date <= end_date)
        if report_type:
            query = query.filter(Report.report_type == report_type)
        
        return query.all() 