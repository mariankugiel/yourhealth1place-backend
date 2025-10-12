from sqlalchemy import Column, Integer, String, DateTime, Date, Text, ForeignKey, Boolean, Enum
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
    
    # Basic metadata
    medication_name = Column(String(255), nullable=False)
    medication_type = Column(Enum(MedicationType), default=MedicationType.PRESCRIPTION)
    dosage = Column(String(100), nullable=True)
    frequency = Column(String(100), nullable=True)
    purpose = Column(String(500), nullable=True)
    instructions = Column(Text, nullable=True)
    
    # Prescription information (5 fields only)
    rx_number = Column(String(100), nullable=True)
    pharmacy = Column(String(255), nullable=True)
    original_quantity = Column(Integer, nullable=True)
    refills_remaining = Column(Integer, nullable=True)
    last_filled_date = Column(Date, nullable=True)
    
    # Medication metadata
    status = Column(Enum(MedicationStatus), default=MedicationStatus.ACTIVE)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    reason_ended = Column(Text, nullable=True)
    
    # Audit fields
    prescribed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], backref="medications")
    prescriber = relationship("User", foreign_keys=[prescribed_by], backref="prescribed_medications")
    
    def __repr__(self):
        return f"<Medication(id={self.id}, name='{self.medication_name}', patient_id={self.patient_id})>" 