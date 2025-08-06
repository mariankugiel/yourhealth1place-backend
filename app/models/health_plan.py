from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class PlanStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PlanType(str, enum.Enum):
    TREATMENT = "treatment"
    PREVENTION = "prevention"
    REHABILITATION = "rehabilitation"
    EDUCATION = "education"

class HealthPlan(Base):
    __tablename__ = "health_plans"

    id = Column(Integer, primary_key=True, index=True)
    
    # Plan Information
    title = Column(String(200), nullable=False)
    description = Column(Text)
    plan_type = Column(Enum(PlanType), default=PlanType.TREATMENT)
    target_condition = Column(String(200))
    duration_weeks = Column(Integer)
    
    # Professional and Patient
    professional_id = Column(Integer, ForeignKey("professionals.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"))
    
    # Plan Details
    goals = Column(JSON)  # List of treatment goals
    milestones = Column(JSON)  # List of milestones with dates
    medications = Column(JSON)  # List of prescribed medications
    activities = Column(JSON)  # List of activities/exercises
    diet_restrictions = Column(JSON)  # Dietary guidelines
    follow_up_schedule = Column(JSON)  # Follow-up appointments
    
    # Status and Progress
    status = Column(Enum(PlanStatus), default=PlanStatus.DRAFT)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    progress_percentage = Column(Integer, default=0)
    
    # Monitoring
    monitoring_metrics = Column(JSON)  # What to track
    alert_thresholds = Column(JSON)  # When to alert professional
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    professional = relationship("Professional", back_populates="health_plans")
    patient = relationship("Patient", back_populates="health_plans")
    plan_progress = relationship("HealthPlanProgress", back_populates="health_plan")
    
    def __repr__(self):
        return f"<HealthPlan(id={self.id}, title='{self.title}', status='{self.status}')>" 