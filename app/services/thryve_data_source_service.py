from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.thryve_data_source import ThryveDataSource


class ThryveDataSourceService:
    """Service for Thryve data source operations"""
    
    @staticmethod
    def get_by_id(db: Session, data_source_id: int) -> Optional[ThryveDataSource]:
        """Get Thryve data source by ID"""
        return db.query(ThryveDataSource).filter(
            ThryveDataSource.id == data_source_id,
            ThryveDataSource.is_active == True
        ).first()
    
    @staticmethod
    def get_all(db: Session) -> List[ThryveDataSource]:
        """Get all active Thryve data sources"""
        return db.query(ThryveDataSource).filter(
            ThryveDataSource.is_active == True
        ).order_by(ThryveDataSource.name).all()
    
    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[ThryveDataSource]:
        """Get Thryve data source by name"""
        return db.query(ThryveDataSource).filter(
            ThryveDataSource.name.ilike(name),
            ThryveDataSource.is_active == True
        ).first()

