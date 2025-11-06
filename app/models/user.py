from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Date, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class UserRole(str, enum.Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    supabase_user_id = Column(String(255), unique=True, index=True)  # Link to Supabase
    email = Column(String(255), nullable=False, index=True)  # For lookups only (not unique - patients can also be doctors)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.PATIENT)  # User role
    is_active = Column(Boolean, default=True)  # Application state
    # timezone is stored in Supabase, not in local PostgreSQL
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships to application data (not personal info)
    # Patient and Professional data now stored in Supabase user metadata
    health_records = relationship("HealthRecord", foreign_keys="HealthRecord.created_by", back_populates="user")
    ios_devices = relationship("IOSDevice", foreign_keys="IOSDevice.user_id", back_populates="user")
    
    # Document Management Relationships
    documents = relationship("Document", foreign_keys="Document.owner_id", back_populates="owner")
    created_documents = relationship("Document", foreign_keys="Document.created_by", back_populates="creator")
    updated_documents = relationship("Document", foreign_keys="Document.updated_by", back_populates="updater")
    
    # Document Permissions (Legacy)
    document_permissions = relationship("DocumentPermission", foreign_keys="DocumentPermission.user_id", back_populates="user")
    granted_permissions = relationship("DocumentPermission", foreign_keys="DocumentPermission.granted_by", back_populates="granter")
    
    # General Permissions
    permissions = relationship("Permission", foreign_keys="Permission.user_id", back_populates="user")
    granted_permissions_general = relationship("Permission", foreign_keys="Permission.granted_by", back_populates="granter")
    
    # Document Sharing
    shared_documents = relationship("DocumentShare", foreign_keys="DocumentShare.shared_by", back_populates="sharer")
    received_shares = relationship("DocumentShare", foreign_keys="DocumentShare.shared_with_id", back_populates="shared_with")
    
    # Document Access Logs
    document_access_logs = relationship("DocumentAccessLog", foreign_keys="DocumentAccessLog.accessed_by", back_populates="user")
    
    # Health Record Permissions
    health_record_permissions_given = relationship("HealthRecordPermission", foreign_keys="HealthRecordPermission.patient_id", back_populates="patient")
    health_record_permissions_received = relationship("HealthRecordPermission", foreign_keys="HealthRecordPermission.professional_id", back_populates="professional")
    health_record_permissions_granted = relationship("HealthRecordPermission", foreign_keys="HealthRecordPermission.granted_by", back_populates="granter")
    
    # AI Analysis History
    ai_analysis_history = relationship("AIAnalysisHistory", back_populates="user", lazy="dynamic") 