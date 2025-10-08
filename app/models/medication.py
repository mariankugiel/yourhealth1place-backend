from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class MedicationStatus(str, enum.Enum):
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"

class MedicationType(str, enum.Enum):
    PRESCRIPTION = "prescription"
    OVER_THE_COUNTER = "over_the_counter"
    SUPPLEMENT = "supplement"
    VACCINE = "vaccine"

class Medication(Base):
    __tablename__ = "medications"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Basic metadata only - sensitive data stored in AWS S3
    medication_name = Column(String(255), nullable=False)
    medication_type = Column(Enum(MedicationType), default=MedicationType.PRESCRIPTION)
    
    # AWS S3 file reference
    aws_file_id = Column(String(255), unique=True, index=True, nullable=False)
    
    # Non-sensitive metadata
    status = Column(Enum(MedicationStatus), default=MedicationStatus.ACTIVE)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    
    # Audit fields
    prescribed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], backref="medications")
    prescriber = relationship("User", foreign_keys=[prescribed_by], backref="prescribed_medications")
    
    def __repr__(self):
        return f"<Medication(id={self.id}, name='{self.medication_name}', patient_id={self.patient_id}, aws_file_id='{self.aws_file_id}')>" 