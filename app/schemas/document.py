from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

from app.models.documents import (
    DocumentCategory, DocumentStatus, PermissionLevel, ShareType
)

# ============================================================================
# BASE SCHEMAS
# ============================================================================

class DocumentBase(BaseModel):
    """Base document schema"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: DocumentCategory
    document_type: str = Field(..., min_length=1, max_length=100)
    file_name: str = Field(..., min_length=1, max_length=255)
    original_file_name: str = Field(..., min_length=1, max_length=255)
    file_type: str = Field(..., min_length=1, max_length=50)
    file_size: int = Field(..., gt=0)
    file_extension: str = Field(..., min_length=1, max_length=10)
    s3_bucket: str = Field(..., min_length=1, max_length=100)
    s3_key: str = Field(..., min_length=1, max_length=500)
    s3_url: Optional[str] = None
    version: Optional[str] = "1.0"
    is_template: bool = False
    is_public: bool = False
    tags: Optional[List[str]] = None
    custom_metadata: Optional[Dict[str, Any]] = None
    medical_metadata: Optional[Dict[str, Any]] = None

class DocumentCreate(DocumentBase):
    """Schema for creating a new document"""
    owner_id: int
    owner_type: str = Field(..., pattern="^(patient|professional|system)$")

class DocumentUpdate(BaseModel):
    """Schema for updating a document"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[DocumentCategory] = None
    document_type: Optional[str] = Field(None, min_length=1, max_length=100)
    version: Optional[str] = None
    is_template: Optional[bool] = None
    is_public: Optional[bool] = None
    is_archived: Optional[bool] = None
    tags: Optional[List[str]] = None
    custom_metadata: Optional[Dict[str, Any]] = None
    medical_metadata: Optional[Dict[str, Any]] = None
    status: Optional[DocumentStatus] = None

class DocumentResponse(DocumentBase):
    """Schema for document response"""
    id: int
    owner_id: int
    owner_type: str
    status: DocumentStatus
    download_count: int
    view_count: int
    last_accessed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    updated_by: Optional[int]
    
    class Config:
        from_attributes = True

# ============================================================================
# DOCUMENT PERMISSION SCHEMAS
# ============================================================================

class DocumentPermissionBase(BaseModel):
    """Base document permission schema"""
    document_id: int
    user_id: int
    permission_type: PermissionLevel
    granted_for: Optional[str] = None
    can_view: bool = False
    can_download: bool = False
    can_edit: bool = False
    can_delete: bool = False
    can_share: bool = False
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None

class DocumentPermissionCreate(DocumentPermissionBase):
    """Schema for creating a new document permission"""
    pass

class DocumentPermissionUpdate(BaseModel):
    """Schema for updating a document permission"""
    permission_type: Optional[PermissionLevel] = None
    granted_for: Optional[str] = None
    can_view: Optional[bool] = None
    can_download: Optional[bool] = None
    can_edit: Optional[bool] = None
    can_delete: Optional[bool] = None
    can_share: Optional[bool] = None
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None

class DocumentPermissionResponse(DocumentPermissionBase):
    """Schema for document permission response"""
    id: int
    granted_by: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# ============================================================================
# DOCUMENT SHARE SCHEMAS
# ============================================================================

class DocumentShareBase(BaseModel):
    """Base document share schema"""
    document_id: int
    share_type: ShareType
    shared_with_id: Optional[int] = None
    shared_with_email: Optional[str] = None
    appointment_id: Optional[int] = None
    permission_level: PermissionLevel = PermissionLevel.VIEW
    expires_at: Optional[datetime] = None

class DocumentShareCreate(DocumentShareBase):
    """Schema for creating a new document share"""
    pass

class DocumentShareUpdate(BaseModel):
    """Schema for updating a document share"""
    permission_level: Optional[PermissionLevel] = None
    expires_at: Optional[datetime] = None

class DocumentShareResponse(DocumentShareBase):
    """Schema for document share response"""
    id: int
    shared_by: int
    share_token: Optional[str] = None
    share_url: Optional[str] = None
    access_count: int
    last_accessed_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# ============================================================================
# DOCUMENT ACCESS LOG SCHEMAS
# ============================================================================

class DocumentAccessLogBase(BaseModel):
    """Base document access log schema"""
    document_id: int
    access_type: str = Field(..., min_length=1, max_length=50)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    share_id: Optional[int] = None
    permission_id: Optional[int] = None

class DocumentAccessLogCreate(DocumentAccessLogBase):
    """Schema for creating a new document access log"""
    accessed_by: int

class DocumentAccessLogResponse(DocumentAccessLogBase):
    """Schema for document access log response"""
    id: int
    accessed_by: int
    accessed_at: datetime
    
    class Config:
        from_attributes = True

# ============================================================================
# SPECIALIZED DOCUMENT SCHEMAS
# ============================================================================

class LabDocumentBase(BaseModel):
    """Base lab document schema"""
    lab_test_name: str = Field(..., min_length=1, max_length=200)
    lab_test_type: Optional[str] = Field(None, max_length=100)
    lab_test_date: datetime
    lab_provider: Optional[str] = Field(None, max_length=200)
    lab_order_number: Optional[str] = Field(None, max_length=100)
    test_results: Optional[Dict[str, Any]] = None
    reference_ranges: Optional[Dict[str, Any]] = None
    abnormal_flags: Optional[Dict[str, Any]] = None
    units: Optional[Dict[str, Any]] = None
    analysis_status: str = "pending"
    analysis_notes: Optional[str] = None

class LabDocumentCreate(LabDocumentBase):
    """Schema for creating a new lab document"""
    document_id: int

class LabDocumentUpdate(BaseModel):
    """Schema for updating a lab document"""
    lab_test_name: Optional[str] = Field(None, min_length=1, max_length=200)
    lab_test_type: Optional[str] = Field(None, max_length=100)
    lab_test_date: Optional[datetime] = None
    lab_provider: Optional[str] = Field(None, max_length=200)
    lab_order_number: Optional[str] = Field(None, max_length=100)
    test_results: Optional[Dict[str, Any]] = None
    reference_ranges: Optional[Dict[str, Any]] = None
    abnormal_flags: Optional[Dict[str, Any]] = None
    units: Optional[Dict[str, Any]] = None
    analysis_status: Optional[str] = None
    analysis_notes: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None

class LabDocumentResponse(LabDocumentBase):
    """Schema for lab document response"""
    id: int
    document_id: int
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class ImagingDocumentBase(BaseModel):
    """Base imaging document schema"""
    image_type: str = Field(..., min_length=1, max_length=100)
    body_part: str = Field(..., min_length=1, max_length=100)
    image_date: datetime
    findings: Optional[str] = None
    conclusions: Optional[str] = None
    imaging_facility: Optional[str] = Field(None, max_length=200)
    radiologist: Optional[str] = Field(None, max_length=200)
    analysis_status: str = "pending"
    analysis_notes: Optional[str] = None

class ImagingDocumentCreate(ImagingDocumentBase):
    """Schema for creating a new imaging document"""
    document_id: int

class ImagingDocumentUpdate(BaseModel):
    """Schema for updating an imaging document"""
    image_type: Optional[str] = Field(None, min_length=1, max_length=100)
    body_part: Optional[str] = Field(None, min_length=1, max_length=100)
    image_date: Optional[datetime] = None
    findings: Optional[str] = None
    conclusions: Optional[str] = None
    imaging_facility: Optional[str] = Field(None, max_length=200)
    radiologist: Optional[str] = Field(None, max_length=200)
    analysis_status: Optional[str] = None
    analysis_notes: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None

class ImagingDocumentResponse(ImagingDocumentBase):
    """Schema for imaging document response"""
    id: int
    document_id: int
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class PrescriptionDocumentBase(BaseModel):
    """Base prescription document schema"""
    medication_name: str = Field(..., min_length=1, max_length=200)
    dosage: Optional[str] = Field(None, max_length=100)
    frequency: Optional[str] = Field(None, max_length=100)
    duration: Optional[str] = Field(None, max_length=100)
    route: Optional[str] = Field(None, max_length=50)
    prescriber_name: Optional[str] = Field(None, max_length=200)
    prescriber_license: Optional[str] = Field(None, max_length=100)
    prescriber_specialty: Optional[str] = Field(None, max_length=100)
    prescription_date: datetime
    refills_remaining: int = 0
    total_refills: int = 0
    pharmacy_notes: Optional[str] = None
    status: str = "active"

class PrescriptionDocumentCreate(PrescriptionDocumentBase):
    """Schema for creating a new prescription document"""
    document_id: int

class PrescriptionDocumentUpdate(BaseModel):
    """Schema for updating a prescription document"""
    medication_name: Optional[str] = Field(None, min_length=1, max_length=200)
    dosage: Optional[str] = Field(None, max_length=100)
    frequency: Optional[str] = Field(None, max_length=100)
    duration: Optional[str] = Field(None, max_length=100)
    route: Optional[str] = Field(None, max_length=50)
    prescriber_name: Optional[str] = Field(None, max_length=200)
    prescriber_license: Optional[str] = Field(None, max_length=100)
    prescriber_specialty: Optional[str] = Field(None, max_length=100)
    prescription_date: Optional[datetime] = None
    refills_remaining: Optional[int] = None
    total_refills: Optional[int] = None
    pharmacy_notes: Optional[str] = None
    status: Optional[str] = None

class PrescriptionDocumentResponse(PrescriptionDocumentBase):
    """Schema for prescription document response"""
    id: int
    document_id: int
    
    class Config:
        from_attributes = True

# ============================================================================
# HEALTH RECORD PERMISSION SCHEMAS
# ============================================================================

class HealthRecordPermissionBase(BaseModel):
    """Base health record permission schema"""
    patient_id: int
    professional_id: int
    can_view_health_records: bool = False
    can_view_medical_history: bool = False
    can_view_health_plans: bool = False
    can_view_medications: bool = False
    can_view_appointments: bool = False
    can_view_messages: bool = False
    can_view_lab_results: bool = False
    can_view_imaging: bool = False
    granted_for: Optional[str] = None
    expires_at: Optional[datetime] = None

class HealthRecordPermissionCreate(HealthRecordPermissionBase):
    """Schema for creating new health record permissions"""
    pass

class HealthRecordPermissionUpdate(BaseModel):
    """Schema for updating health record permissions"""
    can_view_health_records: Optional[bool] = None
    can_view_medical_history: Optional[bool] = None
    can_view_health_plans: Optional[bool] = None
    can_view_medications: Optional[bool] = None
    can_view_appointments: Optional[bool] = None
    can_view_messages: Optional[bool] = None
    can_view_lab_results: Optional[bool] = None
    can_view_imaging: Optional[bool] = None
    granted_for: Optional[str] = None
    expires_at: Optional[datetime] = None

class HealthRecordPermissionResponse(HealthRecordPermissionBase):
    """Schema for health record permission response"""
    id: int
    granted_by: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# ============================================================================
# COMPOSITE RESPONSE SCHEMAS
# ============================================================================

class DocumentWithDetails(DocumentResponse):
    """Document with all related information"""
    permissions: List[DocumentPermissionResponse] = []
    shares: List[DocumentShareResponse] = []
    lab_document: Optional[LabDocumentResponse] = None
    imaging_document: Optional[ImagingDocumentResponse] = None
    prescription_document: Optional[PrescriptionDocumentResponse] = None

class DocumentSearchResult(BaseModel):
    """Document search result"""
    documents: List[DocumentResponse]
    total: int
    skip: int
    limit: int

class DocumentPermissionSummary(BaseModel):
    """Summary of document permissions for a user"""
    document_id: int
    document_title: str
    can_view: bool
    can_download: bool
    can_edit: bool
    can_delete: bool
    can_share: bool
    granted_by: int
    granted_for: Optional[str]
    expires_at: Optional[datetime]

class DocumentShareSummary(BaseModel):
    """Summary of document shares"""
    share_id: int
    document_id: int
    document_title: str
    share_type: ShareType
    shared_with: Optional[str]  # User name or email
    permission_level: PermissionLevel
    expires_at: Optional[datetime]
    access_count: int
    last_accessed_at: Optional[datetime]
    is_active: bool
