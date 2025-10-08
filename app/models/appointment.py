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
    appointments = relationship("Appointment", back_populates="manual_appointment")

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Basic Appointment Info
    appointment_type_id = Column(Integer, ForeignKey("appointment_types.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    professional_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("professional_locations.id"), nullable=False)
    
    # Health Plan and Documents
    health_plan_id = Column(Integer, ForeignKey("health_plans.id"))  # Link to health plan if applicable
    related_document_ids = Column(JSON)  # Array of document IDs related to this appointment
    
    # Consultation Type
    consultation_type = Column(String(50), nullable=False)  # "in_person", "virtual", "phone"
    
    # Scheduling
    scheduled_at = Column(DateTime, nullable=False)  # When appointment is scheduled
    duration_minutes = Column(Integer, nullable=False)  # Actual duration
    timezone = Column(String(50), nullable=False, default="UTC")
    
    # Status and Type
    status = Column(String(50), nullable=False, default="SCHEDULED")  # "SCHEDULED", "CONFIRMED", "IN_PROGRESS", "COMPLETED", "CANCELLED", "NO_SHOW"
    appointment_category = Column(String(50), nullable=False)  # "consultation", "follow_up", "emergency", "routine_checkup"
    
    # Cost and Payment
    appointment_type_pricing_id = Column(Integer, ForeignKey("appointment_type_pricing.id"), nullable=False)
    cost = Column(Numeric(10, 2), nullable=False)  # Actual cost for this appointment
    currency = Column(String(3), default="USD")
    payment_status = Column(String(50), nullable=False, default="PENDING")  # "PENDING", "PAID", "REFUNDED", "FAILED"
    stripe_payment_intent_id = Column(String(255))  # Stripe Payment Intent ID
    stripe_charge_id = Column(String(255))  # Stripe Charge ID
    
    # External Service Integration
    acuity_appointment_id = Column(String(255))  # Acuity Scheduling appointment ID
    acuity_calendar_id = Column(String(255))  # Acuity calendar ID
    
    # Virtual Consultation Details
    virtual_meeting_url = Column(Text)  # Video call URL
    virtual_meeting_id = Column(String(255))  # Meeting ID
    virtual_meeting_platform = Column(String(50))  # "zoom", "teams", "daily_co", "custom"
    virtual_meeting_password = Column(String(100))  # Meeting password if required
    
    # Booking Information
    booked_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Who booked the appointment
    booked_at = Column(DateTime, nullable=False)  # When it was booked
    booking_notes = Column(Text)  # Notes from booking process
    
    # Appointment Details
    reason = Column(Text)  # Patient's reason for appointment
    symptoms = Column(Text)  # Patient's symptoms
    notes = Column(Text)  # Professional's notes (shared with patient)
    private_notes = Column(Text)  # Professional's private notes (NOT shared with patient)
    diagnosis = Column(Text)  # Professional's diagnosis
    treatment_plan = Column(Text)  # Treatment plan
    prescription = Column(Text)  # Prescription if any
    
    # Medical Impact
    medical_condition_updates = Column(JSON)  # Array of medical condition changes
    
    # Follow-up
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(Date)
    follow_up_notes = Column(Text)
    
    # Manual Appointment Link
    manual_appointment_id = Column(Integer, ForeignKey("manual_appointments.id"))  # Link to manual appointment if created from one
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    appointment_type = relationship("AppointmentType", backref="appointments")
    patient = relationship("User", foreign_keys=[patient_id], backref="patient_appointments")
    professional = relationship("User", foreign_keys=[professional_id], backref="professional_appointments")
    location = relationship("ProfessionalLocation", back_populates="appointments")
    health_plan = relationship("HealthPlan", back_populates="appointments")
    appointment_type_pricing = relationship("AppointmentTypePricing", backref="appointments")
    manual_appointment = relationship("ManualAppointment", back_populates="appointments")
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

 