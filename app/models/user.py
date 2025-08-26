from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Date, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    date_of_birth = Column(Date)
    gender = Column(String(20))
    phone_number = Column(String(20))
    address = Column(Text)
    emergency_contact_name = Column(String(255))
    emergency_contact_phone = Column(String(20))
    emergency_contact_relationship = Column(String(100))
    blood_type = Column(String(10))
    allergies = Column(Text)
    current_medications = Column(JSON)
    emergency_medical_info = Column(Text)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 