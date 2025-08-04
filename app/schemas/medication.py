from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.medication import MedicationStatus, MedicationType

class MedicationBase(BaseModel):
    patient_id: int
    medication_name: str
    generic_name: Optional[str] = None
    medication_type: MedicationType = MedicationType.PRESCRIPTION
    dosage: str
    frequency: str
    route: Optional[str] = None
    strength: Optional[str] = None
    quantity: Optional[str] = None
    refills_remaining: int = 0
    start_date: datetime
    end_date: Optional[datetime] = None
    prescribed_date: datetime
    prescribed_by: int
    reason: Optional[str] = None
    side_effects: Optional[str] = None
    instructions: Optional[str] = None
    special_instructions: Optional[str] = None
    cost: Optional[float] = None
    insurance_coverage: bool = True
    requires_monitoring: bool = False
    contraindications: Optional[str] = None
    drug_interactions: Optional[str] = None

class MedicationCreate(MedicationBase):
    pass

class MedicationUpdate(BaseModel):
    medication_name: Optional[str] = None
    generic_name: Optional[str] = None
    medication_type: Optional[MedicationType] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    strength: Optional[str] = None
    quantity: Optional[str] = None
    refills_remaining: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[MedicationStatus] = None
    reason: Optional[str] = None
    side_effects: Optional[str] = None
    instructions: Optional[str] = None
    special_instructions: Optional[str] = None
    cost: Optional[float] = None
    insurance_coverage: Optional[bool] = None
    requires_monitoring: Optional[bool] = None
    contraindications: Optional[str] = None
    drug_interactions: Optional[str] = None

class MedicationResponse(MedicationBase):
    id: int
    status: MedicationStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 