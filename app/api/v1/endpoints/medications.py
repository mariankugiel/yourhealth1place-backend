from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.user import User
from app.schemas.medication import MedicationCreate, MedicationUpdate, MedicationResponse, EndMedicationRequest
from app.api.v1.endpoints.auth import get_current_user
from app.crud.medication import medication_crud
from app.models.medication import MedicationStatus
from app.core.patient_access import check_patient_access
from app.utils.translation_helpers import apply_translations_to_medication
from app.utils.user_language import get_user_language_from_cache
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=MedicationResponse)
@router.post("", response_model=MedicationResponse)
async def create_medication(
    medication: MedicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new medication"""
    try:
        # Add current user as the patient_id and prescribed_by
        medication_data = medication.dict()
        medication_data['patient_id'] = current_user.id
        medication_data['prescribed_by'] = current_user.id
        
        # Get user's current language to save as source_language
        source_lang = await get_user_language_from_cache(current_user.id, db)
        medication_data['source_language'] = source_lang
        medication_data['version'] = 1
        
        created_medication = medication_crud.create(db, medication_data)
        
        # Convert to dict and apply translations
        medication_dict = {
            "id": created_medication.id,
            "patient_id": created_medication.patient_id,
            "medication_name": created_medication.medication_name,
            "medication_type": created_medication.medication_type,
            "dosage": created_medication.dosage,
            "frequency": created_medication.frequency,
            "purpose": created_medication.purpose,
            "instructions": created_medication.instructions,
            "rx_number": created_medication.rx_number,
            "pharmacy": created_medication.pharmacy,
            "original_quantity": created_medication.original_quantity,
            "refills_remaining": created_medication.refills_remaining,
            "last_filled_date": created_medication.last_filled_date.isoformat() if created_medication.last_filled_date else None,
            "status": created_medication.status,
            "start_date": created_medication.start_date.isoformat() if created_medication.start_date else None,
            "end_date": created_medication.end_date.isoformat() if created_medication.end_date else None,
            "reason_ended": created_medication.reason_ended,
            "prescribed_by": created_medication.prescribed_by,
            "created_at": created_medication.created_at.isoformat() if created_medication.created_at else None,
            "updated_at": created_medication.updated_at.isoformat() if created_medication.updated_at else None,
            "source_language": getattr(created_medication, 'source_language', 'en'),
            "version": getattr(created_medication, 'version', 1)
        }
        
        # Apply translations
        translated_medication = await apply_translations_to_medication(
            db, medication_dict, current_user.id
        )
        
        return MedicationResponse(**translated_medication)
    except Exception as e:
        logger.error(f"Failed to create medication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create medication: {str(e)}"
        )

@router.get("/", response_model=List[MedicationResponse])
@router.get("", response_model=List[MedicationResponse])
async def read_medications(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    patient_id: Optional[int] = Query(None, description="Patient ID to access (requires permission)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get medications for the current user or a specific patient (if permission granted)"""
    try:
        # Determine target user ID
        target_user_id = current_user.id
        
        if patient_id:
            # Check permissions
            has_access, error_message = await check_patient_access(
                db=db,
                patient_id=patient_id,
                current_user=current_user,
                permission_type="view_medications"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_message or "You do not have permission to access this patient's medications"
                )
            
            target_user_id = patient_id
        
        medications = medication_crud.get_by_patient(db, target_user_id)
        
        # Filter by status if provided
        if status_filter:
            if status_filter == "current":
                medications = [m for m in medications if m.status == MedicationStatus.ACTIVE]
            elif status_filter == "previous":
                medications = [m for m in medications if m.status != MedicationStatus.ACTIVE]
        
        # Apply pagination
        medications = medications[skip:skip + limit]
        
        # Convert to dictionaries and apply translations
        medication_list = []
        for med in medications:
            medication_dict = {
                "id": med.id,
                "patient_id": med.patient_id,
                "medication_name": med.medication_name,
                "medication_type": med.medication_type,
                "dosage": med.dosage,
                "frequency": med.frequency,
                "purpose": med.purpose,
                "instructions": med.instructions,
                "rx_number": med.rx_number,
                "pharmacy": med.pharmacy,
                "original_quantity": med.original_quantity,
                "refills_remaining": med.refills_remaining,
                "last_filled_date": med.last_filled_date.isoformat() if med.last_filled_date else None,
                "status": med.status,
                "start_date": med.start_date.isoformat() if med.start_date else None,
                "end_date": med.end_date.isoformat() if med.end_date else None,
                "reason_ended": med.reason_ended,
                "prescribed_by": med.prescribed_by,
                "created_at": med.created_at.isoformat() if med.created_at else None,
                "updated_at": med.updated_at.isoformat() if med.updated_at else None,
                "source_language": getattr(med, 'source_language', 'en'),
                "version": getattr(med, 'version', 1)
            }
            
            # Apply translations
            translated_medication = await apply_translations_to_medication(
                db, medication_dict, target_user_id
            )
            medication_list.append(MedicationResponse(**translated_medication))
        
        return medication_list
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get medications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get medications: {str(e)}"
        )

@router.get("/{medication_id}", response_model=MedicationResponse)
async def read_medication(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get medication by ID"""
    try:
        medication = medication_crud.get_by_id(db, medication_id)
        if not medication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medication not found"
            )
        
        # Check if user owns this medication
        if medication.patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Convert to dict and apply translations
        medication_dict = {
            "id": medication.id,
            "patient_id": medication.patient_id,
            "medication_name": medication.medication_name,
            "medication_type": medication.medication_type,
            "dosage": medication.dosage,
            "frequency": medication.frequency,
            "purpose": medication.purpose,
            "instructions": medication.instructions,
            "rx_number": medication.rx_number,
            "pharmacy": medication.pharmacy,
            "original_quantity": medication.original_quantity,
            "refills_remaining": medication.refills_remaining,
            "last_filled_date": medication.last_filled_date.isoformat() if medication.last_filled_date else None,
            "status": medication.status,
            "start_date": medication.start_date.isoformat() if medication.start_date else None,
            "end_date": medication.end_date.isoformat() if medication.end_date else None,
            "reason_ended": medication.reason_ended,
            "prescribed_by": medication.prescribed_by,
            "created_at": medication.created_at.isoformat() if medication.created_at else None,
            "updated_at": medication.updated_at.isoformat() if medication.updated_at else None,
            "source_language": getattr(medication, 'source_language', 'en'),
            "version": getattr(medication, 'version', 1)
        }
        
        # Apply translations
        translated_medication = await apply_translations_to_medication(
            db, medication_dict, current_user.id
        )
        
        return MedicationResponse(**translated_medication)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get medication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get medication: {str(e)}"
        )

@router.put("/{medication_id}", response_model=MedicationResponse)
async def update_medication(
    medication_id: int,
    medication_data: MedicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update medication"""
    try:
        medication = medication_crud.get_by_id(db, medication_id)
        if not medication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medication not found"
            )
        
        # Check if user owns this medication
        if medication.patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        update_dict = medication_data.dict(exclude_unset=True)
        # Increment version if translatable fields are updated
        if any(field in update_dict for field in ['medication_name', 'purpose', 'instructions']):
            current_version = getattr(medication, 'version', 1)
            update_dict['version'] = current_version + 1
        
        updated_medication = medication_crud.update(db, medication_id, update_dict)
        
        # Convert to dict and apply translations
        medication_dict = {
            "id": updated_medication.id,
            "patient_id": updated_medication.patient_id,
            "medication_name": updated_medication.medication_name,
            "medication_type": updated_medication.medication_type,
            "dosage": updated_medication.dosage,
            "frequency": updated_medication.frequency,
            "purpose": updated_medication.purpose,
            "instructions": updated_medication.instructions,
            "rx_number": updated_medication.rx_number,
            "pharmacy": updated_medication.pharmacy,
            "original_quantity": updated_medication.original_quantity,
            "refills_remaining": updated_medication.refills_remaining,
            "last_filled_date": updated_medication.last_filled_date.isoformat() if updated_medication.last_filled_date else None,
            "status": updated_medication.status,
            "start_date": updated_medication.start_date.isoformat() if updated_medication.start_date else None,
            "end_date": updated_medication.end_date.isoformat() if updated_medication.end_date else None,
            "reason_ended": updated_medication.reason_ended,
            "prescribed_by": updated_medication.prescribed_by,
            "created_at": updated_medication.created_at.isoformat() if updated_medication.created_at else None,
            "updated_at": updated_medication.updated_at.isoformat() if updated_medication.updated_at else None,
            "source_language": getattr(updated_medication, 'source_language', 'en'),
            "version": getattr(updated_medication, 'version', 1)
        }
        
        # Apply translations
        translated_medication = await apply_translations_to_medication(
            db, medication_dict, current_user.id
        )
        
        return MedicationResponse(**translated_medication)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update medication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update medication: {str(e)}"
        )

@router.delete("/{medication_id}")
def delete_medication(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete medication"""
    try:
        medication = medication_crud.get_by_id(db, medication_id)
        if not medication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medication not found"
            )
        
        # Check if user owns this medication
        if medication.patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        success = medication_crud.delete(db, medication_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete medication"
            )
        
        return {"message": "Medication deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete medication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete medication: {str(e)}"
        )

@router.patch("/{medication_id}/end")
def end_medication(
    medication_id: int,
    end_request: EndMedicationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """End a medication (set status to discontinued with optional reason)"""
    try:
        medication = medication_crud.get_by_id(db, medication_id)
        if not medication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medication not found"
            )
        
        # Check if user owns this medication
        if medication.patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        from datetime import date
        
        # Update status to discontinued with optional reason and set end_date
        update_data = {
            "status": MedicationStatus.DISCONTINUED,
            "end_date": date.today()
        }
        
        if end_request.reason:
            update_data["reason_ended"] = end_request.reason
        
        updated_medication = medication_crud.update(db, medication_id, update_data)
        
        return {"message": "Medication ended successfully", "medication": MedicationResponse.from_orm(updated_medication)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end medication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end medication: {str(e)}"
        ) 