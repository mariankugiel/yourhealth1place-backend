from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class MetricStatus(str, enum.Enum):
    NORMAL = "normal"
    ABNORMAL = "abnormal"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class MetricTrend(str, enum.Enum):
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    UNKNOWN = "unknown"

# Note: HealthMetricSection, HealthMetric, and HealthMetricDataPoint models removed
# These are now handled by the existing health_records system:
# - HealthRecordSection (for sections)
# - HealthRecordMetric (for metrics) 
# - HealthRecord (for actual data points)

class HealthAnalysis(Base):
    __tablename__ = "health_analyses"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    analysis_date = Column(DateTime(timezone=True), nullable=False)
    analysis_type = Column(String(50), nullable=False)  # e.g., "comprehensive", "lab_review", "trend_analysis"
    insights = Column(JSON)  # Store AI insights and recommendations
    areas_of_concern = Column(JSON)  # Array of concerning metrics
    positive_trends = Column(JSON)  # Array of improving metrics
    recommendations = Column(JSON)  # Array of recommendations
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

# Template tables for admin-defined metric templates
class HealthRecordSectionTemplate(Base):
    __tablename__ = "health_record_sections_tmp"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)  # e.g., "Blood Work", "Chemistry Panel"
    display_name = Column(String(100), nullable=False)  # Display name in source language
    description = Column(Text)
    source_language = Column(String(10), nullable=False, default='en')  # Language of original content ('en', 'es', 'pt')
    health_record_type_id = Column(Integer, ForeignKey("health_record_type.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=True)  # True for admin pre-defined, False for user custom
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Admin who created this template
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    health_record_type = relationship("HealthRecordType")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    metric_templates = relationship("HealthRecordMetricTemplate", back_populates="section_template")

class HealthRecordMetricTemplate(Base):
    __tablename__ = "health_record_metrics_tmp"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    section_template_id = Column(Integer, ForeignKey("health_record_sections_tmp.id"), nullable=False)
    name = Column(String(100), nullable=False)  # e.g., "White Blood Cells"
    display_name = Column(String(100), nullable=False)  # Display name in source language
    description = Column(Text)
    default_unit = Column(String(20))  # Unit in source language (e.g., "K/uL")
    source_language = Column(String(10), nullable=False, default='en')  # Language of original content ('en', 'es', 'pt')
    original_reference = Column(Text)  # Store original reference string like "Men: <25%, Female: <35%"
    reference_data = Column(JSON)  # Store parsed reference data for all metrics (includes gender-specific when applicable)
    data_type = Column(String(50), default="number")  # "number", "json", "text", "boolean"
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=True)  # True for admin pre-defined, False for user custom
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Admin who created this template
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    section_template = relationship("HealthRecordSectionTemplate", back_populates="metric_templates")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
