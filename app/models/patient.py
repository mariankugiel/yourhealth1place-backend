from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    patient_id_number = Column(String(50), unique=True, index=True)
    insurance_provider = Column(String(100))
    insurance_policy_number = Column(String(100))
    primary_care_physician = Column(String(255))
    emergency_contact_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="patient")
    health_plan_assignments = relationship("HealthPlanAssignment", back_populates="patient")
    goal_tracking = relationship("GoalTracking", back_populates="patient")
    goal_tracking_details = relationship("GoalTrackingDetail", back_populates="patient")
    task_tracking = relationship("TaskTracking", back_populates="patient")
    task_tracking_details = relationship("TaskTrackingDetail", back_populates="patient") 