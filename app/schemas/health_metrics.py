from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class MetricStatus(str, Enum):
    NORMAL = "normal"
    ABNORMAL = "abnormal"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class MetricTrend(str, Enum):
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    UNKNOWN = "unknown"

# Note: Health Metric Section schemas removed - using existing health_records system

# Note: Health Metric schemas removed - using existing health_records system

# Note: Health Metric Data Point schemas removed - using existing health_records system

# Analysis Schemas
class HealthAnalysisBase(BaseModel):
    analysis_date: datetime
    analysis_type: str = Field(..., max_length=50)
    insights: Optional[Dict[str, Any]] = None
    areas_of_concern: Optional[List[Dict[str, Any]]] = None
    positive_trends: Optional[List[Dict[str, Any]]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None

class HealthAnalysisCreate(HealthAnalysisBase):
    pass

class HealthAnalysisUpdate(BaseModel):
    analysis_date: Optional[datetime] = None
    analysis_type: Optional[str] = Field(None, max_length=50)
    insights: Optional[Dict[str, Any]] = None
    areas_of_concern: Optional[List[Dict[str, Any]]] = None
    positive_trends: Optional[List[Dict[str, Any]]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None

class HealthAnalysisResponse(HealthAnalysisBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

# Combined Response Schemas for Frontend
class MetricWithData(BaseModel):
    id: int
    name: str
    unit: Optional[str] = None
    normal_range_min: Optional[float] = None
    normal_range_max: Optional[float] = None
    current_value: Optional[float] = None
    current_status: Optional[MetricStatus] = None
    trend: Optional[MetricTrend] = None
    change_from_previous: Optional[float] = None
    data_points: List[dict] = []  # Using dict since HealthMetricDataPointResponse was removed

class SectionWithMetrics(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    display_order: int
    metrics: List[MetricWithData] = []

class AnalysisDashboardResponse(BaseModel):
    sections: List[SectionWithMetrics] = []
    latest_analysis: Optional[HealthAnalysisResponse] = None
    summary_stats: Optional[Dict[str, Any]] = None

# Health Record Template Schemas
class HealthRecordSectionTemplateCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    health_record_type_id: int

class HealthRecordSectionTemplateUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    health_record_type_id: Optional[int] = None
    is_active: Optional[bool] = None

class HealthRecordSectionTemplateResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    health_record_type_id: int
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None
    metric_templates: List['HealthRecordMetricTemplateResponse'] = []

    class Config:
        from_attributes = True

class HealthRecordMetricTemplateCreate(BaseModel):
    section_template_id: int
    name: str
    display_name: str
    description: Optional[str] = None
    default_unit: Optional[str] = None
    normal_range_min: Optional[float] = None
    normal_range_max: Optional[float] = None
    data_type: str = "number"

class HealthRecordMetricTemplateUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    default_unit: Optional[str] = None
    normal_range_min: Optional[float] = None
    normal_range_max: Optional[float] = None
    data_type: Optional[str] = None
    is_active: Optional[bool] = None

class HealthRecordMetricTemplateResponse(BaseModel):
    id: int
    section_template_id: int
    name: str
    display_name: str
    description: Optional[str] = None
    default_unit: Optional[str] = None
    normal_range_min: Optional[float] = None
    normal_range_max: Optional[float] = None
    data_type: str
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

# Update the forward reference
HealthRecordSectionTemplateResponse.model_rebuild()
