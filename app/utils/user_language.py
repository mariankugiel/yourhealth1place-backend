"""
Utility functions for getting user language preference from cache
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.core.supabase_client import supabase_service
from app.models.user import User
import logging

logger = logging.getLogger(__name__)


async def get_user_language_from_cache(user_id: int, db: Session) -> str:
    """
    Get user's language from cached profile using internal user_id.
    If cache is expired or missing, fetches fresh profile and updates cache.
    
    Args:
        user_id: Internal user ID (integer)
        db: Database session
    
    Returns:
        Language code: 'en', 'es', or 'pt' (defaults to 'en')
    """
    try:
        # Get user from database to get Supabase user ID
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.supabase_user_id:
            logger.warning(f"User {user_id} not found or no Supabase ID")
            return 'en'
        
        # Get language from cached profile (auto-refreshes if expired)
        return await supabase_service.get_user_language_from_cache(user.supabase_user_id)
        
    except Exception as e:
        logger.warning(f"Failed to get user language from cache for user {user_id}: {e}")
        return 'en'  # Default fallback
