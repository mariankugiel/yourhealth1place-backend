from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class HealthRecordBase(BaseModel):
    patient_id: int
    record_date: datetime
    record_type: str  # vital_signs, lab_results, imaging, etc.
    
    # Vital Signs
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    temperature: Optional[float] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    bmi: Optional[float] = None
    
    # Lab Results
    glucose_level: Optional[float] = None
    cholesterol_total: Optional[float] = None
    cholesterol_hdl: Optional[float] = None
    cholesterol_ldl: Optional[float] = None
    triglycerides: Optional[float] = None
    hemoglobin: Optional[float] = None
    white_blood_cells: Optional[float] = None
    platelets: Optional[float] = None
    
    # Additional Data
    notes: Optional[str] = None
    doctor_notes: Optional[str] = None
    is_abnormal: bool = False
    requires_follow_up: bool = False

class HealthRecordCreate(HealthRecordBase):
    recorded_by: Optional[int] = None

class HealthRecordUpdate(BaseModel):
    record_date: Optional[datetime] = None
    record_type: Optional[str] = None
    
    # Vital Signs
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    temperature: Optional[float] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    bmi: Optional[float] = None
    
    # Lab Results
    glucose_level: Optional[float] = None
    cholesterol_total: Optional[float] = None
    cholesterol_hdl: Optional[float] = None
    cholesterol_ldl: Optional[float] = None
    triglycerides: Optional[float] = None
    hemoglobin: Optional[float] = None
    white_blood_cells: Optional[float] = None
    platelets: Optional[float] = None
    
    # Additional Data
    notes: Optional[str] = None
    doctor_notes: Optional[str] = None
    is_abnormal: Optional[bool] = None
    requires_follow_up: Optional[bool] = None

class HealthRecordResponse(HealthRecordBase):
    id: int
    recorded_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 