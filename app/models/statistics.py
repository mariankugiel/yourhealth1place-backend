from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class ProfessionalStatistics(Base):
    __tablename__ = "professional_statistics"

    id = Column(Integer, primary_key=True, index=True)
    professional_id = Column(Integer, ForeignKey("professionals.id"))
    
    # Time Period
    period_type = Column(String(50))  # daily, weekly, monthly, yearly
    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))
    
    # Appointment Statistics
    total_appointments = Column(Integer, default=0)
    completed_appointments = Column(Integer, default=0)
    cancelled_appointments = Column(Integer, default=0)
    rescheduled_appointments = Column(Integer, default=0)
    no_show_appointments = Column(Integer, default=0)
    
    # Patient Statistics
    total_patients = Column(Integer, default=0)
    new_patients = Column(Integer, default=0)
    returning_patients = Column(Integer, default=0)
    active_patients = Column(Integer, default=0)
    
    # Consultation Types
    physical_consultations = Column(Integer, default=0)
    video_consultations = Column(Integer, default=0)
    phone_consultations = Column(Integer, default=0)
    
    # Financial Statistics
    total_revenue = Column(Float, default=0.0)
    consultation_revenue = Column(Float, default=0.0)
    plan_revenue = Column(Float, default=0.0)
    average_consultation_fee = Column(Float, default=0.0)
    
    # Health Plan Statistics
    active_health_plans = Column(Integer, default=0)
    completed_health_plans = Column(Integer, default=0)
    average_plan_duration = Column(Float, default=0.0)
    
    # Patient Demographics
    patient_age_distribution = Column(JSON)  # Age groups and counts
    patient_gender_distribution = Column(JSON)  # Gender distribution
    patient_condition_distribution = Column(JSON)  # Condition types
    
    # Performance Metrics
    average_consultation_duration = Column(Float, default=0.0)
    patient_satisfaction_score = Column(Float, default=0.0)
    treatment_success_rate = Column(Float, default=0.0)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    professional = relationship("Professional")
    
    def __repr__(self):
        return f"<ProfessionalStatistics(id={self.id}, professional_id={self.professional_id}, period='{self.period_type}')>" 