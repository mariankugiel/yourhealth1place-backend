from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.core.database import get_db
from app.models.user import User
from app.schemas.document import (
    HealthRecordPermissionCreate, HealthRecordPermissionUpdate, 
    HealthRecordPermissionResponse
)
from app.services.health_record_permission_service import health_record_permission_service
from app.api.v1.endpoints.auth import get_current_user
import logging
from sqlalchemy import func

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================================================
# HEALTH RECORD PERMISSION ENDPOINTS
# ============================================================================

@router.post("/grant", response_model=HealthRecordPermissionResponse, status_code=status.HTTP_201_CREATED)
async def grant_health_record_permission(
    patient_id: int,
    professional_id: int,
    permissions: Dict[str, bool],
    granted_for: str = "consultation",
    expires_in_hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Grant health record access to a professional"""
    try:
        # Check if current user is the patient or has permission to grant access
        if current_user.id != patient_id:
            # TODO: Add admin permission check
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the patient can grant health record permissions"
            )
        
        # Grant temporary access
        permission = health_record_permission_service.grant_temporary_access(
            db=db,
            patient_id=patient_id,
            professional_id=professional_id,
            permissions=permissions,
            granter_id=current_user.id,
            granted_for=granted_for,
            expires_in_hours=expires_in_hours
        )
        
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to grant permission"
            )
        
        return HealthRecordPermissionResponse(
            id=permission.id,
            patient_id=permission.patient_id,
            professional_id=permission.professional_id,
            can_view_health_records=permission.can_view_health_records,
            can_view_medical_history=permission.can_view_medical_history,
            can_view_health_plans=permission.can_view_health_plans,
            can_view_medications=permission.can_view_medications,
            can_view_appointments=permission.can_view_appointments,
            can_view_messages=permission.can_view_messages,
            can_view_lab_results=permission.can_view_lab_results,
            can_view_imaging=permission.can_view_imaging,
            granted_for=permission.granted_for,
            expires_at=permission.expires_at,
            is_active=permission.is_active,
            granted_by=permission.granted_by,
            created_at=permission.created_at,
            updated_at=permission.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to grant health record permission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to grant permission: {str(e)}"
        )

@router.get("/check/{patient_id}/{professional_id}")
async def check_health_record_permission(
    patient_id: int,
    professional_id: int,
    access_type: str = Query("view", description="Type of access to check"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if a professional has access to a patient's health records"""
    try:
        # Check if current user is the professional or has permission to check
        if current_user.id != professional_id:
            # TODO: Add admin permission check
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only check your own permissions"
            )
        
        has_access, reason = health_record_permission_service.check_health_record_access(
            db=db,
            patient_id=patient_id,
            professional_id=professional_id,
            access_type=access_type
        )
        
        return {
            "has_access": has_access,
            "reason": reason,
            "patient_id": patient_id,
            "professional_id": professional_id,
            "access_type": access_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check health record permission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check permission: {str(e)}"
        )

@router.get("/check/medical-history/{patient_id}/{professional_id}")
async def check_medical_history_permission(
    patient_id: int,
    professional_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if a professional has access to a patient's medical history"""
    try:
        if current_user.id != professional_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only check your own permissions"
            )
        
        has_access, reason = health_record_permission_service.check_medical_history_access(
            db=db,
            patient_id=patient_id,
            professional_id=professional_id
        )
        
        return {
            "has_access": has_access,
            "reason": reason,
            "patient_id": patient_id,
            "professional_id": professional_id,
            "access_type": "medical_history"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check medical history permission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check permission: {str(e)}"
        )

@router.get("/check/health-plans/{patient_id}/{professional_id}")
async def check_health_plan_permission(
    patient_id: int,
    professional_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if a professional has access to a patient's health plans"""
    try:
        if current_user.id != professional_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only check your own permissions"
            )
        
        has_access, reason = health_record_permission_service.check_health_plan_access(
            db=db,
            patient_id=patient_id,
            professional_id=professional_id
        )
        
        return {
            "has_access": has_access,
            "reason": reason,
            "patient_id": patient_id,
            "professional_id": professional_id,
            "access_type": "health_plans"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check health plan permission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check permission: {str(e)}"
        )

@router.get("/check/medications/{patient_id}/{professional_id}")
async def check_medication_permission(
    patient_id: int,
    professional_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if a professional has access to a patient's medications"""
    try:
        if current_user.id != professional_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only check your own permissions"
            )
        
        has_access, reason = health_record_permission_service.check_medication_access(
            db=db,
            patient_id=patient_id,
            professional_id=professional_id
        )
        
        return {
            "has_access": has_access,
            "reason": reason,
            "patient_id": patient_id,
            "professional_id": professional_id,
            "access_type": "medications"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check medication permission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check permission: {str(e)}"
        )

@router.get("/check/appointments/{patient_id}/{professional_id}")
async def check_appointment_permission(
    patient_id: int,
    professional_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if a professional has access to a patient's appointments"""
    try:
        if current_user.id != professional_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only check your own permissions"
            )
        
        has_access, reason = health_record_permission_service.check_appointment_access(
            db=db,
            patient_id=patient_id,
            professional_id=professional_id
        )
        
        return {
            "has_access": has_access,
            "reason": reason,
            "patient_id": patient_id,
            "professional_id": professional_id,
            "access_type": "appointments"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check appointment permission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check permission: {str(e)}"
        )

@router.get("/check/messages/{patient_id}/{professional_id}")
async def check_message_permission(
    patient_id: int,
    professional_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if a professional has access to a patient's messages"""
    try:
        if current_user.id != professional_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only check your own permissions"
            )
        
        has_access, reason = health_record_permission_service.check_message_access(
            db=db,
            patient_id=patient_id,
            professional_id=professional_id
        )
        
        return {
            "has_access": has_access,
            "reason": reason,
            "patient_id": patient_id,
            "professional_id": professional_id,
            "access_type": "messages"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check message permission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check permission: {str(e)}"
        )

@router.get("/check/lab-results/{patient_id}/{professional_id}")
async def check_lab_result_permission(
    patient_id: int,
    professional_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if a professional has access to a patient's lab results"""
    try:
        if current_user.id != professional_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only check your own permissions"
            )
        
        has_access, reason = health_record_permission_service.check_lab_result_access(
            db=db,
            patient_id=patient_id,
            professional_id=professional_id
        )
        
        return {
            "has_access": has_access,
            "reason": reason,
            "patient_id": patient_id,
            "professional_id": professional_id,
            "access_type": "lab_results"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check lab result permission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check permission: {str(e)}"
        )

@router.get("/check/imaging/{patient_id}/{professional_id}")
async def check_imaging_permission(
    patient_id: int,
    professional_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if a professional has access to a patient's imaging"""
    try:
        if current_user.id != professional_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only check your own permissions"
            )
        
        has_access, reason = health_record_permission_service.check_imaging_access(
            db=db,
            patient_id=patient_id,
            professional_id=professional_id
        )
        
        return {
            "has_access": has_access,
            "reason": reason,
            "patient_id": patient_id,
            "professional_id": professional_id,
            "access_type": "imaging"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check imaging permission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check permission: {str(e)}"
        )

@router.get("/patient-data/{patient_id}")
async def get_patient_data_with_permissions(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get patient data based on granted permissions (for professionals)"""
    try:
        # This endpoint is for professionals to get patient data
        professional_id = current_user.id
        
        patient_data = health_record_permission_service.get_patient_data_with_permissions(
            db=db,
            patient_id=patient_id,
            professional_id=professional_id
        )
        
        if "error" in patient_data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=patient_data["error"]
            )
        
        return patient_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get patient data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get patient data: {str(e)}"
        )

@router.get("/summary/{patient_id}")
async def get_permission_summary(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a summary of all permissions for a patient"""
    try:
        # Check if current user is the patient or has permission to view
        if current_user.id != patient_id:
            # TODO: Add admin permission check
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only view your own permission summary"
            )
        
        from app.crud.document import health_record_permission_crud
        
        # Get all permissions for this patient
        permissions = health_record_permission_crud.get_by_patient(db, patient_id)
        
        summary = {
            "patient_id": patient_id,
            "total_permissions": len(permissions),
            "active_permissions": len([p for p in permissions if p.is_active]),
            "expired_permissions": len([p for p in permissions if p.expires_at and p.expires_at < db.query(func.now()).scalar()]),
            "permissions": [
                {
                    "id": p.id,
                    "professional_id": p.professional_id,
                    "granted_for": p.granted_for,
                    "expires_at": p.expires_at,
                    "is_active": p.is_active,
                    "can_view_health_records": p.can_view_health_records,
                    "can_view_medical_history": p.can_view_medical_history,
                    "can_view_health_plans": p.can_view_health_plans,
                    "can_view_medications": p.can_view_medications,
                    "can_view_appointments": p.can_view_appointments,
                    "can_view_messages": p.can_view_messages,
                    "can_view_lab_results": p.can_view_lab_results,
                    "can_view_imaging": p.can_view_imaging
                } for p in permissions
            ]
        }
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get permission summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get permission summary: {str(e)}"
        )
