from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class ProfessionalPractice(Base):
    __tablename__ = "professional_practices"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    professional_id = Column(Integer, ForeignKey("professionals.id"), nullable=False)
    
    # Practice Details
    practice_name = Column(String(255), nullable=False)
    practice_type = Column(String(50), nullable=False)  # "private_practice", "hospital", "clinic", "telemedicine", "home_visits"
    description = Column(Text)
    website_url = Column(String(500))
    
    # Contact Information
    phone = Column(String(20))
    email = Column(String(255))
    fax = Column(String(20))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)  # Primary practice location
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    professional = relationship("Professional", backref="practices")
    locations = relationship("ProfessionalLocation", back_populates="practice") 