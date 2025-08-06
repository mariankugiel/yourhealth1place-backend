from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class PlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PlanType(str, Enum):
    TREATMENT = "treatment"
    PREVENTION = "prevention"
    REHABILITATION = "rehabilitation"
    EDUCATION = "education"

class HealthPlanBase(BaseModel):
    title: str
    description: Optional[str] = None
    plan_type: PlanType = PlanType.TREATMENT
    target_condition: Optional[str] = None
    duration_weeks: Optional[int] = None
    goals: Optional[List[Dict[str, Any]]] = None
    milestones: Optional[List[Dict[str, Any]]] = None
    medications: Optional[List[Dict[str, Any]]] = None
    activities: Optional[List[Dict[str, Any]]] = None
    diet_restrictions: Optional[List[str]] = None
    follow_up_schedule: Optional[List[Dict[str, Any]]] = None
    monitoring_metrics: Optional[List[str]] = None
    alert_thresholds: Optional[Dict[str, Any]] = None

class HealthPlanCreate(HealthPlanBase):
    professional_id: int
    patient_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class HealthPlanUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    plan_type: Optional[PlanType] = None
    target_condition: Optional[str] = None
    duration_weeks: Optional[int] = None
    goals: Optional[List[Dict[str, Any]]] = None
    milestones: Optional[List[Dict[str, Any]]] = None
    medications: Optional[List[Dict[str, Any]]] = None
    activities: Optional[List[Dict[str, Any]]] = None
    diet_restrictions: Optional[List[str]] = None
    follow_up_schedule: Optional[List[Dict[str, Any]]] = None
    status: Optional[PlanStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    progress_percentage: Optional[int] = None
    monitoring_metrics: Optional[List[str]] = None
    alert_thresholds: Optional[Dict[str, Any]] = None

class HealthPlan(HealthPlanBase):
    id: int
    professional_id: int
    patient_id: int
    status: PlanStatus = PlanStatus.DRAFT
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    progress_percentage: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class HealthPlanWithRelations(HealthPlan):
    professional: Optional[Dict[str, Any]] = None
    patient: Optional[Dict[str, Any]] = None
    plan_progress: Optional[List[Dict[str, Any]]] = None

class HealthPlanList(BaseModel):
    health_plans: List[HealthPlan]
    total: int
    page: int
    size: int 