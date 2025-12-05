from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional
import logging
from app.models.surgery_hospitalization import SurgeryHospitalization
from app.schemas.surgery_hospitalization import SurgeryHospitalizationCreate, SurgeryHospitalizationUpdate

logger = logging.getLogger(__name__)

class SurgeryHospitalizationCRUD:
    """CRUD operations for SurgeryHospitalization model"""
    
    async def create(self, db: Session, surgery_data: SurgeryHospitalizationCreate, user_id: int) -> SurgeryHospitalization:
        """Create a new surgery or hospitalization record"""
        try:
            # Get user's current language to save as source_language
            from app.utils.user_language import get_user_language
            source_lang = await get_user_language(user_id, db)
            
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
                source_language=source_lang,
                version=1,  # Initial version
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
    
    async def update(
        self, 
        db: Session, 
        surgery_id: int, 
        surgery_update: SurgeryHospitalizationUpdate, 
        user_id: int
    ) -> Optional[SurgeryHospitalization]:
        """Update a surgery/hospitalization record. If user's current language differs from source_language, saves to translations table."""
        try:
            db_surgery = self.get_by_id(db, surgery_id, user_id)
            if not db_surgery:
                return None
            
            # Get user's current language
            from app.utils.user_language import get_user_language
            current_language = await get_user_language(user_id, db)
            source_language = getattr(db_surgery, 'source_language', 'en')
            
            update_data = surgery_update.dict(exclude_unset=True)
            
            # Text fields that can be translated
            text_fields = ['name', 'reason', 'treatment', 'body_area', 'notes']
            text_fields_updated = {field: update_data[field] for field in text_fields if field in update_data}
            
            # If user's language differs from source language and text fields are being updated
            if current_language != source_language and text_fields_updated:
                # Save to translations table instead of original entry
                from app.crud.translation import translation_crud
                
                current_version = getattr(db_surgery, 'version', 1)
                
                for field, value in text_fields_updated.items():
                    if value:  # Only save non-empty values
                        translation_crud.create_translation(
                            db=db,
                            entity_type='surgery_hospitalization',
                            entity_id=surgery_id,
                            field_name=field,
                            language=current_language,
                            translated_text=str(value),
                            source_language=source_language,
                            content_version=current_version
                        )
                        # Remove from update_data so we don't update the original
                        del update_data[field]
                
                logger.info(f"Saved translations for surgery {surgery_id} in language {current_language}")
            
            # Update non-text fields or if languages match
            if update_data:
                update_data['updated_by'] = user_id
            
                # If updating original entry and text fields changed, increment version
                if current_language == source_language:
                    text_fields_updated_in_original = any(field in update_data for field in text_fields)
                    if text_fields_updated_in_original:
                        current_version = getattr(db_surgery, 'version', 1)
                        update_data['version'] = current_version + 1
                        logger.info(f"Incrementing version for surgery {surgery_id} from {current_version} to {update_data['version']}")
                
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
