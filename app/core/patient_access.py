"""
Helper functions for checking patient access permissions
"""
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.core.supabase_client import supabase_service
from app.services.health_record_permission_service import health_record_permission_service
import logging

logger = logging.getLogger(__name__)


async def check_patient_access(
    db: Session,
    patient_id: int,
    current_user: User,
    permission_type: str = "view_health_records"
) -> Tuple[bool, Optional[str]]:
    """
    Check if current user has permission to access a patient's data
    
    Args:
        db: Database session
        patient_id: ID of the patient to access
        current_user: Current authenticated user
        permission_type: Type of permission to check (default: "view_health_records")
        
    Returns:
        Tuple[bool, Optional[str]]: (has_access, error_message)
    """
    try:
        logger.info(f"🔍 Checking patient access: current_user_id={current_user.id}, patient_id={patient_id}, permission_type={permission_type}")
        
        # If user is trying to access their own data, allow it
        if current_user.id == patient_id:
            logger.info(f"✅ User accessing own data, allowing access")
            return True, None
        
        # Get patient user from database
        patient_user = db.query(User).filter(User.id == patient_id).first()
        if not patient_user:
            logger.warning(f"❌ Patient not found in database: patient_id={patient_id}")
            return False, "Patient not found"
        
        logger.info(f"📋 Found patient: id={patient_user.id}, email={patient_user.email}, supabase_id={patient_user.supabase_user_id}")
        
        # Get current user's email
        current_user_email = current_user.email
        if not current_user_email:
            logger.warning(f"❌ Current user has no email address: user_id={current_user.id}")
            return False, "Current user has no email address"
        
        logger.info(f"📧 Checking access for current_user_email={current_user_email} in patient's shared access")
        
        # Check user_shared_access table in Supabase (primary method)
        try:
            shared_access = supabase_service.client.table("user_shared_access").select("*").eq(
                "user_id", patient_user.supabase_user_id
            ).execute()
            
            logger.info(f"📊 Found {len(shared_access.data) if shared_access.data else 0} shared_access records for patient")
            
            if shared_access.data and len(shared_access.data) > 0:
                shared_access_record = shared_access.data[0]
                
                # Check health_professionals
                health_professionals = shared_access_record.get("health_professionals", [])
                logger.info(f"👨‍⚕️ Checking {len(health_professionals) if isinstance(health_professionals, list) else 0} health professionals")
                if isinstance(health_professionals, list):
                    for contact in health_professionals:
                        contact_email = contact.get("profile_email") or contact.get("email")
                        is_active = contact.get("is_active", True)
                        logger.info(f"  - Contact: email={contact_email}, is_active={is_active}")
                        if contact_email and contact_email.lower() == current_user_email.lower():
                            if is_active:
                                logger.info(f"✅ Access granted via user_shared_access (health_professionals) for patient {patient_id}")
                                return True, None
                            else:
                                logger.warning(f"⚠️ Contact found but is_active=False")
                
                # Check family_friends
                family_friends = shared_access_record.get("family_friends", [])
                logger.info(f"👨‍👩‍👧 Checking {len(family_friends) if isinstance(family_friends, list) else 0} family/friends")
                if isinstance(family_friends, list):
                    for contact in family_friends:
                        contact_email = contact.get("profile_email") or contact.get("email")
                        is_active = contact.get("is_active", True)
                        logger.info(f"  - Contact: email={contact_email}, is_active={is_active}")
                        if contact_email and contact_email.lower() == current_user_email.lower():
                            if is_active:
                                logger.info(f"✅ Access granted via user_shared_access (family_friends) for patient {patient_id}")
                                return True, None
                            else:
                                logger.warning(f"⚠️ Contact found but is_active=False")
            else:
                logger.warning(f"⚠️ No shared_access records found for patient {patient_id} (supabase_id={patient_user.supabase_user_id})")
        except Exception as e:
            logger.error(f"❌ Error checking user_shared_access: {e}", exc_info=True)
        
        # Fallback: Check health_record_permissions table
        has_access, reason = health_record_permission_service.check_health_record_access(
            db=db,
            patient_id=patient_id,
            professional_id=current_user.id,
            access_type="view"
        )
        
        if has_access:
            logger.info(f"✅ Access granted via health_record_permissions for patient {patient_id}")
            return True, None
        
        logger.warning(f"❌ Access denied for patient {patient_id}: {reason}")
        return False, reason or "No permission to access this patient's data"
        
    except Exception as e:
        logger.error(f"❌ Error checking patient access: {e}")
        return False, f"Error checking permissions: {str(e)}"


def get_target_user_id(
    db: Session,
    patient_id: Optional[int],
    current_user: User
) -> int:
    """
    Get the target user ID for data access.
    If patient_id is provided, check permissions and return patient_id.
    Otherwise, return current_user.id
    
    Args:
        db: Database session
        patient_id: Optional patient ID from query parameter
        current_user: Current authenticated user
        
    Returns:
        int: Target user ID
    """
    if patient_id:
        # Permission check will be done in the endpoint
        return patient_id
    return current_user.id

