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
    
    def create(self, db: Session, health_record: HealthRecordCreate, user_id: int) -> tuple[HealthRecord, bool]:
        """Create a new health record with duplicate detection. Returns (record, was_created_new)"""
        try:
            # Check for duplicate values on the same date/hour
            duplicate_record = self._check_duplicate_record(
                db, user_id, health_record.metric_id, health_record.recorded_at
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
                duplicate_record.updated_at = func.now()
                
                db.commit()
                db.refresh(duplicate_record)
                
                logger.info(f"Updated duplicate health record {duplicate_record.id} for user {user_id}")
                return duplicate_record, False  # False = was not created new, was updated
            
            # Create new record if no duplicate found
            db_health_record = HealthRecord(
                created_by=user_id,
                section_id=health_record.section_id,
                metric_id=health_record.metric_id,
                value=health_record.value,
                status=health_record.status,
                source=health_record.source,
                recorded_at=health_record.recorded_at,
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
        recorded_at: datetime
    ) -> Optional[HealthRecord]:
        """Check for duplicate records on the same date/hour"""
        try:
            # Round recorded_at to the nearest hour for comparison
            recorded_hour = recorded_at.replace(minute=0, second=0, microsecond=0)
            next_hour = recorded_hour + timedelta(hours=1)
            
            return db.query(HealthRecord).filter(
                and_(
                    HealthRecord.created_by == user_id,
                    HealthRecord.metric_id == metric_id,
                    HealthRecord.recorded_at >= recorded_hour,
                    HealthRecord.recorded_at < next_hour
                )
            ).first()
            
        except Exception as e:
            logger.error(f"Failed to check for duplicate record: {e}")
            return None
    
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
                    query = query.filter(HealthRecord.recorded_at >= filters.start_date)
                if filters.end_date:
                    query = query.filter(HealthRecord.recorded_at <= filters.end_date)
            
            return query.order_by(desc(HealthRecord.recorded_at)).offset(skip).limit(limit).all()
            
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
                    base_query = base_query.filter(HealthRecord.recorded_at >= filters.start_date)
                if filters.end_date:
                    base_query = base_query.filter(HealthRecord.recorded_at <= filters.end_date)
            
            return base_query.order_by(desc(HealthRecord.recorded_at)).offset(offset).limit(limit).all()
            
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
            
            # Recent records (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_records = db.query(func.count(HealthRecord.id)).filter(
                and_(
                    HealthRecord.created_by == user_id,
                    HealthRecord.recorded_at >= thirty_days_ago
                )
            ).scalar()
            
            # Average records per day
            first_record = db.query(HealthRecord.recorded_at).filter(
                HealthRecord.created_by == user_id
            ).order_by(HealthRecord.recorded_at.asc()).first()
            
            if first_record and first_record[0]:
                days_since_first = (datetime.utcnow() - first_record[0]).days
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
    
    def create(self, db: Session, condition: MedicalConditionCreate, user_id: int) -> MedicalCondition:
        """Create a new medical condition"""
        try:
            db_condition = MedicalCondition(
                condition_name=condition.condition_name,
                description=condition.description,
                diagnosed_date=condition.diagnosed_date,
                status=condition.status,
                severity=condition.severity,
                source=condition.source,
                treatment_plan=condition.treatment_plan,
                current_medications=condition.current_medications,
                outcome=condition.outcome,
                resolved_date=condition.resolved_date,
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
    
    def update(
        self, 
        db: Session, 
        condition_id: int, 
        condition_update: MedicalConditionUpdate, 
        user_id: int
    ) -> Optional[MedicalCondition]:
        """Update a medical condition"""
        try:
            db_condition = self.get_by_id(db, condition_id, user_id)
            if not db_condition:
                return None
            
            update_data = condition_update.dict(exclude_unset=True)
            update_data['updated_by'] = user_id
            
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
    
    def create(self, db: Session, history: FamilyMedicalHistoryCreate, user_id: int) -> FamilyMedicalHistory:
        """Create a new family medical history record"""
        try:
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
                outcome=history.outcome,
                status=history.status,
                source=history.source,
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
    
    def update(
        self, 
        db: Session, 
        history_id: int, 
        history_update: FamilyMedicalHistoryUpdate, 
        user_id: int
    ) -> Optional[FamilyMedicalHistory]:
        """Update a family medical history record"""
        try:
            db_history = self.get_by_id(db, history_id, user_id)
            if not db_history:
                return None
            
            update_data = history_update.dict(exclude_unset=True)
            
            # Handle chronic_diseases conversion
            if 'chronic_diseases' in update_data and update_data['chronic_diseases'] is not None:
                update_data['chronic_diseases'] = [
                    disease.dict() if hasattr(disease, 'dict') else disease 
                    for disease in update_data['chronic_diseases']
                ]
            
            update_data['updated_by'] = user_id
            
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
            db_section = HealthRecordSection(
                name=section_data.name,
                display_name=section_data.display_name,
                description=section_data.description,
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
            metrics = db.query(HealthRecordMetric).filter(
                HealthRecordMetric.section_id == section_id
            ).order_by(HealthRecordMetric.name.asc()).all()
            
            total_deleted_records = 0
            
            # For each metric, delete all associated health records
            for metric in metrics:
                health_records = db.query(HealthRecord).filter(
                    HealthRecord.metric_id == metric.id
                ).all()
                
                for record in health_records:
                    db.delete(record)
                    total_deleted_records += 1
                    logger.info(f"Deleted health record {record.id} associated with metric {metric.id}")
                
                # Delete the metric itself
                db.delete(metric)
                logger.info(f"Deleted metric {metric.id} from section {section_id}")
            
            # Handle template cleanup based on section type
            if db_section.section_template_id:
                from app.models.health_metrics import HealthRecordMetricTemplate, HealthRecordSectionTemplate
                
                if is_user_created:
                    # For user-created sections: delete from both normal and template tables
                    logger.info(f"Deleting user-created section {section_id} from both normal and template tables")
                    
                    # Delete user-created metric templates
                    user_metric_templates = db.query(HealthRecordMetricTemplate).filter(
                        and_(
                            HealthRecordMetricTemplate.section_template_id == db_section.section_template_id,
                            HealthRecordMetricTemplate.created_by == user_id,
                            HealthRecordMetricTemplate.is_default == False  # User-created templates
                        )
                    ).all()
                    
                    for metric_template in user_metric_templates:
                        db.delete(metric_template)
                        logger.info(f"Deleted user-created metric template {metric_template.id}")
                    
                    # Delete user-created section template
                    section_template = db.query(HealthRecordSectionTemplate).filter(
                        and_(
                            HealthRecordSectionTemplate.id == db_section.section_template_id,
                            HealthRecordSectionTemplate.created_by == user_id,
                            HealthRecordSectionTemplate.is_default == False  # User-created template
                        )
                    ).first()
                    
                    if section_template:
                        db.delete(section_template)
                        logger.info(f"Deleted user-created section template {section_template.id}")
                else:
                    # For admin template sections: delete from normal table only
                    logger.info(f"Deleting admin template section {section_id} from normal table only")
            
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
            db_metric = HealthRecordMetric(
                section_id=metric_data.section_id,
                metric_tmp_id=metric_data.metric_tmp_id,
                name=metric_data.name,
                display_name=metric_data.display_name,
                description=metric_data.description,
                default_unit=metric_data.default_unit,
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
                
                # Get recent activity (last 7 days)
                seven_days_ago = datetime.utcnow() - timedelta(days=7)
                recent_activity = db.query(func.count(HealthRecord.id)).filter(
                    and_(
                        HealthRecord.created_by == user_id,
                        HealthRecord.section_id == section.id,
                        HealthRecord.recorded_at >= seven_days_ago
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
                    # Get metric statistics
                    metric_total_records = db.query(func.count(HealthRecord.id)).filter(
                        and_(
                            HealthRecord.created_by == user_id,
                            HealthRecord.metric_id == metric.id
                        )
                    ).scalar()
                    
                    # Get latest record for this metric
                    latest_record = db.query(HealthRecord).filter(
                        and_(
                            HealthRecord.created_by == user_id,
                            HealthRecord.metric_id == metric.id
                        )
                    ).order_by(HealthRecord.recorded_at.desc()).first()
                    
                    # Get all historical data points for trend analysis
                    historical_records = db.query(HealthRecord).filter(
                        and_(
                            HealthRecord.created_by == user_id,
                            HealthRecord.metric_id == metric.id
                        )
                    ).order_by(HealthRecord.recorded_at.asc()).all()
                    
                    # Debug logging
                    
                    # Convert historical records to data points format
                    data_points = []
                    for record in historical_records:
                        data_points.append({
                            "id": record.id,
                            "value": record.value,
                            "status": record.status,
                            "recorded_at": record.recorded_at.isoformat() if record.recorded_at else None,
                            "source": record.source
                        })
                    
                    
                    metric_data = {
                        "id": metric.id,
                        "name": metric.name,
                        "display_name": metric.display_name,
                        "description": metric.description,
                        "default_unit": metric.default_unit,
                        "reference_data": metric.reference_data,
                        "data_type": metric.data_type,
                        "is_default": metric.is_default,
                        "total_records": metric_total_records,
                        "latest_value": latest_record.value if latest_record else None,
                        "latest_status": latest_record.status if latest_record else None,
                        "latest_recorded_at": latest_record.recorded_at if latest_record else None,
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
                
                # Get recent activity (last 7 days)
                seven_days_ago = datetime.utcnow() - timedelta(days=7)
                recent_activity = db.query(func.count(HealthRecord.id)).filter(
                    and_(
                        HealthRecord.created_by == user_id,
                        HealthRecord.section_id == section.id,
                        HealthRecord.recorded_at >= seven_days_ago
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
                    # Get metric statistics
                    metric_total_records = db.query(func.count(HealthRecord.id)).filter(
                        and_(
                            HealthRecord.created_by == user_id,
                            HealthRecord.metric_id == metric.id
                        )
                    ).scalar()
                    
                    # Get latest record for this metric
                    latest_record = db.query(HealthRecord).filter(
                        and_(
                            HealthRecord.created_by == user_id,
                            HealthRecord.metric_id == metric.id
                        )
                    ).order_by(HealthRecord.recorded_at.desc()).first()
                    
                    # Get all historical data points for trend analysis
                    historical_records = db.query(HealthRecord).filter(
                        and_(
                            HealthRecord.created_by == user_id,
                            HealthRecord.metric_id == metric.id
                        )
                    ).order_by(HealthRecord.recorded_at.asc()).all()
                    
                    
                    # Convert historical records to data points format
                    data_points = []
                    for record in historical_records:
                        data_points.append({
                            "id": record.id,
                            "value": record.value,
                            "status": record.status,
                            "recorded_at": record.recorded_at.isoformat() if record.recorded_at else None,
                            "source": record.source,
                            "notes": getattr(record, 'notes', None)  # Use getattr to safely access notes field
                        })
                    
                    metric_data = {
                        "id": metric.id,
                        "name": metric.name,
                        "display_name": metric.display_name,
                        "description": metric.description,
                        "data_type": metric.data_type,
                        "default_unit": metric.default_unit,
                        "unit": metric.default_unit,  # For compatibility
                        "reference_data": metric.reference_data,
                        "total_records": metric_total_records,
                        "latest_value": latest_record.value if latest_record else None,
                        "latest_status": latest_record.status if latest_record else "unknown",
                        "latest_recorded_at": latest_record.recorded_at.isoformat() if latest_record and latest_record.recorded_at else None,
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
            
            # Get recent data points for this metric
            recent_records = db.query(HealthRecord).filter(
                HealthRecord.metric_id == metric_id,
                HealthRecord.created_by == user_id
            ).order_by(HealthRecord.recorded_at.desc()).limit(10).all()
            
            return {
                "id": metric.id,
                "name": metric.name,
                "display_name": metric.display_name,
                "description": metric.description,
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
                        "recorded_at": record.recorded_at.isoformat() if record.recorded_at else None,
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
