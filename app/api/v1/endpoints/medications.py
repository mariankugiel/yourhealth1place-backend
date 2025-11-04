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
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=MedicationResponse)
def create_medication(
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
        
        created_medication = medication_crud.create(db, medication_data)
        return MedicationResponse.from_orm(created_medication)
    except Exception as e:
        logger.error(f"Failed to create medication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create medication: {str(e)}"
        )

@router.get("/", response_model=List[MedicationResponse])
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
        
        return [MedicationResponse.from_orm(med) for med in medications]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get medications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get medications: {str(e)}"
        )

@router.get("/{medication_id}", response_model=MedicationResponse)
def read_medication(
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
        
        return MedicationResponse.from_orm(medication)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get medication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get medication: {str(e)}"
        )

@router.put("/{medication_id}", response_model=MedicationResponse)
def update_medication(
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
        
        updated_medication = medication_crud.update(db, medication_id, medication_data.dict(exclude_unset=True))
        return MedicationResponse.from_orm(updated_medication)
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