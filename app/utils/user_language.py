"""
Utility functions for getting user language preference
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.core.supabase_client import SupabaseService
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

supabase_service = SupabaseService()


async def get_user_language(user_id: int, db: Session) -> str:
    """
    Get user's language preference from Supabase profile
    
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
        
        # Get user profile from Supabase
        profile = await supabase_service.get_user_profile(user.supabase_user_id)
        if profile and profile.get('language'):
            language = profile['language']
            # Validate language code
            if language in ['en', 'es', 'pt']:
                return language
        
        return 'en'  # Default to English
        
    except Exception as e:
        logger.warning(f"Failed to get user language for user {user_id}: {e}")
        return 'en'  # Default to English


def get_user_language_sync(user_id: int, db: Session) -> str:
    """
    Synchronous version - tries to get from database if available
    For now, returns default 'en' (can be enhanced later)
    """
    try:
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.supabase_user_id:
            return 'en'
        
        # For sync version, we can't easily call async Supabase service
        # Return default for now - async version should be used when possible
        return 'en'
    except Exception as e:
        logger.warning(f"Failed to get user language sync for user {user_id}: {e}")
        return 'en'

