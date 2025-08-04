from sqlalchemy.orm import Session
from app.models.patient import Patient
from app.schemas.patient import PatientCreate
from typing import Optional, List

def get_patient(db: Session, patient_id: int) -> Optional[Patient]:
    """Get patient by ID"""
    return db.query(Patient).filter(Patient.id == patient_id).first()

def get_patient_by_user_id(db: Session, user_id: int) -> Optional[Patient]:
    """Get patient by user ID"""
    return db.query(Patient).filter(Patient.user_id == user_id).first()

def get_patient_by_mrn(db: Session, medical_record_number: str) -> Optional[Patient]:
    """Get patient by medical record number"""
    return db.query(Patient).filter(Patient.medical_record_number == medical_record_number).first()

def get_patients(db: Session, skip: int = 0, limit: int = 100) -> List[Patient]:
    """Get all patients with pagination"""
    return db.query(Patient).offset(skip).limit(limit).all()

def create_patient(db: Session, patient: PatientCreate) -> Patient:
    """Create a new patient"""
    db_patient = Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

def update_patient(db: Session, patient_id: int, patient_data: dict) -> Optional[Patient]:
    """Update patient information"""
    db_patient = get_patient(db, patient_id)
    if not db_patient:
        return None
    
    for field, value in patient_data.items():
        if value is not None:
            setattr(db_patient, field, value)
    
    db.commit()
    db.refresh(db_patient)
    return db_patient

def delete_patient(db: Session, patient_id: int) -> bool:
    """Delete a patient"""
    db_patient = get_patient(db, patient_id)
    if not db_patient:
        return False
    
    db.delete(db_patient)
    db.commit()
    return True

def get_active_patients(db: Session, skip: int = 0, limit: int = 100) -> List[Patient]:
    """Get all active patients"""
    return db.query(Patient).filter(Patient.is_active == True).offset(skip).limit(limit).all() 