from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from app.models.thryve_data_type import ThryveDataType, ThryveDailyEpoch


class ThryveDataTypeService:
    """Service for Thryve data type operations"""
    
    @staticmethod
    def get_by_id(db: Session, data_type_id: int, type: str) -> Optional[ThryveDataType]:
        """Get Thryve data type by data_type_id and type (Daily/Epoch)"""
        data_type_enum = ThryveDailyEpoch.DAILY if type.lower() == "daily" else ThryveDailyEpoch.EPOCH
        return db.query(ThryveDataType).filter(
            ThryveDataType.data_type_id == data_type_id,
            ThryveDataType.type == data_type_enum,
            ThryveDataType.is_active == True
        ).first()
    
    @staticmethod
    def get_by_name(db: Session, name: str) -> List[ThryveDataType]:
        """Get Thryve data types by name"""
        return db.query(ThryveDataType).filter(
            ThryveDataType.name.ilike(f"%{name}%"),
            ThryveDataType.is_active == True
        ).all()
    
    @staticmethod
    def map_data_type_id(db: Session, data_type_id: int, event_type: str) -> Optional[str]:
        """Map dataTypeId to name based on event type"""
        # Determine type from event_type
        # event.data.epoch.create -> Epoch
        # event.data.daily.update or event.data.daily.create -> Daily
        if "epoch" in event_type.lower():
            data_type = ThryveDataTypeService.get_by_id(db, data_type_id, "epoch")
        elif "daily" in event_type.lower():
            data_type = ThryveDataTypeService.get_by_id(db, data_type_id, "daily")
        else:
            return None
        
        return data_type.name if data_type else None
    
    @staticmethod
    def get_all_by_category(db: Session, category: str) -> List[ThryveDataType]:
        """Get all Thryve data types by category"""
        return db.query(ThryveDataType).filter(
            ThryveDataType.category.ilike(f"%{category}%"),
            ThryveDataType.is_active == True
        ).all()
    
    @staticmethod
    def get_platform_support(db: Session, data_type_id: int, type: str) -> Optional[Dict]:
        """Get platform support for a data type"""
        data_type = ThryveDataTypeService.get_by_id(db, data_type_id, type)
        return data_type.platform_support if data_type else None
    
    @staticmethod
    def find_matching_thryve_data_type(db: Session, metric_name: str) -> Optional[ThryveDataType]:
        """Find matching Thryve data type by metric name (for auto-linking admin metrics)"""
        # Try exact match first
        exact_match = db.query(ThryveDataType).filter(
            ThryveDataType.name.ilike(metric_name),
            ThryveDataType.is_active == True
        ).first()
        
        if exact_match:
            return exact_match
        
        # Try partial match
        partial_match = db.query(ThryveDataType).filter(
            ThryveDataType.name.ilike(f"%{metric_name}%"),
            ThryveDataType.is_active == True
        ).first()
        
        return partial_match

