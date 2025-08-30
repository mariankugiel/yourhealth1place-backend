from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON, Float, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

# ============================================================================
# HEALTH RECORD TYPE ENUMS
# ============================================================================

class VitalMetric(str, enum.Enum):
    HEART_RATE = "heart_rate"
    BLOOD_PRESSURE = "blood_pressure"
    TEMPERATURE = "temperature"
    RESPIRATORY_RATE = "respiratory_rate"
    OXYGEN_SATURATION = "oxygen_saturation"
    BLOOD_GLUCOSE = "blood_glucose"
    WEIGHT = "weight"
    HEIGHT = "height"
    BMI = "bmi"

class LifestyleMetric(str, enum.Enum):
    STEPS = "steps"
    SLEEP = "sleep"
    EXERCISE = "exercise"
    NUTRITION = "nutrition"
    WATER_INTAKE = "water_intake"
    ALCOHOL_CONSUMPTION = "alcohol_consumption"
    SMOKING = "smoking"
    STRESS_LEVEL = "stress_level"
    MOOD = "mood"

class BodyMetric(str, enum.Enum):
    BODY_FAT = "body_fat"
    MUSCLE_MASS = "muscle_mass"
    BONE_DENSITY = "bone_density"
    WAIST_CIRCUMFERENCE = "waist_circumference"
    HIP_CIRCUMFERENCE = "hip_circumference"
    BODY_COMPOSITION = "body_composition"

class MedicalConditionStatus(str, enum.Enum):
    ACTIVE = "Active"
    RESOLVED = "Resolved"
    CHRONIC = "Chronic"
    REMISSION = "Remission"
    DECEASED = "Deceased"

class FamilyHistoryStatus(str, enum.Enum):
    ALIVE = "Alive"
    DECEASED = "Deceased"
    UNKNOWN = "Unknown"

class DocumentType(str, enum.Enum):
    LAB_RESULT = "lab_result"
    IMAGING = "imaging"
    PRESCRIPTION = "prescription"
    REFERRAL = "referral"
    DISCHARGE_SUMMARY = "discharge_summary"
    OPERATION_REPORT = "operation_report"
    PATHOLOGY_REPORT = "pathology_report"
    VACCINATION_RECORD = "vaccination_record"
    ALLERGY_TEST = "allergy_test"
    GENETIC_TEST = "genetic_test"

class AnalysisCategory(str, enum.Enum):
    TREND_ANALYSIS = "trend_analysis"
    PATTERN_DETECTION = "pattern_detection"
    ANOMALY_DETECTION = "anomaly_detection"
    CORRELATION_ANALYSIS = "correlation_analysis"
    PREDICTIVE_ANALYSIS = "predictive_analysis"

class VitalStatus(str, enum.Enum):
    NORMAL = "Normal"
    ELEVATED = "Elevated"
    HIGH = "High"
    LOW = "Low"
    CRITICAL = "Critical"

class LifestyleStatus(str, enum.Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"
    NEEDS_IMPROVEMENT = "Needs Improvement"

class BodyStatus(str, enum.Enum):
    HEALTHY = "Healthy"
    OVERWEIGHT = "Overweight"
    UNDERWEIGHT = "Underweight"
    OBESE = "Obese"
    ATHLETIC = "Athletic"

class ConditionSeverity(str, enum.Enum):
    MILD = "Mild"
    MODERATE = "Moderate"
    SEVERE = "Severe"
    CRITICAL = "Critical"

class ConditionSource(str, enum.Enum):
    DOCTOR_DIAGNOSIS = "Doctor Diagnosis"
    SELF_DIAGNOSIS = "Self Diagnosis"
    LAB_RESULTS = "Lab Results"
    IMAGING = "Imaging"
    GENETIC_TESTING = "Genetic Testing"
    FAMILY_HISTORY = "Family History"

class FamilyRelation(str, enum.Enum):
    FATHER = "Father"
    MOTHER = "Mother"
    SIBLING = "Sibling"
    GRANDPARENT = "Grandparent"
    CHILD = "Child"
    SPOUSE = "Spouse"

class FamilyHistorySource(str, enum.Enum):
    FAMILY_MEMBER = "Family Member"
    MEDICAL_RECORDS = "Medical Records"
    GENETIC_TESTING = "Genetic Testing"
    DOCTOR_INTERVIEW = "Doctor Interview"

class DocumentSource(str, enum.Enum):
    UPLOADED = "Uploaded"
    LAB_SYSTEM = "Lab System"
    HOSPITAL_SYSTEM = "Hospital System"
    PHARMACY = "Pharmacy"
    INSURANCE = "Insurance"
    PATIENT_PORTAL = "Patient Portal"

class AnalysisStatus(str, enum.Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    FAILED = "Failed"

class AnalysisSource(str, enum.Enum):
    AUTOMATED = "Automated"
    MANUAL = "Manual"
    AI_ANALYSIS = "AI Analysis"
    DOCTOR_REVIEW = "Doctor Review"

# ============================================================================
# HEALTH RECORD MODELS
# ============================================================================

class HealthRecordType(Base):
    __tablename__ = "health_record_type"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Admin user
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    sections = relationship("HealthRecordSection", back_populates="health_record_type")

class HealthRecordSection(Base):
    __tablename__ = "health_record_sections"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    health_record_type_id = Column(Integer, ForeignKey("health_record_type.id"), nullable=False)
    is_default = Column(Boolean, default=True)  # true = admin, false = user custom
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Admin user for predefined, regular user for custom
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    health_record_type = relationship("HealthRecordType", back_populates="sections")
    metrics = relationship("HealthRecordMetric", back_populates="section")
    health_records = relationship("HealthRecord", back_populates="section")

class HealthRecordMetric(Base):
    __tablename__ = "health_record_metrics"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    section_id = Column(Integer, ForeignKey("health_record_sections.id"), nullable=False)
    name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    default_unit = Column(String(20))
    threshold = Column(JSON)  # Reference ranges
    data_type = Column(String(50), nullable=False)  # "number", "json", "text", "boolean"
    is_default = Column(Boolean, default=True)  # true = admin, false = user custom
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Admin user for predefined, regular user for custom
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    section = relationship("HealthRecordSection", back_populates="metrics")
    health_records = relationship("HealthRecord", back_populates="metric")
    goals = relationship("Goal", back_populates="metric")

class HealthRecord(Base):
    __tablename__ = "health_records"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # User who owns and created this record
    section_id = Column(Integer, ForeignKey("health_record_sections.id"), nullable=False)
    metric_id = Column(Integer, ForeignKey("health_record_metrics.id"), nullable=False)
    value = Column(JSON, nullable=False)  # Flexible for numbers, objects, arrays
    status = Column(String(50))  # "normal", "abnormal", "excellent"
    source = Column(String(100))  # "ios_app", "manual_entry", "lab_result", "apple_watch", "fitbit"
    recorded_at = Column(DateTime, nullable=False)  # When measurement was taken
    
    # iOS Integration Fields
    device_id = Column(Integer, ForeignKey("ios_devices.id"))  # Link to ios_devices table
    device_info = Column(JSON)  # {device_name: "iPhone 15 Pro", device_model: "iPhone15,2", ios_version: "17.2.1", app_version: "1.0.0"}
    accuracy = Column(String(50))  # "high", "medium", "low" - for device data
    location_data = Column(JSON)  # GPS coordinates if available
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", foreign_keys=[created_by], back_populates="health_records")
    section = relationship("HealthRecordSection", back_populates="health_records")
    metric = relationship("HealthRecordMetric", back_populates="health_records")
    device = relationship("IOSDevice", back_populates="health_records")
    goal_tracking_details = relationship("GoalTrackingDetail", back_populates="health_record")
    task_tracking_details = relationship("TaskTrackingDetail", back_populates="health_record")

class MedicalDocument(Base):
    __tablename__ = "medical_documents"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # User who owns and uploaded this document
    health_record_type_id = Column(Integer, ForeignKey("health_record_type.id"), nullable=False)
    document_type = Column(String(50), nullable=False)
    lab_test_name = Column(String(200))
    lab_test_type = Column(String(100))
    lab_test_date = Column(DateTime)
    provider = Column(String(200))
    file_name = Column(String(255), nullable=False)
    s3_url = Column(Text)
    file_type = Column(String(20))
    description = Column(Text)
    source = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", foreign_keys=[created_by], backref="medical_documents")
    health_record_type = relationship("HealthRecordType", backref="medical_documents")

class MedicalCondition(Base):
    __tablename__ = "medical_conditions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # User who has this condition
    condition_name = Column(String(200), nullable=False)
    description = Column(Text)
    diagnosed_date = Column(DateTime)
    status = Column(Enum(MedicalConditionStatus), nullable=False)
    severity = Column(Enum(ConditionSeverity))
    source = Column(Enum(ConditionSource))
    treatment_plan = Column(Text)
    current_medications = Column(JSON)  # Array of medications
    outcome = Column(Text)
    resolved_date = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", foreign_keys=[created_by], backref="medical_conditions")

class FamilyMedicalHistory(Base):
    __tablename__ = "family_medical_history"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # User whose family history this is
    condition_name = Column(String(200), nullable=False)
    relation = Column(Enum(FamilyRelation), nullable=False)
    age_of_onset = Column(Integer)
    description = Column(Text)
    outcome = Column(Text)
    status = Column(Enum(FamilyHistoryStatus))
    source = Column(Enum(FamilyHistorySource))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", foreign_keys=[created_by], backref="family_medical_history")

# ============================================================================
# iOS INTEGRATION MODELS
# ============================================================================

class IOSDevice(Base):
    __tablename__ = "ios_devices"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Device Information
    device_name = Column(String(200))  # "iPhone 15 Pro", "iPad Air"
    device_model = Column(String(100))  # "iPhone15,2", "iPad13,2"
    device_type = Column(String(50))  # "iphone", "ipad", "apple_watch", "airpods", "mac"
    ios_version = Column(String(20))  # "17.2.1"
    app_version = Column(String(20))  # "1.0.0"
    
    # Unique Device Identification
    device_uuid = Column(String(255), nullable=False, unique=True)  # Unique device identifier
    device_token = Column(String(255))  # For push notifications
    advertising_id = Column(String(255))  # IDFA (if user allows)
    
    # Health Data Permissions
    health_kit_permissions = Column(JSON)  # {"heart_rate": "granted", "steps": "denied"}
    health_data_types = Column(JSON)  # ["heart_rate", "steps", "sleep"]
    
    # Sync Configuration
    sync_frequency_minutes = Column(Integer, default=15)  # How often to sync data
    auto_sync_enabled = Column(Boolean, default=True)
    last_sync_at = Column(DateTime)
    next_sync_at = Column(DateTime)
    
    # Device Status
    is_active = Column(Boolean, default=True)
    is_primary_device = Column(Boolean, default=False)  # User's main device
    last_seen_at = Column(DateTime)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="ios_devices")
    health_data_permissions = relationship("HealthDataPermission", back_populates="device")
    sync_logs = relationship("IOSSyncLog", back_populates="device")
    health_records = relationship("HealthRecord", back_populates="device")

class HealthDataPermission(Base):
    __tablename__ = "health_data_permissions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("ios_devices.id"), nullable=False)
    
    # Permission Details
    data_type = Column(String(50), nullable=False)  # "heart_rate", "steps", "sleep", "blood_pressure", "glucose", "weight", "activity", "nutrition", "medication", "mood"
    permission_status = Column(String(50), nullable=False, default="not_requested")  # "granted", "denied", "not_requested", "limited"
    granted_at = Column(DateTime)
    revoked_at = Column(DateTime)
    
    # Permission Scope
    read_permission = Column(Boolean, default=False)
    write_permission = Column(Boolean, default=False)
    share_permission = Column(Boolean, default=False)
    
    # Additional Context
    permission_reason = Column(Text)  # Why permission was requested
    user_notes = Column(Text)  # User's notes about this permission
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="health_data_permissions")
    device = relationship("IOSDevice", back_populates="health_data_permissions")

class IOSSyncLog(Base):
    __tablename__ = "ios_sync_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("ios_devices.id"), nullable=False)
    
    # Sync Details
    sync_type = Column(String(50), nullable=False)  # "manual", "automatic", "scheduled", "background"
    status = Column(String(50), nullable=False)  # "pending", "in_progress", "completed", "failed", "partial"
    
    # Data Statistics
    records_processed = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    data_types_synced = Column(JSON)  # ["heart_rate", "steps", "sleep"]
    
    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Error Handling
    error_message = Column(Text)
    error_code = Column(String(100))
    retry_count = Column(Integer, default=0)
    
    # Network Information
    network_type = Column(String(50))  # "wifi", "cellular", "ethernet"
    connection_quality = Column(String(20))  # "excellent", "good", "poor"
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="ios_sync_logs")
    device = relationship("IOSDevice", back_populates="sync_logs") 