from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Date, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    supabase_user_id = Column(String(255), unique=True, index=True)  # Link to Supabase
    email = Column(String(255), nullable=False, unique=True, index=True)  # For lookups only
    is_active = Column(Boolean, default=True)  # Application state
    is_superuser = Column(Boolean, default=False)  # Application permissions
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships to application data (not personal info)
    patient = relationship("Patient", back_populates="user")
    professional = relationship("Professional", back_populates="user")
    health_records = relationship("HealthRecord", foreign_keys="HealthRecord.created_by", back_populates="user")
    ios_devices = relationship("IOSDevice", foreign_keys="IOSDevice.user_id", back_populates="user") 