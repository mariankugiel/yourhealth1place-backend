from .user import UserCreate, UserUpdate, UserResponse, UserLogin, Token, UserProfile, UserEmergency, UserNotifications, UserIntegrations, UserPrivacy, UserSharedAccess, UserAccessLogs, UserDataSharing, UserRegistration, PasswordChange, MFAEnrollRequest, MFAEnrollResponse, MFAVerifyRequest, MFAFactor
from .appointment import AppointmentCreate, AppointmentUpdate, AppointmentResponse
from .health_record import (
    # Base Health Record
    HealthRecordCreate, HealthRecordUpdate, HealthRecordResponse,
    # Medical Conditions
    MedicalConditionCreate, MedicalConditionUpdate, MedicalConditionResponse,
    # Family Medical History
    FamilyMedicalHistoryCreate, FamilyMedicalHistoryUpdate, FamilyMedicalHistoryResponse,
    # Medical Documents
    HealthRecordDocLabCreate, HealthRecordDocLabUpdate, HealthRecordDocLabResponse,
    # Health Record Types
    HealthRecordTypeCreate, HealthRecordTypeUpdate, HealthRecordTypeResponse,
    # Health Record Sections
    HealthRecordSectionCreate, HealthRecordSectionUpdate, HealthRecordSectionResponse,
    # Health Record Metrics
    HealthRecordMetricCreate, HealthRecordMetricUpdate, HealthRecordMetricResponse,
    # Composite Schemas
    HealthRecordWithDetails, MedicalConditionWithDetails, FamilyMedicalHistoryWithDetails, HealthRecordDocLabWithDetails,
    # Bulk Operations
    BulkHealthRecordCreate, BulkHealthRecordResponse,
    # Health Record Images
    HealthRecordDocExamCreate, HealthRecordDocExamUpdate, HealthRecordDocExamResponse, HealthRecordDocExamSummary,
    # Statistics and Analytics
    MetricRecordResponse, PaginatedImageResponse
)
from .medication import MedicationCreate, MedicationUpdate, MedicationResponse
from .message import MessageCreate, MessageUpdate, Message
# Professional schemas removed - data now stored in Supabase user metadata
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
    "UserCreate", "UserUpdate", "UserResponse", "UserLogin", "Token", "UserProfile", "UserEmergency", "UserNotifications", "UserIntegrations", "UserPrivacy", "UserSharedAccess", "UserAccessLogs", "UserDataSharing", "UserRegistration", "PasswordChange", "MFAEnrollRequest", "MFAEnrollResponse", "MFAVerifyRequest", "MFAFactor",
    "PatientCreate", "PatientUpdate", "PatientResponse",
    "AppointmentCreate", "AppointmentUpdate", "AppointmentResponse",
    # Health Record Schemas
    "HealthRecordCreate", "HealthRecordUpdate", "HealthRecordResponse",
    "MedicalConditionCreate", "MedicalConditionUpdate", "MedicalConditionResponse",
    "FamilyMedicalHistoryCreate", "FamilyMedicalHistoryUpdate", "FamilyMedicalHistoryResponse",
    "HealthRecordDocLabCreate", "HealthRecordDocLabUpdate", "HealthRecordDocLabResponse",
    "HealthRecordTypeCreate", "HealthRecordTypeUpdate", "HealthRecordTypeResponse",
    "HealthRecordSectionCreate", "HealthRecordSectionUpdate", "HealthRecordSectionResponse",
    "HealthRecordMetricCreate", "HealthRecordMetricUpdate", "HealthRecordMetricResponse",
    "HealthRecordWithDetails", "MedicalConditionWithDetails", "FamilyMedicalHistoryWithDetails", "HealthRecordDocLabWithDetails",
    "BulkHealthRecordCreate", "BulkHealthRecordResponse",
    "HealthRecordDocExamCreate", "HealthRecordDocExamUpdate", "HealthRecordDocExamResponse", "HealthRecordDocExamSummary",
    "MetricRecordResponse", "PaginatedImageResponse",
    # Other Schemas
    "MedicationCreate", "MedicationUpdate", "MedicationResponse",
    "MessageCreate", "MessageUpdate", "Message",
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