from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime, date
from app.models.medication import MedicationStatus, MedicationType

class EndMedicationRequest(BaseModel):
    reason: Optional[str] = None

class MedicationBase(BaseModel):
    medication_name: str
    medication_type: MedicationType = MedicationType.PRESCRIPTION
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    purpose: Optional[str] = None
    instructions: Optional[str] = None
    # Prescription information (5 fields only)
    rx_number: Optional[str] = None
    pharmacy: Optional[str] = None
    original_quantity: Optional[int] = None
    refills_remaining: Optional[int] = None
    last_filled_date: Optional[date] = None
    status: MedicationStatus = MedicationStatus.ACTIVE
    start_date: date
    end_date: Optional[date] = None
    reason_ended: Optional[str] = None
    prescribed_by: Optional[int] = None
    
    @field_validator('start_date', 'end_date', 'last_filled_date', mode='before')
    @classmethod
    def parse_date(cls, value):
        """Parse date strings from frontend (YYYY-MM-DD) to date"""
        if value is None:
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            # Handle date string (YYYY-MM-DD)
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError(f"Invalid date format: {value}. Expected YYYY-MM-DD")
        return value

class MedicationCreate(MedicationBase):
    pass

class MedicationUpdate(BaseModel):
    medication_name: Optional[str] = None
    medication_type: Optional[MedicationType] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    purpose: Optional[str] = None
    instructions: Optional[str] = None
    # Prescription information (5 fields only)
    rx_number: Optional[str] = None
    pharmacy: Optional[str] = None
    original_quantity: Optional[int] = None
    refills_remaining: Optional[int] = None
    last_filled_date: Optional[date] = None
    status: Optional[MedicationStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reason_ended: Optional[str] = None
    
    @field_validator('start_date', 'end_date', 'last_filled_date', mode='before')
    @classmethod
    def parse_date(cls, value):
        """Parse date strings from frontend (YYYY-MM-DD) to date"""
        if value is None:
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            # Handle date string (YYYY-MM-DD)
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError(f"Invalid date format: {value}. Expected YYYY-MM-DD")
        return value

class MedicationResponse(BaseModel):
    id: int
    patient_id: int
    medication_name: str
    medication_type: MedicationType
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    purpose: Optional[str] = None
    instructions: Optional[str] = None
    # Prescription information (5 fields only)
    rx_number: Optional[str] = None
    pharmacy: Optional[str] = None
    original_quantity: Optional[int] = None
    refills_remaining: Optional[int] = None
    last_filled_date: Optional[date] = None
    status: MedicationStatus
    start_date: date
    end_date: Optional[date] = None
    reason_ended: Optional[str] = None
    prescribed_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 