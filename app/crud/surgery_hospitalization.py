from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional
import logging
from app.models.surgery_hospitalization import SurgeryHospitalization
from app.schemas.surgery_hospitalization import SurgeryHospitalizationCreate, SurgeryHospitalizationUpdate

logger = logging.getLogger(__name__)

class SurgeryHospitalizationCRUD:
    """CRUD operations for SurgeryHospitalization model"""
    
    def create(self, db: Session, surgery_data: SurgeryHospitalizationCreate, user_id: int) -> SurgeryHospitalization:
        """Create a new surgery or hospitalization record"""
        try:
            db_surgery = SurgeryHospitalization(
                user_id=user_id,
                procedure_type=surgery_data.procedure_type,
                name=surgery_data.name,
                procedure_date=surgery_data.procedure_date,
                reason=surgery_data.reason,
                treatment=surgery_data.treatment,
                body_area=surgery_data.body_area,
                recovery_status=surgery_data.recovery_status,
                notes=surgery_data.notes,
                created_by=user_id
            )
            
            db.add(db_surgery)
            db.commit()
            db.refresh(db_surgery)
            
            logger.info(f"Created surgery/hospitalization {db_surgery.id} for user {user_id}")
            return db_surgery
            
        except Exception as e:
            logger.error(f"Failed to create surgery/hospitalization: {e}")
            db.rollback()
            raise
    
    def get_by_id(self, db: Session, surgery_id: int, user_id: int) -> Optional[SurgeryHospitalization]:
        """Get surgery/hospitalization by ID"""
        try:
            return db.query(SurgeryHospitalization).filter(
                and_(
                    SurgeryHospitalization.id == surgery_id,
                    SurgeryHospitalization.user_id == user_id
                )
            ).first()
        except Exception as e:
            logger.error(f"Failed to get surgery/hospitalization {surgery_id}: {e}")
            return None
    
    def get_by_user(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[SurgeryHospitalization]:
        """Get all surgeries/hospitalizations for a specific user"""
        try:
            return db.query(SurgeryHospitalization).filter(
                SurgeryHospitalization.user_id == user_id
            ).order_by(desc(SurgeryHospitalization.procedure_date)).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to get surgeries/hospitalizations for user {user_id}: {e}")
            return []
    
    def update(
        self, 
        db: Session, 
        surgery_id: int, 
        surgery_update: SurgeryHospitalizationUpdate, 
        user_id: int
    ) -> Optional[SurgeryHospitalization]:
        """Update a surgery/hospitalization record"""
        try:
            db_surgery = self.get_by_id(db, surgery_id, user_id)
            if not db_surgery:
                return None
            
            update_data = surgery_update.dict(exclude_unset=True)
            update_data['updated_by'] = user_id
            
            for field, value in update_data.items():
                setattr(db_surgery, field, value)
            
            db.commit()
            db.refresh(db_surgery)
            
            logger.info(f"Updated surgery/hospitalization {surgery_id} for user {user_id}")
            return db_surgery
            
        except Exception as e:
            logger.error(f"Failed to update surgery/hospitalization {surgery_id}: {e}")
            db.rollback()
            return None
    
    def delete(self, db: Session, surgery_id: int, user_id: int) -> bool:
        """Delete a surgery/hospitalization record"""
        try:
            db_surgery = self.get_by_id(db, surgery_id, user_id)
            if not db_surgery:
                return False
            
            db.delete(db_surgery)
            db.commit()
            
            logger.info(f"Deleted surgery/hospitalization {surgery_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete surgery/hospitalization {surgery_id}: {e}")
            db.rollback()
            return False

# Create instance
surgery_hospitalization_crud = SurgeryHospitalizationCRUD()
