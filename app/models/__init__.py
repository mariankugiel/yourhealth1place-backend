from app.core.database import Base

# Core User Models
from .user import User

# Professional Practice System
# ProfessionalPractice model removed - data now stored in Supabase user metadata
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
    ImagingDocument,
    PrescriptionDocument,
    DocumentCategory,
    DocumentStatus,
    PermissionLevel,
    ShareType
)

# S3 Storage Management - REMOVED

# Messaging System
from .message import Message, Conversation, MessageDeliveryLog, MessageAction, MessageType, MessagePriority, MessageStatus, SenderType

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
    HealthRecordDocLab,
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
    GeneralDocumentType,
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

# Medical Condition Updates - REMOVED (duplicate of medical_conditions)

# Health Metrics System (Templates and Analysis only)
from .health_metrics import (
    HealthAnalysis,
    HealthRecordSectionTemplate,
    HealthRecordMetricTemplate,
    MetricStatus,
    MetricTrend
)

# Surgery & Hospitalization System
from .surgery_hospitalization import (
    ProcedureType,
    RecoveryStatus,
    SurgeryHospitalization
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

# Medication Reminder System
from .medication_reminder import MedicationReminder, ReminderStatus
from .notification import Notification, NotificationType, NotificationStatus, NotificationPriority
from .notification_channel import NotificationChannel
from .websocket_connection import WebSocketConnection
from .web_push_subscription import WebPushSubscription
from .notification_delivery_log import NotificationDeliveryLog, DeliveryChannel, DeliveryStatus

__all__ = [
    "Base",
    
    # Core User Models
    "User",
    
    # Professional Practice System
    # ProfessionalPractice model removed
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
    "ImagingDocument",
    "PrescriptionDocument",
    "HealthRecordPermission",
    "DocumentCategory",
    "DocumentStatus",
    "PermissionLevel",
    "ShareType",
    
    # S3 Storage Management - REMOVED
    
    # Messaging System
    "Message",
    "Conversation",
    "MessageDeliveryLog",
    "MessageAction",
    "MessageType",
    "MessagePriority",
    "MessageStatus",
    "SenderType",
    
    # Payment System
    "SubscriptionPlan",
    "UserSubscription",
    "PaymentTransaction",
    
    # Health Records System
    "HealthRecordType",
    "HealthRecordSection",
    "HealthRecordMetric",
    "HealthRecord",
    "HealthRecordDocLab",
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
    "GeneralDocumentType",
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
    
    # Medical Condition Updates - REMOVED
    
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
    "ProfessionalStatistics",
    
    # Surgery & Hospitalization System
    "ProcedureType",
    "RecoveryStatus",
    "SurgeryHospitalization",
    
    # Medication Reminder System
    "MedicationReminder",
    "ReminderStatus",
    "Notification",
    "NotificationType",
    "NotificationStatus",
    "NotificationPriority",
    "NotificationChannel",
    "WebSocketConnection",
    "WebPushSubscription",
    "NotificationDeliveryLog",
    "DeliveryChannel",
    "DeliveryStatus"
] 