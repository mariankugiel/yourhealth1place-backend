from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ProfessionalStatisticsBase(BaseModel):
    period_type: str
    period_start: datetime
    period_end: datetime
    total_appointments: int = 0
    completed_appointments: int = 0
    cancelled_appointments: int = 0
    rescheduled_appointments: int = 0
    no_show_appointments: int = 0
    total_patients: int = 0
    new_patients: int = 0
    returning_patients: int = 0
    active_patients: int = 0
    physical_consultations: int = 0
    video_consultations: int = 0
    phone_consultations: int = 0
    total_revenue: float = 0.0
    consultation_revenue: float = 0.0
    plan_revenue: float = 0.0
    average_consultation_fee: float = 0.0
    active_health_plans: int = 0
    completed_health_plans: int = 0
    average_plan_duration: float = 0.0
    patient_age_distribution: Optional[Dict[str, Any]] = None
    patient_gender_distribution: Optional[Dict[str, Any]] = None
    patient_condition_distribution: Optional[Dict[str, Any]] = None
    average_consultation_duration: float = 0.0
    patient_satisfaction_score: float = 0.0
    treatment_success_rate: float = 0.0

class ProfessionalStatisticsCreate(ProfessionalStatisticsBase):
    professional_id: int

class ProfessionalStatisticsUpdate(BaseModel):
    period_type: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    total_appointments: Optional[int] = None
    completed_appointments: Optional[int] = None
    cancelled_appointments: Optional[int] = None
    rescheduled_appointments: Optional[int] = None
    no_show_appointments: Optional[int] = None
    total_patients: Optional[int] = None
    new_patients: Optional[int] = None
    returning_patients: Optional[int] = None
    active_patients: Optional[int] = None
    physical_consultations: Optional[int] = None
    video_consultations: Optional[int] = None
    phone_consultations: Optional[int] = None
    total_revenue: Optional[float] = None
    consultation_revenue: Optional[float] = None
    plan_revenue: Optional[float] = None
    average_consultation_fee: Optional[float] = None
    active_health_plans: Optional[int] = None
    completed_health_plans: Optional[int] = None
    average_plan_duration: Optional[float] = None
    patient_age_distribution: Optional[Dict[str, Any]] = None
    patient_gender_distribution: Optional[Dict[str, Any]] = None
    patient_condition_distribution: Optional[Dict[str, Any]] = None
    average_consultation_duration: Optional[float] = None
    patient_satisfaction_score: Optional[float] = None
    treatment_success_rate: Optional[float] = None

class ProfessionalStatistics(ProfessionalStatisticsBase):
    id: int
    professional_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProfessionalStatisticsWithRelations(ProfessionalStatistics):
    professional: Optional[Dict[str, Any]] = None

class ProfessionalStatisticsList(BaseModel):
    statistics: List[ProfessionalStatistics]
    total: int
    page: int
    size: int

class DashboardStatistics(BaseModel):
    today_appointments: int
    upcoming_appointments: int
    total_patients: int
    active_health_plans: int
    pending_insights: int
    monthly_revenue: float
    patient_satisfaction: float
    consultation_completion_rate: float 