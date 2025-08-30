from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Professional(Base):
    __tablename__ = "professionals"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    license_number = Column(String(100), unique=True, index=True)
    specialization = Column(String(100))
    years_of_experience = Column(Integer)
    education = Column(Text)
    certifications = Column(Text)
    languages_spoken = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="professional")
    created_health_plans = relationship("HealthPlan", back_populates="doctor") 