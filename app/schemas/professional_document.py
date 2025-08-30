from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    LAB_ORDER = "lab_order"
    PRESCRIPTION = "prescription"
    REFERRAL = "referral"
    CONSENT_FORM = "consent_form"
    DISCHARGE_SUMMARY = "discharge_summary"
    MEDICAL_CERTIFICATE = "medical_certificate"
    TREATMENT_PLAN = "treatment_plan"
    FOLLOW_UP_NOTES = "follow_up_notes"

class DocumentStatus(str, Enum):
    DRAFT = "draft"
    FINALIZED = "finalized"
    SENT_TO_PATIENT = "sent_to_patient"
    ARCHIVED = "archived"

# Base document schema
class ProfessionalDocumentBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_template: bool = False
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class ProfessionalDocumentCreate(ProfessionalDocumentBase):
    category_id: int
    file_name: str
    original_file_name: str
    file_type: str
    file_size: int
    file_extension: str
    s3_url: str
    s3_key: str

class ProfessionalDocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_template: Optional[bool] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[DocumentStatus] = None

class ProfessionalDocument(ProfessionalDocumentBase):
    id: int
    professional_id: int
    category_id: int
    file_name: str
    original_file_name: str
    file_type: str
    file_size: int
    file_extension: str
    s3_url: str
    s3_key: str
    version: str
    is_public: bool
    is_archived: bool
    download_count: int
    view_count: int
    last_accessed_at: Optional[datetime] = None
    status: DocumentStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: int
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

# Document assignment to appointments
class DocumentAssignmentBase(BaseModel):
    assignment_type: DocumentType
    assignment_notes: Optional[str] = None
    is_required: bool = True

class DocumentAssignmentCreate(DocumentAssignmentBase):
    appointment_id: int
    document_id: int

class DocumentAssignmentUpdate(BaseModel):
    assignment_notes: Optional[str] = None
    is_required: Optional[bool] = None
    is_completed: Optional[bool] = None

class DocumentAssignment(DocumentAssignmentBase):
    id: int
    appointment_id: int
    document_id: int
    is_completed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: int
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

# Patient data for document creation
class PatientDataForDocument(BaseModel):
    patient_name: str
    patient_dob: str
    patient_id: str
    contact_info: Dict[str, str]
    medical_history: Optional[Dict[str, Any]] = None
    current_medications: Optional[List[Dict[str, Any]]] = None
    allergies: Optional[List[str]] = None
    lab_results: Optional[List[Dict[str, Any]]] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    referral_specialty: Optional[str] = None
    referral_reason: Optional[str] = None

# Document creation from template
class CreateDocumentFromTemplate(BaseModel):
    template_document_id: int
    appointment_id: int
    patient_data: PatientDataForDocument
    custom_variables: Optional[Dict[str, Any]] = None
    new_title: str

# Response schemas
class ProfessionalDocumentList(BaseModel):
    documents: List[ProfessionalDocument]
    total: int
    page: int
    size: int

class DocumentAssignmentList(BaseModel):
    assignments: List[DocumentAssignment]
    total: int
    page: int
    size: int

class AppointmentDocumentSummary(BaseModel):
    appointment_id: int
    total_documents: int
    completed_documents: int
    pending_documents: int
    document_types: List[DocumentType]

class AppointmentWithDocuments(BaseModel):
    appointment_id: int
    patient_name: str
    professional_name: str
    appointment_date: datetime
    documents: List[ProfessionalDocument]
    assignments: List[DocumentAssignment]
