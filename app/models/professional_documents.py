from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class ProfessionalDocumentCategory(Base):
    __tablename__ = "professional_document_categories"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)  # "forms", "templates", "education", "legal", "marketing", "media"
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    icon_name = Column(String(50))  # For UI icons
    color = Column(String(7))  # Hex color code for UI
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)  # For ordering in UI
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Admin user
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    documents = relationship("ProfessionalDocument", back_populates="category")
    templates = relationship("ProfessionalDocumentTemplate", back_populates="category")

class ProfessionalDocument(Base):
    __tablename__ = "professional_documents"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    professional_id = Column(Integer, ForeignKey("professionals.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("professional_document_categories.id"), nullable=False)
    
    # Document Details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    file_name = Column(String(255), nullable=False)
    original_file_name = Column(String(255), nullable=False)  # Original uploaded filename
    file_type = Column(String(50), nullable=False)  # MIME type
    file_size = Column(Integer, nullable=False)  # Size in bytes
    file_extension = Column(String(10), nullable=False)  # pdf, docx, jpg, etc.
    
    # Storage
    s3_url = Column(Text, nullable=False)
    s3_key = Column(String(500), nullable=False)  # S3 object key
    
    # Document Properties
    version = Column(String(20), default="1.0")
    is_template = Column(Boolean, default=False)  # Can be used as template
    is_public = Column(Boolean, default=False)  # Visible to patients/public
    is_archived = Column(Boolean, default=False)
    
    # Usage Tracking
    download_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime)
    
    # Tags and Metadata
    tags = Column(JSON)  # Array of tags for easy searching
    metadata = Column(JSON)  # Additional metadata (form fields, template variables, etc.)
    
    # Status
    status = Column(String(50), nullable=False, default="ACTIVE")  # "ACTIVE", "DRAFT", "ARCHIVED", "DELETED"
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    professional = relationship("Professional", backref="documents")
    category = relationship("ProfessionalDocumentCategory", back_populates="documents")
    shares = relationship("ProfessionalDocumentShare", back_populates="document")
    access_logs = relationship("ProfessionalDocumentAccessLog", back_populates="document")

class ProfessionalDocumentShare(Base):
    __tablename__ = "professional_document_shares"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("professional_documents.id"), nullable=False)
    
    # Share Details
    share_type = Column(String(50), nullable=False)  # "patient", "professional", "public_link", "email"
    shared_with_id = Column(Integer, ForeignKey("users.id"))  # User ID if shared with specific user
    shared_with_email = Column(String(255))  # Email if shared via email
    
    # Access Control
    access_level = Column(String(50), nullable=False, default="VIEW")  # "VIEW", "DOWNLOAD", "EDIT"
    expires_at = Column(DateTime)  # When share expires (NULL = never)
    
    # Share Link (for public sharing)
    share_token = Column(String(255), unique=True)  # Unique token for public access
    share_url = Column(Text)  # Generated share URL
    
    # Usage Tracking
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    document = relationship("ProfessionalDocument", back_populates="shares")
    shared_with = relationship("User", foreign_keys=[shared_with_id])

class ProfessionalDocumentAccessLog(Base):
    __tablename__ = "professional_document_access_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("professional_documents.id"), nullable=False)
    
    # Access Details
    accessed_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # User who accessed the document
    access_type = Column(String(50), nullable=False)  # "VIEW", "DOWNLOAD", "EDIT", "SHARE"
    
    # Access Context
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    referrer = Column(Text)  # Where the access came from
    
    # Share Context
    share_id = Column(Integer, ForeignKey("professional_document_shares.id"))  # If accessed via share
    
    # Audit fields
    accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("ProfessionalDocument", back_populates="access_logs")
    accessed_by_user = relationship("User", foreign_keys=[accessed_by])
    share = relationship("ProfessionalDocumentShare", foreign_keys=[share_id])

class ProfessionalDocumentTemplate(Base):
    __tablename__ = "professional_document_templates"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    professional_id = Column(Integer, ForeignKey("professionals.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("professional_document_categories.id"), nullable=False)
    
    # Template Details
    template_name = Column(String(255), nullable=False)
    description = Column(Text)
    template_type = Column(String(50), nullable=False)  # "form", "letter", "prescription", "lab_order", "referral"
    
    # Template File
    template_file_name = Column(String(255), nullable=False)
    template_file_url = Column(Text, nullable=False)
    template_file_type = Column(String(50), nullable=False)  # MIME type
    template_file_size = Column(Integer, nullable=False)
    
    # Template Variables
    template_variables = Column(JSON, nullable=False)  # Define variables that can be filled
    
    # Template Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)  # Default template for this type
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    professional = relationship("Professional", backref="document_templates")
    category = relationship("ProfessionalDocumentCategory", back_populates="templates")
    instances = relationship("ProfessionalDocumentInstance", back_populates="template")

class ProfessionalDocumentInstance(Base):
    __tablename__ = "professional_document_instances"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey("professional_document_templates.id"), nullable=False)
    professional_id = Column(Integer, ForeignKey("professionals.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)  # Link to specific appointment
    
    # Instance Details
    instance_name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Filled Variables
    filled_variables = Column(JSON, nullable=False)  # Actual values filled in the template
    
    # Generated Document
    generated_file_name = Column(String(255), nullable=False)
    generated_file_url = Column(Text, nullable=False)
    generated_file_type = Column(String(50), nullable=False)
    generated_file_size = Column(Integer, nullable=False)
    
    # Document Status
    status = Column(String(50), nullable=False, default="DRAFT")  # "DRAFT", "FINALIZED", "SENT_TO_PATIENT", "ARCHIVED"
    
    # Patient Access
    shared_with_patient = Column(Boolean, default=False)
    shared_at = Column(DateTime)
    patient_access_token = Column(String(255), unique=True)  # For secure patient access
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    template = relationship("ProfessionalDocumentTemplate", back_populates="instances")
    professional = relationship("Professional", backref="document_instances")
    appointment = relationship("Appointment", backref="document_instances")
    assignments = relationship("ProfessionalDocumentAssignment", back_populates="document_instance")
    approvals = relationship("ProfessionalDocumentApproval", back_populates="document_instance")

class ProfessionalDocumentAssignment(Base):
    __tablename__ = "professional_document_assignments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    document_instance_id = Column(Integer, ForeignKey("professional_document_instances.id"), nullable=False)
    
    # Assignment Details
    assignment_type = Column(String(50), nullable=False)  # "prescription", "lab_order", "referral", "consent_form", "discharge_summary"
    assignment_notes = Column(Text)  # Notes about this document assignment
    
    # Status
    is_required = Column(Boolean, default=True)  # Whether this document is required for the appointment
    is_completed = Column(Boolean, default=False)  # Whether the document has been completed
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    appointment = relationship("Appointment", back_populates="document_assignments")
    document_instance = relationship("ProfessionalDocumentInstance", back_populates="assignments")

class ProfessionalDocumentApproval(Base):
    __tablename__ = "professional_document_approvals"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_instance_id = Column(Integer, ForeignKey("professional_document_instances.id"), nullable=False)
    
    # Approval Details
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Professional who approved
    approval_status = Column(String(50), nullable=False)  # "PENDING", "APPROVED", "REJECTED", "REQUIRES_CHANGES"
    approval_notes = Column(Text)  # Notes from approver
    
    # Approval Process
    submitted_at = Column(DateTime, nullable=False)
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)  # If rejected
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    document_instance = relationship("ProfessionalDocumentInstance", back_populates="approvals")
    approver = relationship("User", foreign_keys=[approver_id]) 