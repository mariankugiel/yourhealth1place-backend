from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class DataResourceType(Base):
    __tablename__ = "data_resource_types"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)  # "medical_history", "health_records", "health_plan", "medications"
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Admin user
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    permissions = relationship("DataPermission", back_populates="resource_type")

class DataAccessType(Base):
    __tablename__ = "data_access_types"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)  # "view", "download", "edit"
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Admin user
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    permissions = relationship("DataPermission", back_populates="access_type")

class DataPermission(Base):
    __tablename__ = "data_permissions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Permission Details
    granter_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # User granting permission
    grantee_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # User receiving permission
    resource_type_id = Column(Integer, ForeignKey("data_resource_types.id"), nullable=False)
    access_type_id = Column(Integer, ForeignKey("data_access_types.id"), nullable=False)
    
    # Resource Scope
    resource_id = Column(Integer)  # Specific resource ID (optional - NULL means all resources of this type)
    resource_scope = Column(String(50), default="ALL")  # "ALL", "SPECIFIC", "CATEGORY"
    
    # Permission Details
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)  # When permission expires (NULL = never)
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime)  # When permission was revoked
    
    # Additional Context
    reason = Column(Text)  # Why permission was granted
    conditions = Column(JSON)  # Any conditions for this permission
    notes = Column(Text)  # Additional notes
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    granter = relationship("User", foreign_keys=[granter_id], backref="granted_permissions")
    grantee = relationship("User", foreign_keys=[grantee_id], backref="received_permissions")
    resource_type = relationship("DataResourceType", back_populates="permissions")
    access_type = relationship("DataAccessType", back_populates="permissions")
    access_logs = relationship("DataAccessLog", back_populates="permission")

class DataAccessLog(Base):
    __tablename__ = "data_access_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Access Details
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # User who accessed the data
    permission_id = Column(Integer, ForeignKey("data_permissions.id"))  # Permission used for access
    resource_type_id = Column(Integer, ForeignKey("data_resource_types.id"), nullable=False)
    resource_id = Column(Integer)  # Specific resource accessed
    
    # Access Context
    access_type = Column(String(50), nullable=False)  # "view", "download", "edit", "create", "delete"
    access_method = Column(String(50))  # "api", "web_interface", "mobile_app", "export"
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    session_id = Column(String(255))
    
    # Access Result
    access_successful = Column(Boolean, default=True)
    error_message = Column(Text)  # If access failed
    
    # Audit fields
    accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="data_access_logs")
    permission = relationship("DataPermission", back_populates="access_logs")
    resource_type = relationship("DataResourceType", backref="access_logs") 