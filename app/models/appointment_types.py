from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class AppointmentType(Base):
    __tablename__ = "appointment_types"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    duration_minutes = Column(Integer, nullable=False)  # Duration in minutes
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Professional who created this type
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    pricing = relationship("AppointmentTypePricing", back_populates="appointment_type")
    slots = relationship("ProfessionalAppointmentSlot", back_populates="appointment_type")

class AppointmentTypePricing(Base):
    __tablename__ = "appointment_type_pricing"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    appointment_type_id = Column(Integer, ForeignKey("appointment_types.id"), nullable=False)
    professional_id = Column(Integer, ForeignKey("professionals.id"), nullable=False)
    
    # Pricing Details
    consultation_type = Column(String(50), nullable=False)  # "in_person", "virtual", "phone"
    fee_type = Column(String(50), nullable=False)  # "first_consultation", "follow_up", "emergency", "routine_checkup"
    base_fee = Column(Numeric(10, 2), nullable=False)  # Base consultation fee
    currency = Column(String(3), nullable=False, default="USD")
    
    # Additional Charges
    additional_fees = Column(JSON)  # {"after_hours": 50, "weekend": 75, "holiday": 100}
    
    # Insurance
    accepts_insurance = Column(Boolean, default=True)
    insurance_codes = Column(JSON)  # ["CPT_99213", "CPT_99214"]
    
    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)  # Default pricing for this type
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    appointment_type = relationship("AppointmentType", back_populates="pricing")
    professional = relationship("Professional", backref="pricing") 