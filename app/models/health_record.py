from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class HealthRecord(Base):
    __tablename__ = "health_records"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    # Metadata only - sensitive data stored in AWS DynamoDB
    record_date = Column(DateTime, nullable=False)
    record_type = Column(String(50), nullable=False)  # vital_signs, lab_results, imaging, etc.
    
    # AWS DynamoDB record reference
    dynamodb_record_id = Column(String(255), unique=True, index=True, nullable=False)
    
    # Non-sensitive metadata
    is_abnormal = Column(Boolean, default=False)
    requires_follow_up = Column(Boolean, default=False)
    
    # Audit fields
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient")
    recorder = relationship("User", foreign_keys=[recorded_by])
    
    def __repr__(self):
        return f"<HealthRecord(id={self.id}, patient_id={self.patient_id}, type='{self.record_type}', dynamodb_record_id='{self.dynamodb_record_id}')>" 