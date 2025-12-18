from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, String
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from app.models.health_record import (
    HealthRecord, MedicalCondition, FamilyMedicalHistory, 
    HealthRecordDocLab, HealthRecordSection, HealthRecordMetric, HealthRecordType, HealthRecordDocExam
)
from app.models.health_metrics import HealthRecordSectionTemplate, HealthRecordMetricTemplate
from app.schemas.health_record import (
    HealthRecordCreate, HealthRecordUpdate, HealthRecordFilter,
    MedicalConditionCreate, MedicalConditionUpdate,
    FamilyMedicalHistoryCreate, FamilyMedicalHistoryUpdate,
    HealthRecordDocLabCreate, HealthRecordDocLabUpdate
)
import logging

logger = logging.getLogger(__name__)

class HealthRecordCRUD:
    """CRUD operations for HealthRecord model"""
    
    def create(self, db: Session, health_record: HealthRecordCreate, user_id: int, skip_duplicate_check: bool = False) -> tuple[HealthRecord, bool]:
        """
        Create a new health record with optional duplicate detection.
        Returns (record, was_created_new)
        
        Args:
            skip_duplicate_check: If True, skip duplicate check (for webhook data).
                                 If False, check for duplicates in same hour (for manual entries).
        """
        try:
            # Check for duplicate values on the same date/hour (only if not skipped)
            # For manual entries, use measure_start_time if available, otherwise created_at will be used
            if not skip_duplicate_check:
                timestamp_for_check = health_record.measure_start_time
                if timestamp_for_check:
                    duplicate_record = self._check_duplicate_record(
                        db, user_id, health_record.metric_id, timestamp_for_check
                    )
                    
                    if duplicate_record:
                        # Update existing record instead of creating new one
                        duplicate_record.value = health_record.value
                        duplicate_record.status = health_record.status
                        duplicate_record.source = health_record.source
                        duplicate_record.device_id = health_record.device_id
                        duplicate_record.device_info = health_record.device_info
                        duplicate_record.accuracy = health_record.accuracy
                        duplicate_record.location_data = health_record.location_data
                        duplicate_record.measure_start_time = health_record.measure_start_time
                        duplicate_record.measure_end_time = health_record.measure_end_time
                        duplicate_record.data_type = health_record.data_type
                        duplicate_record.updated_at = func.now()
                        
                        db.commit()
                        db.refresh(duplicate_record)
                        
                        logger.info(f"Updated duplicate health record {duplicate_record.id} for user {user_id}")
                        return duplicate_record, False  # False = was not created new, was updated
            
            # Create new record if no duplicate found or duplicate check skipped
            db_health_record = HealthRecord(
                created_by=user_id,
                section_id=health_record.section_id,
                metric_id=health_record.metric_id,
                value=health_record.value,
                status=health_record.status,
                source=health_record.source,
                measure_start_time=health_record.measure_start_time,
                measure_end_time=health_record.measure_end_time,
                data_type=health_record.data_type,
                device_id=health_record.device_id,
                device_info=health_record.device_info,
                accuracy=health_record.accuracy,
                location_data=health_record.location_data
            )
            
            db.add(db_health_record)
            db.commit()
            db.refresh(db_health_record)
            
            logger.info(f"Created health record {db_health_record.id} for user {user_id}")
            return db_health_record, True  # True = was created new
            
        except Exception as e:
            logger.error(f"Failed to create health record: {e}")
            db.rollback()
            raise
    
    def _check_duplicate_record(
        self, 
        db: Session, 
        user_id: int, 
        metric_id: int, 
        measure_start_time: datetime
    ) -> Optional[HealthRecord]:
        """Check for duplicate records on the same date/hour using measure_start_time"""
        try:
            # Round measure_start_time to the nearest hour for comparison
            recorded_hour = measure_start_time.replace(minute=0, second=0, microsecond=0)
            next_hour = recorded_hour + timedelta(hours=1)
            
            return db.query(HealthRecord).filter(
                and_(
                    HealthRecord.created_by == user_id,
                    HealthRecord.metric_id == metric_id,
                    HealthRecord.measure_start_time >= recorded_hour,
                    HealthRecord.measure_start_time < next_hour
                )
            ).first()
            
        except Exception as e:
            logger.error(f"Failed to check for duplicate record: {e}")
            return None
    
    def _find_record_by_exact_timestamp(
        self, 
        db: Session, 
        user_id: int, 
        metric_id: int, 
        measure_start_time: datetime,
        data_type: Optional[str] = None
    ) -> Optional[HealthRecord]:
        """
        Find record by exact measure_start_time (not hour-based).
        Used for update events to find existing records to update.
        
        Args:
            data_type: Optional filter by data_type ('epoch' or 'daily')
        """
        try:
            query = db.query(HealthRecord).filter(
                and_(
                    HealthRecord.created_by == user_id,
                    HealthRecord.metric_id == metric_id,
                    HealthRecord.measure_start_time == measure_start_time
                )
            )
            
            # Optionally filter by data_type
            if data_type:
                query = query.filter(HealthRecord.data_type == data_type)
            
            return query.first()
            
        except Exception as e:
            logger.error(f"Failed to find record by exact timestamp: {e}")
            return None
    
    def update_or_create(
        self, 
        db: Session, 
        health_record: HealthRecordCreate, 
        user_id: int,
        data_type: Optional[str] = None
    ) -> tuple[HealthRecord, bool]:
        """
        For update events: find by exact timestamp, update if found, create if not.
        Returns (record, was_created_new)
        
        Args:
            data_type: Optional data_type filter ('epoch' or 'daily')
        """
        try:
            # Use measure_start_time for matching
            timestamp_to_match = health_record.measure_start_time
            
            if not timestamp_to_match:
                logger.warning("No measure_start_time available for update_or_create, creating new record")
                return self.create(db, health_record, user_id, skip_duplicate_check=True)
            
            # Find existing record by exact timestamp
            existing_record = self._find_record_by_exact_timestamp(
                db, user_id, health_record.metric_id, timestamp_to_match, data_type
            )
            
            if existing_record:
                # Update existing record
                existing_record.value = health_record.value
                existing_record.status = health_record.status
                existing_record.source = health_record.source
                existing_record.device_id = health_record.device_id
                existing_record.device_info = health_record.device_info
                existing_record.accuracy = health_record.accuracy
                existing_record.location_data = health_record.location_data
                existing_record.measure_start_time = health_record.measure_start_time
                existing_record.measure_end_time = health_record.measure_end_time
                existing_record.data_type = health_record.data_type
                existing_record.updated_at = func.now()
                
                db.commit()
                db.refresh(existing_record)
                
                logger.info(f"Updated existing health record {existing_record.id} for user {user_id} (update event)")
                return existing_record, False  # False = was not created new, was updated
            
            # No existing record found, create new one
            logger.info(f"No existing record found for timestamp {timestamp_to_match}, creating new record")
            return self.create(db, health_record, user_id, skip_duplicate_check=True)
            
        except Exception as e:
            logger.error(f"Failed to update or create health record: {e}")
            db.rollback()
            raise
    
    def get_by_id(self, db: Session, record_id: int, user_id: int) -> Optional[HealthRecord]:
        """Get health record by ID for a specific user"""
        try:
            return db.query(HealthRecord).filter(
                and_(
                    HealthRecord.id == record_id,
                    HealthRecord.created_by == user_id
                )
            ).first()
        except Exception as e:
            logger.error(f"Failed to get health record {record_id}: {e}")
            return None
    
    def get_by_user(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[HealthRecordFilter] = None
    ) -> List[HealthRecord]:
        """Get health records for a specific user with optional filtering"""
        try:
            query = db.query(HealthRecord).filter(HealthRecord.created_by == user_id)
            
            if filters:
                if filters.section_id:
                    query = query.filter(HealthRecord.section_id == filters.section_id)
                if filters.metric_id:
                    query = query.filter(HealthRecord.metric_id == filters.metric_id)
                if filters.status:
                    query = query.filter(HealthRecord.status == filters.status)
                if filters.source:
                    query = query.filter(HealthRecord.source == filters.source)
                if filters.device_id:
                    query = query.filter(HealthRecord.device_id == filters.device_id)
                if filters.start_date:
                    # Use measure_start_time if available, otherwise fall back to created_at
                    query = query.filter(
                        or_(
                            and_(
                                HealthRecord.measure_start_time.isnot(None),
                                HealthRecord.measure_start_time >= filters.start_date
                            ),
                            and_(
                                HealthRecord.measure_start_time.is_(None),
                                HealthRecord.created_at >= filters.start_date
                            )
                        )
                    )
                if filters.end_date:
                    # Use measure_start_time if available, otherwise fall back to created_at
                    query = query.filter(
                        or_(
                            and_(
                                HealthRecord.measure_start_time.isnot(None),
                                HealthRecord.measure_start_time <= filters.end_date
                            ),
                            and_(
                                HealthRecord.measure_start_time.is_(None),
                                HealthRecord.created_at <= filters.end_date
                            )
                        )
                    )
            
            # Order by measure_start_time if available, otherwise created_at
            return query.order_by(
                desc(
                    func.coalesce(HealthRecord.measure_start_time, HealthRecord.created_at)
                )
            ).offset(skip).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Failed to get health records for user {user_id}: {e}")
            return []
    
    def search_records(
        self, 
        db: Session, 
        user_id: int, 
        query: str, 
        filters: Optional[HealthRecordFilter] = None,
        limit: int = 100, 
        offset: int = 0
    ) -> List[HealthRecord]:
        """Search health records by text query"""
        try:
            base_query = db.query(HealthRecord).filter(HealthRecord.created_by == user_id)
            
            # Add text search
            search_query = f"%{query}%"
            base_query = base_query.filter(
                or_(
                    HealthRecord.value.cast(String).ilike(search_query),
                    HealthRecord.status.ilike(search_query),
                    HealthRecord.source.ilike(search_query)
                )
            )
            
            # Add filters
            if filters:
                if filters.section_id:
                    base_query = base_query.filter(HealthRecord.section_id == filters.section_id)
                if filters.metric_id:
                    base_query = base_query.filter(HealthRecord.metric_id == filters.metric_id)
                if filters.status:
                    base_query = base_query.filter(HealthRecord.status == filters.status)
                if filters.source:
                    base_query = base_query.filter(HealthRecord.source == filters.source)
                if filters.start_date:
                    # Use measure_start_time if available, otherwise created_at
                    base_query = base_query.filter(
                        or_(
                            and_(
                                HealthRecord.measure_start_time.isnot(None),
                                HealthRecord.measure_start_time >= filters.start_date
                            ),
                            and_(
                                HealthRecord.measure_start_time.is_(None),
                                HealthRecord.created_at >= filters.start_date
                            )
                        )
                    )
                if filters.end_date:
                    # Use measure_start_time if available, otherwise created_at
                    base_query = base_query.filter(
                        or_(
                            and_(
                                HealthRecord.measure_start_time.isnot(None),
                                HealthRecord.measure_start_time <= filters.end_date
                            ),
                            and_(
                                HealthRecord.measure_start_time.is_(None),
                                HealthRecord.created_at <= filters.end_date
                            )
                        )
                    )
            
            # Order by measure_start_time if available, otherwise created_at
            return base_query.order_by(
                desc(
                    func.coalesce(HealthRecord.measure_start_time, HealthRecord.created_at)
                )
            ).offset(offset).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Failed to search health records for user {user_id}: {e}")
            return []
    
    def get_stats(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get health record statistics for a user"""
        try:
            total_records = db.query(func.count(HealthRecord.id)).filter(
                HealthRecord.created_by == user_id
            ).scalar()
            
            # Records by section
            records_by_section = db.query(
                HealthRecord.section_id,
                func.count(HealthRecord.id)
            ).filter(
                HealthRecord.created_by == user_id
            ).group_by(HealthRecord.section_id).all()
            
            # Records by source
            records_by_source = db.query(
                HealthRecord.source,
                func.count(HealthRecord.id)
            ).filter(
                HealthRecord.created_by == user_id
            ).group_by(HealthRecord.source).all()
            
            # Records by status
            records_by_status = db.query(
                HealthRecord.status,
                func.count(HealthRecord.id)
            ).filter(
                HealthRecord.created_by == user_id
            ).group_by(HealthRecord.status).all()
            
            # Recent records (last 30 days) - use measure_start_time if available, otherwise created_at
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_records = db.query(func.count(HealthRecord.id)).filter(
                and_(
                    HealthRecord.created_by == user_id,
                    or_(
                        and_(
                            HealthRecord.measure_start_time.isnot(None),
                            HealthRecord.measure_start_time >= thirty_days_ago
                        ),
                        and_(
                            HealthRecord.measure_start_time.is_(None),
                            HealthRecord.created_at >= thirty_days_ago
                        )
                    )
                )
            ).scalar()
            
            # Average records per day - use measure_start_time if available, otherwise created_at
            first_record = db.query(
                func.coalesce(HealthRecord.measure_start_time, HealthRecord.created_at).label('first_date')
            ).filter(
                HealthRecord.created_by == user_id
            ).order_by(
                func.coalesce(HealthRecord.measure_start_time, HealthRecord.created_at).asc()
            ).first()
            
            if first_record and first_record.first_date:
                days_since_first = (datetime.utcnow() - first_record.first_date).days
                avg_per_day = total_records / max(days_since_first, 1)
            else:
                avg_per_day = 0.0
            
            return {
                "total_records": total_records,
                "records_by_section": dict(records_by_section),
                "records_by_source": dict(records_by_source),
                "records_by_status": dict(records_by_status),
                "recent_records": recent_records,
                "average_records_per_day": round(avg_per_day, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get health record stats for user {user_id}: {e}")
            return {
                "total_records": 0,
                "records_by_section": {},
                "records_by_source": {},
                "records_by_status": {},
                "recent_records": 0,
                "average_records_per_day": 0.0
            }
    
    def update(
        self, 
        db: Session, 
        record_id: int, 
        health_record_update: HealthRecordUpdate, 
        user_id: int
    ) -> Optional[HealthRecord]:
        """Update a health record"""
        try:
            db_health_record = self.get_by_id(db, record_id, user_id)
            if not db_health_record:
                return None
            
            update_data = health_record_update.dict(exclude_unset=True)
            update_data['updated_by'] = user_id
            
            for field, value in update_data.items():
                setattr(db_health_record, field, value)
            
            db.commit()
            db.refresh(db_health_record)
            
            logger.info(f"Updated health record {record_id} for user {user_id}")
            return db_health_record
            
        except Exception as e:
            logger.error(f"Failed to update health record {record_id}: {e}")
            db.rollback()
            return None
    
    def delete(self, db: Session, record_id: int, user_id: int) -> bool:
        """Delete a health record"""
        try:
            db_health_record = self.get_by_id(db, record_id, user_id)
            if not db_health_record:
                return False
            
            db.delete(db_health_record)
            db.commit()
            
            logger.info(f"Deleted health record {record_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete health record {record_id}: {e}")
            db.rollback()
            return False

class MedicalConditionCRUD:
    """CRUD operations for MedicalCondition model"""
    
    async def create(self, db: Session, condition: MedicalConditionCreate, user_id: int) -> MedicalCondition:
        """Create a new medical condition"""
        try:
            # Get user's current language to save as source_language
            from app.utils.user_language import get_user_language_from_cache
            source_lang = await get_user_language_from_cache(user_id, db)
            
            db_condition = MedicalCondition(
                condition_name=condition.condition_name,
                description=condition.description,
                diagnosed_date=condition.diagnosed_date,
                status=condition.status,
                source=condition.source,
                treatment_plan=condition.treatment_plan,
                resolved_date=condition.resolved_date,
                source_language=source_lang,
                version=1,  # Initial version
                created_by=user_id
            )
            
            db.add(db_condition)
            db.commit()
            db.refresh(db_condition)
            
            logger.info(f"Created medical condition {db_condition.id} for user {user_id}")
            return db_condition
            
        except Exception as e:
            logger.error(f"Failed to create medical condition: {e}")
            db.rollback()
            raise
    
    def get_by_id(self, db: Session, condition_id: int, user_id: int) -> Optional[MedicalCondition]:
        """Get medical condition by ID for a specific user"""
        try:
            return db.query(MedicalCondition).filter(
                and_(
                    MedicalCondition.id == condition_id,
                    MedicalCondition.created_by == user_id
                )
            ).first()
        except Exception as e:
            logger.error(f"Failed to get medical condition {condition_id}: {e}")
            return None
    
    def get_by_user(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[MedicalCondition]:
        """Get medical conditions for a specific user"""
        try:
            return db.query(MedicalCondition).filter(
                MedicalCondition.created_by == user_id
            ).order_by(desc(MedicalCondition.created_at)).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to get medical conditions for user {user_id}: {e}")
            return []
    
    async def update(
        self, 
        db: Session, 
        condition_id: int, 
        condition_update: MedicalConditionUpdate, 
        user_id: int
    ) -> Optional[MedicalCondition]:
        """Update a medical condition. If user's current language differs from source_language, saves to translations table."""
        try:
            db_condition = self.get_by_id(db, condition_id, user_id)
            if not db_condition:
                return None
            
            # Get user's current language from cache
            from app.utils.user_language import get_user_language_from_cache
            current_language = await get_user_language_from_cache(user_id, db)
            source_language = getattr(db_condition, 'source_language', 'en')
            
            update_data = condition_update.dict(exclude_unset=True)
            
            # Text fields that can be translated
            text_fields = ['condition_name', 'description', 'treatment_plan']
            text_fields_updated = {field: update_data[field] for field in text_fields if field in update_data}
            
            # If user's language differs from source language and text fields are being updated
            if current_language != source_language and text_fields_updated:
                # Save to translations table instead of original entry
                from app.crud.translation import translation_crud
                
                current_version = getattr(db_condition, 'version', 1)
                
                for field, value in text_fields_updated.items():
                    if value:  # Only save non-empty values
                        translation_crud.create_translation(
                            db=db,
                            entity_type='medical_condition',
                            entity_id=condition_id,
                            field_name=field,
                            language=current_language,
                            translated_text=str(value),
                            source_language=source_language,
                            content_version=current_version
                        )
                        # Remove from update_data so we don't update the original
                        del update_data[field]
                
                logger.info(f"Saved translations for condition {condition_id} in language {current_language}")
            
            # Update non-text fields or if languages match
            if update_data:
                update_data['updated_by'] = user_id
            
                # If updating original entry and text fields changed, increment version
                if current_language == source_language:
                    text_fields_updated_in_original = any(field in update_data for field in text_fields)
                    if text_fields_updated_in_original:
                        current_version = getattr(db_condition, 'version', 1)
                        update_data['version'] = current_version + 1
                        logger.info(f"Incrementing version for condition {condition_id} from {current_version} to {update_data['version']}")
                
            for field, value in update_data.items():
                setattr(db_condition, field, value)
            
            db.commit()
            db.refresh(db_condition)
            
            logger.info(f"Updated medical condition {condition_id} for user {user_id}")
            return db_condition
            
        except Exception as e:
            logger.error(f"Failed to update medical condition {condition_id}: {e}")
            db.rollback()
            return None
    
    def delete(self, db: Session, condition_id: int, user_id: int) -> bool:
        """Delete a medical condition"""
        try:
            db_condition = self.get_by_id(db, condition_id, user_id)
            if not db_condition:
                return False
            
            db.delete(db_condition)
            db.commit()
            
            logger.info(f"Deleted medical condition {condition_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete medical condition {condition_id}: {e}")
            db.rollback()
            return False

class FamilyMedicalHistoryCRUD:
    """CRUD operations for FamilyMedicalHistory model"""
    
    async def create(self, db: Session, history: FamilyMedicalHistoryCreate, user_id: int) -> FamilyMedicalHistory:
        """Create a new family medical history record"""
        try:
            # Get user's current language to save as source_language
            from app.utils.user_language import get_user_language_from_cache
            source_lang = await get_user_language_from_cache(user_id, db)
            
            # Convert chronic_diseases to dict format for JSON column
            chronic_diseases_data = [disease.dict() for disease in history.chronic_diseases] if history.chronic_diseases else []
            
            db_history = FamilyMedicalHistory(
                relation=history.relation,
                is_deceased=history.is_deceased,
                age_at_death=history.age_at_death,
                cause_of_death=history.cause_of_death,
                chronic_diseases=chronic_diseases_data,
                # Legacy fields
                condition_name=history.condition_name,
                age_of_onset=history.age_of_onset,
                description=history.description,
                status=history.status,
                source=history.source,
                source_language=source_lang,
                version=1,  # Initial version
                created_by=user_id
            )
            
            db.add(db_history)
            db.commit()
            db.refresh(db_history)
            
            logger.info(f"Created family medical history {db_history.id} for user {user_id}")
            return db_history
            
        except Exception as e:
            logger.error(f"Failed to create family medical history: {e}")
            db.rollback()
            raise
    
    def get_by_id(self, db: Session, history_id: int, user_id: int) -> Optional[FamilyMedicalHistory]:
        """Get family medical history by ID for a specific user"""
        try:
            return db.query(FamilyMedicalHistory).filter(
                and_(
                    FamilyMedicalHistory.id == history_id,
                    FamilyMedicalHistory.created_by == user_id
                )
            ).first()
        except Exception as e:
            logger.error(f"Failed to get family medical history {history_id}: {e}")
            return None
    
    def get_by_user(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[FamilyMedicalHistory]:
        """Get family medical history for a specific user"""
        try:
            return db.query(FamilyMedicalHistory).filter(
                FamilyMedicalHistory.created_by == user_id
            ).order_by(FamilyMedicalHistory.id.asc()).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to get family medical history for user {user_id}: {e}")
            return []
    
    async def update(
        self, 
        db: Session, 
        history_id: int, 
        history_update: FamilyMedicalHistoryUpdate, 
        user_id: int
    ) -> Optional[FamilyMedicalHistory]:
        """Update a family medical history record. If user's current language differs from source_language, saves to translations table."""
        try:
            db_history = self.get_by_id(db, history_id, user_id)
            if not db_history:
                return None
            
            # Get user's current language from cache
            from app.utils.user_language import get_user_language_from_cache
            current_language = await get_user_language_from_cache(user_id, db)
            source_language = getattr(db_history, 'source_language', 'en')
            
            update_data = history_update.dict(exclude_unset=True)
            
            # Handle chronic_diseases conversion
            if 'chronic_diseases' in update_data and update_data['chronic_diseases'] is not None:
                update_data['chronic_diseases'] = [
                    disease.dict() if hasattr(disease, 'dict') else disease 
                    for disease in update_data['chronic_diseases']
                ]
            
            # Text fields that can be translated
            text_fields = ['cause_of_death', 'condition_name', 'description', 'outcome']
            text_fields_updated = {field: update_data[field] for field in text_fields if field in update_data}
            
            # Handle chronic_diseases separately (it's a JSON field)
            chronic_diseases_updated = 'chronic_diseases' in update_data
            
            # If user's language differs from source language and text fields are being updated
            if current_language != source_language and (text_fields_updated or chronic_diseases_updated):
                # Save to translations table instead of original entry
                from app.crud.translation import translation_crud
                import json
                
                current_version = getattr(db_history, 'version', 1)
                
                # Save text field translations
                for field, value in text_fields_updated.items():
                    if value:  # Only save non-empty values
                        translation_crud.create_translation(
                            db=db,
                            entity_type='family_medical_history',
                            entity_id=history_id,
                            field_name=field,
                            language=current_language,
                            translated_text=str(value),
                            source_language=source_language,
                            content_version=current_version
                        )
                        # Remove from update_data so we don't update the original
                        del update_data[field]
                
                # Save chronic_diseases translation (as JSON string)
                if chronic_diseases_updated and update_data['chronic_diseases']:
                    chronic_diseases_json = json.dumps(update_data['chronic_diseases'], ensure_ascii=False)
                    translation_crud.create_translation(
                        db=db,
                        entity_type='family_medical_history',
                        entity_id=history_id,
                        field_name='chronic_diseases',
                        language=current_language,
                        translated_text=chronic_diseases_json,
                        source_language=source_language,
                        content_version=current_version
                    )
                    # Remove from update_data so we don't update the original
                    del update_data['chronic_diseases']
                
                logger.info(f"Saved translations for family history {history_id} in language {current_language}")
            
            # Update non-text fields or if languages match
            if update_data:
                update_data['updated_by'] = user_id
            
                # If updating original entry and text fields changed, increment version
                if current_language == source_language:
                    text_fields_updated_in_original = any(field in update_data for field in text_fields + ['chronic_diseases'])
                    if text_fields_updated_in_original:
                        current_version = getattr(db_history, 'version', 1)
                        update_data['version'] = current_version + 1
                        logger.info(f"Incrementing version for family history {history_id} from {current_version} to {update_data['version']}")
                
            for field, value in update_data.items():
                setattr(db_history, field, value)
            
            db.commit()
            db.refresh(db_history)
            
            logger.info(f"Updated family medical history {history_id} for user {user_id}")
            return db_history
            
        except Exception as e:
            logger.error(f"Failed to update family medical history {history_id}: {e}")
            db.rollback()
            return None
    
    def delete(self, db: Session, history_id: int, user_id: int) -> bool:
        """Delete a family medical history record"""
        try:
            db_history = self.get_by_id(db, history_id, user_id)
            if not db_history:
                return False
            
            db.delete(db_history)
            db.commit()
            
            logger.info(f"Deleted family medical history {history_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete family medical history {history_id}: {e}")
            db.rollback()
            return False

class HealthRecordDocLabCRUD:
    """CRUD operations for HealthRecordDocLab model"""
    
    def create(self, db: Session, document: HealthRecordDocLabCreate, user_id: int) -> HealthRecordDocLab:
        """Create a new medical document"""
        try:
            db_document = HealthRecordDocLab(
                created_by=user_id,
                health_record_type_id=document.health_record_type_id,
                lab_doc_type=document.lab_doc_type,
                lab_test_date=document.lab_test_date,
                provider=document.provider,
                file_name=document.file_name,
                s3_url=document.s3_url,
                file_type=document.file_type,
                description=document.description,
                general_doc_type=document.general_doc_type
            )
            
            db.add(db_document)
            db.commit()
            db.refresh(db_document)
            
            logger.info(f"Created medical document {db_document.id} for user {user_id}")
            return db_document
            
        except Exception as e:
            logger.error(f"Failed to create medical document: {e}")
            db.rollback()
            raise
    
    def get_by_id(self, db: Session, document_id: int, user_id: int) -> Optional[HealthRecordDocLab]:
        """Get medical document by ID for a specific user"""
        try:
            return db.query(HealthRecordDocLab).filter(
                and_(
                    HealthRecordDocLab.id == document_id,
                    HealthRecordDocLab.created_by == user_id
                )
            ).first()
        except Exception as e:
            logger.error(f"Failed to get medical document {document_id}: {e}")
            return None
    
    def get_by_user(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[HealthRecordDocLab]:
        """Get medical documents for a specific user"""
        try:
            return db.query(HealthRecordDocLab).filter(
                HealthRecordDocLab.created_by == user_id
            ).order_by(desc(HealthRecordDocLab.created_at)).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to get medical documents for user {user_id}: {e}")
            return []
    
    def update(
        self, 
        db: Session, 
        document_id: int, 
        document_update: HealthRecordDocLabUpdate, 
        user_id: int
    ) -> Optional[HealthRecordDocLab]:
        """Update a medical document record"""
        try:
            db_document = self.get_by_id(db, document_id, user_id)
            if not db_document:
                return None
            
            update_data = document_update.dict(exclude_unset=True)
            update_data['updated_by'] = user_id
            
            # Handle date string conversion if lab_test_date is provided
            if 'lab_test_date' in update_data and update_data['lab_test_date']:
                from app.utils.date_utils import parse_date_string
                try:
                    parsed_date = parse_date_string(update_data['lab_test_date'])
                    update_data['lab_test_date'] = parsed_date
                except Exception as date_error:
                    logger.warning(f"Could not parse date string '{update_data['lab_test_date']}': {date_error}")
            
            for field, value in update_data.items():
                setattr(db_document, field, value)
            
            db.commit()
            db.refresh(db_document)
            
            logger.info(f"Updated medical document {document_id} for user {user_id}")
            return db_document
            
        except Exception as e:
            logger.error(f"Failed to update medical document {document_id}: {e}")
            db.rollback()
            return None
    
    def delete(self, db: Session, document_id: int, user_id: int) -> bool:
        """Delete a medical document record"""
        try:
            db_document = self.get_by_id(db, document_id, user_id)
            if not db_document:
                return False
            
            db.delete(db_document)
            db.commit()
            
            logger.info(f"Deleted medical document {document_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete medical document {document_id}: {e}")
            db.rollback()
            return False
    
    def check_duplicate_file(
        self,
        db: Session,
        user_id: int,
        filename: str,
        file_size: int
    ) -> Optional[HealthRecordDocLab]:
        """Check for duplicate lab document by filename AND file size (both must match)"""
        try:
            # Note: HealthRecordDocLab doesn't have file_size field, so we check by filename only
            # In the future, file_size should be added to the model for proper duplicate detection
            duplicate = db.query(HealthRecordDocLab).filter(
                and_(
                    HealthRecordDocLab.created_by == user_id,
                    HealthRecordDocLab.file_name == filename
                )
            ).first()
            
            return duplicate
            
        except Exception as e:
            logger.error(f"Error checking for duplicate lab document: {e}")
            return None

# ============================================================================
# HEALTH RECORD TYPE CRUD
# ============================================================================

class HealthRecordTypeCRUD:
    """CRUD operations for HealthRecordType model"""
    
    def create(self, db: Session, type_data, user_id: int):
        """Create a new health record type"""
        try:
            db_type = HealthRecordType(
                name=type_data.name,
                display_name=type_data.display_name,
                description=type_data.description,
                is_active=type_data.is_active,
                created_by=user_id
            )
            
            db.add(db_type)
            db.commit()
            db.refresh(db_type)
            
            logger.info(f"Created health record type {db_type.id} for user {user_id}")
            return db_type
            
        except Exception as e:
            logger.error(f"Failed to create health record type: {e}")
            db.rollback()
            raise
    
    def get_by_id(self, db: Session, type_id: int):
        """Get health record type by ID"""
        try:
            return db.query(HealthRecordType).filter(HealthRecordType.id == type_id).first()
        except Exception as e:
            logger.error(f"Failed to get health record type {type_id}: {e}")
            return None
    
    def get_all(self, db: Session, skip: int = 0, limit: int = 100):
        """Get all health record types"""
        try:
            return db.query(HealthRecordType).filter(
                HealthRecordType.is_active == True
            ).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to get health record types: {e}")
            return []
    
    def update(self, db: Session, type_id: int, type_update, user_id: int):
        """Update a health record type"""
        try:
            db_type = self.get_by_id(db, type_id)
            if not db_type:
                return None
            
            update_data = type_update.dict(exclude_unset=True)
            update_data['updated_by'] = user_id
            
            for field, value in update_data.items():
                setattr(db_type, field, value)
            
            db.commit()
            db.refresh(db_type)
            
            logger.info(f"Updated health record type {type_id} for user {user_id}")
            return db_type
            
        except Exception as e:
            logger.error(f"Failed to update health record type {type_id}: {e}")
            db.rollback()
            return None
    
    def delete(self, db: Session, type_id: int, user_id: int) -> bool:
        """Delete a health record type (soft delete by setting is_active to False)"""
        try:
            db_type = self.get_by_id(db, type_id)
            if not db_type:
                return False
            
            db_type.is_active = False
            db_type.updated_by = user_id
            db.commit()
            
            logger.info(f"Deleted health record type {type_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete health record type {type_id}: {e}")
            db.rollback()
            return False

# ============================================================================
# HEALTH RECORD SECTION CRUD
# ============================================================================

class HealthRecordSectionCRUD:
    """CRUD operations for HealthRecordSection model"""
    
    def create(self, db: Session, section_data, user_id: int):
        """Create a new health record section"""
        try:
            # Get user's language preference for source_language
            # Note: In sync context, default to 'en' for source_language
            # This is acceptable as source_language is mainly for tracking original language
            source_language = 'en'
            
            db_section = HealthRecordSection(
                name=section_data.name,
                display_name=section_data.display_name,
                description=section_data.description,
                source_language=source_language,
                health_record_type_id=section_data.health_record_type_id,
                section_template_id=getattr(section_data, 'section_template_id', None),
                is_default=section_data.is_default,
                created_by=user_id
            )
            
            db.add(db_section)
            db.commit()
            db.refresh(db_section)
            
            logger.info(f"Created health record section {db_section.id} for user {user_id}")
            return db_section
            
        except Exception as e:
            logger.error(f"Failed to create health record section: {e}")
            db.rollback()
            raise
    
    def get_by_id(self, db: Session, section_id: int):
        """Get health record section by ID"""
        try:
            return db.query(HealthRecordSection).filter(HealthRecordSection.id == section_id).first()
        except Exception as e:
            logger.error(f"Failed to get health record section {section_id}: {e}")
            return None
    
    def get_by_type(self, db: Session, type_id: int, skip: int = 0, limit: int = 100):
        """Get sections by health record type"""
        try:
            return db.query(HealthRecordSection).filter(
                HealthRecordSection.health_record_type_id == type_id
            ).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to get sections for type {type_id}: {e}")
            return []
    
    def get_by_user(self, db: Session, user_id: int, skip: int = 0, limit: int = 100):
        """Get sections created by a specific user"""
        try:
            return db.query(HealthRecordSection).filter(
                HealthRecordSection.created_by == user_id
            ).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to get sections for user {user_id}: {e}")
            return []
    
    def update(self, db: Session, section_id: int, section_update, user_id: int):
        """Update a health record section"""
        try:
            db_section = self.get_by_id(db, section_id)
            if not db_section:
                return None
            
            update_data = section_update.dict(exclude_unset=True)
            update_data['updated_by'] = user_id
            
            for field, value in update_data.items():
                setattr(db_section, field, value)
            
            db.commit()
            db.refresh(db_section)
            
            logger.info(f"Updated health record section {section_id} for user {user_id}")
            return db_section
            
        except Exception as e:
            logger.error(f"Failed to update health record section {section_id}: {e}")
            db.rollback()
            return None
    
    def delete(self, db: Session, section_id: int, user_id: int) -> bool:
        """Delete a health record section and all related metrics and health records"""
        try:
            db_section = self.get_by_id(db, section_id)
            if not db_section:
                return False
            
            # Determine if this is a user-created section or admin template
            is_user_created = not db_section.is_default
            
            # First, get all metrics in this section
            from app.models.health_record import HealthRecordMetric, HealthRecord
            from app.crud.translation import translation_crud
            metrics = db.query(HealthRecordMetric).filter(
                HealthRecordMetric.section_id == section_id
            ).order_by(HealthRecordMetric.name.asc()).all()
            
            total_deleted_records = 0
            
            # For each metric, delete all associated health records and translations
            for metric in metrics:
                health_records = db.query(HealthRecord).filter(
                    HealthRecord.metric_id == metric.id
                ).all()
                
                for record in health_records:
                    db.delete(record)
                    total_deleted_records += 1
                    logger.info(f"Deleted health record {record.id} associated with metric {metric.id}")
                
                # Delete translations for this metric
                translation_crud.delete_translations(
                    db, 
                    entity_type='health_record_metrics',
                    entity_id=metric.id
                )
                logger.info(f"Deleted translations for metric {metric.id}")
                
                # Delete the metric itself
                db.delete(metric)
                logger.info(f"Deleted metric {metric.id} from section {section_id}")
            
            # Handle template cleanup based on section type
            if db_section.section_template_id:
                from app.models.health_metrics import HealthRecordMetricTemplate, HealthRecordSectionTemplate
                
                if is_user_created:
                    # For user-created sections: delete from both normal and template tables
                    logger.info(f"Deleting user-created section {section_id} from both normal and template tables")
                    
                    # Get the section template first
                    section_template = db.query(HealthRecordSectionTemplate).filter(
                        and_(
                            HealthRecordSectionTemplate.id == db_section.section_template_id,
                            HealthRecordSectionTemplate.created_by == user_id,
                            HealthRecordSectionTemplate.is_default == False  # User-created template
                        )
                    ).first()
                    
                    if section_template:
                        # Delete ALL metric templates that reference this section template
                        # This prevents foreign key constraint violations when deleting the section template
                        all_metric_templates = db.query(HealthRecordMetricTemplate).filter(
                            HealthRecordMetricTemplate.section_template_id == section_template.id
                        ).all()
                        
                        # Delete user-created metric templates
                        for metric_template in all_metric_templates:
                            if metric_template.is_default == False and metric_template.created_by == user_id:
                                db.delete(metric_template)
                                logger.info(f"Deleted user-created metric template {metric_template.id}")
                            else:
                                # If there are admin-created metric templates referencing a user-created section template,
                                # this is a data inconsistency. We need to delete them too to avoid FK constraint violations.
                                logger.warning(f"Admin-created metric template {metric_template.id} references user-created section template {section_template.id}. Deleting to avoid FK constraint violation.")
                                db.delete(metric_template)
                                logger.info(f"Deleted admin-created metric template {metric_template.id} that referenced user-created section template")
                        
                        # Verify no metric templates remain before deleting section template
                        remaining_count = db.query(HealthRecordMetricTemplate).filter(
                            HealthRecordMetricTemplate.section_template_id == section_template.id
                        ).count()
                        
                        if remaining_count > 0:
                            logger.error(f"Cannot delete section template {section_template.id}: {remaining_count} metric templates still reference it")
                            raise ValueError(f"Cannot delete section template: {remaining_count} metric templates still reference it")
                        
                        # Now safe to delete the section template
                        db.delete(section_template)
                        logger.info(f"Deleted user-created section template {section_template.id}")
                else:
                    # For admin template sections: delete from normal table only
                    logger.info(f"Deleting admin template section {section_id} from normal table only")
            
            # Delete translations for this section
            translation_crud.delete_translations(
                db,
                entity_type='health_record_sections',
                entity_id=section_id
            )
            logger.info(f"Deleted translations for section {section_id}")
            
            # Finally, delete the section itself
            db.delete(db_section)
            db.commit()
            
            logger.info(f"Deleted health record section {section_id}, {len(metrics)} metrics, and {total_deleted_records} health records for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete health record section {section_id}: {e}")
            db.rollback()
            return False

# ============================================================================
# HEALTH RECORD METRIC CRUD
# ============================================================================

class HealthRecordMetricCRUD:
    """CRUD operations for HealthRecordMetric model"""
    
    def create(self, db: Session, metric_data, user_id: int):
        """Create a new health record metric"""
        try:
            # Get user's language preference for source_language
            # Note: In sync context, default to 'en' for source_language
            # This is acceptable as source_language is mainly for tracking original language
            source_language = 'en'
            
            db_metric = HealthRecordMetric(
                section_id=metric_data.section_id,
                metric_tmp_id=metric_data.metric_tmp_id,
                name=metric_data.name,
                display_name=metric_data.display_name,
                description=metric_data.description,
                default_unit=metric_data.default_unit,
                source_language=source_language,
                reference_data=metric_data.reference_data,
                data_type=metric_data.data_type,
                is_default=metric_data.is_default,
                created_by=user_id
            )
            
            db.add(db_metric)
            db.commit()
            db.refresh(db_metric)
            
            logger.info(f"Created health record metric {db_metric.id} for user {user_id}")
            return db_metric
            
        except Exception as e:
            logger.error(f"Failed to create health record metric: {e}")
            db.rollback()
            raise
    
    def get_by_id(self, db: Session, metric_id: int):
        """Get health record metric by ID"""
        try:
            return db.query(HealthRecordMetric).filter(HealthRecordMetric.id == metric_id).first()
        except Exception as e:
            logger.error(f"Failed to get health record metric {metric_id}: {e}")
            return None
    
    def get_by_section(self, db: Session, section_id: int, skip: int = 0, limit: int = 100):
        """Get metrics by section"""
        try:
            return db.query(HealthRecordMetric).filter(
                HealthRecordMetric.section_id == section_id
            ).order_by(HealthRecordMetric.name.asc()).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to get metrics for section {section_id}: {e}")
            return []
    
    def get_by_section_and_name(self, db: Session, section_id: int, name: str):
        """Get metric by section and name"""
        try:
            return db.query(HealthRecordMetric).filter(
                HealthRecordMetric.section_id == section_id,
                HealthRecordMetric.name == name
            ).first()
        except Exception as e:
            logger.error(f"Failed to get metric by section {section_id} and name {name}: {e}")
            return None
    
    def get_by_user(self, db: Session, user_id: int, skip: int = 0, limit: int = 100):
        """Get metrics created by a specific user"""
        try:
            return db.query(HealthRecordMetric).filter(
                HealthRecordMetric.created_by == user_id
            ).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to get metrics for user {user_id}: {e}")
            return []
    
    def update(self, db: Session, metric_id: int, metric_update, user_id: int):
        """Update a health record metric"""
        try:
            db_metric = self.get_by_id(db, metric_id)
            if not db_metric:
                return None
            
            update_data = metric_update.dict(exclude_unset=True)
            update_data['updated_by'] = user_id
            
            for field, value in update_data.items():
                setattr(db_metric, field, value)
            
            db.commit()
            db.refresh(db_metric)
            
            logger.info(f"Updated health record metric {metric_id} for user {user_id}")
            return db_metric
            
        except Exception as e:
            logger.error(f"Failed to update health record metric {metric_id}: {e}")
            db.rollback()
            return None
    
    def delete(self, db: Session, metric_id: int, user_id: int) -> bool:
        """Delete a health record metric and all related health records"""
        try:
            db_metric = self.get_by_id(db, metric_id)
            if not db_metric:
                return False
            
            # Determine if this is a user-created metric or admin template
            is_user_created = not db_metric.is_default
            
            # First, delete all health records associated with this metric
            from app.models.health_record import HealthRecord
            from app.crud.translation import translation_crud
            health_records = db.query(HealthRecord).filter(
                HealthRecord.metric_id == metric_id
            ).all()
            
            for record in health_records:
                db.delete(record)
                logger.info(f"Deleted health record {record.id} associated with metric {metric_id}")
            
            # Handle template cleanup based on metric type
            if is_user_created:
                # For user-created metrics: delete from both normal and template tables
                logger.info(f"Deleting user-created metric {metric_id} from both normal and template tables")
                
                # Delete the corresponding metric template using metric_tmp_id
                if db_metric.metric_tmp_id:
                    from app.models.health_metrics import HealthRecordMetricTemplate
                    metric_template = db.query(HealthRecordMetricTemplate).filter(
                        and_(
                            HealthRecordMetricTemplate.id == db_metric.metric_tmp_id,
                            HealthRecordMetricTemplate.created_by == user_id,
                            HealthRecordMetricTemplate.is_default == False  # User-created template
                        )
                    ).first()
                    
                    if metric_template:
                        db.delete(metric_template)
                        logger.info(f"Deleted user-created metric template {metric_template.id}")
                else:
                    logger.warning(f"User-created metric {metric_id} has no metric_tmp_id - cannot delete template")
            else:
                # For admin template metrics: delete from normal table only
                logger.info(f"Deleting admin template metric {metric_id} from normal table only")
            
            # Delete translations for this metric
            translation_crud.delete_translations(
                db,
                entity_type='health_record_metrics',
                entity_id=metric_id
            )
            logger.info(f"Deleted translations for metric {metric_id}")
            
            # Delete the metric itself
            db.delete(db_metric)
            db.commit()
            
            logger.info(f"Deleted health record metric {metric_id} and {len(health_records)} related records for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete health record metric {metric_id}: {e}")
            db.rollback()
            return False

# ============================================================================
# SECTION AND METRIC MANAGEMENT CRUD
# ============================================================================

class HealthRecordSectionMetricCRUD:
    """CRUD operations for managing sections and metrics together"""
    
    def get_sections_with_metrics(
        self, 
        db: Session, 
        user_id: int,
        include_inactive: bool = False,
        health_record_type_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all sections with their associated metrics"""
        try:
            # Get only user-created sections (not admin defaults)
            query = db.query(HealthRecordSection).filter(
                and_(
                    HealthRecordSection.created_by == user_id,  # User's own sections only
                    HealthRecordSection.is_default == False     # Exclude admin defaults
                )
            )
            
            # Filter by health record type if specified
            if health_record_type_id is not None:
                query = query.filter(HealthRecordSection.health_record_type_id == health_record_type_id)
            
            if not include_inactive:
                # Assuming there's an is_active field, if not, we'll skip this filter
                pass
            
            sections = query.all()
            
            sections_with_metrics = []
            for section in sections:
                # Get metrics for this section - order by name to maintain consistent order
                metrics = db.query(HealthRecordMetric).filter(
                    HealthRecordMetric.section_id == section.id
                ).order_by(HealthRecordMetric.name.asc()).all()
                
                # Get section statistics
                total_records = db.query(func.count(HealthRecord.id)).filter(
                    and_(
                        HealthRecord.created_by == user_id,
                        HealthRecord.section_id == section.id
                    )
                ).scalar()
                
                # Get recent activity (last 7 days) - use measure_start_time if available, otherwise created_at
                seven_days_ago = datetime.utcnow() - timedelta(days=7)
                recent_activity = db.query(func.count(HealthRecord.id)).filter(
                    and_(
                        HealthRecord.created_by == user_id,
                        HealthRecord.section_id == section.id,
                        or_(
                            and_(
                                HealthRecord.measure_start_time.isnot(None),
                                HealthRecord.measure_start_time >= seven_days_ago
                            ),
                            and_(
                                HealthRecord.measure_start_time.is_(None),
                                HealthRecord.created_at >= seven_days_ago
                            )
                        )
                    )
                ).scalar()
                
                section_data = {
                    "id": section.id,
                    "name": section.name,
                    "display_name": section.display_name,
                    "description": section.description,
                    "health_record_type_id": section.health_record_type_id,
                    "section_template_id": section.section_template_id,
                    "is_default": section.is_default,
                    "total_records": total_records,
                    "recent_activity": recent_activity,
                    "metrics": []
                }
                
                # Add metrics data
                for metric in metrics:
                    # Get metric template to check thryve_type
                    from app.models.health_metrics import HealthRecordMetricTemplate
                    metric_template = None
                    if metric.metric_tmp_id:
                        metric_template = db.query(HealthRecordMetricTemplate).filter(
                            HealthRecordMetricTemplate.id == metric.metric_tmp_id
                        ).first()
                    
                    # Get metric statistics
                    metric_total_records = db.query(func.count(HealthRecord.id)).filter(
                        and_(
                            HealthRecord.created_by == user_id,
                            HealthRecord.metric_id == metric.id
                        )
                    ).scalar()
                    
                    # Get latest record for this metric - use measure_start_time if available, otherwise created_at
                    latest_record = db.query(HealthRecord).filter(
                        and_(
                            HealthRecord.created_by == user_id,
                            HealthRecord.metric_id == metric.id
                        )
                    ).order_by(
                        desc(
                            func.coalesce(HealthRecord.measure_start_time, HealthRecord.created_at)
                        )
                    ).first()
                    
                    # Get all historical data points for trend analysis
                    # Filter based on thryve_type from metric template:
                    # - If thryve_type is "Daily": show only daily data (one value per date)
                    # - If thryve_type is "Epoch": show all epoch data (multiple values per date)
                    # - If thryve_type is None: show all data (backward compatibility)
                    historical_records_query = db.query(HealthRecord).filter(
                        and_(
                            HealthRecord.created_by == user_id,
                            HealthRecord.metric_id == metric.id
                        )
                    )
                    
                    if metric_template and metric_template.thryve_type == "Daily":
                        # For Daily type: only show daily data
                        historical_records_query = historical_records_query.filter(
                            or_(
                                HealthRecord.data_type == 'daily',
                                HealthRecord.data_type.is_(None)  # Backward compatibility
                            )
                        )
                    elif metric_template and metric_template.thryve_type == "Epoch":
                        # For Epoch type: show all epoch data (multiple values per date allowed)
                        historical_records_query = historical_records_query.filter(
                            or_(
                                HealthRecord.data_type == 'epoch',
                                HealthRecord.data_type.is_(None)  # Backward compatibility
                            )
                        )
                    # If thryve_type is None, show all data (no additional filter)
                    
                    historical_records = historical_records_query.order_by(
                        func.coalesce(HealthRecord.measure_start_time, HealthRecord.created_at).asc()
                    ).all()
                    
                    # Debug logging
                    
                    # Convert historical records to data points format
                    data_points = []
                    for record in historical_records:
                        # Use measure_start_time if available, otherwise created_at
                        timestamp = record.measure_start_time if record.measure_start_time else record.created_at
                        data_points.append({
                            "id": record.id,
                            "value": record.value,
                            "status": record.status,
                            "recorded_at": timestamp.isoformat() if timestamp else None,
                            "source": record.source
                        })
                    
                    
                    # Get thryve_type from metric template if available
                    thryve_type = None
                    if metric_template:
                        thryve_type = metric_template.thryve_type
                    
                    metric_data = {
                        "id": metric.id,
                        "name": metric.name,
                        "display_name": metric.display_name,
                        "description": metric.description,
                        "source_language": getattr(metric, 'source_language', 'en'),
                        "default_unit": metric.default_unit,
                        "reference_data": metric.reference_data,
                        "data_type": metric.data_type,
                        "is_default": metric.is_default,
                        "thryve_type": thryve_type,  # Add thryve_type from template
                        "total_records": metric_total_records,
                        "latest_value": latest_record.value if latest_record else None,
                        "latest_status": latest_record.status if latest_record else None,
                        "latest_recorded_at": (latest_record.measure_start_time if latest_record.measure_start_time else latest_record.created_at) if latest_record else None,
                        "data_points": data_points  # Add historical data points for trend analysis
                    }
                    
                    section_data["metrics"].append(metric_data)
                
                sections_with_metrics.append(section_data)
            
            return sections_with_metrics
            
        except Exception as e:
            logger.error(f"Failed to get sections with metrics for user {user_id}: {e}")
            return []
    
    def get_default_section_templates(self, db: Session, health_record_type_id: Optional[int] = None):
        """Get admin-created default section templates that users can choose from"""
        try:
            from app.models.health_metrics import HealthRecordSectionTemplate, HealthRecordMetricTemplate
            
            # Query admin default sections from the template table
            query = db.query(HealthRecordSectionTemplate).filter(
                HealthRecordSectionTemplate.is_default == True,
                HealthRecordSectionTemplate.is_active == True
            )
            
            # Filter by health record type if specified
            if health_record_type_id is not None:
                query = query.filter(HealthRecordSectionTemplate.health_record_type_id == health_record_type_id)
            
            sections = query.all()
            
            result = []
            for section in sections:
                # Get metrics for this section template
                metrics = db.query(HealthRecordMetricTemplate).filter(
                    HealthRecordMetricTemplate.section_template_id == section.id,
                    HealthRecordMetricTemplate.is_default == True,
                    HealthRecordMetricTemplate.is_active == True
                ).all()
                
                section_data = {
                    "id": section.id,
                    "name": section.name,
                    "display_name": section.display_name,
                    "description": section.description,
                    "source_language": getattr(section, 'source_language', 'en'),
                    "health_record_type_id": section.health_record_type_id,
                    "section_template_id": section.id,
                    "is_default": section.is_default,
                    "created_by": section.created_by,
                    "created_at": section.created_at.isoformat() if section.created_at else None,
                    "updated_at": section.updated_at.isoformat() if section.updated_at else None,
                    "updated_by": section.updated_by,
                    "metrics": [
                        {
                            "id": metric.id,
                            "name": metric.name,
                            "display_name": metric.display_name,
                            "description": metric.description,
                            "source_language": getattr(metric, 'source_language', 'en'),
                            "data_type": metric.data_type,
                            "default_unit": metric.default_unit,
                            "original_reference": metric.original_reference,
                            "reference_data": metric.reference_data,
                            "created_by": metric.created_by,
                            "created_at": metric.created_at.isoformat() if metric.created_at else None,
                            "updated_at": metric.updated_at.isoformat() if metric.updated_at else None,
                            "updated_by": metric.updated_by
                        }
                        for metric in metrics
                    ]
                }
                result.append(section_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get default section templates: {e}")
            return []
    
    def get_all_sections_with_user_data(
        self, 
        db: Session, 
        user_id: int,
        include_inactive: bool = False,
        health_record_type_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get ALL sections (both user-created and admin defaults) that have user's health records"""
        try:
            # First, find all sections that have health records for this user
            sections_with_data = db.query(HealthRecordSection).join(
                HealthRecord, HealthRecord.section_id == HealthRecordSection.id
            ).filter(
                and_(
                    HealthRecord.created_by == user_id,
                    HealthRecordSection.health_record_type_id == health_record_type_id
                )
            ).distinct().all()
            
            
            sections_with_metrics = []
            for section in sections_with_data:
                
                # Get metrics for this section - order by name to maintain consistent order
                metrics = db.query(HealthRecordMetric).filter(
                    HealthRecordMetric.section_id == section.id
                ).order_by(HealthRecordMetric.name.asc()).all()
                
                # Get section statistics
                total_records = db.query(func.count(HealthRecord.id)).filter(
                    and_(
                        HealthRecord.created_by == user_id,
                        HealthRecord.section_id == section.id
                    )
                ).scalar()
                
                # Get recent activity (last 7 days) - use measure_start_time if available, otherwise created_at
                seven_days_ago = datetime.utcnow() - timedelta(days=7)
                recent_activity = db.query(func.count(HealthRecord.id)).filter(
                    and_(
                        HealthRecord.created_by == user_id,
                        HealthRecord.section_id == section.id,
                        or_(
                            and_(
                                HealthRecord.measure_start_time.isnot(None),
                                HealthRecord.measure_start_time >= seven_days_ago
                            ),
                            and_(
                                HealthRecord.measure_start_time.is_(None),
                                HealthRecord.created_at >= seven_days_ago
                            )
                        )
                    )
                ).scalar()
                
                section_data = {
                    "id": section.id,
                    "name": section.name,
                    "display_name": section.display_name,
                    "description": section.description,
                    "health_record_type_id": section.health_record_type_id,
                    "section_template_id": section.section_template_id,
                    "is_default": section.is_default,
                    "total_records": total_records,
                    "recent_activity": recent_activity,
                    "metrics": []
                }
                
                # Add metrics data
                for metric in metrics:
                    # Get metric template to check thryve_type
                    from app.models.health_metrics import HealthRecordMetricTemplate
                    metric_template = None
                    if metric.metric_tmp_id:
                        metric_template = db.query(HealthRecordMetricTemplate).filter(
                            HealthRecordMetricTemplate.id == metric.metric_tmp_id
                        ).first()
                    
                    # Get metric statistics
                    metric_total_records = db.query(func.count(HealthRecord.id)).filter(
                        and_(
                            HealthRecord.created_by == user_id,
                            HealthRecord.metric_id == metric.id
                        )
                    ).scalar()
                    
                    # Build filter for latest record and historical records based on thryve_type
                    latest_record_filter = and_(
                        HealthRecord.created_by == user_id,
                        HealthRecord.metric_id == metric.id
                    )
                    historical_records_filter = and_(
                        HealthRecord.created_by == user_id,
                        HealthRecord.metric_id == metric.id
                    )
                    
                    # Apply thryve_type filtering
                    if metric_template and metric_template.thryve_type == "Daily":
                        # For Daily type: only show daily data
                        daily_filter = or_(
                            HealthRecord.data_type == 'daily',
                            HealthRecord.data_type.is_(None)  # Backward compatibility
                        )
                        latest_record_filter = and_(latest_record_filter, daily_filter)
                        historical_records_filter = and_(historical_records_filter, daily_filter)
                    elif metric_template and metric_template.thryve_type == "Epoch":
                        # For Epoch type: show all epoch data (multiple values per date allowed)
                        epoch_filter = or_(
                            HealthRecord.data_type == 'epoch',
                            HealthRecord.data_type.is_(None)  # Backward compatibility
                        )
                        latest_record_filter = and_(latest_record_filter, epoch_filter)
                        historical_records_filter = and_(historical_records_filter, epoch_filter)
                    # If thryve_type is None, show all data (no additional filter)
                    
                    # Get latest record for this metric - use measure_start_time if available, otherwise created_at
                    latest_record = db.query(HealthRecord).filter(
                        latest_record_filter
                    ).order_by(
                        desc(
                            func.coalesce(HealthRecord.measure_start_time, HealthRecord.created_at)
                        )
                    ).first()
                    
                    # Get all historical data points for trend analysis
                    historical_records = db.query(HealthRecord).filter(
                        historical_records_filter
                    ).order_by(
                        func.coalesce(HealthRecord.measure_start_time, HealthRecord.created_at).asc()
                    ).all()
                    
                    
                    # Convert historical records to data points format
                    data_points = []
                    for record in historical_records:
                        # Use measure_start_time if available, otherwise created_at
                        timestamp = record.measure_start_time if record.measure_start_time else record.created_at
                        data_points.append({
                            "id": record.id,
                            "value": record.value,
                            "status": record.status,
                            "recorded_at": timestamp.isoformat() if timestamp else None,
                            "source": record.source,
                            "notes": getattr(record, 'notes', None)  # Use getattr to safely access notes field
                        })
                    
                    # Get thryve_type from metric template if available
                    thryve_type = None
                    if metric_template:
                        thryve_type = metric_template.thryve_type
                    
                    metric_data = {
                        "id": metric.id,
                        "name": metric.name,
                        "display_name": metric.display_name,
                        "description": metric.description,
                        "source_language": getattr(metric, 'source_language', 'en'),
                        "data_type": metric.data_type,
                        "default_unit": metric.default_unit,
                        "unit": metric.default_unit,  # For compatibility
                        "reference_data": metric.reference_data,
                        "thryve_type": thryve_type,  # Add thryve_type from template
                        "total_records": metric_total_records,
                        "latest_value": latest_record.value if latest_record else None,
                        "latest_status": latest_record.status if latest_record else "unknown",
                        "latest_recorded_at": (latest_record.measure_start_time if latest_record.measure_start_time else latest_record.created_at).isoformat() if latest_record and (latest_record.measure_start_time or latest_record.created_at) else None,
                        "data_points": data_points,
                        "trend": "unknown"  # Could be calculated based on data points
                    }
                    
                    section_data["metrics"].append(metric_data)
                
                sections_with_metrics.append(section_data)
            
            return sections_with_metrics
            
        except Exception as e:
            logger.error(f"Failed to get all sections with user data for user {user_id}: {e}")
            return []
    
    def get_metric_details(self, db: Session, metric_id: int, user_id: int):
        """Get detailed information about a specific metric"""
        try:
            metric = db.query(HealthRecordMetric).filter(
                HealthRecordMetric.id == metric_id
            ).first()
            
            if not metric:
                return None
            
            # Get recent data points for this metric - use measure_start_time if available, otherwise created_at
            recent_records = db.query(HealthRecord).filter(
                HealthRecord.metric_id == metric_id,
                HealthRecord.created_by == user_id
            ).order_by(
                desc(
                    func.coalesce(HealthRecord.measure_start_time, HealthRecord.created_at)
                )
            ).limit(10).all()
            
            return {
                "id": metric.id,
                "name": metric.name,
                "display_name": metric.display_name,
                "description": metric.description,
                "source_language": getattr(metric, 'source_language', 'en'),
                "data_type": metric.data_type,
                "default_unit": metric.default_unit,
                "reference_data": metric.reference_data,
                "created_by": metric.created_by,
                "created_at": metric.created_at.isoformat() if metric.created_at else None,
                "updated_at": metric.updated_at.isoformat() if metric.updated_at else None,
                "updated_by": metric.updated_by,
                "recent_data": [
                    {
                        "id": record.id,
                        "value": record.value,
                        "status": record.status,
                        "recorded_at": (record.measure_start_time if record.measure_start_time else record.created_at).isoformat() if (record.measure_start_time or record.created_at) else None,
                        "source": record.source
                    }
                    for record in recent_records
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get metric details: {e}")
            return None

# ============================================================================
# HEALTH RECORD IMAGE CRUD
# ============================================================================

class HealthRecordDocExamCRUD:
    """CRUD operations for HealthRecordDocExam model"""
    
    def create_image(self, db: Session, image_data: dict, user_id: int) -> HealthRecordDocExam:
        """Create a new health record image"""
        db_image = HealthRecordDocExam(
            created_by=user_id,
            **image_data
        )
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        return db_image
    
    def get_image_by_id(self, db: Session, image_id: int, user_id: int) -> Optional[HealthRecordDocExam]:
        """Get a specific image by ID for a user"""
        return db.query(HealthRecordDocExam).filter(
            HealthRecordDocExam.id == image_id,
            HealthRecordDocExam.created_by == user_id
        ).first()
    
    def get_user_images(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100,
        image_type: Optional[str] = None,
        body_part: Optional[str] = None,
        findings: Optional[str] = None
    ) -> List[HealthRecordDocExam]:
        """Get paginated images for a user with optional filters"""
        query = db.query(HealthRecordDocExam).filter(HealthRecordDocExam.created_by == user_id)
        
        # Apply filters
        if image_type:
            query = query.filter(HealthRecordDocExam.image_type == image_type)
        if body_part:
            query = query.filter(HealthRecordDocExam.body_part.ilike(f"%{body_part}%"))
        if findings:
            query = query.filter(HealthRecordDocExam.findings == findings)
        
        # Order by most recent first
        query = query.order_by(HealthRecordDocExam.image_date.desc())
        
        return query.offset(skip).limit(limit).all()
    
    def update_image(
        self, 
        db: Session, 
        image_id: int, 
        user_id: int, 
        update_data: dict
    ) -> Optional[HealthRecordDocExam]:
        """Update an existing image"""
        db_image = self.get_image_by_id(db, image_id, user_id)
        if not db_image:
            return None
        
        for field, value in update_data.items():
            if hasattr(db_image, field):
                setattr(db_image, field, value)
        
        db_image.updated_by = user_id
        db.commit()
        db.refresh(db_image)
        return db_image
    
    def delete_image(self, db: Session, image_id: int, user_id: int) -> bool:
        """Delete an image"""
        db_image = self.get_image_by_id(db, image_id, user_id)
        if not db_image:
            return False
        
        db.delete(db_image)
        db.commit()
        return True
    
    def get_images_by_type(self, db: Session, user_id: int, image_type: str) -> List[HealthRecordDocExam]:
        """Get all images of a specific type for a user"""
        return db.query(HealthRecordDocExam).filter(
            HealthRecordDocExam.created_by == user_id,
            HealthRecordDocExam.image_type == image_type
        ).order_by(HealthRecordDocExam.image_date.desc()).all()
    
    def get_images_by_body_part(self, db: Session, user_id: int, body_part: str) -> List[HealthRecordDocExam]:
        """Get all images for a specific body part for a user"""
        return db.query(HealthRecordDocExam).filter(
            HealthRecordDocExam.created_by == user_id,
            HealthRecordDocExam.body_part.ilike(f"%{body_part}%")
        ).order_by(HealthRecordDocExam.image_date.desc()).all()
    
    def get_recent_images(self, db: Session, user_id: int, limit: int = 10) -> List[HealthRecordDocExam]:
        """Get recent images for a user"""
        return db.query(HealthRecordDocExam).filter(
            HealthRecordDocExam.created_by == user_id
        ).order_by(HealthRecordDocExam.created_at.desc()).limit(limit).all()
    
    def check_duplicate_file(
        self,
        db: Session,
        user_id: int,
        filename: str,
        file_size: int
    ) -> Optional[HealthRecordDocExam]:
        """Check for duplicate medical image by filename AND file size (both must match)"""
        try:
            if file_size > 0:
                duplicate = db.query(HealthRecordDocExam).filter(
                    and_(
                        HealthRecordDocExam.created_by == user_id,
                        HealthRecordDocExam.original_filename == filename,
                        HealthRecordDocExam.file_size_bytes == file_size
                    )
                ).first()
                
                if duplicate:
                    return duplicate
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking for duplicate medical image: {e}")
            return None
    
    def get_image_statistics(self, db: Session, user_id: int) -> dict:
        """Get statistics about user's images"""
        total_images = db.query(HealthRecordDocExam).filter(
            HealthRecordDocExam.created_by == user_id
        ).count()
        
        # Count by image type
        type_counts = db.query(
            HealthRecordDocExam.image_type,
            func.count(HealthRecordDocExam.id)
        ).filter(
            HealthRecordDocExam.created_by == user_id
        ).group_by(HealthRecordDocExam.image_type).all()
        
        # Count by findings
        findings_counts = db.query(
            HealthRecordDocExam.findings,
            func.count(HealthRecordDocExam.id)
        ).filter(
            HealthRecordDocExam.created_by == user_id
        ).group_by(HealthRecordDocExam.findings).all()
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_images = db.query(HealthRecordDocExam).filter(
            HealthRecordDocExam.created_by == user_id,
            HealthRecordDocExam.created_at >= thirty_days_ago
        ).count()
        
        return {
            "total_images": total_images,
            "type_distribution": dict(type_counts),
            "findings_distribution": dict(findings_counts),
            "recent_activity": recent_images
        }

# Global instances for CRUD operations
health_record_crud = HealthRecordCRUD()
medical_condition_crud = MedicalConditionCRUD()
family_medical_history_crud = FamilyMedicalHistoryCRUD()
health_record_doc_lab_crud = HealthRecordDocLabCRUD()
health_record_type_crud = HealthRecordTypeCRUD()
health_record_section_crud = HealthRecordSectionCRUD()
health_record_metric_crud = HealthRecordMetricCRUD()
health_record_section_metric_crud = HealthRecordSectionMetricCRUD()
health_record_doc_exam_crud = HealthRecordDocExamCRUD()

# ============================================================================
# TEMPORARY TABLE CRUD OPERATIONS
# ============================================================================

class HealthRecordSectionTemplateCRUD:
    """CRUD operations for HealthRecordSectionTemplate model"""
    
    def create(self, db: Session, section_data: Dict[str, Any]) -> HealthRecordSectionTemplate:
        """Create a new section template definition"""
        try:
            # Get creator's language preference for source_language if not provided
            if 'source_language' not in section_data:
                # Note: In sync context, default to 'en' for source_language
                # This is acceptable as source_language is mainly for tracking original language
                section_data['source_language'] = 'en'
            
            db_section = HealthRecordSectionTemplate(**section_data)
            db.add(db_section)
            db.commit()
            db.refresh(db_section)
            logger.info(f"Created section template {db_section.id}: {db_section.display_name}")
            return db_section
        except Exception as e:
            logger.error(f"Failed to create section template: {e}")
            db.rollback()
            raise
    
    def get_by_name_and_type(self, db: Session, name: str, health_record_type_id: int) -> Optional[HealthRecordSectionTemplate]:
        """Get section template by name and type"""
        return db.query(HealthRecordSectionTemplate).filter(
            HealthRecordSectionTemplate.name == name,
            HealthRecordSectionTemplate.health_record_type_id == health_record_type_id
        ).first()
    
    def get_all_by_type(self, db: Session, health_record_type_id: int) -> List[HealthRecordSectionTemplate]:
        """Get all section templates by type"""
        return db.query(HealthRecordSectionTemplate).filter(
            HealthRecordSectionTemplate.health_record_type_id == health_record_type_id
        ).all()
    
    def get_admin_sections(self, db: Session, health_record_type_id: int) -> List[HealthRecordSectionTemplate]:
        """Get admin pre-defined sections"""
        return db.query(HealthRecordSectionTemplate).filter(
            HealthRecordSectionTemplate.health_record_type_id == health_record_type_id,
            HealthRecordSectionTemplate.is_active == True,
            HealthRecordSectionTemplate.is_default == True
        ).all()
    
    def get_user_sections(self, db: Session, health_record_type_id: int, user_id: int) -> List[HealthRecordSectionTemplate]:
        """Get user custom sections"""
        return db.query(HealthRecordSectionTemplate).filter(
            HealthRecordSectionTemplate.health_record_type_id == health_record_type_id,
            HealthRecordSectionTemplate.is_active == True,
            HealthRecordSectionTemplate.is_default == False,
            HealthRecordSectionTemplate.created_by == user_id
        ).all()

class HealthRecordMetricTemplateCRUD:
    """CRUD operations for HealthRecordMetricTemplate model"""
    
    def create(self, db: Session, metric_data: Dict[str, Any]) -> HealthRecordMetricTemplate:
        """Create a new metric template definition"""
        try:
            # Get creator's language preference for source_language if not provided
            if 'source_language' not in metric_data:
                # Note: In sync context, default to 'en' for source_language
                # This is acceptable as source_language is mainly for tracking original language
                metric_data['source_language'] = 'en'
            
            db_metric = HealthRecordMetricTemplate(**metric_data)
            db.add(db_metric)
            db.commit()
            db.refresh(db_metric)
            logger.info(f"Created metric template {db_metric.id}: {db_metric.display_name}")
            return db_metric
        except Exception as e:
            logger.error(f"Failed to create metric template: {e}")
            db.rollback()
            raise
    
    def get_by_section_and_name(self, db: Session, section_id: int, name: str) -> Optional[HealthRecordMetricTemplate]:
        """Get metric template by section and name"""
        return db.query(HealthRecordMetricTemplate).filter(
            HealthRecordMetricTemplate.section_template_id == section_id,
            HealthRecordMetricTemplate.name == name
        ).first()
    
    def get_by_section(self, db: Session, section_id: int) -> List[HealthRecordMetricTemplate]:
        """Get all metric templates by section"""
        return db.query(HealthRecordMetricTemplate).filter(
            HealthRecordMetricTemplate.section_template_id == section_id
        ).all()
    
    def get_admin_metrics(self, db: Session, section_id: int) -> List[HealthRecordMetricTemplate]:
        """Get admin pre-defined metrics for a section"""
        return db.query(HealthRecordMetricTemplate).filter(
            HealthRecordMetricTemplate.section_template_id == section_id,
            HealthRecordMetricTemplate.is_active == True,
            HealthRecordMetricTemplate.is_default == True
        ).all()
    
    def get_user_metrics(self, db: Session, section_id: int, user_id: int) -> List[HealthRecordMetricTemplate]:
        """Get user custom metrics for a section"""
        return db.query(HealthRecordMetricTemplate).filter(
            HealthRecordMetricTemplate.section_template_id == section_id,
            HealthRecordMetricTemplate.is_active == True,
            HealthRecordMetricTemplate.is_default == False,
            HealthRecordMetricTemplate.created_by == user_id
        ).all()

# Initialize CRUD instances
health_record_section_template_crud = HealthRecordSectionTemplateCRUD()
health_record_metric_template_crud = HealthRecordMetricTemplateCRUD()
