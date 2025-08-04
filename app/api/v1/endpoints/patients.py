from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from app.crud.patient import get_patients, get_patient, create_patient, update_patient, delete_patient, get_patient_by_user_id
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=PatientResponse)
def create_patient_profile(
    patient: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new patient profile"""
    if current_user.role != "admin" and current_user.id != patient.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Check if patient already exists for this user
    existing_patient = get_patient_by_user_id(db, patient.user_id)
    if existing_patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient profile already exists for this user"
        )
    
    return create_patient(db=db, patient=patient)

@router.get("/", response_model=List[PatientResponse])
def read_patients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all patients (admin/doctor only)"""
    if current_user.role not in ["admin", "doctor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    patients = get_patients(db, skip=skip, limit=limit)
    return patients

@router.get("/{patient_id}", response_model=PatientResponse)
def read_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get patient by ID"""
    patient = get_patient(db, patient_id=patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Check permissions
    if current_user.role not in ["admin", "doctor"] and patient.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return patient

@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient_profile(
    patient_id: int,
    patient_data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update patient profile"""
    patient = get_patient(db, patient_id=patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Check permissions
    if current_user.role not in ["admin", "doctor"] and patient.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    updated_patient = update_patient(db, patient_id=patient_id, patient_data=patient_data.dict(exclude_unset=True))
    return updated_patient

@router.delete("/{patient_id}")
def delete_patient_profile(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete patient profile (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    success = delete_patient(db, patient_id=patient_id)
    if not success:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"message": "Patient profile deleted successfully"}

@router.get("/me/profile", response_model=PatientResponse)
def read_my_patient_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's patient profile"""
    if current_user.role != "patient":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a patient"
        )
    
    patient = get_patient_by_user_id(db, current_user.id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    return patient 