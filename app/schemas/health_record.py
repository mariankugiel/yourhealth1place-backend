from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

# ============================================================================
# ENUM IMPORTS
# ============================================================================

from app.models.health_record import (
    VitalMetric, LifestyleMetric, BodyMetric, MedicalConditionStatus, 
    FamilyHistoryStatus, DocumentType, AnalysisCategory, VitalStatus,
    LifestyleStatus, BodyStatus, ConditionSeverity, ConditionSource,
    FamilyRelation, FamilyHistorySource, DocumentSource, AnalysisStatus,
    AnalysisSource
)

# ============================================================================
# BASE HEALTH RECORD SCHEMAS
# ============================================================================

class HealthRecordBase(BaseModel):
    user_id: int

class HealthRecordCreate(HealthRecordBase):
    created_by: int

class HealthRecordUpdate(BaseModel):
    pass

class HealthRecordResponse(HealthRecordBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: int
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

# ============================================================================
# VITAL SIGNS SCHEMAS
# ============================================================================

class VitalSignsBase(BaseModel):
    health_record_id: int
    metric: VitalMetric
    value: Dict[str, Any]  # JSON for complex values like blood pressure
    unit: Optional[str] = None
    threshold: Optional[Dict[str, Any]] = None  # JSON for thresholds
    status: Optional[VitalStatus] = None
    source: Optional[str] = None
    recorded_at: datetime

class VitalSignsCreate(VitalSignsBase):
    created_by: int

class VitalSignsUpdate(BaseModel):
    value: Optional[Dict[str, Any]] = None
    unit: Optional[str] = None
    threshold: Optional[Dict[str, Any]] = None
    status: Optional[VitalStatus] = None
    source: Optional[str] = None
    recorded_at: Optional[datetime] = None

class VitalSignsResponse(VitalSignsBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: int
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

# ============================================================================
# LIFESTYLE METRICS SCHEMAS
# ============================================================================

class LifestyleMetricsBase(BaseModel):
    health_record_id: int
    metric: LifestyleMetric
    value: Dict[str, Any]  # JSON for complex values like sleep
    unit: Optional[str] = None
    threshold: Optional[Dict[str, Any]] = None  # JSON for thresholds
    status: Optional[LifestyleStatus] = None
    source: Optional[str] = None
    recorded_at: datetime

class LifestyleMetricsCreate(LifestyleMetricsBase):
    created_by: int

class LifestyleMetricsUpdate(BaseModel):
    value: Optional[Dict[str, Any]] = None
    unit: Optional[str] = None
    threshold: Optional[Dict[str, Any]] = None
    status: Optional[LifestyleStatus] = None
    source: Optional[str] = None
    recorded_at: Optional[datetime] = None

class LifestyleMetricsResponse(LifestyleMetricsBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: int
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

# ============================================================================
# BODY METRICS SCHEMAS
# ============================================================================

class BodyMetricsBase(BaseModel):
    health_record_id: int
    metric: BodyMetric
    value: Dict[str, Any]  # JSON for complex values like body composition
    unit: Optional[str] = None
    threshold: Optional[Dict[str, Any]] = None  # JSON for thresholds
    status: Optional[BodyStatus] = None
    metric_type: Optional[str] = None
    source: Optional[str] = None
    recorded_at: datetime

class BodyMetricsCreate(BodyMetricsBase):
    created_by: int

class BodyMetricsUpdate(BaseModel):
    value: Optional[Dict[str, Any]] = None
    unit: Optional[str] = None
    threshold: Optional[Dict[str, Any]] = None
    status: Optional[BodyStatus] = None
    metric_type: Optional[str] = None
    source: Optional[str] = None
    recorded_at: Optional[datetime] = None

class BodyMetricsResponse(BodyMetricsBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: int
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

# ============================================================================
# MEDICAL CONDITIONS SCHEMAS
# ============================================================================

class MedicalConditionsBase(BaseModel):
    health_record_id: int
    condition: str
    diagnosed_date: Optional[datetime] = None
    treatment_plan: Optional[str] = None
    status: Optional[MedicalConditionStatus] = None
    severity: Optional[ConditionSeverity] = None
    description: Optional[str] = None
    resolved_date: Optional[datetime] = None
    source: Optional[ConditionSource] = None

class MedicalConditionsCreate(MedicalConditionsBase):
    created_by: int

class MedicalConditionsUpdate(BaseModel):
    condition: Optional[str] = None
    diagnosed_date: Optional[datetime] = None
    treatment_plan: Optional[str] = None
    status: Optional[MedicalConditionStatus] = None
    severity: Optional[ConditionSeverity] = None
    description: Optional[str] = None
    resolved_date: Optional[datetime] = None
    source: Optional[ConditionSource] = None

class MedicalConditionsResponse(MedicalConditionsBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: int
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

# ============================================================================
# FAMILY MEDICAL HISTORY SCHEMAS
# ============================================================================

class FamilyMedicalHistoryBase(BaseModel):
    health_record_id: int
    condition: str
    relation: FamilyRelation
    age_of_onset: Optional[int] = None
    description: Optional[str] = None
    outcome: Optional[str] = None
    status: Optional[FamilyHistoryStatus] = None
    source: Optional[FamilyHistorySource] = None

class FamilyMedicalHistoryCreate(FamilyMedicalHistoryBase):
    created_by: int

class FamilyMedicalHistoryUpdate(BaseModel):
    condition: Optional[str] = None
    relation: Optional[FamilyRelation] = None
    age_of_onset: Optional[int] = None
    description: Optional[str] = None
    outcome: Optional[str] = None
    status: Optional[FamilyHistoryStatus] = None
    source: Optional[FamilyHistorySource] = None

class FamilyMedicalHistoryResponse(FamilyMedicalHistoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: int
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

# ============================================================================
# MEDICAL DOCUMENTS SCHEMAS
# ============================================================================

class MedicalDocumentsBase(BaseModel):
    health_record_id: int
    document_type: DocumentType
    file_name: str
    s3_url: Optional[str] = None
    file_type: Optional[str] = None
    description: Optional[str] = None
    source: Optional[DocumentSource] = None
    uploaded_at: datetime

class MedicalDocumentsCreate(MedicalDocumentsBase):
    created_by: int

class MedicalDocumentsUpdate(BaseModel):
    document_type: Optional[DocumentType] = None
    file_name: Optional[str] = None
    s3_url: Optional[str] = None
    file_type: Optional[str] = None
    description: Optional[str] = None
    source: Optional[DocumentSource] = None
    uploaded_at: Optional[datetime] = None

class MedicalDocumentsResponse(MedicalDocumentsBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: int
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

# ============================================================================
# HEALTH ANALYSIS SCHEMAS (NEW - Meeting Requirement)
# ============================================================================

class HealthAnalysisBase(BaseModel):
    medical_document_id: int
    metric: str
    value: Dict[str, Any]  # JSON for complex values or simple numbers
    unit: Optional[str] = None
    threshold: Optional[Dict[str, Any]] = None  # JSON for thresholds
    status: Optional[AnalysisStatus] = None
    analysis_category: Optional[AnalysisCategory] = None
    lab_test_name: Optional[str] = None
    reference_range: Optional[Dict[str, Any]] = None  # JSON for reference ranges
    test_date: Optional[datetime] = None
    source: Optional[AnalysisSource] = None

class HealthAnalysisCreate(HealthAnalysisBase):
    created_by: int

class HealthAnalysisUpdate(BaseModel):
    metric: Optional[str] = None
    value: Optional[Dict[str, Any]] = None
    unit: Optional[str] = None
    threshold: Optional[Dict[str, Any]] = None
    status: Optional[AnalysisStatus] = None
    analysis_category: Optional[AnalysisCategory] = None
    lab_test_name: Optional[str] = None
    reference_range: Optional[Dict[str, Any]] = None
    test_date: Optional[datetime] = None
    source: Optional[AnalysisSource] = None

class HealthAnalysisResponse(HealthAnalysisBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: int
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

# ============================================================================
# COMPOSITE RESPONSE SCHEMAS
# ============================================================================

class HealthRecordWithDetails(HealthRecordResponse):
    vital_signs: List[VitalSignsResponse] = []
    lifestyle_metrics: List[LifestyleMetricsResponse] = []
    body_metrics: List[BodyMetricsResponse] = []
    medical_conditions: List[MedicalConditionsResponse] = []
    family_medical_history: List[FamilyMedicalHistoryResponse] = []
    medical_documents: List[MedicalDocumentsResponse] = []

class MedicalDocumentWithAnalysis(MedicalDocumentsResponse):
    analysis_metrics: List[HealthAnalysisResponse] = []

# ============================================================================
# SAMPLE DATA SCHEMAS FOR DOCUMENTATION
# ============================================================================

class BloodPressureValue(BaseModel):
    systolic: int
    diastolic: int

class BloodPressureThreshold(BaseModel):
    systolic: Dict[str, int]
    diastolic: Dict[str, int]

class SleepValue(BaseModel):
    hours: float
    quality: str
    deep_sleep_percentage: Optional[float] = None

class BodyCompositionValue(BaseModel):
    fat_percentage: float
    muscle_percentage: float
    bone_percentage: float
    water_percentage: float 