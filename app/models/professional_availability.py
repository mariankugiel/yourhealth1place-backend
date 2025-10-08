from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class ProfessionalAvailabilitySchedule(Base):
    __tablename__ = "professional_availability_schedules"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    professional_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("professional_locations.id"), nullable=False)
    
    # Schedule Type
    schedule_type = Column(String(50), nullable=False)  # "regular_hours", "blocked_period", "specific_date"
    
    # Consultation Type
    consultation_type = Column(String(50), nullable=False)  # "in_person", "virtual", "both", "phone"
    
    # Flexible Schedule Data
    schedule_data = Column(JSON, nullable=False)  # Store all schedule information in JSON
    
    # Timezone
    timezone = Column(String(50), nullable=False, default="UTC")
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    professional = relationship("User", foreign_keys=[professional_id], backref="availability_schedules")
    location = relationship("ProfessionalLocation", back_populates="availability_schedules")

class ProfessionalAppointmentSlot(Base):
    __tablename__ = "professional_appointment_slots"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    professional_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("professional_locations.id"), nullable=False)
    appointment_type_id = Column(Integer, ForeignKey("appointment_types.id"), nullable=False)
    
    # Slot Details
    slot_date = Column(DateTime, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    
    # Consultation Type
    consultation_type = Column(String(50), nullable=False)  # "in_person", "virtual", "phone"
    
    # Slot Status
    status = Column(String(50), nullable=False, default="AVAILABLE")  # "AVAILABLE", "BOOKED", "BLOCKED", "PAST"
    
    # Booking Info
    appointment_id = Column(Integer, ForeignKey("appointments.id"))  # If booked, link to appointment
    
    # Auto-generated flag
    is_auto_generated = Column(Boolean, default=True)  # true = generated from availability, false = manually created
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    professional = relationship("User", foreign_keys=[professional_id], backref="appointment_slots")
    location = relationship("ProfessionalLocation", back_populates="appointment_slots")
    appointment_type = relationship("AppointmentType", back_populates="slots")
    appointment = relationship("Appointment", backref="slot") 