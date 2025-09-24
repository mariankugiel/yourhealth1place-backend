from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# ============================================================================
# ENUM IMPORTS
# ============================================================================

from app.models.health_record import (
    MedicalConditionStatus, 
    FamilyHistoryStatus, DocumentType,
    ConditionSeverity, ConditionSource,
    FamilyRelation, FamilyHistorySource,
    ImageType, ImageFindings
)

# ============================================================================
# HEALTH RECORD SCHEMAS (Updated to match actual models)
# ============================================================================

class HealthRecordBase(BaseModel):
    section_id: int
    metric_id: int
    value: Dict[str, Any] = Field(..., description="Flexible JSON value for the health metric")
    status: Optional[str] = Field(None, description="Status like normal, abnormal, excellent")
    source: Optional[str] = Field(None, description="Source like ios_app, manual_entry, lab_result")
    recorded_at: datetime = Field(..., description="When the measurement was taken")
    device_id: Optional[int] = Field(None, description="iOS device ID if applicable")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Device information JSON")
    accuracy: Optional[str] = Field(None, description="Accuracy level: high, medium, low")
    location_data: Optional[Dict[str, Any]] = Field(None, description="GPS coordinates if available")

class HealthRecordCreate(HealthRecordBase):
    pass

class HealthRecordUpdate(BaseModel):
    section_id: Optional[int] = None
    metric_id: Optional[int] = None
    value: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    source: Optional[str] = None
    recorded_at: Optional[datetime] = None
    device_id: Optional[int] = None
    device_info: Optional[Dict[str, Any]] = None
    accuracy: Optional[str] = None
    location_data: Optional[Dict[str, Any]] = None

class HealthRecordResponse(HealthRecordBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

# ============================================================================
# MEDICAL CONDITION SCHEMAS
# ============================================================================

class MedicalConditionBase(BaseModel):
    condition_name: str = Field(..., description="Name of the medical condition")
    description: Optional[str] = Field(None, description="Detailed description of the condition")
    diagnosed_date: Optional[datetime] = Field(None, description="When the condition was diagnosed")
    status: MedicalConditionStatus = Field(..., description="Current status of the condition")
    severity: Optional[ConditionSeverity] = Field(None, description="Severity level of the condition")
    source: Optional[ConditionSource] = Field(None, description="Source of the diagnosis")
    treatment_plan: Optional[str] = Field(None, description="Treatment plan details")
    current_medications: Optional[List[str]] = Field(None, description="List of current medications")
    outcome: Optional[str] = Field(None, description="Outcome or prognosis")
    resolved_date: Optional[datetime] = Field(None, description="When the condition was resolved")

class MedicalConditionCreate(MedicalConditionBase):
    pass

class MedicalConditionUpdate(BaseModel):
    condition_name: Optional[str] = None
    description: Optional[str] = None
    diagnosed_date: Optional[datetime] = None
    status: Optional[MedicalConditionStatus] = None
    severity: Optional[ConditionSeverity] = None
    source: Optional[ConditionSource] = None
    treatment_plan: Optional[str] = None
    current_medications: Optional[List[str]] = None
    outcome: Optional[str] = None
    resolved_date: Optional[datetime] = None

class MedicalConditionResponse(MedicalConditionBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

# ============================================================================
# FAMILY MEDICAL HISTORY SCHEMAS
# ============================================================================

class FamilyMedicalHistoryBase(BaseModel):
    condition_name: str = Field(..., description="Name of the family medical condition")
    relation: FamilyRelation = Field(..., description="Family relationship")
    age_of_onset: Optional[int] = Field(None, description="Age when condition started")
    description: Optional[str] = Field(None, description="Description of the condition")
    outcome: Optional[str] = Field(None, description="Outcome or current status")
    status: Optional[FamilyHistoryStatus] = Field(None, description="Current status of family member")
    source: Optional[FamilyHistorySource] = Field(None, description="Source of the information")

class FamilyMedicalHistoryCreate(FamilyMedicalHistoryBase):
    pass

class FamilyMedicalHistoryUpdate(BaseModel):
    condition_name: Optional[str] = None
    relation: Optional[FamilyRelation] = None
    age_of_onset: Optional[int] = None
    description: Optional[str] = None
    outcome: Optional[str] = None
    status: Optional[FamilyHistoryStatus] = None
    source: Optional[FamilyHistorySource] = None

class FamilyMedicalHistoryResponse(FamilyMedicalHistoryBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

# ============================================================================
# MEDICAL DOCUMENT SCHEMAS
# ============================================================================

class MedicalDocumentBase(BaseModel):
    health_record_type_id: int = Field(..., description="Type of health record")
    document_type: str = Field(..., description="Type of medical document")
    lab_test_name: Optional[str] = Field(None, description="Name of the lab test")
    lab_test_type: Optional[str] = Field(None, description="Type of lab test")
    lab_test_date: Optional[datetime] = Field(None, description="Date of the lab test")
    provider: Optional[str] = Field(None, description="Healthcare provider name")
    file_name: str = Field(..., description="Name of the uploaded file")
    s3_url: Optional[str] = Field(None, description="S3 URL of the stored document")
    file_type: Optional[str] = Field(None, description="File type/extension")
    description: Optional[str] = Field(None, description="Document description")
    source: Optional[str] = Field(None, description="Source of the document")

class MedicalDocumentCreate(BaseModel):
    health_record_type_id: int = Field(..., description="Type of health record")
    document_type: DocumentType = Field(..., description="Type of medical document")
    lab_test_name: Optional[str] = Field(None, description="Name of the lab test")
    lab_test_type: Optional[str] = Field(None, description="Type of lab test")
    lab_test_date: Optional[datetime] = Field(None, description="Date of the lab test")
    provider: Optional[str] = Field(None, description="Healthcare provider name")
    file_name: str = Field(..., description="Name of the uploaded file")
    s3_url: Optional[str] = Field(None, description="S3 URL of the stored document")
    file_type: Optional[str] = Field(None, description="File type/extension")
    description: Optional[str] = Field(None, description="Document description")
    source: Optional[str] = Field(None, description="Source of the document")

class MedicalDocumentUpdate(BaseModel):
    health_record_type_id: Optional[int] = None
    document_type: Optional[DocumentType] = None
    lab_test_name: Optional[str] = None
    lab_test_type: Optional[str] = None
    lab_test_date: Optional[datetime] = None
    provider: Optional[str] = None
    file_name: Optional[str] = None
    s3_url: Optional[str] = None
    file_type: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None

class MedicalDocumentResponse(MedicalDocumentBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

# ============================================================================
# SECTION AND METRIC SCHEMAS
# ============================================================================

class HealthRecordTypeBase(BaseModel):
    name: str = Field(..., description="Unique identifier for the health record type")
    display_name: str = Field(..., description="Human-readable name for the health record type")
    description: Optional[str] = Field(None, description="Detailed description of the health record type")
    is_active: bool = Field(True, description="Whether this type is currently active")

class HealthRecordTypeCreate(HealthRecordTypeBase):
    pass

class HealthRecordTypeUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class HealthRecordTypeResponse(HealthRecordTypeBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

class HealthRecordSectionBase(BaseModel):
    name: str = Field(..., description="Unique identifier for the section within a type")
    display_name: str = Field(..., description="Human-readable name for the section")
    description: Optional[str] = Field(None, description="Detailed description of the section")
    health_record_type_id: int = Field(..., description="ID of the parent health record type")
    is_default: bool = Field(True, description="Whether this is a default admin section or user custom")

class HealthRecordSectionCreate(HealthRecordSectionBase):
    pass

class HealthRecordSectionUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    health_record_type_id: Optional[int] = None
    is_default: Optional[bool] = None

class HealthRecordSectionResponse(HealthRecordSectionBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

class HealthRecordMetricBase(BaseModel):
    section_id: int = Field(..., description="ID of the parent section")
    name: str = Field(..., description="Unique identifier for the metric within a section")
    display_name: str = Field(..., description="Human-readable name for the metric")
    description: Optional[str] = Field(None, description="Detailed description of the metric")
    default_unit: Optional[str] = Field(None, description="Default unit of measurement")
    reference_data: Optional[Dict[str, Any]] = Field(None, description="Reference ranges and thresholds")
    data_type: str = Field(..., description="Data type: number, json, text, boolean")
    is_default: bool = Field(True, description="Whether this is a default admin metric or user custom")

class HealthRecordMetricCreate(HealthRecordMetricBase):
    pass

class HealthRecordMetricUpdate(BaseModel):
    section_id: Optional[int] = None
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    default_unit: Optional[str] = None
    reference_data: Optional[Dict[str, Any]] = None
    data_type: Optional[str] = None
    is_default: Optional[bool] = None

class HealthRecordMetricResponse(HealthRecordMetricBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

# ============================================================================
# COMPOSITE RESPONSE SCHEMAS
# ============================================================================

class HealthRecordWithDetails(HealthRecordResponse):
    section_name: Optional[str] = None
    metric_name: Optional[str] = None
    device_name: Optional[str] = None

class MedicalConditionWithDetails(MedicalConditionResponse):
    pass

class FamilyMedicalHistoryWithDetails(FamilyMedicalHistoryResponse):
    pass

class MedicalDocumentWithDetails(MedicalDocumentResponse):
    pass

# ============================================================================
# BULK OPERATION SCHEMAS
# ============================================================================

class BulkHealthRecordCreate(BaseModel):
    records: List[HealthRecordCreate] = Field(..., description="List of health records to create")

class BulkHealthRecordResponse(BaseModel):
    created_count: int
    failed_count: int
    created_records: List[HealthRecordResponse]
    failed_records: List[Dict[str, Any]]

# ============================================================================
# SEARCH AND FILTER SCHEMAS
# ============================================================================

class HealthRecordFilter(BaseModel):
    section_id: Optional[int] = None
    metric_id: Optional[int] = None
    status: Optional[str] = None
    source: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    device_id: Optional[int] = None

class HealthRecordSearch(BaseModel):
    query: str = Field(..., description="Search query for health records")
    filters: Optional[HealthRecordFilter] = None
    limit: int = Field(100, description="Maximum number of results")
    offset: int = Field(0, description="Number of results to skip")

# ============================================================================
# STATISTICS SCHEMAS
# ============================================================================

class HealthRecordStats(BaseModel):
    total_records: int
    records_by_section: Dict[str, int]
    records_by_source: Dict[str, int]
    records_by_status: Dict[str, int]
    recent_records: int  # Last 30 days
    average_records_per_day: float

# ============================================================================
# SAMPLE DATA SCHEMAS FOR DOCUMENTATION
# ============================================================================

class BloodPressureValue(BaseModel):
    systolic: int = Field(..., description="Systolic blood pressure")
    diastolic: int = Field(..., description="Diastolic blood pressure")

class BloodPressureThreshold(BaseModel):
    systolic: Dict[str, int] = Field(..., description="Systolic thresholds by category")
    diastolic: Dict[str, int] = Field(..., description="Diastolic thresholds by category")

class SleepValue(BaseModel):
    hours: float = Field(..., description="Hours of sleep")
    quality: str = Field(..., description="Sleep quality rating")
    deep_sleep_percentage: Optional[float] = Field(None, description="Percentage of deep sleep")

class BodyCompositionValue(BaseModel):
    fat_percentage: float = Field(..., description="Body fat percentage")
    muscle_percentage: float = Field(..., description="Muscle mass percentage")
    bone_percentage: float = Field(..., description="Bone density percentage")
    water_percentage: float = Field(..., description="Body water percentage") 

# ============================================================================
# ENHANCED HEALTH RECORD SCHEMAS
# ============================================================================

class MetricTrendData(BaseModel):
    """Schema for metric trend data"""
    id: int
    value: Dict[str, Any]
    status: Optional[str] = None
    recorded_at: datetime
    source: Optional[str] = None
    accuracy: Optional[str] = None

class MetricSummary(BaseModel):
    """Schema for metric summary data"""
    metric_id: int
    name: str
    display_name: str
    default_unit: Optional[str] = None
    recent_records: int
    total_records: int
    latest_value: Optional[Dict[str, Any]] = None
    latest_status: Optional[str] = None
    latest_recorded_at: Optional[datetime] = None

class SectionSummary(BaseModel):
    """Schema for section summary data"""
    section_id: int
    metrics: List[MetricSummary]
    total_records: int
    recent_activity: int

class PaginationInfo(BaseModel):
    """Schema for pagination information"""
    total: int
    skip: int
    limit: int
    has_more: bool
    total_pages: int
    current_page: int

class MetricRecordResponse(BaseModel):
    """Schema for individual metric record response"""
    id: int
    value: Dict[str, Any]
    status: Optional[str] = None
    source: Optional[str] = None
    recorded_at: datetime
    device_id: Optional[int] = None
    device_info: Optional[Dict[str, Any]] = None
    accuracy: Optional[str] = None
    location_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class PaginatedMetricRecords(BaseModel):
    """Schema for paginated metric records response"""
    records: List[MetricRecordResponse]
    pagination: PaginationInfo

class DailyAverage(BaseModel):
    """Schema for daily average data"""
    date: str
    average_value: float
    record_count: int

class MetricAnalytics(BaseModel):
    """Schema for metric analytics data"""
    metric_id: int
    total_records: int
    trend: str  # "increasing", "decreasing", "stable"
    average_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    status_distribution: Dict[str, int]
    source_distribution: Dict[str, int]
    daily_averages: List[DailyAverage]

class DashboardStats(BaseModel):
    """Schema for dashboard statistics"""
    total_records: int
    total_sections: int

class RecentRecord(BaseModel):
    """Schema for recent record data"""
    id: int
    section_id: int
    metric_id: int
    value: Dict[str, Any]
    status: Optional[str] = None
    recorded_at: datetime
    source: Optional[str] = None

class UserDashboardData(BaseModel):
    """Schema for complete user dashboard data"""
    user_id: int
    sections: List[SectionSummary]
    overall_stats: DashboardStats
    recent_records: List[RecentRecord]

# ============================================================================
# HEALTH RECORD IMAGE SCHEMAS
# ============================================================================

class HealthRecordImageBase(BaseModel):
    """Base schema for health record images"""
    image_type: ImageType = Field(..., description="Type of medical image (X-Ray, Ultrasound, MRI, CT Scan, Others)")
    body_part: str = Field(..., description="Body part imaged (e.g., Chest, Left Knee, Brain)")
    image_date: datetime = Field(..., description="When the image was taken/created")
    findings: ImageFindings = Field(..., description="Findings from the image analysis")
    conclusions: Optional[str] = Field(None, description="Text input for conclusions/notes")

class HealthRecordImageCreate(HealthRecordImageBase):
    """Schema for creating a new health record image (metadata only)"""
    interpretation: Optional[str] = Field(None, description="Medical interpretation of the image")
    doctor_name: Optional[str] = Field(None, description="Name of the doctor who analyzed the image")
    doctor_number: Optional[str] = Field(None, description="Doctor's license/ID number")
    original_filename: str = Field(..., description="Original filename of the uploaded file")
    file_size_bytes: int = Field(..., description="Size of the file in bytes")
    content_type: str = Field(..., description="MIME type of the file")
    s3_bucket: Optional[str] = Field(None, description="S3 bucket where the file is stored")
    s3_key: str = Field(..., description="S3 key/path of the file")
    s3_url: Optional[str] = Field(None, description="S3 URL of the file")
    file_id: Optional[str] = Field(None, description="Unique file identifier")

class HealthRecordImageUpload(BaseModel):
    """Schema for file upload with metadata"""
    image_type: ImageType = Field(..., description="Type of medical image")
    body_part: str = Field(..., description="Body part imaged")
    image_date: datetime = Field(..., description="When the image was taken")
    findings: ImageFindings = Field(..., description="Findings from the image analysis")
    conclusions: Optional[str] = Field(None, description="Text input for conclusions/notes")

class HealthRecordImageUpdate(BaseModel):
    """Schema for updating a health record image"""
    image_type: Optional[ImageType] = None
    body_part: Optional[str] = None
    image_date: Optional[datetime] = None
    findings: Optional[ImageFindings] = None
    conclusions: Optional[str] = None

class HealthRecordImageResponse(HealthRecordImageBase):
    """Schema for health record image response"""
    id: int
    created_by: int
    original_filename: str
    file_size_bytes: int
    content_type: str
    s3_bucket: Optional[str] = None
    s3_key: str
    s3_url: Optional[str] = None
    file_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

class HealthRecordImageSummary(BaseModel):
    """Schema for health record image summary (for lists/dashboards)"""
    id: int
    image_type: ImageType
    body_part: str
    image_date: datetime
    findings: ImageFindings
    conclusions: Optional[str] = None
    original_filename: str
    content_type: str
    file_size_bytes: int
    s3_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PaginatedImageResponse(BaseModel):
    """Schema for paginated image records response"""
    images: List[HealthRecordImageSummary]
    pagination: PaginationInfo 