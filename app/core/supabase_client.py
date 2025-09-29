from supabase import create_client, Client
from app.core.config import settings
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self):
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
        self.anon_client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
    
    def _get_user_client(self, user_token: str) -> Client:
        """Create a Supabase client with user's JWT token for RLS enforcement"""
        from supabase import create_client
        
        # Create client with user token
        client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
        
        # Set the authorization header manually
        client.postgrest.auth(user_token)
        
        return client
    
    async def sign_up(self, email: str, password: str, user_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user with Supabase Auth"""
        try:
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata
                }
            })
            return response
        except Exception as e:
            logger.error(f"Supabase sign up error: {e}")
            raise
    
    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in user with Supabase Auth"""
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return response
        except Exception as e:
            logger.error(f"Supabase sign in error: {e}")
            raise
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from Supabase"""
        try:
            response = self.client.auth.admin.get_user_by_id(user_id)
            return response
        except Exception as e:
            logger.error(f"Supabase get user error: {e}")
            return None
    
    def get_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user information from JWT token"""
        try:
            # Use the admin client to verify the token
            # This bypasses the need for refresh tokens
            user = self.client.auth.get_user(token)
            
            if user and user.user:
                return {
                    "id": user.user.id,
                    "email": user.user.email,
                    "user_metadata": user.user.user_metadata
                }
            return None
        except Exception as e:
            logger.error(f"Supabase get user from token error: {e}")
            return None
    
    async def update_user_metadata(self, user_id: str, metadata: Dict[str, Any]) -> bool:
        """Update user metadata in Supabase"""
        try:
            response = self.client.auth.admin.update_user_by_id(
                user_id,
                {"user_metadata": metadata}
            )
            return True
        except Exception as e:
            logger.error(f"Supabase update user metadata error: {e}")
            return False
    
    async def store_personal_info(self, user_id: str, personal_info: Dict[str, Any]) -> bool:
        """Store personal information in Supabase user_profiles table"""
        try:
            # Store in user_profiles table with profile_data field
            response = self.client.table("user_profiles").insert({
                "user_id": user_id,
                "profile_data": personal_info
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase store personal info error: {e}")
            return False
    
    async def get_personal_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve personal information from Supabase user_profiles table"""
        try:
            response = self.client.table("user_profiles").select("profile_data").eq("user_id", user_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0].get("profile_data", {})
            return None
        except Exception as e:
            logger.error(f"Supabase get personal info error: {e}")
            return None
    
    async def store_user_settings(self, user_id: str, settings: Dict[str, Any]) -> bool:
        """Store lightweight user settings in Supabase user metadata"""
        try:
            # Get existing metadata first
            user_response = self.client.auth.admin.get_user_by_id(user_id)
            existing_metadata = user_response.user_metadata if user_response else {}
            
            # Merge with new settings
            updated_metadata = {**existing_metadata, "settings": settings}
            
            response = self.client.auth.admin.update_user_by_id(
                user_id,
                {"user_metadata": updated_metadata}
            )
            return True
        except Exception as e:
            logger.error(f"Supabase store user settings error: {e}")
            return False
    
    async def get_user_settings(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user settings from Supabase user metadata"""
        try:
            user_response = self.client.auth.admin.get_user_by_id(user_id)
            if user_response and user_response.user_metadata and "settings" in user_response.user_metadata:
                return user_response.user_metadata["settings"]
            return None
        except Exception as e:
            logger.error(f"Supabase get user settings error: {e}")
            return None
    
    async def store_user_profile(self, user_id: str, profile: Dict[str, Any], user_token: Optional[str] = None) -> bool:
        """Store user profile in Supabase database"""
        try:
            # Use user token if provided, otherwise use service role
            client = self._get_user_client(user_token) if user_token else self.client
            
            # Use upsert to insert or update existing record
            response = client.table("user_profiles").upsert({
                "user_id": user_id,
                **profile  # Store each field as individual column
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase store user profile error: {e}")
            return False
    
    async def get_user_profile(self, user_id: str, user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve user profile from Supabase database"""
        try:
            # Use user token if provided, otherwise use service role
            client = self._get_user_client(user_token) if user_token else self.client
            
            # Get profile data from user_profiles table
            profile_response = client.table("user_profiles").select("*").eq("user_id", user_id).execute()
            profile_data = {}
            
            if profile_response.data and len(profile_response.data) > 0:
                profile_data = profile_response.data[0]
                # Remove system columns and user_id
                profile_data.pop("id", None)
                profile_data.pop("user_id", None)
                profile_data.pop("created_at", None)
                profile_data.pop("updated_at", None)
            
            # Get email from auth.users table using admin client
            try:
                # Use admin client to get user by ID
                admin_client = self.client
                user_response = admin_client.auth.admin.get_user_by_id(user_id)
                if user_response.user and user_response.user.email:
                    profile_data["email"] = user_response.user.email
                    logger.info(f"Successfully retrieved email for user {user_id}")
                else:
                    logger.warning(f"No email found for user {user_id}")
            except Exception as admin_error:
                logger.warning(f"Could not get email from admin auth: {admin_error}")
                # Try to get email from profile data if it was stored there
                if "email" in profile_data and profile_data["email"]:
                    logger.info(f"Using email from profile data for user {user_id}")
                else:
                    logger.warning(f"No email available for user {user_id}")
                    # If we can't get email from auth, we'll return profile without email
                    # The frontend should handle this case gracefully
            
            return profile_data if profile_data else {}
        except Exception as e:
            logger.error(f"Supabase get user profile error: {e}")
            return {}  # Return empty dict instead of None
    
    async def update_user_profile(self, user_id: str, profile: Dict[str, Any], user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update user profile in Supabase database"""
        try:
            # Use user token if provided, otherwise use service role
            client = self._get_user_client(user_token) if user_token else self.client
            
            # Use upsert to insert or update existing record
            response = client.table("user_profiles").upsert({
                "user_id": user_id,
                **profile
            }).execute()
            
            # Return the updated profile data
            if response.data and len(response.data) > 0:
                profile_data = response.data[0]
                # Remove system columns and user_id
                profile_data.pop("id", None)
                profile_data.pop("user_id", None)
                profile_data.pop("created_at", None)
                profile_data.pop("updated_at", None)
                return profile_data
            return profile
        except Exception as e:
            logger.error(f"Supabase update user profile error: {e}")
            return None

# Global instance
supabase_service = SupabaseService() 