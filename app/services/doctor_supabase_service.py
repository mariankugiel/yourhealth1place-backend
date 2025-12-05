"""
Doctor Supabase Service
Refactored to use main Supabase project (single project for all users)
"""
from app.core.supabase_client import supabase_service
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class DoctorSupabaseService:
    """
    Service for interacting with doctor profiles in main Supabase project
    
    This service handles all doctor-related operations using the main Supabase project,
    using doctor_profiles and doctor_acuity_calendars tables.
    """
    
    def __init__(self):
        # No longer needs separate Supabase client initialization
        # Uses main supabase_service from app.core.supabase_client
        pass
    
    @property
    def client(self):
        """Get the main Supabase client (for compatibility with existing code)"""
        return supabase_service.client
    
    # ============================================================================
    # Doctor Profile Methods (using doctor_profiles table)
    # ============================================================================
    
    async def store_doctor_profile(self, user_id: str, profile: Dict[str, Any], user_token: Optional[str] = None) -> bool:
        """Store doctor profile in Supabase doctor_profiles table"""
        try:
            # Use user token if provided, otherwise use service role
            client = supabase_service._get_user_client(user_token) if user_token else supabase_service.client
            
            # Use upsert to insert or update existing record
            response = client.table("doctor_profiles").upsert({
                "id": user_id,  # Primary key
                "user_id": user_id,  # Also store as user_id for consistency
                **profile  # Store each field as individual column
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase store doctor profile error: {e}")
            return False
    
    async def update_doctor_profile(self, user_id: str, profile: Dict[str, Any], user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update doctor profile in Supabase doctor_profiles table"""
        try:
            client = supabase_service.client
            
            # Update the profile
            response = client.table("doctor_profiles").update({
                **profile,
                "updated_at": "now()"
            }).eq("user_id", user_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error updating doctor profile: {e}")
            return None
    
    async def store_acuity_calendar(self, doctor_id: str, calendar_id: str) -> bool:
        """Store Acuity calendar mapping in doctor_acuity_calendars table"""
        try:
            client = supabase_service.client
            response = client.table("doctor_acuity_calendars").upsert({
                "doctor_id": doctor_id,
                "calendar_id": calendar_id
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Error storing Acuity calendar: {e}")
            return False
    
    async def get_doctor_profile(self, supabase_user_id: str, user_token: Optional[str] = None, include_acuity_calendar: bool = True) -> Optional[Dict[str, Any]]:
        """
        Retrieve doctor's profile from main Supabase project
        
        Args:
            supabase_user_id: Doctor's Supabase user ID (from auth.users), which equals doctor_profiles.id
            user_token: Optional user token for RLS enforcement
            include_acuity_calendar: If True, also fetch and include acuity_calendar_id in the response
        
        Returns:
            Doctor profile data dictionary or None (includes 'id', 'user_id', and optionally 'acuity_calendar_id' fields)
        """
        try:
            if not supabase_user_id or not supabase_user_id.strip():
                logger.warning("get_doctor_profile called with empty supabase_user_id")
                return None
            
            supabase_user_id = supabase_user_id.strip()
            
            # Always use service role client to avoid token expiration issues
            client = supabase_service.client
            
            # Query by id (primary key) which equals supabase_user_id
            # Also try user_id as fallback in case data is inconsistent
            profile_response = client.table("doctor_profiles").select("*").eq("id", supabase_user_id).execute()
            
            # If no result, try querying by user_id as fallback
            if not profile_response.data or len(profile_response.data) == 0:
                profile_response = client.table("doctor_profiles").select("*").eq("user_id", supabase_user_id).execute()
            
            if profile_response.data and len(profile_response.data) > 0:
                profile_data = profile_response.data[0].copy()
                
                # Keep both 'id' and 'user_id' fields - user_id is needed for calendar lookup
                # Remove only system columns that aren't needed
                profile_data.pop("created_at", None)
                profile_data.pop("updated_at", None)
                
                # If requested, also fetch the acuity calendar ID
                if include_acuity_calendar:
                    doctor_id = profile_data.get("id") or profile_data.get("user_id")
                    if doctor_id:
                        try:
                            acuity_calendar_id = await self.get_acuity_calendar_id_by_doctor_id(doctor_id)
                            if acuity_calendar_id:
                                profile_data["acuity_calendar_id"] = acuity_calendar_id
                        except Exception as e:
                            logger.error(f"Could not fetch acuity calendar for doctor {doctor_id}: {e}")
                
                return profile_data
            
            return None
        except Exception as e:
            logger.error(f"Error getting doctor profile: {e}", exc_info=True)
            return None
    
    async def get_doctor_profiles_bulk(self, supabase_user_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Bulk fetch multiple doctor profiles from Supabase
        
        Args:
            supabase_user_ids: List of Supabase user IDs to fetch profiles for
        
        Returns:
            Dictionary mapping supabase_user_id -> profile data
        """
        if not supabase_user_ids:
            return {}
        
        try:
            client = supabase_service.client
            
            # Fetch all profiles in one query using IN clause
            profile_response = client.table("doctor_profiles").select("*").in_("id", supabase_user_ids).execute()
            
            # Build dictionary mapping id -> profile
            profiles_dict = {}
            if profile_response.data:
                for profile in profile_response.data:
                    profile_id = profile.get("id") or profile.get("user_id")
                    if profile_id:
                        # Remove system columns
                        profile_copy = profile.copy()
                        profile_copy.pop("created_at", None)
                        profile_copy.pop("updated_at", None)
                        profiles_dict[profile_id] = profile_copy
            
            return profiles_dict
        except Exception as e:
            logger.error(f"Supabase bulk get doctor profiles error: {e}", exc_info=True)
            return {}
    
    async def get_acuity_calendars_bulk(self, doctor_ids: List[str]) -> Dict[str, str]:
        """
        Bulk fetch Acuity calendar IDs for multiple doctors
        
        Args:
            doctor_ids: List of doctor IDs (from doctor_profiles.id)
        
        Returns:
            Dictionary mapping doctor_id -> calendar_id
        """
        if not doctor_ids:
            return {}
        
        try:
            client = supabase_service.client
            
            # Fetch all calendar mappings in one query
            calendar_response = client.table("doctor_acuity_calendars").select("doctor_id,calendar_id").in_("doctor_id", doctor_ids).execute()
            
            # Build dictionary mapping doctor_id -> calendar_id
            calendars_dict = {}
            if calendar_response.data:
                for calendar in calendar_response.data:
                    doctor_id = calendar.get("doctor_id")
                    calendar_id = calendar.get("calendar_id")
                    if doctor_id and calendar_id:
                        calendars_dict[doctor_id] = calendar_id
            
            return calendars_dict
        except Exception as e:
            logger.error(f"Supabase bulk get acuity calendars error: {e}", exc_info=True)
            return {}
    
    async def get_doctor_ids_by_calendar_ids_bulk(self, calendar_ids: List[str]) -> Dict[str, str]:
        """
        Bulk fetch doctor IDs for multiple calendar IDs
        
        Args:
            calendar_ids: List of Acuity calendar IDs
        
        Returns:
            Dictionary mapping calendar_id -> doctor_id
        """
        if not calendar_ids:
            return {}
        
        try:
            client = supabase_service.client
            
            # Fetch all doctor IDs in one query using IN clause
            calendar_response = client.table("doctor_acuity_calendars").select("doctor_id,calendar_id").in_("calendar_id", calendar_ids).execute()
            
            # Build dictionary mapping calendar_id -> doctor_id
            calendars_dict = {}
            if calendar_response.data:
                for calendar in calendar_response.data:
                    doctor_id = calendar.get("doctor_id")
                    calendar_id = calendar.get("calendar_id")
                    if doctor_id and calendar_id:
                        calendars_dict[calendar_id] = doctor_id
            
            return calendars_dict
        except Exception as e:
            logger.error(f"Supabase bulk get doctor IDs by calendar IDs error: {e}", exc_info=True)
            return {}
    
    async def get_doctor_id_by_calendar_id(self, calendar_id: str) -> Optional[str]:
        """
        Get doctor_id (UUID) from doctor_acuity_calendars table by calendar_id
        
        This is useful for webhook handlers that receive a calendar_id and need to find the doctor.
        
        Args:
            calendar_id: Acuity calendar ID
        
        Returns:
            Doctor UUID (from doctor_profiles.id) or None
        """
        try:
            if not calendar_id or not calendar_id.strip():
                logger.warning("get_doctor_id_by_calendar_id called with empty calendar_id")
                return None
            
            calendar_id = calendar_id.strip()
            
            client = supabase_service.client
            calendar_response = client.table("doctor_acuity_calendars").select("doctor_id").eq("calendar_id", calendar_id).execute()
            
            if calendar_response.data and len(calendar_response.data) > 0:
                calendar_data = calendar_response.data[0]
                doctor_id = calendar_data.get("doctor_id")
                if doctor_id:
                    return doctor_id
            
            return None
        except Exception as e:
            logger.error(f"Error getting doctor_id by calendar_id: {e}")
            return None
    
    async def get_supabase_user_id_by_doctor_id(self, doctor_id: str) -> Optional[str]:
        """
        Get Supabase user_id (auth.users.id) from doctor_id (doctor_profiles.id)
        
        This is useful for finding the local User record by matching supabase_user_id.
        
        Args:
            doctor_id: Doctor UUID (from doctor_profiles.id)
        
        Returns:
            Supabase user_id (auth.users.id) or None
        """
        try:
            if not doctor_id or not doctor_id.strip():
                logger.warning("get_supabase_user_id_by_doctor_id called with empty doctor_id")
                return None
            
            doctor_id = doctor_id.strip()
            
            # Get profile from doctor_profiles table
            profile = await self.get_doctor_profile(doctor_id)
            
            if profile:
                # Return user_id from profile (which is the same as id in most cases)
                user_id = profile.get("user_id") or profile.get("id")
                if user_id:
                    return user_id
            
            return None
        except Exception as e:
            logger.error(f"Error getting user_id by doctor_id: {e}")
            return None
    
    async def get_acuity_calendar_id_by_doctor_id(self, doctor_id: str) -> Optional[str]:
        """
        Get Acuity calendar ID from doctor_acuity_calendars table by doctor_id (UUID)
        
        Note: doctor_id in doctor_acuity_calendars = id in doctor_profiles
        
        Args:
            doctor_id: Doctor's UUID (from doctor_profiles.id or doctor_profiles.user_id)
        
        Returns:
            Acuity calendar ID string or None
        """
        try:
            if not doctor_id or not doctor_id.strip():
                logger.warning("get_acuity_calendar_id_by_doctor_id called with empty doctor_id")
                return None
            
            doctor_id = doctor_id.strip()
            client = supabase_service.client
            
            # Get calendar by doctor_id from doctor_acuity_calendars table
            calendar_response = client.table("doctor_acuity_calendars").select("calendar_id").eq("doctor_id", doctor_id).execute()
            
            if calendar_response.data and len(calendar_response.data) > 0:
                calendar_data = calendar_response.data[0]
                calendar_id = calendar_data.get("calendar_id")
                return calendar_id
            
            return None
        except Exception as e:
            logger.error(f"Error getting calendar ID by doctor_id: {e}")
            return None
    
    async def get_acuity_calendar_id(self, supabase_user_id: str, doctor_id: Optional[str] = None) -> Optional[str]:
        """
        Get doctor's Acuity calendar ID by doctor_id (UUID)
        
        Args:
            supabase_user_id: Doctor's Supabase user ID (from auth.users)
            doctor_id: Doctor UUID (from doctor_profiles.id) - required for lookup
        
        Returns:
            Acuity calendar ID string or None
        """
        # Get calendar from doctor_acuity_calendars table by doctor_id
        if doctor_id:
            calendar_id = await self.get_acuity_calendar_id_by_doctor_id(doctor_id)
            if calendar_id:
                return calendar_id
        
        # Fallback: try to get doctor_id from profile first
        profile = await self.get_doctor_profile(supabase_user_id)
        if profile:
            profile_doctor_id = profile.get("id") or profile.get("user_id")
            if profile_doctor_id:
                calendar_id = await self.get_acuity_calendar_id_by_doctor_id(profile_doctor_id)
                if calendar_id:
                    return calendar_id
        
        return None
    
    async def get_acuity_owner_id(self, supabase_user_id: str) -> Optional[str]:
        """
        Get doctor's Acuity owner ID from Supabase profile
        
        Args:
            supabase_user_id: Doctor's Supabase user ID
        
        Returns:
            Acuity owner ID string or None
        """
        profile = await self.get_doctor_profile(supabase_user_id)
        if profile:
            # Try acuity_owner_id first, fallback to acuity_user_id
            return profile.get("acuity_owner_id") or profile.get("acuity_user_id")
        return None


# Global instance (maintained for backward compatibility)
doctor_supabase_service = DoctorSupabaseService()
