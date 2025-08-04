from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    # Internal linkage ID - never exposed externally
    id = Column(Integer, primary_key=True, index=True)
    
    # Supabase user ID for linkage
    supabase_user_id = Column(String(255), unique=True, index=True, nullable=False)
    
    # Internal user ID for AWS linkage (never exposed in AWS metadata)
    internal_user_id = Column(String(255), unique=True, index=True, nullable=False)
    
    # Basic role and status (stored locally for quick access)
    role = Column(String(50), default="patient")  # patient, doctor, admin
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, supabase_user_id='{self.supabase_user_id}', internal_user_id='{self.internal_user_id}')>" 