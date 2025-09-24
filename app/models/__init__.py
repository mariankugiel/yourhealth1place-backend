from app.core.database import Base

# Core User Models
from .user import User
from .patient import Patient
from .professional import Professional

# Professional Practice System
from .professional_practices import ProfessionalPractice
from .professional_locations import ProfessionalLocation
from .professional_availability import ProfessionalAvailabilitySchedule, ProfessionalAppointmentSlot

# Appointment System
from .appointment_types import AppointmentType, AppointmentTypePricing
from .appointment import ManualAppointment, Appointment, AppointmentReminder

# Professional Document Management (Legacy - to be replaced)
from .professional_documents import (
    ProfessionalDocumentCategory,
    ProfessionalDocument,
    ProfessionalDocumentShare,
    ProfessionalDocumentAccessLog,
    ProfessionalDocumentAssignment
)

# Centralized Document Management System
from .documents import (
    Document,
    DocumentShare,
    DocumentAccessLog,
    LabDocument,
    ImagingDocument,
    PrescriptionDocument,
    DocumentCategory,
    DocumentStatus,
    PermissionLevel,
    ShareType
)

# S3 Storage Management
from .s3_storage import (
    S3StorageInfo,
    S3BucketInfo,
    S3AccessLog
)

# Messaging System
from .message import Message

# Payment System
from .payment import SubscriptionPlan, UserSubscription, PaymentTransaction

# Health Records System
from .health_record import (
    # Health Record Types
    HealthRecordType,
    HealthRecordSection,
    HealthRecordMetric,
    HealthRecord,
    
    # Medical Records
    MedicalDocument,
    MedicalCondition,
    FamilyMedicalHistory,
    
    # iOS Integration
    IOSDevice,
    HealthDataPermission,
    IOSSyncLog,
    
    # Enums
    VitalMetric,
    LifestyleMetric,
    BodyMetric,
    MedicalConditionStatus,
    FamilyHistoryStatus,
    DocumentType,
    AnalysisCategory,
    VitalStatus,
    LifestyleStatus,
    BodyStatus,
    ConditionSeverity,
    ConditionSource,
    FamilyRelation,
    FamilyHistorySource,
    DocumentSource,
    AnalysisStatus,
    AnalysisSource
)

# Health Plans & Goals System
from .health_plans import (
    HealthPlan,
    HealthPlanAssignment,
    Goal,
    GoalTracking,
    GoalTrackingDetail,
    Task,
    TaskTracking,
    TaskTrackingDetail,
    HealthPlanRecommendation
)

# Medical Condition Updates
from .medical_condition_updates import MedicalConditionUpdate

# Health Metrics System (Templates and Analysis only)
from .health_metrics import (
    HealthAnalysis,
    HealthRecordSectionTemplate,
    HealthRecordMetricTemplate,
    MetricStatus,
    MetricTrend
)

# AI Analysis System
from .ai_analysis import AIAnalysisHistory

# Permission System
from .permissions import (
    Permission,
    PermissionAuditLog,
    HealthRecordPermission,
    DocumentPermission,
    PermissionType,
    PermissionLevel,
    PermissionStatus
)

# Legacy Models (to be removed or updated)
from .medication import Medication
from .health_plan_progress import HealthPlanProgress
from .patient_insight import PatientInsight
from .statistics import ProfessionalStatistics

__all__ = [
    "Base",
    
    # Core User Models
    "User",
    "Patient", 
    "Professional",
    
    # Professional Practice System
    "ProfessionalPractice",
    "ProfessionalLocation",
    "ProfessionalAvailabilitySchedule",
    "ProfessionalAppointmentSlot",
    
    # Appointment System
    "AppointmentType",
    "AppointmentTypePricing",
    "ManualAppointment",
    "Appointment",
    "AppointmentReminder",

    
    # Professional Document Management (Legacy - to be replaced)
    "ProfessionalDocumentCategory",
    "ProfessionalDocument",
    "ProfessionalDocumentShare",
    "ProfessionalDocumentAccessLog",
    "ProfessionalDocumentAssignment",
    
    # Centralized Document Management System
    "Document",
    "DocumentPermission",
    "DocumentShare",
    "DocumentAccessLog",
    "LabDocument",
    "ImagingDocument",
    "PrescriptionDocument",
    "HealthRecordPermission",
    "DocumentCategory",
    "DocumentStatus",
    "PermissionLevel",
    "ShareType",
    
    # S3 Storage Management
    "S3StorageInfo",
    "S3BucketInfo",
    "S3AccessLog",
    
    # Messaging System
    "Message",
    
    # Payment System
    "SubscriptionPlan",
    "UserSubscription",
    "PaymentTransaction",
    
    # Health Records System
    "HealthRecordType",
    "HealthRecordSection",
    "HealthRecordMetric",
    "HealthRecord",
    "MedicalDocument",
    "MedicalCondition",
    "FamilyMedicalHistory",
    "IOSDevice",
    "HealthDataPermission",
    "IOSSyncLog",
    
    # Health Record Enums
    "VitalMetric",
    "LifestyleMetric",
    "BodyMetric",
    "MedicalConditionStatus",
    "FamilyHistoryStatus",
    "DocumentType",
    "AnalysisCategory",
    "VitalStatus",
    "LifestyleStatus",
    "BodyStatus",
    "ConditionSeverity",
    "ConditionSource",
    "FamilyRelation",
    "FamilyHistorySource",
    "DocumentSource",
    "AnalysisStatus",
    "AnalysisSource",
    
    # Health Plans & Goals System
    "HealthPlan",
    "HealthPlanAssignment",
    "Goal",
    "GoalTracking",
    "GoalTrackingDetail",
    "Task",
    "TaskTracking",
    "TaskTrackingDetail",
    "HealthPlanRecommendation",
    
    # Medical Condition Updates
    "MedicalConditionUpdate",
    
    # Health Metrics System (Templates and Analysis only)
    "HealthAnalysis",
    "HealthRecordSectionTemplate",
    "HealthRecordMetricTemplate",
    "MetricStatus",
    "MetricTrend",
    
    # AI Analysis System
    "AIAnalysisHistory",
    
    # Permission System
    "Permission",
    "PermissionAuditLog",
    "HealthRecordPermission",
    "DocumentPermission",
    "PermissionType",
    "PermissionLevel",
    "PermissionStatus",
    
    # Legacy Models
    "Medication",
    "HealthPlanProgress",
    "PatientInsight",
    "ProfessionalStatistics"
] 