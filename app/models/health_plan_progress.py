from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class ProgressStatus(str, enum.Enum):
    ON_TRACK = "on_track"
    BEHIND = "behind"
    COMPLETED = "completed"
    NEEDS_ATTENTION = "needs_attention"

class HealthPlanProgress(Base):
    __tablename__ = "health_plan_progress"

    id = Column(Integer, primary_key=True, index=True)
    health_plan_id = Column(Integer, ForeignKey("health_plans.id"))
    
    # Progress Information
    milestone_id = Column(String(100))  # Reference to milestone in plan
    status = Column(Enum(ProgressStatus), default=ProgressStatus.ON_TRACK)
    completion_percentage = Column(Integer, default=0)
    
    # Patient Input
    patient_notes = Column(Text)
    patient_rating = Column(Integer)  # 1-10 scale
    adherence_score = Column(Integer)  # 0-100 percentage
    
    # Metrics
    recorded_metrics = Column(JSON)  # Actual measurements
    target_metrics = Column(JSON)  # Expected values
    
    # Professional Review
    professional_notes = Column(Text)
    professional_rating = Column(Integer)  # 1-10 scale
    needs_follow_up = Column(Boolean, default=False)
    
    # Dates
    due_date = Column(DateTime(timezone=True))
    completed_date = Column(DateTime(timezone=True))
    reviewed_date = Column(DateTime(timezone=True))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    health_plan = relationship("HealthPlan", back_populates="plan_progress")
    
    def __repr__(self):
        return f"<HealthPlanProgress(id={self.id}, status='{self.status}', completion='{self.completion_percentage}%')>" 