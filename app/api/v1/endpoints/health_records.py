from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, Form, File
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict, Any
from app.core.database import get_db
from app.crud.health_record import (
    health_record_crud, medical_condition_crud, 
    family_medical_history_crud, health_record_doc_lab_crud,
    health_record_section_metric_crud, health_record_metric_crud, health_record_doc_exam_crud,
    health_record_section_crud, HealthRecordTypeCRUD
)
from app.crud.surgery_hospitalization import surgery_hospitalization_crud
from app.models.user import User
from app.models.health_record import HealthRecordSection, HealthRecordDocLab, HealthRecordDocExam
from app.schemas.health_record import (
    HealthRecordCreate, HealthRecordUpdate, HealthRecordResponse, HealthRecordWithDetails,
    MedicalConditionCreate, MedicalConditionUpdate, MedicalConditionResponse,
    FamilyMedicalHistoryCreate, FamilyMedicalHistoryUpdate, FamilyMedicalHistoryResponse,
    HealthRecordDocLabCreate, HealthRecordDocLabUpdate, HealthRecordDocLabResponse,
    HealthRecordFilter, HealthRecordSearch, HealthRecordStats,
    BulkHealthRecordCreate, BulkHealthRecordResponse,
    HealthRecordDocExamCreate, HealthRecordDocExamUpdate, 
    HealthRecordDocExamResponse, HealthRecordDocExamSummary, PaginatedImageResponse,
    PaginationInfo, ImageType, ImageFindings,
    HealthRecordMetricCreate, HealthRecordMetricUpdate, HealthRecordSectionUpdate,
    HealthRecordTypeCreate, HealthRecordTypeUpdate, HealthRecordTypeResponse
)
from app.schemas.surgery_hospitalization import (
    SurgeryHospitalizationCreate, SurgeryHospitalizationUpdate, 
    SurgeryHospitalizationResponse, SurgeryHospitalizationListResponse
)
from app.api.v1.endpoints.auth import get_current_user
from datetime import datetime
import logging
import uuid
from app.core.aws_service import aws_service


logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================================================
# HEALTH RECORDS ENDPOINTS
# ============================================================================

@router.post("/", response_model=HealthRecordResponse)
async def create_health_record(
    health_record: HealthRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new health record with duplicate detection"""
    try:
        db_health_record, was_created = health_record_crud.create(db, health_record, current_user.id)
        
        return HealthRecordResponse(
            id=db_health_record.id,
            section_id=db_health_record.section_id,
            metric_id=db_health_record.metric_id,
            value=db_health_record.value,
            status=db_health_record.status,
            source=db_health_record.source,
            recorded_at=db_health_record.recorded_at,
            device_id=db_health_record.device_id,
            device_info=db_health_record.device_info,
            accuracy=db_health_record.accuracy,
            location_data=db_health_record.location_data,
            created_by=db_health_record.created_by,
            created_at=db_health_record.created_at,
            updated_at=db_health_record.updated_at,
            updated_by=db_health_record.updated_by
        )
        
    except Exception as e:
        logger.error(f"Failed to create health record: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create health record: {str(e)}"
        )

@router.post("/check-duplicate")
async def check_duplicate_health_record(
    metric_id: int,
    recorded_at: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check for duplicate health records on the same date/hour"""
    try:
        from datetime import datetime
        recorded_datetime = datetime.fromisoformat(recorded_at.replace('Z', '+00:00'))
        
        duplicate_record = health_record_crud._check_duplicate_record(
            db, current_user.id, metric_id, recorded_datetime
        )
        
        if duplicate_record:
            return {
                "duplicate_found": True,
                "existing_record": {
                    "id": duplicate_record.id,
                    "value": duplicate_record.value,
                    "recorded_at": duplicate_record.recorded_at.isoformat(),
                    "status": duplicate_record.status
                },
                "message": f"A value already exists for this metric on {recorded_datetime.strftime('%Y-%m-%d at %H:00')}"
            }
        
        return {
            "duplicate_found": False,
            "message": "No duplicate found"
        }
        
    except Exception as e:
        logger.error(f"Failed to check for duplicate health record: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check for duplicate: {str(e)}"
        )

@router.post("/bulk", response_model=BulkHealthRecordResponse)
async def create_bulk_health_records(
    bulk_data: BulkHealthRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create multiple health records at once"""
    try:
        created_records = []
        failed_records = []
        
        for record in bulk_data.records:
            try:
                db_record, was_created = health_record_crud.create(db, record, current_user.id)
                created_records.append(HealthRecordResponse(
                    id=db_record.id,
                    section_id=db_record.section_id,
                    metric_id=db_record.metric_id,
                    value=db_record.value,
                    status=db_record.status,
                    source=db_record.source,
                    recorded_at=db_record.recorded_at,
                    device_id=db_record.device_id,
                    device_info=db_record.device_info,
                    accuracy=db_record.accuracy,
                    location_data=db_record.location_data,
                    created_by=db_record.created_by,
                    created_at=db_record.created_at,
                    updated_at=db_record.updated_at,
                    updated_by=db_record.updated_by
                ))
            except Exception as e:
                failed_records.append({
                    "record": record.dict(),
                    "error": str(e)
                })
        
        return BulkHealthRecordResponse(
            created_count=len(created_records),
            failed_count=len(failed_records),
            created_records=created_records,
            failed_records=failed_records
        )
        
    except Exception as e:
        logger.error(f"Failed to create bulk health records: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bulk health records: {str(e)}"
        )

@router.get("/", response_model=List[HealthRecordResponse])
async def read_health_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    section_id: Optional[int] = Query(None),
    metric_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    device_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get health records for the current user with optional filtering"""
    try:
        filters = HealthRecordFilter(
            section_id=section_id,
            metric_id=metric_id,
            status=status,
            source=source,
            device_id=device_id,
            start_date=start_date,
            end_date=end_date
        )
        
        records = health_record_crud.get_by_user(db, current_user.id, skip, limit, filters)
        
        return [
            HealthRecordResponse(
                id=record.id,
                section_id=record.section_id,
                metric_id=record.metric_id,
                value=record.value,
                status=record.status,
                source=record.source,
                recorded_at=record.recorded_at,
                device_id=record.device_id,
                device_info=record.device_info,
                accuracy=record.accuracy,
                location_data=record.location_data,
                created_by=record.created_by,
                created_at=record.created_at,
                updated_at=record.updated_at,
                updated_by=record.updated_by
            )
            for record in records
        ]
        
    except Exception as e:
        logger.error(f"Failed to retrieve health records: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve health records: {str(e)}"
        )

@router.get("/search", response_model=List[HealthRecordResponse])
async def search_health_records(
    query: str = Query(..., description="Search query"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    section_id: Optional[int] = Query(None),
    metric_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search health records by text query"""
    try:
        filters = HealthRecordFilter(
            section_id=section_id,
            metric_id=metric_id,
            status=status,
            source=source,
            start_date=start_date,
            end_date=end_date
        )
        
        records = health_record_crud.search_records(
            db, current_user.id, query, filters, limit, offset
        )
        
        return [
            HealthRecordResponse(
                id=record.id,
                section_id=record.section_id,
                metric_id=record.metric_id,
                value=record.value,
                status=record.status,
                source=record.source,
                recorded_at=record.recorded_at,
                device_id=record.device_id,
                device_info=record.device_info,
                accuracy=record.accuracy,
                location_data=record.location_data,
                created_by=record.created_by,
                created_at=record.created_at,
                updated_at=record.updated_at,
                updated_by=record.updated_by
            )
            for record in records
        ]
        
    except Exception as e:
        logger.error(f"Failed to search health records: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search health records: {str(e)}"
        )

@router.get("/stats", response_model=HealthRecordStats)
async def get_health_record_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get health record statistics for the current user"""
    try:
        stats = health_record_crud.get_stats(db, current_user.id)
        return HealthRecordStats(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get health record stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get health record stats: {str(e)}"
        )

# ============================================================================
# MEDICAL CONDITIONS ENDPOINTS (must come before /{record_id} route)
# ============================================================================

@router.post("/conditions", response_model=MedicalConditionResponse)
async def create_medical_condition(
    condition: MedicalConditionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new medical condition"""
    try:
        db_condition = medical_condition_crud.create(db, condition, current_user.id)
        
        return MedicalConditionResponse(
            id=db_condition.id,
            condition_name=db_condition.condition_name,
            description=db_condition.description,
            diagnosed_date=db_condition.diagnosed_date,
            status=db_condition.status,
            severity=db_condition.severity,
            source=db_condition.source,
            treatment_plan=db_condition.treatment_plan,
            current_medications=db_condition.current_medications if isinstance(db_condition.current_medications, list) else None,
            outcome=db_condition.outcome,
            resolved_date=db_condition.resolved_date,
            created_by=db_condition.created_by,
            created_at=db_condition.created_at,
            updated_at=db_condition.updated_at,
            updated_by=db_condition.updated_by
        )
        
    except Exception as e:
        logger.error(f"Failed to create medical condition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create medical condition: {str(e)}"
        )

@router.get("/conditions", response_model=List[MedicalConditionResponse])
async def read_medical_conditions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all medical conditions for the current user"""
    try:
        conditions = medical_condition_crud.get_by_user(db, current_user.id, skip=skip, limit=limit)
        
        return [
            MedicalConditionResponse(
                id=condition.id,
                condition_name=condition.condition_name,
                description=condition.description,
                diagnosed_date=condition.diagnosed_date,
                status=condition.status,
                severity=condition.severity,
                source=condition.source,
                treatment_plan=condition.treatment_plan,
                current_medications=condition.current_medications if isinstance(condition.current_medications, list) else None,
                outcome=condition.outcome,
                resolved_date=condition.resolved_date,
                created_by=condition.created_by,
                created_at=condition.created_at,
                updated_at=condition.updated_at,
                updated_by=condition.updated_by
            )
            for condition in conditions
        ]
        
    except Exception as e:
        logger.error(f"Failed to get medical conditions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get medical conditions: {str(e)}"
        )

@router.get("/conditions/{condition_id}", response_model=MedicalConditionResponse)
async def read_medical_condition(
    condition_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific medical condition by ID"""
    try:
        condition = medical_condition_crud.get_by_id(db, condition_id, current_user.id)
        
        if not condition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical condition not found"
            )
        
        return MedicalConditionResponse(
            id=condition.id,
            condition_name=condition.condition_name,
            description=condition.description,
            diagnosed_date=condition.diagnosed_date,
            status=condition.status,
            severity=condition.severity,
            source=condition.source,
            treatment_plan=condition.treatment_plan,
            current_medications=condition.current_medications if isinstance(condition.current_medications, list) else None,
            outcome=condition.outcome,
            resolved_date=condition.resolved_date,
            created_by=condition.created_by,
            created_at=condition.created_at,
            updated_at=condition.updated_at,
            updated_by=condition.updated_by
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get medical condition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get medical condition: {str(e)}"
        )

@router.put("/conditions/{condition_id}", response_model=MedicalConditionResponse)
async def update_medical_condition(
    condition_id: int,
    condition_update: MedicalConditionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a medical condition"""
    try:
        existing_condition = medical_condition_crud.get_by_id(db, condition_id, current_user.id)
        
        if not existing_condition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical condition not found"
            )
        
        db_condition = medical_condition_crud.update(db, condition_id, condition_update, current_user.id)
        
        return MedicalConditionResponse(
            id=db_condition.id,
            condition_name=db_condition.condition_name,
            description=db_condition.description,
            diagnosed_date=db_condition.diagnosed_date,
            status=db_condition.status,
            severity=db_condition.severity,
            source=db_condition.source,
            treatment_plan=db_condition.treatment_plan,
            current_medications=db_condition.current_medications if isinstance(db_condition.current_medications, list) else None,
            outcome=db_condition.outcome,
            resolved_date=db_condition.resolved_date,
            created_by=db_condition.created_by,
            created_at=db_condition.created_at,
            updated_at=db_condition.updated_at,
            updated_by=db_condition.updated_by
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update medical condition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update medical condition: {str(e)}"
        )

@router.delete("/conditions/{condition_id}")
async def delete_medical_condition(
    condition_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a medical condition"""
    try:
        existing_condition = medical_condition_crud.get_by_id(db, condition_id, current_user.id)
        
        if not existing_condition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical condition not found"
            )
        
        medical_condition_crud.delete(db, condition_id, current_user.id)
        return {"message": "Medical condition deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete medical condition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete medical condition: {str(e)}"
        )

# ============================================================================
# FAMILY MEDICAL HISTORY ENDPOINTS (must come before /{record_id} route)
# ============================================================================





# ============================================================================
# FAMILY MEDICAL HISTORY ENDPOINTS (must come before /{record_id} route)
# ============================================================================

@router.post("/family-history", response_model=FamilyMedicalHistoryResponse)
async def create_family_medical_history(
    history: FamilyMedicalHistoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new family medical history record"""
    try:
        db_history = family_medical_history_crud.create(db, history, current_user.id)
        
        return FamilyMedicalHistoryResponse(
            id=db_history.id,
            condition_name=db_history.condition_name,
            relation=db_history.relation,
            age_of_onset=db_history.age_of_onset,
            description=db_history.description,
            outcome=db_history.outcome,
            status=db_history.status,
            source=db_history.source,
            created_by=db_history.created_by,
            created_at=db_history.created_at,
            updated_at=db_history.updated_at,
            updated_by=db_history.updated_by
        )
        
    except Exception as e:
        logger.error(f"Failed to create family medical history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create family medical history: {str(e)}"
        )

@router.get("/family-history", response_model=List[FamilyMedicalHistoryResponse])
async def read_family_medical_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get family medical history for the current user"""
    try:
        history_records = family_medical_history_crud.get_by_user(db, current_user.id, skip, limit)
        
        return [
            FamilyMedicalHistoryResponse(
                id=history.id,
                condition_name=history.condition_name,
                relation=history.relation,
                age_of_onset=history.age_of_onset,
                description=history.description,
                outcome=history.outcome,
                status=history.status,
                source=history.source,
                created_by=history.created_by,
                created_at=history.created_at,
                updated_at=history.updated_at,
                updated_by=history.updated_by
            )
            for history in history_records
        ]
        
    except Exception as e:
        logger.error(f"Failed to get family medical history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get family medical history: {str(e)}"
        )

@router.get("/family-history/{history_id}", response_model=FamilyMedicalHistoryResponse)
async def read_family_medical_history_by_id(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific family medical history record by ID"""
    try:
        history = family_medical_history_crud.get_by_id(db, history_id, current_user.id)
        
        if not history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family medical history record not found"
            )
        
        return FamilyMedicalHistoryResponse(
            id=history.id,
            condition_name=history.condition_name,
            relation=history.relation,
            age_of_onset=history.age_of_onset,
            description=history.description,
            outcome=history.outcome,
            status=history.status,
            source=history.source,
            created_by=history.created_by,
            created_at=history.created_at,
            updated_at=history.updated_at,
            updated_by=history.updated_by
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get family medical history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get family medical history: {str(e)}"
        )

@router.put("/family-history/{history_id}", response_model=FamilyMedicalHistoryResponse)
async def update_family_medical_history(
    history_id: int,
    family_history_update: FamilyMedicalHistoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a family medical history record"""
    try:
        existing_family_history = family_medical_history_crud.get_by_id(db, history_id, current_user.id)
        
        if not existing_family_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family medical history record not found"
            )
        
        db_family_history = family_medical_history_crud.update(db, history_id, family_history_update, current_user.id)
        
        return FamilyMedicalHistoryResponse(
            id=db_family_history.id,
            condition_name=db_family_history.condition_name,
            relation=db_family_history.relation,
            age_of_onset=db_family_history.age_of_onset,
            description=db_family_history.description,
            outcome=db_family_history.outcome,
            status=db_family_history.status,
            source=db_family_history.source,
            created_by=db_family_history.created_by,
            created_at=db_family_history.created_at,
            updated_at=db_family_history.updated_at,
            updated_by=db_family_history.updated_by
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update family medical history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update family medical history: {str(e)}"
        )

@router.delete("/family-history/{history_id}")
async def delete_family_medical_history(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a family medical history record"""
    try:
        existing_family_history = family_medical_history_crud.get_by_id(db, history_id, current_user.id)
        
        if not existing_family_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family medical history record not found"
            )
        
        family_medical_history_crud.delete(db, history_id, current_user.id)
        return {"message": "Family medical history record deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete family medical history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete family medical history: {str(e)}"
        )

# ============================================================================
# MEDICAL DOCUMENTS ENDPOINTS
# ============================================================================

@router.get("/medical-documents")
async def get_medical_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    document_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get medical documents for the current user"""
    try:
        documents = health_record_doc_lab_crud.get_by_user(db, current_user.id, skip, limit)
        logger.info(f"Found {len(documents)} total documents for user {current_user.id}")
        
        # Filter by document type if provided
        if document_type:
            logger.info(f"Filtering by document_type: {document_type}")
            original_count = len(documents)
            documents = [doc for doc in documents if doc.document_type == document_type]
            logger.info(f"After filtering: {len(documents)} documents (was {original_count})")
        
        # Debug: Log the first document structure
        if documents:
            first_doc = documents[0]
            logger.info(f"First document structure: {first_doc.__dict__}")
            logger.info(f"Document type value: {first_doc.document_type} (type: {type(first_doc.document_type)})")
        
        return documents
    except Exception as e:
        logger.error(f"Failed to get medical documents: {e}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get medical documents: {str(e)}"
        )

@router.get("/health-record-doc-lab")
async def get_health_record_doc_lab(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    document_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get health record lab documents for the current user"""
    try:
        documents = health_record_doc_lab_crud.get_by_user(db, current_user.id, skip, limit)
        logger.info(f"Found {len(documents)} health record lab documents for user {current_user.id}")
        return documents
    except Exception as e:
        logger.error(f"Failed to get health record lab documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get health record lab documents: {str(e)}"
        )

@router.get("/health-record-doc-lab/{document_id}", response_model=HealthRecordDocLabResponse)
async def get_medical_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific medical document by ID"""
    try:
        document = health_record_doc_lab_crud.get_by_id(db, document_id, current_user.id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical document not found"
            )
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get medical document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get medical document: {str(e)}"
        )

@router.post("/health-record-doc-lab", response_model=HealthRecordDocLabResponse)
async def create_health_record_doc_lab(
    document_data: HealthRecordDocLabCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new medical document"""
    try:
        document = health_record_doc_lab_crud.create(db, document_data, current_user.id)
        return document
    except Exception as e:
        logger.error(f"Failed to create medical document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create medical document: {str(e)}"
        )

@router.put("/health-record-doc-lab/{document_id}", response_model=HealthRecordDocLabResponse)
async def update_health_record_doc_lab(
    document_id: int,
    document_data: HealthRecordDocLabUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a medical document"""
    try:
        # Check if document exists and belongs to user
        existing_document = health_record_doc_lab_crud.get_by_id(db, document_id, current_user.id)
        if not existing_document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical document not found"
            )
        
        document = health_record_doc_lab_crud.update(db, document_id, document_data, current_user.id)
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update medical document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update medical document: {str(e)}"
        )

@router.put("/health-record-doc-lab/{document_id}/replace-file")
async def replace_health_record_doc_lab_file(
    document_id: int,
    file: UploadFile = File(..., description="New lab report PDF file"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Replace the file of an existing medical document while preserving health records"""
    try:
        # Check if document exists and belongs to user
        existing_document = health_record_doc_lab_crud.get_by_id(db, document_id, current_user.id)
        if not existing_document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical document not found"
            )
        
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported for lab document replacement"
            )
        
        # Validate file size (max 10MB)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 10MB"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Upload new file to S3
        from app.services.lab_document_analysis_service import LabDocumentAnalysisService
        lab_service = LabDocumentAnalysisService()
        
        try:
            new_s3_url = await lab_service._upload_to_s3(file_content, file.filename, str(current_user.id))
        except Exception as s3_error:
            logger.error(f"Failed to upload new file to S3: {s3_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload new file to S3: {str(s3_error)}"
            )
        
        # Update the document with new file information
        update_data = HealthRecordDocLabUpdate(
            file_name=file.filename,
            s3_url=new_s3_url
        )
        
        updated_document = health_record_doc_lab_crud.update(db, document_id, update_data, current_user.id)
        
        logger.info(f"Successfully replaced file for medical document {document_id} for user {current_user.id}")
        
        return {
            "success": True,
            "message": "File replaced successfully while preserving health records",
            "document": updated_document,
            "new_s3_url": new_s3_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to replace file for medical document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to replace file: {str(e)}"
        )

@router.get("/health-record-doc-lab/{document_id}/download")
async def download_health_record_doc_lab(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download a lab document file"""
    try:
        # Get the document
        document = health_record_doc_lab_crud.get_by_id(db, document_id, current_user.id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lab document not found"
            )
        
        # Check if document has S3 URL
        if not document.s3_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not found"
            )
        
        # Generate presigned URL for download
        download_url = aws_service.generate_presigned_url(document.s3_url, expiration=3600)
        
        logger.info(f"Generated download URL for lab document {document_id} for user {current_user.id}")
        
        return {
            "download_url": download_url,
            "file_name": document.file_name,
            "expires_in": 3600
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate download URL for lab document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate download URL: {str(e)}"
        )

@router.delete("/health-record-doc-lab/{document_id}")
async def delete_health_record_doc_lab(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a medical document"""
    try:
        # Check if document exists and belongs to user
        existing_document = health_record_doc_lab_crud.get_by_id(db, document_id, current_user.id)
        if not existing_document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical document not found"
            )
        
        success = health_record_doc_lab_crud.delete(db, document_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical document not found"
            )
        
        return {"message": "Medical document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete medical document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete medical document: {str(e)}"
        )

@router.delete("/medical-documents/{document_id}")
async def delete_medical_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a medical document"""
    try:
        # Check if document exists and belongs to user
        existing_document = health_record_doc_lab_crud.get_by_id(db, document_id, current_user.id)
        if not existing_document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical document not found"
            )
        
        success = health_record_doc_lab_crud.delete(db, document_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete medical document"
            )
        
        return {"message": "Medical document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete medical document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete medical document: {str(e)}"
        )

@router.get("/medical-documents/{document_id}/download")
async def download_medical_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download a medical document"""
    try:
        # Check if document exists and belongs to user
        document = health_record_doc_lab_crud.get_by_id(db, document_id, current_user.id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical document not found"
            )
        
        if not document.s3_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not found"
            )
        
        # Generate a presigned URL for download
        download_url = aws_service.generate_presigned_url(document.s3_url)
        
        return {"download_url": download_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download medical document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download medical document: {str(e)}"
        )

# ============================================================================
# SECTIONS AND METRICS MANAGEMENT ENDPOINTS
# ============================================================================
async def create_medical_condition(
    condition: MedicalConditionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new medical condition"""
    try:
        db_condition = medical_condition_crud.create(db, condition, current_user.id)
        
        return MedicalConditionResponse(
            id=db_condition.id,
            condition_name=db_condition.condition_name,
            description=db_condition.description,
            diagnosed_date=db_condition.diagnosed_date,
            status=db_condition.status,
            severity=db_condition.severity,
            source=db_condition.source,
            treatment_plan=db_condition.treatment_plan,
            current_medications=db_condition.current_medications,
            outcome=db_condition.outcome,
            resolved_date=db_condition.resolved_date,
            created_by=db_condition.created_by,
            created_at=db_condition.created_at,
            updated_at=db_condition.updated_at,
            updated_by=db_condition.updated_by
        )
        
    except Exception as e:
        logger.error(f"Failed to create medical condition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create medical condition: {str(e)}"
        )

@router.get("/conditions", response_model=List[MedicalConditionResponse])
async def read_medical_conditions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get medical conditions for the current user"""
    try:
        conditions = medical_condition_crud.get_by_user(db, current_user.id, skip, limit)
        
        return [
            MedicalConditionResponse(
                id=condition.id,
                condition_name=condition.condition_name,
                description=condition.description,
                diagnosed_date=condition.diagnosed_date,
                status=condition.status,
                severity=condition.severity,
                source=condition.source,
                treatment_plan=condition.treatment_plan,
                current_medications=condition.current_medications if isinstance(condition.current_medications, list) else None,
                outcome=condition.outcome,
                resolved_date=condition.resolved_date,
                created_by=condition.created_by,
                created_at=condition.created_at,
                updated_at=condition.updated_at,
                updated_by=condition.updated_by
            )
            for condition in conditions
        ]
        
    except Exception as e:
        logger.error(f"Failed to retrieve medical conditions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve medical conditions: {str(e)}"
        )

@router.get("/conditions/{condition_id}", response_model=MedicalConditionResponse)
async def read_medical_condition(
    condition_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific medical condition by ID"""
    try:
        condition = medical_condition_crud.get_by_id(db, condition_id, current_user.id)
        
        if not condition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical condition not found"
            )
        
        return MedicalConditionResponse(
            id=condition.id,
            condition_name=condition.condition_name,
            description=condition.description,
            diagnosed_date=condition.diagnosed_date,
            status=condition.status,
            severity=condition.severity,
            source=condition.source,
            treatment_plan=condition.treatment_plan,
            current_medications=condition.current_medications if isinstance(condition.current_medications, list) else None,
            outcome=condition.outcome,
            resolved_date=condition.resolved_date,
            created_by=condition.created_by,
            created_at=condition.created_at,
            updated_at=condition.updated_at,
            updated_by=condition.updated_by
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve medical condition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve medical condition: {str(e)}"
        )

@router.put("/conditions/{condition_id}", response_model=MedicalConditionResponse)
async def update_medical_condition(
    condition_id: int,
    condition_update: MedicalConditionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a medical condition"""
    try:
        updated_condition = medical_condition_crud.update(
            db, condition_id, condition_update, current_user.id
        )
        
        if not updated_condition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical condition not found"
            )
        
        return MedicalConditionResponse(
            id=updated_condition.id,
            condition_name=updated_condition.condition_name,
            description=updated_condition.description,
            diagnosed_date=updated_condition.diagnosed_date,
            status=updated_condition.status,
            severity=updated_condition.severity,
            source=updated_condition.source,
            treatment_plan=updated_condition.treatment_plan,
            current_medications=updated_condition.current_medications,
            outcome=updated_condition.outcome,
            resolved_date=updated_condition.resolved_date,
            created_by=updated_condition.created_by,
            created_at=updated_condition.created_at,
            updated_at=updated_condition.updated_at,
            updated_by=updated_condition.updated_by
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update medical condition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update medical condition: {str(e)}"
        )

@router.delete("/conditions/{condition_id}")
async def delete_medical_condition(
    condition_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a medical condition"""
    try:
        success = medical_condition_crud.delete(db, condition_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical condition not found"
            )
        
        return {"message": "Medical condition deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete medical condition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete medical condition: {str(e)}"
        )

async def create_family_medical_history(
    history: FamilyMedicalHistoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new family medical history record"""
    try:
        db_history = family_medical_history_crud.create(db, history, current_user.id)
        
        return FamilyMedicalHistoryResponse(
            id=db_history.id,
            condition_name=db_history.condition_name,
            relation=db_history.relation,
            age_of_onset=db_history.age_of_onset,
            description=db_history.description,
            outcome=db_history.outcome,
            status=db_history.status,
            source=db_history.source,
            created_by=db_history.created_by,
            created_at=db_history.created_at,
            updated_at=db_history.updated_at,
            updated_by=db_history.updated_by
        )
        
    except Exception as e:
        logger.error(f"Failed to create family medical history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create family medical history: {str(e)}"
        )


# ============================================================================
# SECTIONS AND METRICS MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/sections", response_model=List[Dict[str, Any]])
async def get_sections_with_metrics(
    health_record_type_id: Optional[int] = Query(None, description="Filter by health record type ID"),
    include_inactive: bool = Query(False, description="Include inactive sections"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all health record sections with their associated metrics"""
    try:
        sections = health_record_section_metric_crud.get_sections_with_metrics(
            db, current_user.id, include_inactive, health_record_type_id
        )
        return sections
        
    except Exception as e:
        logger.error(f"Failed to get sections with metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sections with metrics: {str(e)}"
        )

@router.get("/sections/templates", response_model=List[Dict[str, Any]])
async def get_section_templates(
    health_record_type_id: Optional[int] = Query(None, description="Filter by health record type ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get admin-created default section templates that users can choose from"""
    try:
        templates = health_record_section_metric_crud.get_default_section_templates(
            db, health_record_type_id
        )
        return templates
        
    except Exception as e:
        logger.error(f"Failed to get section templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get section templates: {str(e)}"
        )


@router.post("/sections", response_model=Dict[str, Any])
async def create_health_record_section(
    section_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new health record section"""
    try:
        logger.info(f"Section creation request received: {section_data}")
        logger.info(f"User ID: {current_user.id}")
        
        # Check if this is a template selection (is_default=True) or custom section creation (is_default=False)
        is_template_selection = section_data.get("is_default", False)
        
        logger.info(f"Section creation request: name={section_data['name']}, is_default={is_template_selection}, user_id={current_user.id}")
        
        if is_template_selection:
            # User is selecting an admin template - check if they already have this section in normal table
            from app.models.health_metrics import HealthRecordSectionTemplate
            
            # First, verify the template exists in tmp table
            template = db.query(HealthRecordSectionTemplate).filter(
                and_(
                    HealthRecordSectionTemplate.name == section_data["name"],
                    HealthRecordSectionTemplate.health_record_type_id == section_data["health_record_type_id"],
                    HealthRecordSectionTemplate.is_default == True
                )
            ).first()
            
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Template '{section_data['display_name']}' not found"
                )
            
            # Check if user already has this section in normal table
            existing_user_section = db.query(HealthRecordSection).filter(
                and_(
                    HealthRecordSection.name == section_data["name"],
                    HealthRecordSection.health_record_type_id == section_data["health_record_type_id"],
                    HealthRecordSection.created_by == current_user.id
                )
            ).first()
            
            if existing_user_section:
                logger.info(f"User already has this section: {existing_user_section.id} - {existing_user_section.display_name}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Section '{section_data['display_name']}' already exists"
                )
            
            # Create section in normal table using template data
            new_section = HealthRecordSection(
                name=template.name,
                display_name=template.display_name,
                description=template.description,
                health_record_type_id=template.health_record_type_id,
                section_template_id=template.id,  # Link to the template section
                is_default=False,  # User's active section is always is_default=False
                created_by=current_user.id
            )
        else:
            # User is creating a custom section
            # Check if user already has a section with this name
            existing_user_section = db.query(HealthRecordSection).filter(
                and_(
                    HealthRecordSection.name == section_data["name"],
                    HealthRecordSection.health_record_type_id == section_data["health_record_type_id"],
                    HealthRecordSection.created_by == current_user.id
                )
            ).first()
            
            if existing_user_section:
                logger.info(f"Found existing user section: {existing_user_section.id} - {existing_user_section.display_name}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Section '{section_data['display_name']}' already exists"
                )
            
            # Create custom section in BOTH tmp table (as template) AND normal table (for UI)
            from app.models.health_metrics import HealthRecordSectionTemplate
            
            # First create in tmp table as a template
            new_template = HealthRecordSectionTemplate(
                name=section_data["name"],
                display_name=section_data["display_name"],
                description=section_data.get("description", ""),
                health_record_type_id=section_data["health_record_type_id"],
                is_default=False,  # User custom template
                created_by=current_user.id
            )
            db.add(new_template)
            db.commit()
            db.refresh(new_template)
            
            # Then create in normal table for UI
            new_section = HealthRecordSection(
                name=section_data["name"],
                display_name=section_data["display_name"],
                description=section_data.get("description", ""),
                health_record_type_id=section_data["health_record_type_id"],
                section_template_id=new_template.id,  # Link to the template we just created
                is_default=False,  # User's active section
                created_by=current_user.id
            )
        
        db.add(new_section)
        db.commit()
        db.refresh(new_section)
        
        return {
            "id": new_section.id,
            "name": new_section.name,
            "display_name": new_section.display_name,
            "description": new_section.description,
            "health_record_type_id": new_section.health_record_type_id,
            "is_default": new_section.is_default,
            "created_by": new_section.created_by,
            "created_at": new_section.created_at.isoformat() if new_section.created_at else None,
            "updated_at": new_section.updated_at.isoformat() if new_section.updated_at else None,
            "updated_by": new_section.updated_by,
            "metrics": []
        }
        
    except HTTPException:
        # Re-raise HTTPExceptions (like 409 Conflict) without wrapping them
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Failed to create health record section: {e}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create health record section: {str(e)}"
        )

@router.put("/sections/{section_id}", response_model=Dict[str, Any])
async def update_health_record_section(
    section_id: int,
    section_update: HealthRecordSectionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a health record section"""
    try:
        # Check if section exists and belongs to user
        section = health_record_section_crud.get_by_id(db, section_id)
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
        
        # Check if user owns this section (for custom sections)
        if not section.is_default and section.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this section"
            )
        
        # Update the section
        updated_section = health_record_section_crud.update(
            db, 
            section_id, 
            section_update, 
            current_user.id
        )
        
        return {
            "id": updated_section.id,
            "name": updated_section.name,
            "display_name": updated_section.display_name,
            "description": updated_section.description,
            "health_record_type_id": updated_section.health_record_type_id,
            "is_default": updated_section.is_default,
            "created_by": updated_section.created_by,
            "created_at": updated_section.created_at.isoformat() if updated_section.created_at else None,
            "updated_at": updated_section.updated_at.isoformat() if updated_section.updated_at else None,
            "updated_by": updated_section.updated_by,
            "metrics": []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update health record section: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update health record section: {str(e)}"
        )

@router.get("/sections/combined", response_model=Dict[str, Any])
async def get_sections_combined(
    health_record_type_id: Optional[int] = Query(None, description="Filter by health record type ID"),
    include_inactive: bool = Query(False, description="Include inactive sections"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get both user sections and admin templates in one call"""
    try:
        logger.info("Combined endpoint accessed successfully")
        
        # Get user sections (from normal tables - user's active sections)
        user_sections = health_record_section_metric_crud.get_sections_with_metrics(
            db, current_user.id, include_inactive, health_record_type_id
        )
        
        # Get admin templates (from template tables - for creating new sections)
        admin_templates = health_record_section_metric_crud.get_default_section_templates(
            db, health_record_type_id
        )
        
        logger.info(f"User sections count: {len(user_sections)}")
        logger.info(f"Admin templates count: {len(admin_templates)}")
        
        return {
            "user_sections": user_sections,
            "admin_templates": admin_templates
        }
        
    except Exception as e:
        logger.error(f"Failed to get combined sections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get combined sections: {str(e)}"
        )

@router.get("/sections/{section_id}/metrics", response_model=List[Dict[str, Any]])
async def get_section_metrics(
    section_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all metrics for a specific section"""
    try:
        metrics = health_record_metric_crud.get_by_section(db, section_id)
        
        # Add statistics for each metric
        metrics_with_stats = []
        for metric in metrics:
            metric_details = health_record_section_metric_crud.get_metric_details(
                db, metric.id, current_user.id
            )
            if metric_details:
                metrics_with_stats.append(metric_details)
        
        return metrics_with_stats
        
    except Exception as e:
        logger.error(f"Failed to get section metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get section metrics: {str(e)}"
        )

@router.post("/metrics", response_model=Dict[str, Any])
async def create_health_record_metric(
    metric_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new health record metric"""
    try:
        
        # Validate required fields
        required_fields = ['section_id', 'name', 'display_name', 'data_type']
        for field in required_fields:
            if field not in metric_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Check if section exists and belongs to user
        section = health_record_section_crud.get_by_id(db, metric_data['section_id'])
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
        
        # Check if this is a template selection (is_default=True) or custom metric creation (is_default=False)
        is_template_selection = metric_data.get("is_default", False)
        
        if is_template_selection:
            # User is selecting an admin template - check if they already have this metric in normal table
            from app.models.health_metrics import HealthRecordMetricTemplate, HealthRecordSectionTemplate
            
            # Find the corresponding section template ID
            section_template = db.query(HealthRecordSectionTemplate).filter(
                and_(
                    HealthRecordSectionTemplate.name == section.name,
                    HealthRecordSectionTemplate.health_record_type_id == section.health_record_type_id
                )
            ).first()
            
            if not section_template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Corresponding section template not found"
                )
            
            # First, verify the template exists in tmp table
            template = db.query(HealthRecordMetricTemplate).filter(
                and_(
                    HealthRecordMetricTemplate.name == metric_data["name"],
                    HealthRecordMetricTemplate.section_template_id == section_template.id,
                    HealthRecordMetricTemplate.is_default == True
                )
            ).first()
            
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Template '{metric_data['display_name']}' not found"
                )
            
            # Check if user already has this metric in normal table
            existing_metric = health_record_metric_crud.get_by_section_and_name(
                db, metric_data['section_id'], metric_data['name']
            )
            
            if existing_metric:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Metric '{metric_data['display_name']}' already exists in this section"
                )
            
            # Create metric in normal table using template data
            metric_create_data = HealthRecordMetricCreate(
                section_id=metric_data['section_id'],
                name=template.name,
                display_name=template.display_name,
                description=template.description or '',
                default_unit=template.default_unit or '',
                reference_data=template.reference_data or {},
                data_type=template.data_type,
                is_default=False  # User's active metric is always is_default=False
            )
        else:
            # User is creating a custom metric
            # Check if metric with same name already exists in this section
            existing_metric = health_record_metric_crud.get_by_section_and_name(
                db, metric_data['section_id'], metric_data['name']
            )
            if existing_metric:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Metric '{metric_data['name']}' already exists in this section"
                )
            
            # Create custom metric in BOTH tmp table (as template) AND normal table (for UI)
            from app.models.health_metrics import HealthRecordMetricTemplate
            
            # First create in tmp table as a template
            # Find the corresponding section template ID
            from app.models.health_metrics import HealthRecordSectionTemplate
            section_template = db.query(HealthRecordSectionTemplate).filter(
                and_(
                    HealthRecordSectionTemplate.name == section.name,
                    HealthRecordSectionTemplate.health_record_type_id == section.health_record_type_id
                )
            ).first()
            
            if not section_template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Corresponding section template not found"
                )
            
            reference_data = metric_data.get('reference_data', {})
            new_template = HealthRecordMetricTemplate(
                section_template_id=section_template.id,
                name=metric_data['name'],
                display_name=metric_data['display_name'],
                description=metric_data.get('description', ''),
                default_unit=metric_data.get('default_unit', ''),
                original_reference='',  # Custom metrics don't have original reference
                reference_data=reference_data,
                data_type=metric_data['data_type'],
                is_default=False,  # User custom template
                created_by=current_user.id
            )
            db.add(new_template)
            db.commit()
            db.refresh(new_template)
            
            # Then create in normal table for UI
            metric_create_data = HealthRecordMetricCreate(
                section_id=metric_data['section_id'],
                metric_tmp_id=new_template.id,  # Link to the template we just created
                name=metric_data['name'],
                display_name=metric_data['display_name'],
                description=metric_data.get('description', ''),
                default_unit=metric_data.get('default_unit', ''),
                reference_data=reference_data,
                data_type=metric_data['data_type'],
                is_default=False  # User's active metric
            )
        
        new_metric = health_record_metric_crud.create(db, metric_create_data, current_user.id)
        
        return {
            "id": new_metric.id,
            "section_id": new_metric.section_id,
            "name": new_metric.name,
            "display_name": new_metric.display_name,
            "description": new_metric.description,
            "default_unit": new_metric.default_unit,
            "reference_data": new_metric.reference_data,
            "data_type": new_metric.data_type,
            "is_default": new_metric.is_default,
            "created_at": new_metric.created_at.isoformat() if new_metric.created_at else None,
            "created_by": new_metric.created_by
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create metric: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create metric: {str(e)}"
        )

@router.put("/metrics/{metric_id}", response_model=Dict[str, Any])
async def update_health_record_metric(
    metric_id: int,
    metric_data: HealthRecordMetricUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a health record metric"""
    try:
        # Check if metric exists and belongs to user
        existing_metric = health_record_metric_crud.get_by_id(db, metric_id)
        if not existing_metric:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Metric not found"
            )
        
        # Check if the section belongs to the user
        section = health_record_section_crud.get_by_id(db, existing_metric.section_id)
        if not section or section.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this metric"
            )
        
        # Update the metric
        updated_metric = health_record_metric_crud.update(
            db, metric_id, metric_data, current_user.id
        )
        
        return {
            "id": updated_metric.id,
            "section_id": updated_metric.section_id,
            "name": updated_metric.name,
            "display_name": updated_metric.display_name,
            "description": updated_metric.description,
            "default_unit": updated_metric.default_unit,
            "reference_data": updated_metric.reference_data,
            "data_type": updated_metric.data_type,
            "is_default": updated_metric.is_default,
            "created_at": updated_metric.created_at.isoformat() if updated_metric.created_at else None,
            "updated_at": updated_metric.updated_at.isoformat() if updated_metric.updated_at else None,
            "created_by": updated_metric.created_by,
            "updated_by": updated_metric.updated_by
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update metric: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update metric: {str(e)}"
        )

@router.get("/metrics/{metric_id}/details", response_model=Dict[str, Any])
async def get_metric_details(
    metric_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific metric"""
    try:
        metric_details = health_record_section_metric_crud.get_metric_details(
            db, metric_id, current_user.id
        )
        
        if not metric_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Metric not found"
            )
        
        return metric_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metric details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metric details: {str(e)}"
        )

@router.delete("/metrics/{metric_id}")
async def delete_health_record_metric(
    metric_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a health record metric and all related records"""
    try:
        # Check if metric exists and belongs to user
        metric = health_record_metric_crud.get_by_id(db, metric_id)
        if not metric:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Metric not found"
            )
        
        # Check if user owns the section that contains this metric
        section = health_record_section_crud.get_by_id(db, metric.section_id)
        if not section or section.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this metric"
            )
        
        # Delete the metric (this will cascade delete related records)
        success = health_record_metric_crud.delete(db, metric_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete metric"
            )
        
        logger.info(f"Successfully deleted metric {metric_id} for user {current_user.id}")
        return {"message": "Metric deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete metric {metric_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete metric: {str(e)}"
        )

@router.delete("/sections/{section_id}")
async def delete_health_record_section(
    section_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a health record section and all related metrics and records"""
    try:
        # Check if section exists and belongs to user
        section = health_record_section_crud.get_by_id(db, section_id)
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
        
        if section.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this section"
            )
        
        # Delete the section (this will cascade delete related metrics and records)
        success = health_record_section_crud.delete(db, section_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete section"
            )
        
        logger.info(f"Successfully deleted section {section_id} for user {current_user.id}")
        return {"message": "Section deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete section {section_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete section: {str(e)}"
        )

@router.get("/overview", response_model=Dict[str, Any])
async def get_user_health_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall health overview for the current user"""
    try:
        overview = health_record_section_metric_crud.get_user_health_overview(
            db, current_user.id
        )
        return overview
        
    except Exception as e:
        logger.error(f"Failed to get user health overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user health overview: {str(e)}"
        )

# ============================================================================
# HEALTH RECORD IMAGE ENDPOINTS
# ============================================================================

@router.post("/images/upload-pdf")
async def upload_medical_image_pdf(
    file: UploadFile = File(..., description="Medical image PDF file"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a medical image PDF for analysis"""
    try:
        # Validate file type
        if not file.content_type or file.content_type != 'application/pdf':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a PDF"
            )
        
        # Validate file size (max 50MB)
        if file.size and file.size > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 50MB"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Process with medical image analysis service
        from app.services.medical_image_analysis_service import MedicalImageAnalysisService
        medical_image_service = MedicalImageAnalysisService()
        
        result = await medical_image_service.process_medical_image(
            file_content=file_content,
            filename=file.filename,
            user_id=current_user.id
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process PDF: {result.get('error', 'Unknown error')}"
            )
        
        return {
            "success": True,
            "extracted_info": result["extracted_info"],
            "s3_key": result["s3_key"],
            "message": "PDF processed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload medical image PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload medical image PDF: {str(e)}"
        )

@router.post("/health-record-doc-exam/upload", response_model=HealthRecordDocExamResponse)
async def upload_health_record_image(
    file: UploadFile = File(..., description="Medical image file (JPEG, PNG, DICOM, etc.)"),
    image_type: ImageType = Form(..., description="Type of medical image"),
    body_part: str = Form(..., description="Body part imaged"),
    image_date: datetime = Form(..., description="When the image was taken"),
    findings: ImageFindings = Form(..., description="Findings from the image analysis"),
    conclusions: Optional[str] = Form(None, description="Text input for conclusions/notes"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a new health record image with file and metadata"""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image (JPEG, PNG, etc.)"
            )
        
        # Validate file size (max 50MB for medical images)
        if file.size and file.size > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 50MB"
            )
        
        # Check for duplicate files
        from app.crud.document import document_crud
        duplicate_doc = document_crud.check_duplicate_file(
            db, current_user.id, file.filename, file.size
        )
        
        if duplicate_doc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A similar file already exists: {duplicate_doc.file_name}"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Store file in S3 using AWS service
        s3_url = await aws_service.store_document(
            internal_user_id=str(current_user.id),
            file_data=file_content,
            file_name=file.filename,
            content_type=file.content_type
        )
        
        # Prepare image data for database
        image_data = {
            "image_type": image_type,
            "body_part": body_part,
            "image_date": image_date,
            "findings": findings,
            "conclusions": conclusions,
            "original_filename": file.filename,
            "file_size_bytes": file.size,
            "content_type": file.content_type,
            "s3_bucket": aws_service.s3_client.meta.region_name,  # Get bucket info
            "s3_key": f"health_images/{current_user.id}/{file_id}/{file.filename}",
            "s3_url": s3_url,
            "file_id": file_id
        }
        
        # Create the image record in database
        db_image = health_record_doc_exam_crud.create_image(db, image_data, current_user.id)
        
        return HealthRecordDocExamResponse(
            id=db_image.id,
            created_by=db_image.created_by,
            image_type=db_image.image_type,
            body_part=db_image.body_part,
            image_date=db_image.image_date,
            findings=db_image.findings,
            conclusions=db_image.conclusions,
            original_filename=db_image.original_filename,
            file_size_bytes=db_image.file_size_bytes,
            content_type=db_image.content_type,
            s3_bucket=db_image.s3_bucket,
            s3_key=db_image.s3_key,
            s3_url=db_image.s3_url,
            file_id=db_image.file_id,
            created_at=db_image.created_at,
            updated_at=db_image.updated_at,
            updated_by=db_image.updated_by
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload health record image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload health record image: {str(e)}"
        )

@router.post("/health-record-doc-exam", response_model=HealthRecordDocExamResponse)
async def create_health_record_doc_exam(
    image_data: HealthRecordDocExamCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new health record image (metadata only, no file upload)"""
    try:
        # Convert Pydantic model to dict, excluding unset fields
        image_dict = image_data.dict(exclude_unset=True)
        
        # Create the image record
        db_image = health_record_doc_exam_crud.create_image(db, image_dict, current_user.id)
        
        return HealthRecordDocExamResponse(
            id=db_image.id,
            created_by=db_image.created_by,
            image_type=db_image.image_type,
            body_part=db_image.body_part,
            image_date=db_image.image_date,
            findings=db_image.findings,
            conclusions=db_image.conclusions,
            interpretation=db_image.interpretation,
            notes=db_image.notes,
            original_filename=db_image.original_filename,
            file_size_bytes=db_image.file_size_bytes,
            content_type=db_image.content_type,
            s3_bucket=db_image.s3_bucket,
            s3_key=db_image.s3_key,
            s3_url=db_image.s3_url,
            file_id=db_image.file_id,
            created_at=db_image.created_at,
            updated_at=db_image.updated_at,
            updated_by=db_image.updated_by
        )
        
    except Exception as e:
        logger.error(f"Failed to create health record image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create health record image: {str(e)}"
        )

@router.get("/health-record-doc-exam", response_model=PaginatedImageResponse)
async def get_health_record_doc_exam(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    image_type: Optional[ImageType] = Query(None, description="Filter by image type"),
    body_part: Optional[str] = Query(None, description="Filter by body part"),
    findings: Optional[ImageFindings] = Query(None, description="Filter by findings"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get paginated health record images for the current user with optional filters"""
    try:
        # Get total count for pagination
        total_images = health_record_doc_exam_crud.get_user_images(
            db, current_user.id, 0, 10000, 
            image_type.value if image_type else None, 
            body_part, 
            findings.value if findings else None
        )
        total_count = len(total_images)
        
        # Get paginated results
        images = health_record_doc_exam_crud.get_user_images(
            db, current_user.id, skip, limit, 
            image_type.value if image_type else None, 
            body_part, 
            findings.value if findings else None
        )
        
        # Convert to response schemas
        image_summaries = [
            HealthRecordDocExamSummary(
                id=img.id,
                image_type=img.image_type,
                body_part=img.body_part,
                image_date=img.image_date,
                findings=img.findings,
                conclusions=img.conclusions,
                interpretation=img.interpretation,
                notes=img.notes,
                original_filename=img.original_filename,
                content_type=img.content_type,
                file_size_bytes=img.file_size_bytes,
                s3_url=img.s3_url,
                doctor_name=img.doctor_name,
                doctor_number=img.doctor_number,
                created_at=img.created_at
            )
            for img in images
        ]
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        current_page = (skip // limit) + 1
        has_more = skip + limit < total_count
        
        pagination_info = PaginationInfo(
            total=total_count,
            skip=skip,
            limit=limit,
            has_more=has_more,
            total_pages=total_pages,
            current_page=current_page
        )
        
        return PaginatedImageResponse(
            images=image_summaries,
            pagination=pagination_info
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve health record images: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve health record images: {str(e)}"
        )

@router.get("/health-record-doc-exam/{image_id}", response_model=HealthRecordDocExamResponse)
async def get_health_record_image(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific health record image by ID"""
    try:
        image = health_record_doc_exam_crud.get_image_by_id(db, image_id, current_user.id)
        
        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health record image not found"
            )
        
        return HealthRecordDocExamResponse(
            id=image.id,
            created_by=image.created_by,
            image_type=image.image_type,
            body_part=image.body_part,
            image_date=image.image_date,
            findings=image.findings,
            conclusions=image.conclusions,
            interpretation=image.interpretation,
            notes=image.notes,
            original_filename=image.original_filename,
            file_size_bytes=image.file_size_bytes,
            content_type=image.content_type,
            s3_bucket=image.s3_bucket,
            s3_key=image.s3_key,
            s3_url=image.s3_url,
            file_id=image.file_id,
            doctor_name=image.doctor_name,
            doctor_number=image.doctor_number,
            is_archived=image.is_archived,
            review_status=image.review_status,
            created_at=image.created_at,
            updated_at=image.updated_at,
            updated_by=image.updated_by
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve health record image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve health record image: {str(e)}"
        )

@router.put("/health-record-doc-exam/{image_id}", response_model=HealthRecordDocExamResponse)
async def update_health_record_doc_exam(
    image_id: int,
    image_update: HealthRecordDocExamUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a health record image"""
    try:
        # Convert Pydantic model to dict, excluding unset fields
        update_dict = image_update.dict(exclude_unset=True)
        
        updated_image = health_record_doc_exam_crud.update_image(
            db, image_id, current_user.id, update_dict
        )
        
        if not updated_image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health record image not found"
            )
        
        return HealthRecordDocExamResponse(
            id=updated_image.id,
            created_by=updated_image.created_by,
            image_type=updated_image.image_type,
            body_part=updated_image.body_part,
            image_date=updated_image.image_date,
            findings=updated_image.findings,
            conclusions=updated_image.conclusions,
            interpretation=updated_image.interpretation,
            notes=updated_image.notes,
            original_filename=updated_image.original_filename,
            file_size_bytes=updated_image.file_size_bytes,
            content_type=updated_image.content_type,
            s3_bucket=updated_image.s3_bucket,
            s3_key=updated_image.s3_key,
            s3_url=updated_image.s3_url,
            file_id=updated_image.file_id,
            created_at=updated_image.created_at,
            updated_at=updated_image.updated_at,
            updated_by=updated_image.updated_by
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update health record image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update health record image: {str(e)}"
        )

@router.delete("/health-record-doc-exam/{image_id}")
async def delete_health_record_doc_exam(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a health record exam/image"""
    try:
        success = health_record_doc_exam_crud.delete_image(db, image_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health record exam not found"
            )
        
        return {"message": "Health record exam deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete health record exam: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete health record exam"
        )

@router.delete("/images/{image_id}")
async def delete_health_record_image(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a health record image"""
    try:
        success = health_record_doc_exam_crud.delete_image(db, image_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health record image not found"
            )
        
        return {"message": "Health record image deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete health record image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete health record image: {str(e)}"
        )

@router.get("/images/{image_id}/download")
async def download_health_record_image(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download a health record image"""
    try:
        image = health_record_doc_exam_crud.get_image_by_id(db, image_id, current_user.id)
        
        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health record image not found"
            )
        
        # Generate a presigned URL for download
        if not image.s3_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file associated with this image"
            )
        
        # Construct S3 URL from s3_key
        from app.core.config import settings
        s3_url = f"s3://{settings.AWS_S3_BUCKET}/{image.s3_key}"
        download_url = aws_service.generate_presigned_url(s3_url)
        
        return {
            "download_url": download_url,
            "filename": image.original_filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download health record image {image_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download health record image: {str(e)}"
        )

@router.get("/images/statistics")
async def get_image_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get statistics about the current user's health record images"""
    try:
        stats = health_record_doc_exam_crud.get_image_statistics(db, current_user.id)
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get image statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get image statistics: {str(e)}"
        )

@router.get("/health-record-doc-exam/recent", response_model=List[HealthRecordDocExamSummary])
async def get_recent_images(
    limit: int = Query(10, ge=1, le=50, description="Number of recent images to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent health record images for the current user"""
    try:
        recent_images = health_record_doc_exam_crud.get_recent_images(db, current_user.id, limit)
        
        return [
            HealthRecordDocExamSummary(
                id=img.id,
                image_type=img.image_type,
                body_part=img.body_part,
                image_date=img.image_date,
                findings=img.findings,
                conclusions=img.conclusions,
                interpretation=img.interpretation,
                notes=img.notes,
                original_filename=img.original_filename,
                content_type=img.content_type,
                file_size_bytes=img.file_size_bytes,
                s3_url=img.s3_url,
                doctor_name=img.doctor_name,
                doctor_number=img.doctor_number,
                created_at=img.created_at
            )
            for img in recent_images
        ]
        
    except Exception as e:
        logger.error(f"Failed to get recent images: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent images: {str(e)}"
        )

# ============================================================================
# HEALTH RECORD TYPES ENDPOINTS
# ============================================================================

@router.get("/types", response_model=List[HealthRecordTypeResponse])
async def get_health_record_types(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all health record types"""
    try:
        health_record_type_crud = HealthRecordTypeCRUD()
        types = health_record_type_crud.get_all(db, skip, limit)
        return types
    except Exception as e:
        logger.error(f"Failed to get health record types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get health record types: {str(e)}"
        )

@router.get("/types/{type_id}", response_model=HealthRecordTypeResponse)
async def get_health_record_type(
    type_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific health record type"""
    try:
        health_record_type_crud = HealthRecordTypeCRUD()
        health_record_type = health_record_type_crud.get_by_id(db, type_id)
        if not health_record_type:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health record type not found")
        return health_record_type
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get health record type: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get health record type: {str(e)}"
        )

@router.post("/types", response_model=HealthRecordTypeResponse)
async def create_health_record_type(
    health_record_type: HealthRecordTypeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new health record type (admin only)"""
    try:
        if not current_user.is_superuser:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
        
        health_record_type_crud = HealthRecordTypeCRUD()
        new_type = health_record_type_crud.create(db, health_record_type, current_user.id)
        return new_type
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create health record type: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create health record type: {str(e)}"
        )

@router.put("/types/{type_id}", response_model=HealthRecordTypeResponse)
async def update_health_record_type(
    type_id: int,
    health_record_type_update: HealthRecordTypeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a health record type (admin only)"""
    try:
        if not current_user.is_superuser:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
        
        health_record_type_crud = HealthRecordTypeCRUD()
        updated_type = health_record_type_crud.update(db, type_id, health_record_type_update, current_user.id)
        if not updated_type:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health record type not found")
        return updated_type
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update health record type: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update health record type: {str(e)}"
        )

@router.delete("/types/{type_id}")
async def delete_health_record_type(
    type_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a health record type (admin only)"""
    try:
        if not current_user.is_superuser:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
        
        health_record_type_crud = HealthRecordTypeCRUD()
        success = health_record_type_crud.delete(db, type_id, current_user.id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health record type not found")
        return {"message": "Health record type deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete health record type: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete health record type: {str(e)}"
        )

# ============================================================================
# ADMIN TEMPLATES ENDPOINTS
# ============================================================================

@router.get("/admin-templates/sections")
async def get_admin_section_templates(
    health_record_type_id: int = Query(1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get admin-defined section templates"""
    try:
        from app.models.health_metrics import HealthRecordSectionTemplate
        
        # Get both admin-defined (is_default=True) and user custom (is_default=False) templates
        sections = db.query(HealthRecordSectionTemplate).filter(
            HealthRecordSectionTemplate.health_record_type_id == health_record_type_id
        ).all()
        
        return [
            {
                "id": section.id,
                "name": section.name,
                "display_name": section.display_name,
                "description": section.description,
                "health_record_type_id": section.health_record_type_id,
                "is_default": section.is_default
            }
            for section in sections
        ]
    except Exception as e:
        logger.error(f"Failed to get admin section templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get admin section templates: {str(e)}"
        )

@router.get("/admin-templates/sections")
async def get_admin_section_templates(
    health_record_type_id: int = Query(1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get admin-defined section templates with language support"""
    try:
        from app.models.health_metrics import HealthRecordSectionTemplate
        
        sections = db.query(HealthRecordSectionTemplate).filter(
            HealthRecordSectionTemplate.health_record_type_id == health_record_type_id,
            HealthRecordSectionTemplate.is_default == True
        ).all()
        
        return [
            {
                "id": section.id,
                "name": section.name,
                "display_name": section.display_name,
                "name_pt": section.name_pt,
                "display_name_pt": section.display_name_pt,
                "name_es": section.name_es,
                "display_name_es": section.display_name_es,
                "description": section.description,
                "health_record_type_id": section.health_record_type_id,
                "is_default": section.is_default
            }
            for section in sections
        ]
    except Exception as e:
        logger.error(f"Failed to get admin section templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get admin section templates: {str(e)}"
        )

@router.get("/admin-templates/metrics")
async def get_admin_metric_templates(
    section_template_id: int = Query(None),
    health_record_type_id: int = Query(1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get admin-defined metric templates"""
    try:
        from app.models.health_metrics import HealthRecordMetricTemplate, HealthRecordSectionTemplate
        
        query = db.query(HealthRecordMetricTemplate).join(
            HealthRecordSectionTemplate,
            HealthRecordMetricTemplate.section_template_id == HealthRecordSectionTemplate.id
        ).filter(
            HealthRecordSectionTemplate.health_record_type_id == health_record_type_id,
            HealthRecordMetricTemplate.is_default == True
        )
        
        if section_template_id:
            query = query.filter(HealthRecordMetricTemplate.section_template_id == section_template_id)
        
        metrics = query.all()
        
        return [
            {
                "id": metric.id,
                "section_template_id": metric.section_template_id,
                "name": metric.name,
                "display_name": metric.display_name,
                "name_pt": metric.name_pt,
                "display_name_pt": metric.display_name_pt,
                "name_es": metric.name_es,
                "display_name_es": metric.display_name_es,
                "description": metric.description,
                "default_unit": metric.default_unit,
                "default_unit_pt": metric.default_unit_pt,
                "default_unit_es": metric.default_unit_es,
                "original_reference": metric.original_reference,
                "reference_data": metric.reference_data,
                "data_type": metric.data_type,
                "is_default": metric.is_default
            }
            for metric in metrics
        ]
    except Exception as e:
        logger.error(f"Failed to get admin metric templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get admin metric templates: {str(e)}"
        )

# ============================================================================
# SURGERIES & HOSPITALIZATIONS ENDPOINTS (placed before generic routes)
# ============================================================================

@router.get("/surgeries-hospitalizations", response_model=SurgeryHospitalizationListResponse)
async def get_surgeries_hospitalizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all surgeries and hospitalizations for the current user"""
    try:
        surgeries = surgery_hospitalization_crud.get_by_user(db, current_user.id, skip, limit)
        total = len(surgery_hospitalization_crud.get_by_user(db, current_user.id, 0, 10000))
        
        return SurgeryHospitalizationListResponse(
            surgeries=surgeries,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Failed to get surgeries/hospitalizations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve surgeries and hospitalizations"
        )

@router.get("/surgeries-hospitalizations/{surgery_id}", response_model=SurgeryHospitalizationResponse)
async def get_surgery_hospitalization(
    surgery_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific surgery or hospitalization by ID"""
    try:
        surgery = surgery_hospitalization_crud.get_by_id(db, surgery_id, current_user.id)
        
        if not surgery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Surgery or hospitalization not found"
            )
        
        # Check if the surgery belongs to the current user
        if surgery.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this surgery/hospitalization"
            )
        
        return surgery
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get surgery/hospitalization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve surgery/hospitalization"
        )

@router.post("/surgeries-hospitalizations", response_model=SurgeryHospitalizationResponse)
async def create_surgery_hospitalization(
    surgery_data: SurgeryHospitalizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new surgery or hospitalization record"""
    try:
        surgery = surgery_hospitalization_crud.create(db, surgery_data, current_user.id)
        return surgery
        
    except Exception as e:
        logger.error(f"Failed to create surgery/hospitalization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create surgery/hospitalization"
        )

@router.put("/surgeries-hospitalizations/{surgery_id}", response_model=SurgeryHospitalizationResponse)
async def update_surgery_hospitalization(
    surgery_id: int,
    surgery_data: SurgeryHospitalizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing surgery or hospitalization record"""
    try:
        # First check if the surgery exists and belongs to the user
        existing_surgery = surgery_hospitalization_crud.get_by_id(db, surgery_id, current_user.id)
        
        if not existing_surgery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Surgery or hospitalization not found"
            )
        
        if existing_surgery.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this surgery/hospitalization"
            )
        
        updated_surgery = surgery_hospitalization_crud.update(db, surgery_id, surgery_data, current_user.id)
        return updated_surgery
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update surgery/hospitalization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update surgery/hospitalization"
        )

@router.delete("/surgeries-hospitalizations/{surgery_id}")
async def delete_surgery_hospitalization(
    surgery_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a surgery or hospitalization record"""
    try:
        # First check if the surgery exists and belongs to the user
        existing_surgery = surgery_hospitalization_crud.get_by_id(db, surgery_id, current_user.id)
        
        if not existing_surgery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Surgery or hospitalization not found"
            )
        
        if existing_surgery.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this surgery/hospitalization"
            )
        
        surgery_hospitalization_crud.delete(db, surgery_id, current_user.id)
        
        return {"message": "Surgery/hospitalization deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete surgery/hospitalization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete surgery/hospitalization"
        )

# ============================================================================
# GENERIC HEALTH RECORD ENDPOINTS (moved to end to avoid route conflicts)
# ============================================================================

@router.get("/{record_id}", response_model=HealthRecordResponse)
async def read_health_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific health record by ID"""
    try:
        record = health_record_crud.get_by_id(db, record_id, current_user.id)
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health record not found"
            )
        
        return HealthRecordResponse(
            id=record.id,
            section_id=record.section_id,
            metric_id=record.metric_id,
            value=record.value,
            status=record.status,
            source=record.source,
            recorded_at=record.recorded_at,
            device_id=record.device_id,
            device_info=record.device_info,
            accuracy=record.accuracy,
            location_data=record.location_data,
            created_by=record.created_by,
            created_at=record.created_at,
            updated_at=record.updated_at,
            updated_by=record.updated_by
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve health record: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve health record: {str(e)}"
        )

@router.put("/{record_id}", response_model=HealthRecordResponse)
async def update_health_record(
    record_id: int,
    health_record_update: HealthRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a health record"""
    try:
        updated_record = health_record_crud.update(
            db, record_id, health_record_update, current_user.id
        )
        
        if not updated_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health record not found"
            )
        
        return HealthRecordResponse(
            id=updated_record.id,
            section_id=updated_record.section_id,
            metric_id=updated_record.metric_id,
            value=updated_record.value,
            status=updated_record.status,
            source=updated_record.source,
            recorded_at=updated_record.recorded_at,
            device_id=updated_record.device_id,
            device_info=updated_record.device_info,
            accuracy=updated_record.accuracy,
            location_data=updated_record.location_data,
            created_by=updated_record.created_by,
            created_at=updated_record.created_at,
            updated_at=updated_record.updated_at,
            updated_by=updated_record.updated_by
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update health record: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update health record: {str(e)}"
        )

@router.delete("/{record_id}")
async def delete_health_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a health record"""
    try:
        success = health_record_crud.delete(db, record_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health record not found"
            )
        
        return {"message": "Health record deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete health record: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete health record: {str(e)}"
        )

# ============================================================================
# LAB DOCUMENT UPLOAD ENDPOINTS (moved from lab_documents.py)
# ============================================================================

@router.post("/health-record-doc-lab/upload", response_model=dict)
async def upload_and_analyze_lab_document(
    file: UploadFile = File(..., description="Lab report PDF file"),
    description: Optional[str] = Form(None, description="Optional description for the document"),
    doc_date: Optional[str] = Form(None, description="Document date"),
    doc_type: Optional[str] = Form(None, description="Document type"),
    provider: Optional[str] = Form(None, description="Healthcare provider"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and analyze a lab report PDF document (extraction only)
    
    This endpoint will:
    1. Check for duplicate files
    2. Store the PDF in AWS S3
    3. Extract text using pdfplumber
    4. Parse lab metrics using the multilingual extraction logic
    5. Return extracted data for user review (no health records created)
    
    Use /bulk endpoint to create health records after user confirmation.
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported for lab document analysis"
            )
        
        # Validate file size (max 10MB)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 10MB"
            )
        
        # Check for duplicate files
        from app.crud.document import document_crud
        duplicate_doc = document_crud.check_duplicate_file(
            db, current_user.id, file.filename, file.size
        )
        
        if duplicate_doc:
            return {
                "success": False,
                "duplicate_found": True,
                "existing_document": {
                    "id": duplicate_doc.id,
                    "file_name": duplicate_doc.original_file_name,
                    "file_size_bytes": duplicate_doc.file_size,
                    "created_at": duplicate_doc.created_at.isoformat()
                },
                "message": f"A similar file already exists: {duplicate_doc.original_file_name}"
            }
        
        # Import lab service
        from app.services.lab_document_analysis_service import LabDocumentAnalysisService
        lab_service = LabDocumentAnalysisService()
        
        # Read file content
        file_content = await file.read()
        

        # Extract lab data only (no health records created)
        lab_data = lab_service._extract_lab_data_advanced(
            lab_service._extract_text_from_pdf(file_content)
        )
        
        # Parse reference ranges for each lab data entry
        for item in lab_data:
            if 'reference' in item or 'reference_range' in item:
                original_reference = item.get('reference') or item.get('reference_range', '')
                if original_reference:
                    # Parse the reference range using the existing backend function
                    parsed_range = lab_service._parse_simple_range(original_reference)
                    # Add parsed min/max values to the response
                    item['reference_range_parsed'] = {
                        'min': parsed_range.get('min'),
                        'max': parsed_range.get('max'),
                        'original': original_reference
                    }
        
        # Upload to S3
        s3_url = None
        try:
            s3_url = await lab_service._upload_to_s3(file_content, file.filename, str(current_user.id))
        except Exception as s3_error:
            logger.error(f"Failed to upload file to S3: {s3_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to S3: {str(s3_error)}"
            )
        
        logger.info(f"Successfully extracted {len(lab_data)} lab records for user {current_user.id}")
        
        return {
            "success": True,
            "message": "Lab document analyzed successfully",
            "s3_url": s3_url,
            "lab_data": lab_data,
            "extracted_records_count": len(lab_data),
            "form_data": {
                "doc_date": doc_date,
                "doc_type": doc_type,
                "provider": provider,
                "description": description
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze lab document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze lab document: {str(e)}"
        )

@router.post("/health-record-doc-lab/bulk", response_model=dict)
async def bulk_create_lab_records(
    request: dict,  # Using dict instead of BulkLabRecordsRequest for now
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bulk create health records from lab document analysis results
    
    This endpoint will:
    1. Create sections and metrics if they don't exist
    2. Create health records for all provided lab data
    3. Return summary of created records
    """
    try:
        logger.info(f"Starting bulk creation of {len(request.get('records', []))} lab records for user {current_user.id}")
        
        # Import lab service
        from app.services.lab_document_analysis_service import LabDocumentAnalysisService
        lab_service = LabDocumentAnalysisService()
        
        # Create medical document record first
        medical_doc = await lab_service._create_medical_document(
            db=db,
            user_id=current_user.id,
            file_name=request.get('file_name', ''),
            s3_url=request.get('s3_url', ''),
            description=request.get('description'),
            lab_test_date=request.get('lab_test_date'),
            provider=request.get('provider'),
            document_type=request.get('document_type')
        )
        
        created_records = []
        updated_records = []
        created_sections = []
        created_metrics = []
        
        # Process each record
        for record_data in request.get('records', []):
            try:
                # Skip records with missing metric names
                metric_name = record_data.get('metric_name') or record_data.get('name_of_analysis')
                if not metric_name:
                    logger.warning(f"Skipping record with missing metric name: {record_data}")
                    continue
                
                # Get or create section
                section = await lab_service._get_or_create_section(
                    db=db,
                    user_id=current_user.id,
                    section_type=record_data.get('type_of_analysis')
                )
                
                if section.id not in [s.id for s in created_sections]:
                    created_sections.append(section)
                
                # Get or create metric
                metric_data = {
                    'metric_name': metric_name,
                    'unit': record_data.get('unit'),
                    'reference_range': record_data.get('reference') or record_data.get('reference_range'),
                    'value': record_data.get('value')
                }
                metric = await lab_service._get_or_create_metric(
                    db=db,
                    user_id=current_user.id,
                    section_id=section.id,
                    record_data=metric_data
                )
                
                if metric.id not in [m.id for m in created_metrics]:
                    created_metrics.append(metric)
                
                # Create health record
                from app.schemas.health_record import HealthRecordCreate
                from datetime import datetime
                
                # Convert value to float
                try:
                    value = float(record_data.get('value', 0))
                except (ValueError, TypeError):
                    value = 0.0
                
                # Parse date
                try:
                    date_str = record_data.get('date_of_value', '')
                    if date_str:
                        # Handle DD-MM-YYYY format
                        if '-' in date_str and len(date_str.split('-')[0]) == 2:
                            day, month, year = date_str.split('-')
                            recorded_at = datetime(int(year), int(month), int(day))
                        else:
                            recorded_at = datetime.now()
                    else:
                        recorded_at = datetime.now()
                except (ValueError, TypeError):
                    recorded_at = datetime.now()
                
                health_record_data = HealthRecordCreate(
                    section_id=section.id,
                    metric_id=metric.id,
                    value=value,
                    recorded_at=recorded_at,
                    source="lab_result",
                    status="normal"
                )
                
                health_record, was_created_new = health_record_crud.create(db, health_record_data, current_user.id)
                
                record_info = {
                    "id": health_record.id,
                    "section": section.name,
                    "metric": metric.name,
                    "value": record_data.get('value'),
                    "unit": record_data.get('unit')
                }
                
                if was_created_new:
                    created_records.append(record_info)
                else:
                    updated_records.append(record_info)
                
            except Exception as record_error:
                logger.error(f"Failed to create record for {record_data.get('metric_name')}: {record_error}")
                continue
        
        logger.info(f"Successfully processed {len(created_records)} new and {len(updated_records)} updated health records for user {current_user.id}")
        
        return {
            "success": True,
            "message": f"Successfully created {len(created_records)} new health records and updated {len(updated_records)} existing records",
            "medical_document_id": medical_doc.id if medical_doc else None,
            "created_records": created_records,
            "updated_records": updated_records,
            "created_sections_count": len(created_sections),
            "created_metrics_count": len(created_metrics),
            "summary": {
                "new_records": len(created_records),
                "updated_records": len(updated_records),
                "total_records": len(created_records) + len(updated_records),
                "sections_created": len(created_sections),
                "metrics_created": len(created_metrics)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to bulk create lab records: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk create lab records: {str(e)}"
        )

