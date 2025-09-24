from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.core.database import get_db
from app.models.user import User
from app.services.health_record_analytics_service import health_record_analytics_service
from app.api.v1.endpoints.auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================================================
# HEALTH RECORD ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/trends/{metric_name}")
async def get_health_metric_trends(
    metric_name: str,
    days: int = Query(30, description="Number of days to analyze", ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trend analysis for a specific health metric"""
    try:
        trends = health_record_analytics_service.get_trend_analysis(
            db=db,
            user_id=current_user.id,
            metric_name=metric_name,
            days=days
        )
        
        if "error" in trends:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=trends["error"]
            )
        
        return trends
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get health metric trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze trends: {str(e)}"
        )

@router.get("/correlation/{metric1}/{metric2}")
async def get_metric_correlation(
    metric1: str,
    metric2: str,
    days: int = Query(30, description="Number of days to analyze", ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get correlation analysis between two health metrics"""
    try:
        correlation = health_record_analytics_service.get_correlation_analysis(
            db=db,
            user_id=current_user.id,
            metric1=metric1,
            metric2=metric2,
            days=days
        )
        
        if "error" in correlation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=correlation["error"]
            )
        
        return correlation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metric correlation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze correlation: {str(e)}"
        )

@router.get("/health-score")
async def get_health_score(
    days: int = Query(30, description="Number of days to analyze", ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall health score based on various metrics"""
    try:
        health_score = health_record_analytics_service.get_health_score(
            db=db,
            user_id=current_user.id,
            days=days
        )
        
        if "error" in health_score:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=health_score["error"]
            )
        
        return health_score
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get health score: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate health score: {str(e)}"
        )

@router.get("/trends/vital-signs")
async def get_vital_signs_trends(
    days: int = Query(30, description="Number of days to analyze", ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trends for all vital signs metrics"""
    try:
        from app.models.health_record import VitalMetric
        
        vital_metrics = [metric.value for metric in VitalMetric]
        trends = {}
        
        for metric in vital_metrics:
            trend_data = health_record_analytics_service.get_trend_analysis(
                db=db,
                user_id=current_user.id,
                metric_name=metric,
                days=days
            )
            
            if "error" not in trend_data:
                trends[metric] = trend_data
        
        return {
            "period_days": days,
            "vital_signs_trends": trends,
            "summary": {
                "total_metrics": len(vital_metrics),
                "metrics_with_data": len(trends),
                "metrics_without_data": len(vital_metrics) - len(trends)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get vital signs trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze vital signs trends: {str(e)}"
        )

@router.get("/trends/lifestyle")
async def get_lifestyle_trends(
    days: int = Query(30, description="Number of days to analyze", ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trends for all lifestyle metrics"""
    try:
        from app.models.health_record import LifestyleMetric
        
        lifestyle_metrics = [metric.value for metric in LifestyleMetric]
        trends = {}
        
        for metric in lifestyle_metrics:
            trend_data = health_record_analytics_service.get_trend_analysis(
                db=db,
                user_id=current_user.id,
                metric_name=metric,
                days=days
            )
            
            if "error" not in trend_data:
                trends[metric] = trend_data
        
        return {
            "period_days": days,
            "lifestyle_trends": trends,
            "summary": {
                "total_metrics": len(lifestyle_metrics),
                "metrics_with_data": len(trends),
                "metrics_without_data": len(lifestyle_metrics) - len(trends)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get lifestyle trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze lifestyle trends: {str(e)}"
        )

@router.get("/trends/body-composition")
async def get_body_composition_trends(
    days: int = Query(30, description="Number of days to analyze", ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trends for all body composition metrics"""
    try:
        from app.models.health_record import BodyMetric
        
        body_metrics = [metric.value for metric in BodyMetric]
        trends = {}
        
        for metric in body_metrics:
            trend_data = health_record_analytics_service.get_trend_analysis(
                db=db,
                user_id=current_user.id,
                metric_name=metric,
                days=days
            )
            
            if "error" not in trend_data:
                trends[metric] = trend_data
        
        return {
            "period_days": days,
            "body_composition_trends": trends,
            "summary": {
                "total_metrics": len(body_metrics),
                "metrics_with_data": len(trends),
                "metrics_without_data": len(body_metrics) - len(trends)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get body composition trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze body composition trends: {str(e)}"
        )

@router.get("/comprehensive-analysis")
async def get_comprehensive_health_analysis(
    days: int = Query(30, description="Number of days to analyze", ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive health analysis including trends, correlations, and health score"""
    try:
        # Get health score
        health_score = health_record_analytics_service.get_health_score(
            db=db,
            user_id=current_user.id,
            days=days
        )
        
        # Get key metric trends
        key_metrics = ["heart_rate", "blood_pressure", "weight", "steps", "sleep"]
        trends = {}
        
        for metric in key_metrics:
            trend_data = health_record_analytics_service.get_trend_analysis(
                db=db,
                user_id=current_user.id,
                metric_name=metric,
                days=days
            )
            
            if "error" not in trend_data:
                trends[metric] = trend_data
        
        # Get some key correlations
        correlations = {}
        correlation_pairs = [
            ("steps", "sleep"),
            ("weight", "steps"),
            ("heart_rate", "steps")
        ]
        
        for metric1, metric2 in correlation_pairs:
            correlation_data = health_record_analytics_service.get_correlation_analysis(
                db=db,
                user_id=current_user.id,
                metric1=metric1,
                metric2=metric2,
                days=days
            )
            
            if "error" not in correlation_data:
                correlations[f"{metric1}_vs_{metric2}"] = correlation_data
        
        return {
            "period_days": days,
            "health_score": health_score,
            "key_trends": trends,
            "key_correlations": correlations,
            "analysis_summary": {
                "overall_health": health_score.get("health_status", "Unknown"),
                "trends_analyzed": len(trends),
                "correlations_analyzed": len(correlations),
                "data_quality": "Good" if len(trends) >= 3 else "Limited"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get comprehensive health analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate comprehensive analysis: {str(e)}"
        )

@router.get("/export/{format}")
async def export_health_data(
    format: str = Path(..., description="Export format", regex="^(json|csv)$"),
    days: int = Query(30, description="Number of days to export", ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export health data in specified format"""
    try:
        from datetime import datetime, timedelta
        from app.crud.health_record import health_record_crud
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get health records
        records = health_record_crud.get_by_user(
            db=db,
            user_id=current_user.id,
            limit=1000,  # Large limit for export
            filters=None  # TODO: Add date filter support
        )
        
        # Filter by date
        filtered_records = [
            record for record in records 
            if start_date <= record.recorded_at <= end_date
        ]
        
        if format == "json":
            export_data = [
                {
                    "id": record.id,
                    "section_id": record.section_id,
                    "metric_id": record.metric_id,
                    "value": record.value,
                    "status": record.status,
                    "source": record.source,
                    "recorded_at": record.recorded_at.isoformat(),
                    "device_id": record.device_id,
                    "device_info": record.device_info,
                    "accuracy": record.accuracy,
                    "location_data": record.location_data
                } for record in filtered_records
            ]
            
            return {
                "format": "json",
                "period_days": days,
                "total_records": len(export_data),
                "export_date": datetime.now().isoformat(),
                "data": export_data
            }
        
        elif format == "csv":
            # For CSV, return data that can be converted to CSV format
            # In a real implementation, you might want to use a CSV library
            csv_data = [
                {
                    "id": record.id,
                    "section_id": record.section_id,
                    "metric_id": record.metric_id,
                    "value": str(record.value),
                    "status": record.status,
                    "source": record.source,
                    "recorded_at": record.recorded_at.isoformat(),
                    "device_id": record.device_id,
                    "accuracy": record.accuracy
                } for record in filtered_records
            ]
            
            return {
                "format": "csv",
                "period_days": days,
                "total_records": len(csv_data),
                "export_date": datetime.now().isoformat(),
                "data": csv_data,
                "note": "Data formatted for CSV conversion. Use appropriate CSV library to convert."
            }
        
    except Exception as e:
        logger.error(f"Failed to export health data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export health data: {str(e)}"
        )
