from supabase import create_client, Client
from app.core.config import settings
from typing import Optional, Dict, Any, List
import logging
import httpx

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
            response = self.anon_client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata,
                    "email_confirm": True  # Enable email confirmation
                }
            })
            return response
        except Exception as e:
            logger.error(f"Supabase sign up error: {e}")
            raise
    
    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in user with Supabase Auth"""
        try:
            response = self.anon_client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            # Check if response has error
            if hasattr(response, 'error') and response.error:
                error_msg = str(response.error) if response.error else "Authentication failed"
                logger.error(f"Supabase sign in error in response: {error_msg}")
                raise Exception(f"Invalid login credentials: {error_msg}")
            
            return response
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Supabase sign in error: {error_msg}")
            logger.error(f"Error type: {type(e)}")
            
            # Re-raise with a clearer message for invalid credentials
            if "invalid" in error_msg.lower() or "credentials" in error_msg.lower() or "password" in error_msg.lower():
                raise Exception(f"Invalid login credentials: {error_msg}")
            raise
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from Supabase"""
        try:
            response = self.client.auth.admin.get_user_by_id(user_id)
            return response
        except Exception as e:
            logger.debug(f"Supabase get user error (may be expected): {e}")
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
            logger.debug(f"Supabase store user settings error (may be expected): {e}")
            return False
    
    async def get_user_settings(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user settings from Supabase user metadata"""
        try:
            user_response = self.client.auth.admin.get_user_by_id(user_id)
            if user_response and user_response.user_metadata and "settings" in user_response.user_metadata:
                return user_response.user_metadata["settings"]
            return None
        except Exception as e:
            logger.debug(f"Supabase get user settings error (may be expected): {e}")
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
            logger.info(f"🔍 Getting user profile for user_id: {user_id}")
            # Always use service role client to avoid token expiration issues
            client = self.client
            
            # Get profile data from user_profiles table using * to get all columns
            # Note: If columns don't exist, they will be missing from the response
            try:
                profile_response = client.table("user_profiles").select("*").eq("user_id", user_id).execute()
                logger.info(f"📊 Query executed, rows returned: {len(profile_response.data) if profile_response.data else 0}")
            except Exception as query_error:
                logger.error(f"❌ Database query error (columns may not exist): {query_error}")
                # Return empty profile if query fails
                return {}
            profile_data = {}
            
            if profile_response.data and len(profile_response.data) > 0:
                profile_data = profile_response.data[0]
                # Remove system columns and user_id
                profile_data.pop("id", None)
                profile_data.pop("user_id", None)
                profile_data.pop("created_at", None)
                profile_data.pop("updated_at", None)
                
                # Convert role from lowercase (Supabase) to uppercase (PostgreSQL enum)
                if "role" in profile_data and profile_data["role"]:
                    role_mapping = {
                        "patient": "PATIENT",
                        "doctor": "DOCTOR", 
                        "admin": "ADMIN"
                    }
                    # Convert to uppercase for PostgreSQL enum compatibility
                    profile_data["role"] = role_mapping.get(profile_data["role"].lower(), "PATIENT")
            
            # Get email from auth.users table using admin client
            # Only try to get email if it's not already in profile data
            logger.info(f"📧 Checking for email in profile_data: {'email' in profile_data}, value: {profile_data.get('email')}")
            if "email" not in profile_data or not profile_data.get("email"):
                try:
                    # Use admin client to get user by ID
                    admin_client = self.client
                    logger.info(f"🔍 Attempting to get email from auth.admin.get_user_by_id for user {user_id}")
                    user_response = admin_client.auth.admin.get_user_by_id(user_id)
                    logger.info(f"📦 User response received: {user_response}")
                    if user_response and hasattr(user_response, 'user'):
                        logger.info(f"👤 User object: {user_response.user}")
                        if hasattr(user_response.user, 'email') and user_response.user.email:
                            profile_data["email"] = user_response.user.email
                            logger.info(f"✅ Successfully retrieved email from auth for user {user_id}: {user_response.user.email}")
                        else:
                            logger.warning(f"⚠️ No email attribute or email is None for user {user_id}")
                    else:
                        logger.warning(f"⚠️ No user in response for user {user_id}")
                except Exception as admin_error:
                    # This is expected if service role doesn't have admin permissions
                    logger.error(f"❌ Could not get email from admin auth: {admin_error}")
                    import traceback
                    logger.error(f"❌ Traceback: {traceback.format_exc()}")
                    # Try to get email from profile data if it was stored there
                    if "email" in profile_data and profile_data["email"]:
                        logger.info(f"Using email from profile data for user {user_id}")
                    else:
                        logger.warning(f"No email available for user {user_id}")
                        # If we can't get email from auth, we'll return profile without email
                        # The frontend should handle this case gracefully
            else:
                logger.info(f"✅ Email already in profile data: {profile_data.get('email')}")
            
            logger.info(f"✅ Returning profile data: {len(profile_data)} fields")
            return profile_data if profile_data else {}
        except Exception as e:
            logger.error(f"❌ Supabase get user profile error: {e}")
            return {}  # Return empty dict instead of None
    
    async def update_user_profile(self, user_id: str, profile: Dict[str, Any], user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update user profile in Supabase database"""
        try:
            logger.info(f"💾 Updating user profile for user_id: {user_id}")
            logger.info(f"📝 Profile data: {profile}")
            
            # Always use service role client to avoid token expiration issues
            client = self.client
            
            # First, check if profile exists
            try:
                existing_profile = client.table("user_profiles").select("*").eq("user_id", user_id).execute()
                logger.info(f"📊 Existing profile check: {len(existing_profile.data) if existing_profile.data else 0} rows found")
            except Exception as query_error:
                logger.error(f"❌ Database query error (columns may not exist): {query_error}")
                # Try to create the profile anyway
                existing_profile = type('obj', (object,), {'data': []})()
            
            if existing_profile.data and len(existing_profile.data) > 0:
                # Profile exists, update it
                logger.info("🔄 Profile exists, updating...")
                response = client.table("user_profiles").update({
                    **profile,
                    "updated_at": "now()"
                }).eq("user_id", user_id).execute()
            else:
                # Profile doesn't exist, create it
                logger.info("✨ Profile doesn't exist, creating new...")
                response = client.table("user_profiles").insert({
                    "user_id": user_id,
                    **profile,
                    "created_at": "now()",
                    "updated_at": "now()"
                }).execute()
            
            logger.info(f"✅ Supabase operation completed: {len(response.data) if response.data else 0} rows affected")
            
            # Return the updated profile data
            if response.data and len(response.data) > 0:
                profile_data = response.data[0]
                # Remove system columns and user_id
                profile_data.pop("id", None)
                profile_data.pop("user_id", None)
                profile_data.pop("created_at", None)
                profile_data.pop("updated_at", None)
                logger.info(f"✅ Returning updated profile data: {len(profile_data)} fields")
                return profile_data
            logger.warning("⚠️ No data returned from Supabase, returning original profile")
            return profile
        except Exception as e:
            logger.error(f"❌ Supabase update user profile error: {e}")
            return None
    
    async def get_user_emergency(self, user_id: str, user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve user emergency data from Supabase user_emergency table"""
        try:
            logger.info(f"🔍 Getting user emergency data for user_id: {user_id}")
            # Always use service role client to avoid token expiration issues
            client = self.client
            
            try:
                emergency_response = client.table("user_emergency").select("*").eq("user_id", user_id).execute()
                logger.info(f"📊 Emergency query executed, rows returned: {len(emergency_response.data) if emergency_response.data else 0}")
            except Exception as query_error:
                logger.error(f"❌ Database query error (table may not exist): {query_error}")
                return {}
            
            emergency_data = {}
            
            if emergency_response.data and len(emergency_response.data) > 0:
                emergency_data = emergency_response.data[0]
                # Remove system columns and user_id
                emergency_data.pop("id", None)
                emergency_data.pop("user_id", None)
                emergency_data.pop("created_at", None)
                emergency_data.pop("updated_at", None)
            
            logger.info(f"✅ Returning emergency data: {len(emergency_data)} fields")
            return emergency_data if emergency_data else {}
        except Exception as e:
            logger.error(f"❌ Supabase get user emergency error: {e}")
            return {}
    
    async def update_user_emergency(self, user_id: str, emergency: Dict[str, Any], user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update user emergency data in Supabase user_emergency table"""
        try:
            logger.info(f"💾 Updating user emergency data for user_id: {user_id}")
            logger.info(f"📝 Emergency data: {emergency}")
            
            # Always use service role client to avoid token expiration issues
            client = self.client
            
            # First, check if emergency record exists
            try:
                existing_emergency = client.table("user_emergency").select("*").eq("user_id", user_id).execute()
                logger.info(f"📊 Existing emergency check: {len(existing_emergency.data) if existing_emergency.data else 0} rows found")
            except Exception as query_error:
                logger.error(f"❌ Database query error (table may not exist): {query_error}")
                # Try to create the record anyway
                existing_emergency = type('obj', (object,), {'data': []})()
            
            # Try to update/insert with updated_at
            try:
                if existing_emergency.data and len(existing_emergency.data) > 0:
                    # Emergency record exists, update it
                    logger.info("🔄 Emergency record exists, updating...")
                    response = client.table("user_emergency").update({
                        **emergency,
                        "updated_at": "now()"
                    }).eq("user_id", user_id).execute()
                else:
                    # Emergency record doesn't exist, create it
                    logger.info("✨ Emergency record doesn't exist, creating new...")
                    response = client.table("user_emergency").insert({
                        "user_id": user_id,
                        **emergency,
                        "created_at": "now()",
                        "updated_at": "now()"
                    }).execute()
            except Exception as timestamp_error:
                # Column might not exist yet - try without timestamp fields
                logger.warning(f"⚠️ Timestamp field error, retrying without updated_at: {timestamp_error}")
                if existing_emergency.data and len(existing_emergency.data) > 0:
                    response = client.table("user_emergency").update({
                        **emergency
                    }).eq("user_id", user_id).execute()
                else:
                    response = client.table("user_emergency").insert({
                        "user_id": user_id,
                        **emergency
                    }).execute()
            
            logger.info(f"✅ Supabase emergency operation completed: {len(response.data) if response.data else 0} rows affected")
            
            # Return the updated emergency data
            if response.data and len(response.data) > 0:
                emergency_data = response.data[0]
                # Remove system columns and user_id
                emergency_data.pop("id", None)
                emergency_data.pop("user_id", None)
                emergency_data.pop("created_at", None)
                emergency_data.pop("updated_at", None)
                logger.info(f"✅ Returning updated emergency data: {len(emergency_data)} fields")
                return emergency_data
            logger.warning("⚠️ No data returned from Supabase, returning original emergency data")
            return emergency
        except Exception as e:
            logger.error(f"❌ Supabase update user emergency error: {e}")
            return None
    
    async def get_user_notifications(self, user_id: str, user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve user notification preferences from Supabase user_notifications table"""
        try:
            logger.info(f"🔍 Getting user notification preferences for user_id: {user_id}")
            # Always use service role client to avoid token expiration issues
            client = self.client
            
            try:
                notifications_response = client.table("user_notifications").select("*").eq("user_id", user_id).execute()
                logger.info(f"📊 Notifications query executed, rows returned: {len(notifications_response.data) if notifications_response.data else 0}")
            except Exception as query_error:
                logger.error(f"❌ Database query error (table may not exist): {query_error}")
                return {}
            
            notifications_data = {}
            
            if notifications_response.data and len(notifications_response.data) > 0:
                notifications_data = notifications_response.data[0]
                # Remove system columns and user_id
                notifications_data.pop("id", None)
                notifications_data.pop("user_id", None)
                notifications_data.pop("created_at", None)
                notifications_data.pop("updated_at", None)
            
            logger.info(f"✅ Returning notification preferences: {len(notifications_data)} fields")
            return notifications_data if notifications_data else {}
        except Exception as e:
            logger.error(f"❌ Supabase get user notifications error: {e}")
            return {}
    
    async def update_user_notifications(self, user_id: str, notifications: Dict[str, Any], user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update user notification preferences in Supabase user_notifications table"""
        try:
            logger.info(f"💾 Updating user notification preferences for user_id: {user_id}")
            logger.info(f"📝 Notifications data: {notifications}")
            
            # Always use service role client to avoid token expiration issues
            client = self.client
            
            # First, check if notifications record exists
            try:
                existing_notifications = client.table("user_notifications").select("*").eq("user_id", user_id).execute()
                logger.info(f"📊 Existing notifications check: {len(existing_notifications.data) if existing_notifications.data else 0} rows found")
            except Exception as query_error:
                logger.error(f"❌ Database query error (table may not exist): {query_error}")
                # Try to create the record anyway
                existing_notifications = type('obj', (object,), {'data': []})()
            
            # Try to update/insert with updated_at
            try:
                if existing_notifications.data and len(existing_notifications.data) > 0:
                    # Notifications record exists, update it
                    logger.info("🔄 Notifications record exists, updating...")
                    response = client.table("user_notifications").update({
                        **notifications,
                        "updated_at": "now()"
                    }).eq("user_id", user_id).execute()
                else:
                    # Notifications record doesn't exist, create it
                    logger.info("✨ Notifications record doesn't exist, creating new...")
                    response = client.table("user_notifications").insert({
                        "user_id": user_id,
                        **notifications,
                        "created_at": "now()",
                        "updated_at": "now()"
                    }).execute()
            except Exception as timestamp_error:
                # Column might not exist yet - try without timestamp fields
                logger.warning(f"⚠️ Timestamp field error, retrying without updated_at: {timestamp_error}")
                if existing_notifications.data and len(existing_notifications.data) > 0:
                    response = client.table("user_notifications").update({
                        **notifications
                    }).eq("user_id", user_id).execute()
                else:
                    response = client.table("user_notifications").insert({
                        "user_id": user_id,
                        **notifications
                    }).execute()
            
            logger.info(f"✅ Supabase notifications operation completed: {len(response.data) if response.data else 0} rows affected")
            
            # Return the updated notifications data
            if response.data and len(response.data) > 0:
                notifications_data = response.data[0]
                # Remove system columns and user_id
                notifications_data.pop("id", None)
                notifications_data.pop("user_id", None)
                notifications_data.pop("created_at", None)
                notifications_data.pop("updated_at", None)
                logger.info(f"✅ Returning updated notification preferences: {len(notifications_data)} fields")
                return notifications_data
            logger.warning("⚠️ No data returned from Supabase, returning original notifications data")
            return notifications
        except Exception as e:
            logger.error(f"❌ Supabase update user notifications error: {e}")
            return None
    
    async def get_user_integrations(self, user_id: str, user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve user integration preferences from Supabase user_integrations table"""
        try:
            logger.info(f"🔍 Getting user integrations for user_id: {user_id}")
            client = self.client
            
            try:
                integrations_response = client.table("user_integrations").select("*").eq("user_id", user_id).execute()
                logger.info(f"📊 Integrations query executed, rows returned: {len(integrations_response.data) if integrations_response.data else 0}")
            except Exception as query_error:
                logger.error(f"❌ Database query error (table may not exist): {query_error}")
                return {}
            
            integrations_data = {}
            
            if integrations_response.data and len(integrations_response.data) > 0:
                integrations_data = integrations_response.data[0]
                integrations_data.pop("id", None)
                integrations_data.pop("user_id", None)
                integrations_data.pop("created_at", None)
                integrations_data.pop("updated_at", None)
            
            logger.info(f"✅ Returning integrations: {len(integrations_data)} fields")
            return integrations_data if integrations_data else {}
        except Exception as e:
            logger.error(f"❌ Supabase get user integrations error: {e}")
            return {}
    
    async def update_user_integrations(self, user_id: str, integrations: Dict[str, Any], user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update user integration preferences in Supabase user_integrations table"""
        try:
            logger.info(f"💾 Updating user integrations for user_id: {user_id}")
            logger.info(f"📝 Integrations data: {integrations}")
            
            client = self.client
            
            try:
                existing_integrations = client.table("user_integrations").select("*").eq("user_id", user_id).execute()
                logger.info(f"📊 Existing integrations check: {len(existing_integrations.data) if existing_integrations.data else 0} rows found")
            except Exception as query_error:
                logger.error(f"❌ Database query error (table may not exist): {query_error}")
                existing_integrations = type('obj', (object,), {'data': []})()
            
            try:
                if existing_integrations.data and len(existing_integrations.data) > 0:
                    logger.info("🔄 Integrations record exists, updating...")
                    response = client.table("user_integrations").update({
                        **integrations,
                        "updated_at": "now()"
                    }).eq("user_id", user_id).execute()
                else:
                    logger.info("✨ Integrations record doesn't exist, creating new...")
                    response = client.table("user_integrations").insert({
                        "user_id": user_id,
                        **integrations,
                        "created_at": "now()",
                        "updated_at": "now()"
                    }).execute()
            except Exception as timestamp_error:
                logger.warning(f"⚠️ Timestamp field error, retrying without updated_at: {timestamp_error}")
                if existing_integrations.data and len(existing_integrations.data) > 0:
                    response = client.table("user_integrations").update({
                        **integrations
                    }).eq("user_id", user_id).execute()
                else:
                    response = client.table("user_integrations").insert({
                        "user_id": user_id,
                        **integrations
                    }).execute()
            
            logger.info(f"✅ Supabase integrations operation completed: {len(response.data) if response.data else 0} rows affected")
            
            if response.data and len(response.data) > 0:
                integrations_data = response.data[0]
                integrations_data.pop("id", None)
                integrations_data.pop("user_id", None)
                integrations_data.pop("created_at", None)
                integrations_data.pop("updated_at", None)
                logger.info(f"✅ Returning updated integrations: {len(integrations_data)} fields")
                return integrations_data
            logger.warning("⚠️ No data returned from Supabase, returning original integrations data")
            return integrations
        except Exception as e:
            logger.error(f"❌ Supabase update user integrations error: {e}")
            return None
    
    async def get_user_privacy(self, user_id: str, user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve user privacy preferences from Supabase user_privacy table"""
        try:
            logger.info(f"🔍 Getting user privacy for user_id: {user_id}")
            client = self.client
            
            try:
                privacy_response = client.table("user_privacy").select("*").eq("user_id", user_id).execute()
                logger.info(f"📊 Privacy query executed, rows returned: {len(privacy_response.data) if privacy_response.data else 0}")
            except Exception as query_error:
                logger.error(f"❌ Database query error (table may not exist): {query_error}")
                return {}
            
            privacy_data = {}
            
            if privacy_response.data and len(privacy_response.data) > 0:
                privacy_data = privacy_response.data[0]
                privacy_data.pop("id", None)
                privacy_data.pop("user_id", None)
                privacy_data.pop("created_at", None)
                privacy_data.pop("updated_at", None)
            
            logger.info(f"✅ Returning privacy: {len(privacy_data)} fields")
            return privacy_data if privacy_data else {}
        except Exception as e:
            logger.error(f"❌ Supabase get user privacy error: {e}")
            return {}
    
    async def update_user_privacy(self, user_id: str, privacy: Dict[str, Any], user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update user privacy preferences in Supabase user_privacy table"""
        try:
            logger.info(f"💾 Updating user privacy for user_id: {user_id}")
            logger.info(f"📝 Privacy data: {privacy}")
            
            client = self.client
            
            try:
                existing_privacy = client.table("user_privacy").select("*").eq("user_id", user_id).execute()
                logger.info(f"📊 Existing privacy check: {len(existing_privacy.data) if existing_privacy.data else 0} rows found")
            except Exception as query_error:
                logger.error(f"❌ Database query error (table may not exist): {query_error}")
                existing_privacy = type('obj', (object,), {'data': []})()
            
            try:
                if existing_privacy.data and len(existing_privacy.data) > 0:
                    logger.info("🔄 Privacy record exists, updating...")
                    response = client.table("user_privacy").update({
                        **privacy,
                        "updated_at": "now()"
                    }).eq("user_id", user_id).execute()
                else:
                    logger.info("✨ Privacy record doesn't exist, creating new...")
                    response = client.table("user_privacy").insert({
                        "user_id": user_id,
                        **privacy,
                        "created_at": "now()",
                        "updated_at": "now()"
                    }).execute()
            except Exception as timestamp_error:
                logger.warning(f"⚠️ Timestamp field error, retrying without updated_at: {timestamp_error}")
                if existing_privacy.data and len(existing_privacy.data) > 0:
                    response = client.table("user_privacy").update({
                        **privacy
                    }).eq("user_id", user_id).execute()
                else:
                    response = client.table("user_privacy").insert({
                        "user_id": user_id,
                        **privacy
                    }).execute()
            
            logger.info(f"✅ Supabase privacy operation completed: {len(response.data) if response.data else 0} rows affected")
            
            if response.data and len(response.data) > 0:
                privacy_data = response.data[0]
                privacy_data.pop("id", None)
                privacy_data.pop("user_id", None)
                privacy_data.pop("created_at", None)
                privacy_data.pop("updated_at", None)
                logger.info(f"✅ Returning updated privacy: {len(privacy_data)} fields")
                return privacy_data
            logger.warning("⚠️ No data returned from Supabase, returning original privacy data")
            return privacy
        except Exception as e:
            logger.error(f"❌ Supabase update user privacy error: {e}")
            return None
    
    async def reset_password(self, email: str, redirect_url: str = None) -> Dict[str, Any]:
        """Send password reset email using Supabase Auth"""
        try:
            redirect_to = redirect_url or f"{settings.FRONTEND_URL}/auth/reset-password"
            
            # Use anon client for password reset
            response = self.anon_client.auth.reset_password_email(
                email,
                {
                    "redirectTo": redirect_to
                }
            )
            return response
        except Exception as e:
            logger.error(f"Supabase reset password error: {e}")
            raise
    
    async def update_password(self, user_id: str, new_password: str, user_token: str) -> Dict[str, Any]:
        """Update user password using Supabase Auth admin REST API"""
        try:
            logger.info(f"🔐 Updating password for user_id: {user_id}")
            
            # Use REST API to update password since Python client doesn't support it well
            url = f"{settings.SUPABASE_URL}/auth/v1/admin/users/{user_id}"
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "password": new_password
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.put(url, json=payload, headers=headers, timeout=30.0)
                response.raise_for_status()
                
            logger.info("✅ Password updated successfully")
            return {"user_id": user_id, "success": True}
        except Exception as e:
            logger.error(f"❌ Supabase update password error: {e}")
            raise
    
    async def get_user_shared_access(self, user_id: str, user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve user shared access data from Supabase user_shared_access table"""
        try:
            logger.info(f"🔍 Getting user shared access for user_id: {user_id}")
            client = self.client
            
            try:
                shared_access_response = client.table("user_shared_access").select("*").eq("user_id", user_id).execute()
                logger.info(f"📊 Shared access query executed, rows returned: {len(shared_access_response.data) if shared_access_response.data else 0}")
            except Exception as query_error:
                logger.error(f"❌ Database query error (table may not exist): {query_error}")
                return {}
            
            shared_access_data = {}
            
            if shared_access_response.data and len(shared_access_response.data) > 0:
                shared_access_data = shared_access_response.data[0]
                shared_access_data.pop("id", None)
                shared_access_data.pop("user_id", None)
                shared_access_data.pop("created_at", None)
                shared_access_data.pop("updated_at", None)
            
            logger.info(f"✅ Returning shared access: {len(shared_access_data)} fields")
            return shared_access_data if shared_access_data else {}
        except Exception as e:
            logger.error(f"❌ Supabase get user shared access error: {e}")
            return {}
    
    async def update_user_shared_access(self, user_id: str, shared_access: Dict[str, Any], user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update user shared access data in Supabase user_shared_access table"""
        try:
            logger.info(f"💾 Updating user shared access for user_id: {user_id}")
            logger.info(f"📝 Shared access data: {shared_access}")
            
            client = self.client
            
            try:
                existing_shared_access = client.table("user_shared_access").select("*").eq("user_id", user_id).execute()
                logger.info(f"📊 Existing shared access check: {len(existing_shared_access.data) if existing_shared_access.data else 0} rows found")
            except Exception as query_error:
                logger.error(f"❌ Database query error (table may not exist): {query_error}")
                existing_shared_access = type('obj', (object,), {'data': []})()
            
            try:
                if existing_shared_access.data and len(existing_shared_access.data) > 0:
                    logger.info("🔄 Shared access record exists, updating...")
                    response = client.table("user_shared_access").update({
                        **shared_access,
                        "updated_at": "now()"
                    }).eq("user_id", user_id).execute()
                else:
                    logger.info("✨ Shared access record doesn't exist, creating new...")
                    response = client.table("user_shared_access").insert({
                        "user_id": user_id,
                        **shared_access,
                        "created_at": "now()",
                        "updated_at": "now()"
                    }).execute()
            except Exception as timestamp_error:
                logger.warning(f"⚠️ Timestamp field error, retrying without updated_at: {timestamp_error}")
                if existing_shared_access.data and len(existing_shared_access.data) > 0:
                    response = client.table("user_shared_access").update({
                        **shared_access
                    }).eq("user_id", user_id).execute()
                else:
                    response = client.table("user_shared_access").insert({
                        "user_id": user_id,
                        **shared_access
                    }).execute()
            
            logger.info(f"✅ Supabase shared access operation completed: {len(response.data) if response.data else 0} rows affected")
            
            if response.data and len(response.data) > 0:
                shared_access_data = response.data[0]
                shared_access_data.pop("id", None)
                shared_access_data.pop("user_id", None)
                shared_access_data.pop("created_at", None)
                shared_access_data.pop("updated_at", None)
                logger.info(f"✅ Returning updated shared access: {len(shared_access_data)} fields")
                return shared_access_data
            logger.warning("⚠️ No data returned from Supabase, returning original shared access data")
            return shared_access
        except Exception as e:
            logger.error(f"❌ Supabase update user shared access error: {e}")
            return None
    
    async def get_user_access_logs(self, user_id: str, user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve user access logs from Supabase user_access_logs table"""
        try:
            logger.info(f"🔍 Getting user access logs for user_id: {user_id}")
            client = self.client
            
            try:
                access_logs_response = client.table("user_access_logs").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
                logger.info(f"📊 Access logs query executed, rows returned: {len(access_logs_response.data) if access_logs_response.data else 0}")
            except Exception as query_error:
                logger.error(f"❌ Database query error (table may not exist): {query_error}")
                return {}
            
            access_logs_data = {}
            
            if access_logs_response.data and len(access_logs_response.data) > 0:
                # Map to the expected format with logs array
                logs_list = []
                for log in access_logs_response.data:
                    logs_list.append({
                        "id": str(log.get("id", "")),
                        "name": log.get("name", ""),
                        "role": log.get("role", ""),
                        "action": log.get("action", ""),
                        "date": log.get("date", ""),
                        "authorized": log.get("authorized", True),
                    })
                access_logs_data["logs"] = logs_list
            
            logger.info(f"✅ Returning access logs: {len(logs_list) if access_logs_data.get('logs') else 0} entries")
            return access_logs_data if access_logs_data else {"logs": []}
        except Exception as e:
            logger.error(f"❌ Supabase get user access logs error: {e}")
            return {"logs": []}
    
    async def update_user_access_logs(self, user_id: str, access_logs: Dict[str, Any], user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update user access logs in Supabase user_access_logs table"""
        try:
            logger.info(f"💾 Updating user access logs for user_id: {user_id}")
            logger.info(f"📝 Access logs data: {access_logs}")
            
            client = self.client
            
            # Access logs are typically append-only, so we'll insert new entries
            if "logs" in access_logs and access_logs["logs"]:
                logs_to_insert = []
                for log in access_logs["logs"]:
                    # Only insert if the log doesn't have an id or it's not in the database yet
                    if not log.get("id"):
                        logs_to_insert.append({
                            "user_id": user_id,
                            "name": log.get("name", ""),
                            "role": log.get("role", ""),
                            "action": log.get("action", ""),
                            "date": log.get("date", ""),
                            "authorized": log.get("authorized", True),
                        })
                
                if logs_to_insert:
                    response = client.table("user_access_logs").insert(logs_to_insert).execute()
                    logger.info(f"✅ Inserted {len(response.data) if response.data else 0} new access logs")
                    return {"logs": response.data if response.data else []}
            
            logger.info(f"✅ No new logs to insert")
            return {"logs": []}
        except Exception as e:
            logger.error(f"❌ Supabase update user access logs error: {e}")
            return None
    
    async def get_user_data_sharing(self, user_id: str, user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve user data sharing preferences from Supabase user_data_sharing table"""
        try:
            logger.info(f"🔍 Getting user data sharing preferences for user_id: {user_id}")
            client = self.client
            
            try:
                data_sharing_response = client.table("user_data_sharing").select("*").eq("user_id", user_id).execute()
                logger.info(f"📊 Data sharing query executed, rows returned: {len(data_sharing_response.data) if data_sharing_response.data else 0}")
            except Exception as query_error:
                logger.error(f"❌ Database query error (table may not exist): {query_error}")
                return {}
            
            data_sharing_info = {}
            
            if data_sharing_response.data and len(data_sharing_response.data) > 0:
                data_sharing_info = data_sharing_response.data[0]
                # Remove system columns and user_id
                data_sharing_info.pop("id", None)
                data_sharing_info.pop("user_id", None)
                data_sharing_info.pop("created_at", None)
                data_sharing_info.pop("updated_at", None)
            
            logger.info(f"✅ Returning data sharing preferences: {len(data_sharing_info)} fields")
            return data_sharing_info if data_sharing_info else {}
        except Exception as e:
            logger.error(f"❌ Supabase get user data sharing error: {e}")
            return {}
    
    async def update_user_data_sharing(self, user_id: str, data_sharing: Dict[str, Any], user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update user data sharing preferences in Supabase user_data_sharing table"""
        try:
            logger.info(f"💾 Updating user data sharing preferences for user_id: {user_id}")
            logger.info(f"📝 Data sharing data: {data_sharing}")
            
            client = self.client
            
            # First, check if data sharing record exists
            try:
                existing_data_sharing = client.table("user_data_sharing").select("*").eq("user_id", user_id).execute()
                logger.info(f"📊 Existing data sharing check: {len(existing_data_sharing.data) if existing_data_sharing.data else 0} rows found")
            except Exception as query_error:
                logger.error(f"❌ Database query error (table may not exist): {query_error}")
                existing_data_sharing = type('obj', (object,), {'data': []})()
            
            # Try to update/insert with updated_at
            try:
                if existing_data_sharing.data and len(existing_data_sharing.data) > 0:
                    # Data sharing record exists, update it
                    logger.info("🔄 Data sharing record exists, updating...")
                    response = client.table("user_data_sharing").update({
                        **data_sharing,
                        "updated_at": "now()"
                    }).eq("user_id", user_id).execute()
                else:
                    # Data sharing record doesn't exist, create it
                    logger.info("✨ Data sharing record doesn't exist, creating new...")
                    response = client.table("user_data_sharing").insert({
                        "user_id": user_id,
                        **data_sharing,
                        "created_at": "now()",
                        "updated_at": "now()"
                    }).execute()
            except Exception as timestamp_error:
                # Column might not exist yet - try without timestamp fields
                logger.warning(f"⚠️ Timestamp field error, retrying without updated_at: {timestamp_error}")
                if existing_data_sharing.data and len(existing_data_sharing.data) > 0:
                    response = client.table("user_data_sharing").update({
                        **data_sharing
                    }).eq("user_id", user_id).execute()
                else:
                    response = client.table("user_data_sharing").insert({
                        "user_id": user_id,
                        **data_sharing
                    }).execute()
            
            logger.info(f"✅ Supabase data sharing operation completed: {len(response.data) if response.data else 0} rows affected")
            
            # Return the updated data sharing info
            if response.data and len(response.data) > 0:
                data_sharing_info = response.data[0]
                # Remove system columns and user_id
                data_sharing_info.pop("id", None)
                data_sharing_info.pop("user_id", None)
                data_sharing_info.pop("created_at", None)
                data_sharing_info.pop("updated_at", None)
                logger.info(f"✅ Returning updated data sharing preferences: {len(data_sharing_info)} fields")
                return data_sharing_info
            logger.warning("⚠️ No data returned from Supabase, returning original data sharing data")
            return data_sharing
        except Exception as e:
            logger.error(f"❌ Supabase update user data sharing error: {e}")
            return None
    
    async def enroll_mfa_totp(self, user_id: str, friendly_name: str = "My Authenticator App") -> Dict[str, Any]:
        """Enroll user in TOTP MFA using Supabase Auth admin REST API"""
        try:
            logger.info(f"🔐 Enrolling TOTP MFA for user_id: {user_id}")
            
            # Use REST API for MFA enrollment
            url = f"{settings.SUPABASE_URL}/auth/v1/admin/users/{user_id}/factors"
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "type": "totp",
                "friendly_name": friendly_name
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                response.raise_for_status()
                result = response.json()
                logger.info("✅ MFA enrollment initiated successfully")
                return result
        except Exception as e:
            logger.error(f"❌ MFA enrollment error: {e}")
            raise
    
    async def verify_mfa_totp(self, user_id: str, factor_id: str, code: str) -> Dict[str, Any]:
        """Verify TOTP MFA code during enrollment"""
        try:
            logger.info(f"🔐 Verifying TOTP MFA code for factor_id: {factor_id}")
            
            # Use REST API for MFA verification
            url = f"{settings.SUPABASE_URL}/auth/v1/admin/users/{user_id}/factors/{factor_id}/verify"
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "code": code
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                response.raise_for_status()
                result = response.json()
                logger.info("✅ MFA verification successful")
                return result
        except Exception as e:
            logger.error(f"❌ MFA verification error: {e}")
            raise
    
    async def list_mfa_factors(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all MFA factors for a user"""
        try:
            logger.info(f"🔐 Listing MFA factors for user_id: {user_id}")
            
            # Use REST API to list MFA factors
            url = f"{settings.SUPABASE_URL}/auth/v1/admin/users/{user_id}/factors"
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=30.0)
                response.raise_for_status()
                result = response.json()
                logger.info(f"📦 Raw MFA factors response: {result}")
                
                # Handle different response formats
                if isinstance(result, list):
                    logger.info(f"✅ Retrieved {len(result)} MFA factors (list format)")
                    return result
                elif isinstance(result, dict):
                    logger.info(f"✅ Retrieved {len(result.get('factors', []))} MFA factors (dict format)")
                    return result.get("factors", [])
                else:
                    logger.warning(f"⚠️ Unexpected response format: {type(result)}")
                    return []
        except Exception as e:
            logger.error(f"❌ List MFA factors error: {e}")
            raise
    
    async def unenroll_mfa_factor(self, user_id: str, factor_id: str) -> bool:
        """Remove an MFA factor"""
        try:
            logger.info(f"🔐 Unenrolling MFA factor: {factor_id}")
            
            # Use REST API to remove MFA factor
            url = f"{settings.SUPABASE_URL}/auth/v1/admin/users/{user_id}/factors/{factor_id}"
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.delete(url, headers=headers, timeout=30.0)
                response.raise_for_status()
                logger.info("✅ MFA factor unenrolled successfully")
                return True
        except Exception as e:
            logger.error(f"❌ Unenroll MFA factor error: {e}")
            raise
    
    async def verify_mfa_for_login(self, user_id: str, factor_id: str, code: str, access_token: str) -> Optional[Dict[str, Any]]:
        """Verify MFA code during login using user's access token (challenge and verify flow)"""
        try:
            logger.info(f"🔐 Verifying MFA for login: factor_id={factor_id}")
            
            # Step 1: Challenge the MFA factor using the user's access token
            challenge_url = f"{settings.SUPABASE_URL}/auth/v1/factors/{factor_id}/challenge"
            challenge_headers = {
                "apikey": settings.SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                # Create challenge
                challenge_response = await client.post(challenge_url, headers=challenge_headers, timeout=30.0)
                challenge_response.raise_for_status()
                challenge_result = challenge_response.json()
                challenge_id = challenge_result.get("id")
                
                if not challenge_id:
                    logger.error("❌ No challenge ID returned")
                    return None
                
                logger.info(f"✅ MFA challenge created: {challenge_id}")
                
                # Step 2: Verify the code with the challenge
                verify_url = f"{settings.SUPABASE_URL}/auth/v1/factors/{factor_id}/verify"
                verify_headers = {
                    "apikey": settings.SUPABASE_ANON_KEY,
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                verify_payload = {
                    "challenge_id": challenge_id,
                    "code": code
                }
                
                verify_response = await client.post(verify_url, json=verify_payload, headers=verify_headers, timeout=30.0)
                verify_response.raise_for_status()
                verify_result = verify_response.json()
                
                logger.info("✅ MFA verification successful during login")
                
                # The verify result should contain the session tokens with AAL2
                return {
                    "access_token": verify_result.get("access_token") or access_token,
                    "refresh_token": verify_result.get("refresh_token"),
                    "expires_in": verify_result.get("expires_in", 3600)
                }
        except Exception as e:
            logger.error(f"❌ Verify MFA for login error: {e}")
            raise

# Global instance
supabase_service = SupabaseService() 