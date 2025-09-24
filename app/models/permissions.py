from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

# ============================================================================
# PERMISSION TYPE ENUMS
# ============================================================================

class PermissionType(str, enum.Enum):
    DOCUMENT = "document"
    HEALTH_RECORD = "health_record"
    APPOINTMENT = "appointment"
    MESSAGE = "message"
    HEALTH_PLAN = "health_plan"
    MEDICATION = "medication"
    SYSTEM = "system"

class PermissionLevel(str, enum.Enum):
    VIEW = "view"
    DOWNLOAD = "download"
    EDIT = "edit"
    DELETE = "delete"
    SHARE = "share"
    ADMIN = "admin"

class PermissionStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    REVOKED = "revoked"

# ============================================================================
# PERMISSION MODELS
# ============================================================================

class Permission(Base):
    """Centralized permission system for all resource types"""
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Permission Target
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # User getting permission
    resource_type = Column(Enum(PermissionType), nullable=False)  # Type of resource
    resource_id = Column(Integer, nullable=False)  # ID of the specific resource
    
    # Permission Details
    permission_level = Column(Enum(PermissionLevel), nullable=False)
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Who granted the permission
    
    # Permission Context
    granted_for = Column(String(100))  # Context: "appointment_123", "health_record", "ongoing_care"
    expires_at = Column(DateTime)  # When permission expires (NULL = never)
    
    # Permission Scope (granular permissions)
    can_view = Column(Boolean, default=False)
    can_download = Column(Boolean, default=False)
    can_edit = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_share = Column(Boolean, default=False)
    
    # Additional Context
    notes = Column(Text)  # Notes about this permission
    permission_metadata = Column(JSON)  # Additional metadata specific to resource type
    
    # Status
    status = Column(Enum(PermissionStatus), nullable=False, default=PermissionStatus.ACTIVE)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="permissions")
    granter = relationship("User", foreign_keys=[granted_by], back_populates="granted_permissions_general")
    audit_logs = relationship("PermissionAuditLog", back_populates="permission")

class PermissionAuditLog(Base):
    """Audit trail for permission changes"""
    __tablename__ = "permission_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Permission Reference
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)
    
    # Change Details
    action = Column(String(50), nullable=False)  # "created", "updated", "revoked", "expired"
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Who made the change
    
    # Change Context
    old_values = Column(JSON)  # Previous permission values
    new_values = Column(JSON)  # New permission values
    change_reason = Column(Text)  # Reason for the change
    
    # Audit fields
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    permission = relationship("Permission", back_populates="audit_logs")
    changer = relationship("User", foreign_keys=[changed_by])

# ============================================================================
# HEALTH RECORD SPECIFIC PERMISSIONS
# ============================================================================

class HealthRecordPermission(Base):
    """Specialized permissions for health record access by professionals"""
    __tablename__ = "health_record_permissions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Permission Details
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Patient whose records are being accessed
    professional_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Professional requesting access
    
    # Permission Scope
    can_view_health_records = Column(Boolean, default=False)
    can_view_medical_history = Column(Boolean, default=False)
    can_view_health_plans = Column(Boolean, default=False)
    can_view_medications = Column(Boolean, default=False)
    can_view_appointments = Column(Boolean, default=False)
    can_view_messages = Column(Boolean, default=False)
    can_view_lab_results = Column(Boolean, default=False)
    can_view_imaging = Column(Boolean, default=False)
    
    # Permission Context
    granted_for = Column(String(100))  # "appointment_123", "ongoing_care", "consultation"
    expires_at = Column(DateTime)  # When permission expires
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Usually the patient
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], back_populates="health_record_permissions_given")
    professional = relationship("User", foreign_keys=[professional_id], back_populates="health_record_permissions_received")
    granter = relationship("User", foreign_keys=[granted_by], back_populates="health_record_permissions_granted")

# ============================================================================
# DOCUMENT SPECIFIC PERMISSIONS (Legacy - will be replaced by general Permission table)
# ============================================================================

class DocumentPermission(Base):
    """Document-specific permissions (legacy - will be replaced by general Permission table)"""
    __tablename__ = "document_permissions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    
    # Permission Target
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # User getting permission
    permission_type = Column(Enum(PermissionLevel), nullable=False)
    
    # Permission Context
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Who granted the permission
    granted_for = Column(String(100))  # Context: "appointment_123", "health_record", etc.
    
    # Permission Scope
    can_view = Column(Boolean, default=False)
    can_download = Column(Boolean, default=False)
    can_edit = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_share = Column(Boolean, default=False)
    
    # Permission Details
    expires_at = Column(DateTime)  # When permission expires (NULL = never)
    notes = Column(Text)  # Notes about this permission
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="permissions")
    user = relationship("User", foreign_keys=[user_id], back_populates="document_permissions")
    granter = relationship("User", foreign_keys=[granted_by], back_populates="granted_permissions") 