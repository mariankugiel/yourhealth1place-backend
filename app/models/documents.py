from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

# ============================================================================
# DOCUMENT TYPE ENUMS
# ============================================================================

class DocumentCategory(str, enum.Enum):
    # Professional Documents
    PROFESSIONAL_FORMS = "professional_forms"
    PROFESSIONAL_TEMPLATES = "professional_templates"
    PROFESSIONAL_EDUCATION = "professional_education"
    PROFESSIONAL_LEGAL = "professional_legal"
    PROFESSIONAL_MARKETING = "professional_marketing"
    PROFESSIONAL_MEDIA = "professional_media"
    
    # Medical Documents
    LAB_RESULTS = "lab_results"
    IMAGING = "imaging"
    PRESCRIPTIONS = "prescriptions"
    REFERRALS = "referrals"
    DISCHARGE_SUMMARIES = "discharge_summaries"
    OPERATION_REPORTS = "operation_reports"
    PATHOLOGY_REPORTS = "pathology_reports"
    VACCINATION_RECORDS = "vaccination_records"
    ALLERGY_TESTS = "allergy_tests"
    GENETIC_TESTS = "genetic_tests"
    
    # Patient Documents
    PATIENT_UPLOADS = "patient_uploads"
    PATIENT_FORMS = "patient_forms"
    PATIENT_INSURANCE = "patient_insurance"
    
    # Appointment Documents
    APPOINTMENT_DOCUMENT = "appointment_document"
    APPOINTMENT_FORMS = "appointment_forms"
    CONSENT_FORMS = "consent_forms"
    INTAKE_FORMS = "intake_forms"
    
    # Message Attachments
    MESSAGE_ATTACHMENT = "message_attachment"

class DocumentStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"

class PermissionLevel(str, enum.Enum):
    VIEW = "view"
    DOWNLOAD = "download"
    EDIT = "edit"
    DELETE = "delete"
    SHARE = "share"
    ADMIN = "admin"

class ShareType(str, enum.Enum):
    PATIENT_TO_PROFESSIONAL = "patient_to_professional"
    PROFESSIONAL_TO_PATIENT = "professional_to_professional"
    APPOINTMENT_SHARE = "appointment_share"
    PUBLIC_LINK = "public_link"
    EMAIL_SHARE = "email_share"

# ============================================================================
# CENTRALIZED DOCUMENT MODELS
# ============================================================================

class Document(Base):
    """Centralized document table for all document types"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Document Classification
    category = Column(Enum(DocumentCategory), nullable=False)
    document_type = Column(String(100), nullable=False)  # Specific type within category
    
    # Ownership
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # User who owns/uploaded the document
    owner_type = Column(String(20), nullable=False)  # "patient", "professional", "system"
    
    # Document Details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    file_name = Column(String(255), nullable=False)
    original_file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # MIME type
    file_size = Column(Integer, nullable=False)  # Size in bytes
    file_extension = Column(String(10), nullable=False)
    
    # Storage
    s3_bucket = Column(String(100), nullable=False)
    s3_key = Column(String(500), nullable=False)
    s3_url = Column(Text)  # Public or presigned URL
    
    # Document Properties
    version = Column(String(20), default="1.0")
    is_template = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    
    # Context Links (for different document types)
    message_id = Column(Integer, ForeignKey("messages.id"))  # Link to message if this is a message attachment
    appointment_id = Column(Integer, ForeignKey("appointments.id"))  # Link to appointment if this is an appointment document
    is_message_attachment = Column(Boolean, default=False)  # Flag to identify message attachments
    is_appointment_document = Column(Boolean, default=False)  # Flag to identify appointment documents
    
    # Medical Document Specific Fields (JSON for flexibility)
    medical_metadata = Column(JSON)  # Lab results, imaging findings, etc.
    
    # Usage Tracking
    download_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime)
    
    # Tags and Metadata
    tags = Column(JSON)  # Array of tags
    custom_metadata = Column(JSON)  # Additional metadata
    
    # Status
    status = Column(Enum(DocumentStatus), nullable=False, default=DocumentStatus.ACTIVE)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], back_populates="documents")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_documents")
    updater = relationship("User", foreign_keys=[updated_by], back_populates="updated_documents")
    shares = relationship("DocumentShare", back_populates="document")
    permissions = relationship("DocumentPermission", back_populates="document")
    access_logs = relationship("DocumentAccessLog", back_populates="document")
    message = relationship("Message", back_populates="documents")
    appointment = relationship("Appointment", back_populates="documents")



class DocumentShare(Base):
    """Document sharing mechanism"""
    __tablename__ = "document_shares"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    
    # Share Details
    share_type = Column(Enum(ShareType), nullable=False)
    shared_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Who is sharing
    
    # Share Target
    shared_with_id = Column(Integer, ForeignKey("users.id"))  # User ID if shared with specific user
    shared_with_email = Column(String(255))  # Email if shared via email
    appointment_id = Column(Integer, ForeignKey("appointments.id"))  # If shared for specific appointment
    
    # Access Control
    permission_level = Column(Enum(PermissionLevel), nullable=False, default=PermissionLevel.VIEW)
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
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="shares")
    sharer = relationship("User", foreign_keys=[shared_by], back_populates="shared_documents")
    shared_with = relationship("User", foreign_keys=[shared_with_id], back_populates="received_shares")
    appointment = relationship("Appointment", back_populates="document_shares")

class DocumentAccessLog(Base):
    """Audit trail for document access"""
    __tablename__ = "document_access_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    
    # Access Details
    accessed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    access_type = Column(String(50), nullable=False)  # "VIEW", "DOWNLOAD", "EDIT", "SHARE"
    
    # Access Context
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    referrer = Column(Text)
    
    # Share Context
    share_id = Column(Integer, ForeignKey("document_shares.id"))
    permission_id = Column(Integer, ForeignKey("document_permissions.id"))
    
    # Audit fields
    accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="access_logs")
    user = relationship("User", foreign_keys=[accessed_by], back_populates="document_access_logs")
    share = relationship("DocumentShare", foreign_keys=[share_id])
    permission = relationship("DocumentPermission", foreign_keys=[permission_id])

# ============================================================================
# SPECIALIZED DOCUMENT MODELS
# ============================================================================

class LabDocument(Base):
    """Lab-specific document with medical metadata"""
    __tablename__ = "lab_documents"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, unique=True)
    
    # Lab Test Information
    lab_test_name = Column(String(200), nullable=False)
    lab_test_type = Column(String(100))
    lab_test_date = Column(DateTime, nullable=False)
    lab_provider = Column(String(200))
    lab_order_number = Column(String(100))
    
    # Medical Results
    test_results = Column(JSON)  # Structured lab results
    reference_ranges = Column(JSON)  # Normal ranges
    abnormal_flags = Column(JSON)  # High, low, critical flags
    units = Column(JSON)  # Units for each result
    
    # Analysis
    analysis_status = Column(String(50), default="pending")  # pending, completed, reviewed
    analysis_notes = Column(Text)
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    
    # Relationships
    document = relationship("Document", backref="lab_document")
    reviewer = relationship("User", foreign_keys=[reviewed_by])

class ImagingDocument(Base):
    """Imaging-specific document with medical metadata"""
    __tablename__ = "imaging_documents"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, unique=True)
    
    # Core Imaging Information
    image_type = Column(String(100), nullable=False)  # X-Ray, MRI, CT, Ultrasound, etc.
    body_part = Column(String(100), nullable=False)
    image_date = Column(DateTime, nullable=False)  # Test date when image was taken
    
    # Medical Analysis
    findings = Column(Text)  # Medical findings from the image
    conclusions = Column(Text)  # Medical conclusions/interpretation
    
    # Additional Context (optional)
    imaging_facility = Column(String(200))
    radiologist = Column(String(200))
    analysis_status = Column(String(50), default="pending")  # pending, completed, reviewed
    analysis_notes = Column(Text)
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    
    # Relationships
    document = relationship("Document", backref="imaging_document")
    reviewer = relationship("User", foreign_keys=[reviewed_by])

class PrescriptionDocument(Base):
    """Prescription-specific document with medical metadata"""
    __tablename__ = "prescription_documents"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, unique=True)
    
    # Prescription Information
    medication_name = Column(String(200), nullable=False)
    dosage = Column(String(100))
    frequency = Column(String(100))
    duration = Column(String(100))
    route = Column(String(50))  # oral, topical, injection, etc.
    
    # Prescriber Information
    prescriber_name = Column(String(200))
    prescriber_license = Column(String(100))
    prescriber_specialty = Column(String(100))
    
    # Prescription Details
    prescription_date = Column(DateTime, nullable=False)
    refills_remaining = Column(Integer, default=0)
    total_refills = Column(Integer, default=0)
    pharmacy_notes = Column(Text)
    
    # Status
    status = Column(String(50), default="active")  # active, completed, cancelled, expired
    
    # Relationships
    document = relationship("Document", backref="prescription_document")


