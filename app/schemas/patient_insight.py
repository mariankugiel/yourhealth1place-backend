from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class InsightType(str, Enum):
    ALERT = "alert"
    URGENT = "urgent"
    NORMAL = "normal"
    IMPROVEMENT = "improvement"
    TREND = "trend"

class InsightCategory(str, Enum):
    VITAL_SIGNS = "vital_signs"
    MEDICATION = "medication"
    SYMPTOMS = "symptoms"
    LAB_RESULTS = "lab_results"
    ACTIVITY = "activity"
    DIET = "diet"
    SLEEP = "sleep"

class PatientInsightBase(BaseModel):
    insight_type: InsightType
    category: InsightCategory
    title: str
    message: str
    source_data: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    thresholds: Optional[Dict[str, Any]] = None
    severity_level: Optional[int] = None
    priority: Optional[str] = None
    requires_action: bool = False

class PatientInsightCreate(PatientInsightBase):
    patient_id: int
    professional_id: int
    related_health_record_id: Optional[int] = None
    related_appointment_id: Optional[int] = None

class PatientInsightUpdate(BaseModel):
    insight_type: Optional[InsightType] = None
    category: Optional[InsightCategory] = None
    title: Optional[str] = None
    message: Optional[str] = None
    source_data: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    thresholds: Optional[Dict[str, Any]] = None
    is_read: Optional[bool] = None
    is_acknowledged: Optional[bool] = None
    requires_action: Optional[bool] = None
    action_taken: Optional[str] = None
    severity_level: Optional[int] = None
    priority: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

class PatientInsight(PatientInsightBase):
    id: int
    patient_id: int
    professional_id: int
    is_read: bool = False
    is_acknowledged: bool = False
    action_taken: Optional[str] = None
    related_health_record_id: Optional[int] = None
    related_appointment_id: Optional[int] = None
    detected_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PatientInsightWithRelations(PatientInsight):
    patient: Optional[Dict[str, Any]] = None
    professional: Optional[Dict[str, Any]] = None
    related_health_record: Optional[Dict[str, Any]] = None
    related_appointment: Optional[Dict[str, Any]] = None

class PatientInsightList(BaseModel):
    insights: List[PatientInsight]
    total: int
    page: int
    size: int 