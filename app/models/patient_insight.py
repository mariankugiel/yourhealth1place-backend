from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class InsightType(str, enum.Enum):
    ALERT = "alert"
    URGENT = "urgent"
    NORMAL = "normal"
    IMPROVEMENT = "improvement"
    TREND = "trend"

class InsightCategory(str, enum.Enum):
    VITAL_SIGNS = "vital_signs"
    MEDICATION = "medication"
    SYMPTOMS = "symptoms"
    LAB_RESULTS = "lab_results"
    ACTIVITY = "activity"
    DIET = "diet"
    SLEEP = "sleep"

class PatientInsight(Base):
    __tablename__ = "patient_insights"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"))
    professional_id = Column(Integer, ForeignKey("users.id"))
    
    # Insight Information
    insight_type = Column(Enum(InsightType), nullable=False)
    category = Column(Enum(InsightCategory), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Data Source
    source_data = Column(JSON)  # Raw data that triggered the insight
    metrics = Column(JSON)  # Relevant measurements
    thresholds = Column(JSON)  # Thresholds that were exceeded
    
    # Status
    is_read = Column(Boolean, default=False)
    is_acknowledged = Column(Boolean, default=False)
    requires_action = Column(Boolean, default=False)
    action_taken = Column(Text)
    
    # Severity and Priority
    severity_level = Column(Integer)  # 1-5 scale
    priority = Column(String(50))  # low, medium, high, critical
    
    # Related Records
    related_health_record_id = Column(Integer, ForeignKey("health_records.id"))
    related_appointment_id = Column(Integer, ForeignKey("appointments.id"))
    
    # Dates
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], backref="insights")
    professional = relationship("User", foreign_keys=[professional_id], backref="professional_insights")
    related_health_record = relationship("HealthRecord")
    related_appointment = relationship("Appointment")
    
    def __repr__(self):
        return f"<PatientInsight(id={self.id}, type='{self.insight_type}', title='{self.title}')>" 