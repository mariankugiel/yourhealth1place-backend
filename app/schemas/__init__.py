from .user import UserCreate, UserUpdate, UserResponse, UserLogin, Token
from .patient import PatientCreate, PatientUpdate, PatientResponse
from .appointment import AppointmentCreate, AppointmentUpdate, AppointmentResponse
from .health_record import (
    # Base Health Record
    HealthRecordCreate, HealthRecordUpdate, HealthRecordResponse,
    # Medical Conditions
    MedicalConditionCreate, MedicalConditionUpdate, MedicalConditionResponse,
    # Family Medical History
    FamilyMedicalHistoryCreate, FamilyMedicalHistoryUpdate, FamilyMedicalHistoryResponse,
    # Medical Documents
    MedicalDocumentCreate, MedicalDocumentUpdate, MedicalDocumentResponse,
    # Health Record Types
    HealthRecordTypeCreate, HealthRecordTypeUpdate, HealthRecordTypeResponse,
    # Health Record Sections
    HealthRecordSectionCreate, HealthRecordSectionUpdate, HealthRecordSectionResponse,
    # Health Record Metrics
    HealthRecordMetricCreate, HealthRecordMetricUpdate, HealthRecordMetricResponse,
    # Composite Schemas
    HealthRecordWithDetails, MedicalConditionWithDetails, FamilyMedicalHistoryWithDetails, MedicalDocumentWithDetails,
    # Bulk Operations
    BulkHealthRecordCreate, BulkHealthRecordResponse,
    # Health Record Images
    HealthRecordImageCreate, HealthRecordImageUpdate, HealthRecordImageResponse, HealthRecordImageSummary,
    # Statistics and Analytics
    MetricRecordResponse, PaginatedImageResponse
)
from .medication import MedicationCreate, MedicationUpdate, MedicationResponse
from .message import MessageCreate, MessageUpdate, MessageResponse
from .professional import ProfessionalCreate, ProfessionalUpdate, Professional, ProfessionalList
from .health_plan import HealthPlanCreate, HealthPlanUpdate, HealthPlan, HealthPlanList
from .patient_insight import PatientInsightCreate, PatientInsightUpdate, PatientInsight, PatientInsightList
from .statistics import ProfessionalStatistics, DashboardStatistics
from .professional_document import (
    ProfessionalDocumentCreate, ProfessionalDocumentUpdate, ProfessionalDocument, ProfessionalDocumentList,
    DocumentAssignmentCreate, DocumentAssignmentUpdate, DocumentAssignment, DocumentAssignmentList,
    CreateDocumentFromTemplate, PatientDataForDocument,
    AppointmentDocumentSummary, AppointmentWithDocuments
)

# Centralized Document Management Schemas
from .document import (
    # Base Document Schemas
    DocumentCreate, DocumentUpdate, DocumentResponse, DocumentWithDetails,
    # Document Permission Schemas
    DocumentPermissionCreate, DocumentPermissionUpdate, DocumentPermissionResponse,
    # Document Share Schemas
    DocumentShareCreate, DocumentShareUpdate, DocumentShareResponse,
    # Document Access Log Schemas
    DocumentAccessLogCreate, DocumentAccessLogResponse,
    # Specialized Document Schemas
    LabDocumentCreate, LabDocumentUpdate, LabDocumentResponse,
    ImagingDocumentCreate, ImagingDocumentUpdate, ImagingDocumentResponse,
    PrescriptionDocumentCreate, PrescriptionDocumentUpdate, PrescriptionDocumentResponse,
    # Health Record Permission Schemas
    HealthRecordPermissionCreate, HealthRecordPermissionUpdate, HealthRecordPermissionResponse,
    # Composite Schemas
    DocumentSearchResult, DocumentPermissionSummary, DocumentShareSummary
)

__all__ = [
    "UserCreate", "UserUpdate", "UserResponse", "UserLogin", "Token",
    "PatientCreate", "PatientUpdate", "PatientResponse",
    "AppointmentCreate", "AppointmentUpdate", "AppointmentResponse",
    # Health Record Schemas
    "HealthRecordCreate", "HealthRecordUpdate", "HealthRecordResponse",
    "MedicalConditionCreate", "MedicalConditionUpdate", "MedicalConditionResponse",
    "FamilyMedicalHistoryCreate", "FamilyMedicalHistoryUpdate", "FamilyMedicalHistoryResponse",
    "MedicalDocumentCreate", "MedicalDocumentUpdate", "MedicalDocumentResponse",
    "HealthRecordTypeCreate", "HealthRecordTypeUpdate", "HealthRecordTypeResponse",
    "HealthRecordSectionCreate", "HealthRecordSectionUpdate", "HealthRecordSectionResponse",
    "HealthRecordMetricCreate", "HealthRecordMetricUpdate", "HealthRecordMetricResponse",
    "HealthRecordWithDetails", "MedicalConditionWithDetails", "FamilyMedicalHistoryWithDetails", "MedicalDocumentWithDetails",
    "BulkHealthRecordCreate", "BulkHealthRecordResponse",
    "HealthRecordImageCreate", "HealthRecordImageUpdate", "HealthRecordImageResponse", "HealthRecordImageSummary",
    "MetricRecordResponse", "PaginatedImageResponse",
    # Other Schemas
    "MedicationCreate", "MedicationUpdate", "MedicationResponse",
    "MessageCreate", "MessageUpdate", "MessageResponse",
    "ProfessionalCreate", "ProfessionalUpdate", "Professional", "ProfessionalList",
    "HealthPlanCreate", "HealthPlanUpdate", "HealthPlan", "HealthPlanList",
    "PatientInsightCreate", "PatientInsightUpdate", "PatientInsight", "PatientInsightList",
    "ProfessionalStatistics", "DashboardStatistics",
    # Professional Document Schemas
    "ProfessionalDocumentCreate", "ProfessionalDocumentUpdate", "ProfessionalDocument", "ProfessionalDocumentList",
    "DocumentAssignmentCreate", "DocumentAssignmentUpdate", "DocumentAssignment", "DocumentAssignmentList",
    "CreateDocumentFromTemplate", "PatientDataForDocument",
    "AppointmentDocumentSummary", "AppointmentWithDocuments",
    
    # Centralized Document Management Schemas
    "DocumentCreate", "DocumentUpdate", "DocumentResponse", "DocumentWithDetails",
    "DocumentPermissionCreate", "DocumentPermissionUpdate", "DocumentPermissionResponse",
    "DocumentShareCreate", "DocumentShareUpdate", "DocumentShareResponse",
    "DocumentAccessLogCreate", "DocumentAccessLogResponse",
    "LabDocumentCreate", "LabDocumentUpdate", "LabDocumentResponse",
    "ImagingDocumentCreate", "ImagingDocumentUpdate", "ImagingDocumentResponse",
    "PrescriptionDocumentCreate", "PrescriptionDocumentUpdate", "PrescriptionDocumentResponse",
    "HealthRecordPermissionCreate", "HealthRecordPermissionUpdate", "HealthRecordPermissionResponse",
    "DocumentSearchResult", "DocumentPermissionSummary", "DocumentShareSummary"
] 