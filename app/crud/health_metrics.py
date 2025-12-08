from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.models.health_metrics import (
    HealthAnalysis,
    HealthRecordSectionTemplate,
    HealthRecordMetricTemplate,
    MetricStatus,
    MetricTrend
)
from app.models.health_record import (
    HealthRecordSection,
    HealthRecordMetric,
    HealthRecord
)
from app.schemas.health_metrics import (
    HealthAnalysisCreate,
    HealthAnalysisUpdate,
    HealthRecordSectionTemplateCreate,
    HealthRecordSectionTemplateUpdate,
    HealthRecordMetricTemplateCreate,
    HealthRecordMetricTemplateUpdate
)

# Note: Health Metric Section, Health Metric, and Health Metric Data Point CRUD functions removed
# These are now handled by the existing health_records system CRUD functions

# Health Record Template CRUD Functions
def create_health_record_section_template(db: Session, template: HealthRecordSectionTemplateCreate, user_id: int) -> HealthRecordSectionTemplate:
    """Create a new health record section template"""
    # Note: In sync context, default to 'en' for source_language
    # This is acceptable as source_language is mainly for tracking original language
    source_language = 'en'
    
    db_template = HealthRecordSectionTemplate(
        name=template.name,
        display_name=template.display_name,
        description=template.description,
        source_language=source_language,
        health_record_type_id=template.health_record_type_id,
        created_by=user_id
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

def get_health_record_section_templates(db: Session, health_record_type_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[HealthRecordSectionTemplate]:
    """Get health record section templates, optionally filtered by type"""
    query = db.query(HealthRecordSectionTemplate).filter(HealthRecordSectionTemplate.is_active == True)
    
    if health_record_type_id is not None:
        query = query.filter(HealthRecordSectionTemplate.health_record_type_id == health_record_type_id)
    
    return query.offset(skip).limit(limit).all()

def get_health_record_metric_templates(db: Session, section_template_id: int) -> List[HealthRecordMetricTemplate]:
    """Get metric templates for a specific section template"""
    return db.query(HealthRecordMetricTemplate).filter(
        HealthRecordMetricTemplate.section_template_id == section_template_id,
        HealthRecordMetricTemplate.is_active == True
    ).all()

def search_health_record_metric_templates(db: Session, query: str, limit: int = 10) -> List[HealthRecordMetricTemplate]:
    """Search metric templates by name"""
    return db.query(HealthRecordMetricTemplate).filter(
        HealthRecordMetricTemplate.name.ilike(f"%{query}%"),
        HealthRecordMetricTemplate.is_active == True
    ).limit(limit).all()

# Health Analysis CRUD
def create_health_analysis(db: Session, analysis: HealthAnalysisCreate, user_id: int) -> HealthAnalysis:
    db_analysis = HealthAnalysis(
        user_id=user_id,
        analysis_date=analysis.analysis_date,
        analysis_type=analysis.analysis_type,
        insights=analysis.insights,
        areas_of_concern=analysis.areas_of_concern,
        positive_trends=analysis.positive_trends,
        recommendations=analysis.recommendations
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis

def get_health_analyses(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[HealthAnalysis]:
    return db.query(HealthAnalysis).filter(
        HealthAnalysis.user_id == user_id,
        HealthAnalysis.is_active == True
    ).order_by(desc(HealthAnalysis.analysis_date)).offset(skip).limit(limit).all()

def get_health_analysis_by_id(db: Session, analysis_id: int, user_id: int) -> Optional[HealthAnalysis]:
    return db.query(HealthAnalysis).filter(
        HealthAnalysis.id == analysis_id,
        HealthAnalysis.user_id == user_id,
        HealthAnalysis.is_active == True
    ).first()

def update_health_analysis(db: Session, analysis_id: int, analysis_update: HealthAnalysisUpdate, user_id: int) -> Optional[HealthAnalysis]:
    db_analysis = get_health_analysis_by_id(db, analysis_id, user_id)
    if not db_analysis:
        return None
    
    update_data = analysis_update.dict(exclude_unset=True)
    update_data["updated_by"] = user_id
    
    for field, value in update_data.items():
        setattr(db_analysis, field, value)
    
    db.commit()
    db.refresh(db_analysis)
    return db_analysis

def delete_health_analysis(db: Session, analysis_id: int, user_id: int) -> bool:
    db_analysis = get_health_analysis_by_id(db, analysis_id, user_id)
    if not db_analysis:
        return False
    
    # Soft delete
    db_analysis.is_active = False
    db_analysis.updated_by = user_id
    db.commit()
    return True

# Health Record Template CRUD
def create_health_record_section_template(db: Session, template: HealthRecordSectionTemplateCreate, user_id: int) -> HealthRecordSectionTemplate:
    db_template = HealthRecordSectionTemplate(
        name=template.name,
        display_name=template.display_name,
        description=template.description,
        created_by=user_id
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

def create_health_record_metric_template(db: Session, template: HealthRecordMetricTemplateCreate, user_id: int) -> HealthRecordMetricTemplate:
    # Note: In sync context, default to 'en' for source_language
    # This is acceptable as source_language is mainly for tracking original language
    source_language = 'en'
    
    db_template = HealthRecordMetricTemplate(
        section_template_id=template.section_template_id,
        name=template.name,
        display_name=template.display_name,
        description=template.description,
        default_unit=template.default_unit,
        source_language=source_language,
        normal_range_min=template.normal_range_min,
        normal_range_max=template.normal_range_max,
        data_type=template.data_type,
        created_by=user_id
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

def get_health_record_section_templates(db: Session) -> List[HealthRecordSectionTemplate]:
    return db.query(HealthRecordSectionTemplate).filter(
        HealthRecordSectionTemplate.is_active == True
    ).order_by(HealthRecordSectionTemplate.name).all()

def get_health_record_metric_templates(db: Session, section_template_id: Optional[int] = None) -> List[HealthRecordMetricTemplate]:
    query = db.query(HealthRecordMetricTemplate).filter(HealthRecordMetricTemplate.is_active == True)
    if section_template_id:
        query = query.filter(HealthRecordMetricTemplate.section_template_id == section_template_id)
    return query.order_by(HealthRecordMetricTemplate.name).all()

def search_health_record_metric_templates(db: Session, query: str, limit: int = 10) -> List[HealthRecordMetricTemplate]:
    """Search for metric templates by name similarity"""
    return db.query(HealthRecordMetricTemplate).filter(
        and_(
            HealthRecordMetricTemplate.is_active == True,
            HealthRecordMetricTemplate.name.ilike(f"%{query}%")
        )
    ).limit(limit).all()

def get_metric_suggestions_from_existing(db: Session, user_id: int, metric_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get suggestions from existing user health records with similar metric names"""
    similar_metrics = db.query(HealthRecordMetric).join(HealthRecord).filter(
        and_(
            HealthRecord.created_by == user_id,
            HealthRecordMetric.name.ilike(f"%{metric_name}%")
        )
    ).limit(limit).all()
    
    # Group by name and get the most recent values
    suggestions = {}
    for metric in similar_metrics:
        if metric.name not in suggestions:
            suggestions[metric.name] = {
                "name": metric.name,
                "display_name": metric.display_name,
                "unit": metric.default_unit,
                "normal_range_min": None,  # Would need to parse from threshold JSON
                "normal_range_max": None,  # Would need to parse from threshold JSON
                "count": 1
            }
        else:
            suggestions[metric.name]["count"] += 1
    
    return list(suggestions.values())

def get_metric_suggestions_from_templates(db: Session, metric_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get suggestions from metric templates"""
    templates = search_health_record_metric_templates(db, metric_name, limit)
    
    suggestions = []
    for template in templates:
        suggestions.append({
            "type": "template",
            "name": template.name,
            "display_name": template.display_name,
            "unit": template.default_unit,
            "normal_range_min": template.normal_range_min,
            "normal_range_max": template.normal_range_max,
            "section_name": template.section_template.name
        })
    
    return suggestions

def get_analysis_dashboard_summary(db: Session, user_id: int) -> Dict[str, Any]:
    """Get summary statistics for analysis dashboard"""
    # Get total sections and metrics from health records
    total_sections = db.query(HealthRecordSection).filter(
        HealthRecordSection.created_by == user_id
    ).count()
    
    total_metrics = db.query(HealthRecordMetric).join(HealthRecordSection).filter(
        HealthRecordSection.created_by == user_id
    ).count()
    
    # Get total data points from health records
    total_data_points = db.query(HealthRecord).filter(
        HealthRecord.created_by == user_id
    ).count()
    
    # Get abnormal metrics count (would need to implement logic based on thresholds)
    abnormal_metrics = 0  # Placeholder - would need to implement based on health record status
    
    return {
        "total_sections": total_sections,
        "total_metrics": total_metrics,
        "total_data_points": total_data_points,
        "abnormal_metrics": abnormal_metrics,
        "normal_metrics": total_data_points - abnormal_metrics
    }