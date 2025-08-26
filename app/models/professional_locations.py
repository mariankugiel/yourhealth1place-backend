from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class ProfessionalLocation(Base):
    __tablename__ = "professional_locations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    practice_id = Column(Integer, ForeignKey("professional_practices.id"), nullable=False)
    
    # Location Details
    location_name = Column(String(255), nullable=False)  # "Main Office", "Downtown Branch", "Home Office"
    address_line_1 = Column(String(255), nullable=False)
    address_line_2 = Column(String(255))
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(100), nullable=False, default="USA")
    
    # Location Type
    location_type = Column(String(50), nullable=False)  # "office", "home", "hospital", "clinic", "virtual"
    
    # Virtual Consultation Support
    supports_virtual_consultation = Column(Boolean, default=False)
    virtual_consultation_platforms = Column(JSON)  # ["zoom", "teams", "daily_co", "custom"]
    virtual_consultation_notes = Column(Text)  # Equipment, setup instructions
    
    # Physical Location Details
    parking_available = Column(Boolean, default=False)
    wheelchair_accessible = Column(Boolean, default=False)
    public_transportation = Column(Text)  # Bus routes, subway lines
    
    # Operating Hours (if different from professional's schedule)
    operating_hours = Column(JSON)  # Store operating hours if location-specific
    
    # Status
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)  # Primary location for this practice
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    practice = relationship("ProfessionalPractice", back_populates="locations")
    availability_schedules = relationship("ProfessionalAvailabilitySchedule", back_populates="location")
    appointment_slots = relationship("ProfessionalAppointmentSlot", back_populates="location")
    appointments = relationship("Appointment", back_populates="location") 