from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class MedicalConditionUpdate(Base):
    __tablename__ = "medical_condition_updates"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    
    # Condition Details
    condition_id = Column(Integer, ForeignKey("medical_conditions.id"), nullable=False)  # Link to existing condition
    action = Column(String(50), nullable=False)  # "update", "add", "resolve", "reactivate"
    previous_status = Column(String(50))  # Previous status of the condition
    new_status = Column(String(50), nullable=False)  # New status after appointment
    
    # Update Details
    severity_change = Column(String(50))  # "increased", "decreased", "unchanged"
    new_severity = Column(String(50))  # "MILD", "MODERATE", "SEVERE"
    
    # Treatment Impact
    treatment_plan_updated = Column(Boolean, default=False)
    medication_changes = Column(JSON)  # Array of medication changes
    # Example: [{"medication": "Aspirin", "action": "added", "dosage": "100mg daily"}]
    
    # Notes
    update_notes = Column(Text)  # Professional's notes about this update
    patient_notes = Column(Text)  # Patient's notes about this update
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Professional who made the update
    
    # Relationships
    appointment = relationship("Appointment", backref="medical_condition_updates")
    condition = relationship("MedicalCondition", backref="updates")
    created_by_user = relationship("User", foreign_keys=[created_by]) 