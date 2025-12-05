from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON, Numeric, Date, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class AppointmentStatus(enum.Enum):
    SCHEDULED = "SCHEDULED"
    CONFIRMED = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"

class AppointmentType(enum.Enum):
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"
    ROUTINE_CHECKUP = "routine_checkup"

class ManualAppointment(Base):
    __tablename__ = "manual_appointments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Basic Appointment Info
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    professional_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("professional_locations.id"))  # Optional - if known
    
    # Appointment Details
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    consultation_type = Column(String(50), nullable=False)  # "in_person", "virtual", "phone"
    
    # External Information
    external_provider = Column(String(255))  # "City Hospital", "Dr. Johnson's Office"
    external_reference = Column(String(255))  # External appointment ID or reference
    external_notes = Column(Text)  # Notes about the external appointment
    
    # Status
    status = Column(String(50), nullable=False, default="SCHEDULED")  # "SCHEDULED", "COMPLETED", "CANCELLED", "NO_SHOW"
    
    # Cost (if known)
    cost = Column(Numeric(10, 2))
    currency = Column(String(3), default="USD")
    payment_status = Column(String(50), default="UNKNOWN")  # "UNKNOWN", "PAID", "PENDING", "WAIVED"
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Usually the patient
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], backref="patient_manual_appointments")
    professional = relationship("User", foreign_keys=[professional_id], backref="professional_manual_appointments")
    location = relationship("ProfessionalLocation", backref="manual_appointments")
    # appointments relationship removed - Appointment model no longer has manual_appointment_id

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Basic Appointment Info
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    professional_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Consultation Type
    consultation_type = Column(String(50), nullable=False)  # "in_person", "virtual", "phone"
    
    # Scheduling
    scheduled_at = Column(DateTime, nullable=False)  # When appointment is scheduled
    duration_minutes = Column(Integer, nullable=False)  # Actual duration
    timezone = Column(String(50), nullable=False, default="UTC")
    
    # Status
    status = Column(String(50), nullable=False, default="SCHEDULED")  # "SCHEDULED", "CONFIRMED", "IN_PROGRESS", "COMPLETED", "CANCELLED", "NO_SHOW"
    
    # Cost and Payment (from Acuity)
    cost = Column(Numeric(10, 2), nullable=False)  # Actual cost for this appointment (from Acuity)
    currency = Column(String(3), default="USD")
    payment_status = Column(String(50), nullable=False, default="PENDING")  # "PENDING", "PAID", "REFUNDED", "FAILED"
    
    # External Service Integration
    acuity_appointment_id = Column(String(255))  # Acuity Scheduling appointment ID
    acuity_calendar_id = Column(String(255))  # Acuity calendar ID
    acuity_appointment_type_id = Column(String(255))  # Acuity appointment type ID
    
    # Virtual Consultation Details
    virtual_meeting_url = Column(Text)  # Video call URL (stored in DB, not Acuity custom fields)
    
    # Location (for in-person appointments)
    location = Column(Text)  # Doctor's address for in-person appointments
    
    # Appointment Details
    notes = Column(Text)  # Notes from Acuity (patient's reason/notes)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], backref="patient_appointments")
    professional = relationship("User", foreign_keys=[professional_id], backref="professional_appointments")
    reminders = relationship("AppointmentReminder", back_populates="appointment")
    documents = relationship("Document", back_populates="appointment")
    document_assignments = relationship("ProfessionalDocumentAssignment", back_populates="appointment")
    document_shares = relationship("DocumentShare", back_populates="appointment")
    
    # Helper methods for document management
    def has_documents(self) -> bool:
        """Check if appointment has any documents"""
        return len(self.documents) > 0
    
    def get_documents(self):
        """Get all documents for this appointment"""
        return [doc for doc in self.documents if doc.is_appointment_document]
    
    def get_document_count(self) -> int:
        """Get count of appointment documents"""
        return len(self.get_documents())

class AppointmentReminder(Base):
    __tablename__ = "appointment_reminders"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    reminder_type = Column(String(20), nullable=False)  # "email", "sms", "push"
    scheduled_at = Column(DateTime, nullable=False)  # When reminder should be sent
    sent_at = Column(DateTime)  # When reminder was actually sent
    status = Column(String(20), nullable=False, default="PENDING")  # "PENDING", "SENT", "FAILED"
    error_message = Column(Text)  # If failed, why?
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    appointment = relationship("Appointment", back_populates="reminders")

 