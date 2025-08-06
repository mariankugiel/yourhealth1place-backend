from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class UserRole(str, enum.Enum):
    PATIENT = "patient"
    PROFESSIONAL = "professional"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    supabase_user_id = Column(String, unique=True, index=True)
    internal_user_id = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    role = Column(Enum(UserRole), default=UserRole.PATIENT)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    professional = relationship("Professional", back_populates="user", uselist=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>" 