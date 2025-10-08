from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from app.models.surgery_hospitalization import ProcedureType, RecoveryStatus

class SurgeryHospitalizationBase(BaseModel):
    procedure_type: ProcedureType = Field(..., description="Type of procedure: surgery or hospitalization")
    name: str = Field(..., description="Name of the surgery or hospitalization")
    procedure_date: date = Field(..., description="Date when the procedure occurred")
    reason: Optional[str] = Field(None, description="Reason for the procedure")
    treatment: Optional[str] = Field(None, description="Treatment received")
    body_area: Optional[str] = Field(None, description="Body area affected")
    recovery_status: RecoveryStatus = Field(RecoveryStatus.FULL_RECOVERY, description="Current recovery status")
    notes: Optional[str] = Field(None, description="Additional notes about the procedure")

class SurgeryHospitalizationCreate(SurgeryHospitalizationBase):
    pass

class SurgeryHospitalizationUpdate(BaseModel):
    procedure_type: Optional[ProcedureType] = None
    name: Optional[str] = None
    procedure_date: Optional[date] = None
    reason: Optional[str] = None
    treatment: Optional[str] = None
    body_area: Optional[str] = None
    recovery_status: Optional[RecoveryStatus] = None
    notes: Optional[str] = None

class SurgeryHospitalizationResponse(SurgeryHospitalizationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: int
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

class SurgeryHospitalizationListResponse(BaseModel):
    surgeries: List[SurgeryHospitalizationResponse]
    total: int
    skip: int
    limit: int
