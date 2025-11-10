from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.services.ai_analysis_service import ai_analysis_service
from app.crud.ai_analysis import ai_analysis_history_crud

logger = logging.getLogger(__name__)

router = APIRouter()

class AIAnalysisRequest(BaseModel):
    health_record_type_id: int = 1
    force_check: bool = False
    patient_id: Optional[int] = None

@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_health_data(
    request: AIAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered health analysis for the current user or a specific patient (if permission granted)
    
    Args:
        request: AI analysis request containing health_record_type_id, force_check, and optional patient_id
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AI analysis results with insights, recommendations, and assessments
    """
    try:
        # Determine target user ID
        target_user_id = current_user.id
        
        if request.patient_id:
            # Check permissions
            from app.core.patient_access import check_patient_access
            
            has_access, error_message = await check_patient_access(
                db=db,
                patient_id=request.patient_id,
                current_user=current_user,
                permission_type="view_health_records"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_message or "You don't have permission to access this patient's health records"
                )
            
            target_user_id = request.patient_id
            logger.info(f"Generating AI analysis for patient {request.patient_id} (requested by user {current_user.id})")
        
        # Generate AI analysis
        analysis_result = await ai_analysis_service.analyze_health_data(
            db=db,
            user_id=target_user_id,
            health_record_type_id=request.health_record_type_id,
            force_check=request.force_check
        )
        
        if not analysis_result.get("success", False):
            message = analysis_result.get("message", "Unknown error")

            # Treat "no data" or fallback analysis as normal 200 responses.
            if "No health" in message and "found for analysis" in message:
                logger.info(f"No health data found for user {current_user.id} (type {request.health_record_type_id}): {message}")
                return analysis_result

            if message.startswith("AI analysis failed:"):
                logger.warning(f"AI analysis fell back to local mode for user {current_user.id}: {message}")
                return analysis_result

            logger.warning(f"AI analysis failed for user {current_user.id}: {message}")
            logger.info(f"Returning 500 error with analysis result: {analysis_result}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=message
            )
        
        logger.info(f"AI analysis completed successfully for user {current_user.id}")
        logger.info(f"Returning analysis result: {analysis_result}")
        return analysis_result
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in AI analysis for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during AI analysis: {str(e)}"
        )

@router.get("/status", response_model=Dict[str, Any])
async def get_ai_analysis_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get the status of AI analysis service
    
    Returns:
        Service status and configuration information
    """
    try:
        return {
            "service_status": "active",
            "model": ai_analysis_service.model,
            "features": [
                "health_data_analysis",
                "trend_identification", 
                "risk_assessment",
                "personalized_recommendations",
                "overall_health_assessment"
            ],
            "supported_data_types": [
                "lab_results",
                "vital_signs",
                "body_composition",
                "lifestyle_metrics"
            ]
        }
    except Exception as e:
        logger.error(f"Error getting AI analysis status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting AI analysis status: {str(e)}"
        )

@router.get("/check-new-records", response_model=Dict[str, Any])
async def check_for_new_records(
    health_record_type_id: int = 1,
    patient_id: Optional[int] = Query(None, description="Patient ID to access (requires permission)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if there are new health records since the last AI analysis
    
    Args:
        health_record_type_id: Health record type ID to check
        patient_id: Optional patient ID to check (requires permission)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Information about whether there are new records and the reason
    """
    try:
        # Determine target user ID
        target_user_id = current_user.id
        
        if patient_id:
            # Check permissions
            from app.core.patient_access import check_patient_access
            
            has_access, error_message = await check_patient_access(
                db=db,
                patient_id=patient_id,
                current_user=current_user,
                permission_type="view_health_records"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_message or "You don't have permission to access this patient's health records"
                )
            
            target_user_id = patient_id
            logger.info(f"Checking for new records for patient {patient_id} (requested by user {current_user.id}), type {health_record_type_id}")
        else:
            logger.info(f"Checking for new records for user {current_user.id}, type {health_record_type_id}")
        
        # Get user's health data to count current records
        health_data = await ai_analysis_service._get_user_health_data(db, target_user_id, health_record_type_id)
        
        if not health_data:
            logger.info("No health data found")
            return {
                "hasNewRecords": False,
                "reason": "No health data found"
            }
        
        # Count current health records
        current_health_record_count = 0
        latest_health_record_updated_at = None
        
        for section in health_data.get("sections", []):
            for metric in section.get("metrics", []):
                data_points = metric.get("data_points", [])
                current_health_record_count += len(data_points)
                
                for data_point in data_points:
                    if data_point.get("recorded_at"):
                        from datetime import datetime
                        record_time = datetime.fromisoformat(data_point["recorded_at"].replace('Z', '+00:00'))
                        if not latest_health_record_updated_at or record_time > latest_health_record_updated_at:
                            latest_health_record_updated_at = record_time
        
        logger.info(f"Current health record count: {current_health_record_count}, latest update: {latest_health_record_updated_at}")
        
        # Get the latest analysis history to compare
        latest_analysis = ai_analysis_history_crud.get_by_user_and_type(db, target_user_id, health_record_type_id)
        
        if not latest_analysis:
            logger.info("No previous analysis found")
            return {
                "hasNewRecords": True,
                "reason": "No previous analysis found"
            }
        
        logger.info(f"Last analysis: count={latest_analysis.last_health_record_count}, updated_at={latest_analysis.last_health_record_updated_at}")
        
        # Check if there are new records (without 5-day rule)
        has_new_records = current_health_record_count > latest_analysis.last_health_record_count
        
        # Check if health records were updated since last analysis
        has_updated_records = False
        if latest_health_record_updated_at and latest_analysis.last_health_record_updated_at:
            # Ensure both datetimes have the same timezone info
            if latest_health_record_updated_at.tzinfo is None:
                latest_health_record_updated_at = latest_health_record_updated_at.replace(tzinfo=latest_analysis.last_health_record_updated_at.tzinfo)
            elif latest_analysis.last_health_record_updated_at.tzinfo is None:
                latest_analysis.last_health_record_updated_at = latest_analysis.last_health_record_updated_at.replace(tzinfo=latest_health_record_updated_at.tzinfo)
            has_updated_records = latest_health_record_updated_at > latest_analysis.last_health_record_updated_at
        
        has_new_or_updated = has_new_records or has_updated_records
        
        logger.info(f"Has new records: {has_new_records}, has updated records: {has_updated_records}, has_new_or_updated: {has_new_or_updated}")
        
        if has_new_or_updated:
            reasons = []
            if has_new_records:
                reasons.append(f"new records ({current_health_record_count} vs {latest_analysis.last_health_record_count})")
            if has_updated_records:
                reasons.append("updated records")
            reason = f"Has {' + '.join(reasons)}"
        else:
            reason = f"No new information since last analysis ({current_health_record_count} records)"
        
        logger.info(f"Returning: hasNewRecords={has_new_or_updated}, reason={reason}")
        
        return {
            "hasNewRecords": has_new_or_updated,
            "reason": reason
        }
        
    except Exception as e:
        logger.error(f"Error checking for new records: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking for new records: {str(e)}"
        )
