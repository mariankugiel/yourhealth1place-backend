from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Professional(Base):
    __tablename__ = "professionals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Professional Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    title = Column(String(100))  # Dr., Prof., etc.
    specialty = Column(String(200))
    license_number = Column(String(100), unique=True)
    medical_board = Column(String(200))
    
    # Contact Information
    phone = Column(String(50))
    office_address = Column(Text)
    office_hours = Column(JSON)  # Store as JSON for flexibility
    
    # Professional Details
    education = Column(JSON)  # List of degrees, institutions, years
    certifications = Column(JSON)  # List of certifications
    experience_years = Column(Integer)
    languages = Column(JSON)  # List of spoken languages
    
    # Practice Settings
    consultation_types = Column(JSON)  # physical, video, phone
    consultation_duration = Column(Integer)  # minutes
    consultation_fee = Column(Integer)  # in cents
    
    # Availability
    is_available = Column(Boolean, default=True)
    availability_schedule = Column(JSON)  # Weekly schedule
    
    # Status
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="professional")
    appointments = relationship("Appointment", back_populates="professional")
    health_plans = relationship("HealthPlan", back_populates="professional")
    
    def __repr__(self):
        return f"<Professional(id={self.id}, name='{self.first_name} {self.last_name}', specialty='{self.specialty}')>" 