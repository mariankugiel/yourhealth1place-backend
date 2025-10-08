from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.medication import MedicationStatus, MedicationType

class MedicationBase(BaseModel):
    medication_name: str
    medication_type: MedicationType = MedicationType.PRESCRIPTION
    status: MedicationStatus = MedicationStatus.ACTIVE
    start_date: datetime
    end_date: Optional[datetime] = None
    prescribed_by: int

class MedicationCreate(MedicationBase):
    pass

class MedicationUpdate(BaseModel):
    medication_name: Optional[str] = None
    medication_type: Optional[MedicationType] = None
    status: Optional[MedicationStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class MedicationResponse(MedicationBase):
    id: int
    patient_id: int
    aws_file_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 