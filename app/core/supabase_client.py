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
    
    def _get_user_client(self, user_token: str, refresh_token: Optional[str] = None) -> Client:
        """Create a Supabase client with user's JWT token for RLS enforcement"""
        from supabase import create_client
        
        # Create client with user token
        client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
        
        # Set the authorization header manually for postgrest
        client.postgrest.auth(user_token)
        
        # If refresh_token is provided, try to set the auth session
        # This is needed for auth operations like update_user
        if refresh_token:
            try:
                # Set the session for auth operations
                client.auth.set_session({
                    "access_token": user_token,
                    "refresh_token": refresh_token
                })
            except Exception as session_error:
                logger.debug(f"Could not set auth session (may be expected): {session_error}")
        
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
                error_obj = response.error
                error_msg = str(error_obj) if error_obj else "Authentication failed"
                
                # Try to get more details from the error object
                error_details = {}
                if hasattr(error_obj, '__dict__'):
                    error_details = error_obj.__dict__
                elif hasattr(error_obj, 'message'):
                    error_details['message'] = error_obj.message
                elif hasattr(error_obj, 'status'):
                    error_details['status'] = error_obj.status
                
                logger.error(f"Supabase sign in error in response: {error_msg}, details: {error_details}")
                
                # Preserve the original error message for better debugging
                raise Exception(error_msg)
            
            # Check if response is valid but might indicate MFA requirement
            # (some Supabase versions return response without error but without session when MFA is enabled)
            if hasattr(response, 'session') and response.session is None:
                # Check if there's MFA information
                if hasattr(response, 'user') and response.user:
                    logger.info("Sign in response received but no session (possibly MFA required)")
            
            return response
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(f"Supabase sign in error: {error_msg}")
            logger.error(f"Error type: {error_type}")
            
            # Log full exception details if available
            if hasattr(e, '__dict__'):
                logger.error(f"Error attributes: {e.__dict__}")
            
            # Re-raise the original error to preserve details
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
            print(f"🔍 [get_user_profile] Getting user profile for user_id: {user_id}")
            logger.info(f"🔍 Getting user profile for user_id: {user_id}")
            # Always use service role client to avoid token expiration issues
            # The service role client is initialized with SUPABASE_SERVICE_ROLE_KEY in __init__
            # This key bypasses RLS and never expires (it's not a JWT)
            client = self.client
            
            # Get profile data from user_profiles table using * to get all columns
            # Note: If columns don't exist, they will be missing from the response
            try:
                # Explicitly select img_url and avatar_url to ensure they're included
                profile_response = client.table("user_profiles").select("*").eq("user_id", user_id).execute()
                print(f"📊 [get_user_profile] Query executed, rows returned: {len(profile_response.data) if profile_response.data else 0}")
                
                # If we got data, log the raw response structure
                if profile_response.data and len(profile_response.data) > 0:
                    raw_data = profile_response.data[0]
                    print(f"📊 [get_user_profile] Raw response sample keys: {list(raw_data.keys())[:10]}...")
                    print(f"📊 [get_user_profile] Checking for img_url in raw response: {'img_url' in raw_data}")
                    print(f"📊 [get_user_profile] Checking for avatar_url in raw response: {'avatar_url' in raw_data}")
                
                logger.info(f"📊 Query executed, rows returned: {len(profile_response.data) if profile_response.data else 0}")
            except Exception as query_error:
                error_str = str(query_error)
                # Check if it's a JWT expiration error
                if "JWT expired" in error_str or "PGRST303" in error_str:
                    logger.error(f"❌ JWT expired error detected with service role client!")
                    logger.error(f"   This suggests the client may have cached a user JWT token.")
                    logger.error(f"   Error details: {query_error}")
                    logger.error(f"⚠️ Attempting to recreate client with service role key...")
                    # Recreate client to ensure clean state - this clears any cached user tokens
                    try:
                        fresh_client = create_client(
                            settings.SUPABASE_URL,
                            settings.SUPABASE_SERVICE_ROLE_KEY
                        )
                        # Verify service role key is configured
                        if not settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_SERVICE_ROLE_KEY == "your-supabase-service-role-key":
                            logger.error("❌ SUPABASE_SERVICE_ROLE_KEY is not configured correctly!")
                            return {}
                        profile_response = fresh_client.table("user_profiles").select("*").eq("user_id", user_id).execute()
                        logger.info(f"✅ Query succeeded after recreating client, rows returned: {len(profile_response.data) if profile_response.data else 0}")
                    except Exception as retry_error:
                        logger.error(f"❌ Retry with fresh client also failed: {retry_error}")
                        return {}
                else:
                    logger.error(f"❌ Database query error (columns may not exist): {query_error}")
                    # Return empty profile if query fails
                    return {}
            profile_data = {}
            
            if not profile_response.data or len(profile_response.data) == 0:
                print(f"⚠️ [get_user_profile] No profile data found for user_id: {user_id}")
            
            if profile_response.data and len(profile_response.data) > 0:
                profile_data = profile_response.data[0].copy()  # Make a copy to avoid modifying original
                
                # Log all keys from database response for debugging (using print for visibility)
                print(f"🔍 [get_user_profile] Raw profile data keys from DB: {list(profile_data.keys())}")
                
                # Check raw values from database - be very explicit about None vs missing
                raw_img_url = profile_data.get('img_url')
                raw_avatar_url = profile_data.get('avatar_url')
                
                print(f"🔍 [get_user_profile] img_url value from DB (raw): {repr(raw_img_url)}")
                print(f"🔍 [get_user_profile] img_url type: {type(raw_img_url)}")
                print(f"🔍 [get_user_profile] img_url is None: {raw_img_url is None}")
                print(f"🔍 [get_user_profile] img_url is falsy: {not raw_img_url}")
                print(f"🔍 [get_user_profile] avatar_url value from DB (raw): {repr(raw_avatar_url)}")
                print(f"🔍 [get_user_profile] avatar_url type: {type(raw_avatar_url)}")
                print(f"🔍 [get_user_profile] avatar_url is None: {raw_avatar_url is None}")
                print(f"🔍 [get_user_profile] avatar_url is falsy: {not raw_avatar_url}")
                logger.info(f"🔍 Raw profile data keys from DB: {list(profile_data.keys())}")
                logger.info(f"🔍 img_url value from DB: {profile_data.get('img_url')}")
                logger.info(f"🔍 avatar_url value from DB: {profile_data.get('avatar_url')}")
                
                # Extract the UUID (id field) before removing it - it's the Supabase user ID
                supabase_uuid = profile_data.get("id")
                
                # Remove system columns and user_id
                profile_data.pop("id", None)
                profile_data.pop("user_id", None)
                profile_data.pop("created_at", None)
                profile_data.pop("updated_at", None)
                
                # Add the Supabase UUID explicitly for frontend use (from user_profiles.id or use the passed user_id)
                if supabase_uuid:
                    profile_data["supabase_user_id"] = supabase_uuid
                else:
                    # Fallback: use the user_id parameter if id wasn't in the response
                    profile_data["supabase_user_id"] = user_id
                
                # Convert role from lowercase (Supabase) to uppercase (PostgreSQL enum)
                if "role" in profile_data and profile_data["role"]:
                    role_mapping = {
                        "patient": "PATIENT",
                        "doctor": "DOCTOR", 
                        "admin": "ADMIN"
                    }
                    # Convert to uppercase for PostgreSQL enum compatibility
                    profile_data["role"] = role_mapping.get(profile_data["role"].lower(), "PATIENT")
                
                # Prioritize img_url over avatar_url for avatar image URL
                # If img_url exists, use it; otherwise fall back to avatar_url
                # Note: img_url might be None in the database, so we need to check explicitly
                img_url_value = profile_data.get("img_url")
                avatar_url_value = profile_data.get("avatar_url")
                
                print(f"🔍 [get_user_profile] After processing - img_url: {repr(img_url_value)}, avatar_url: {repr(avatar_url_value)}")
                logger.info(f"🔍 After processing - img_url: {img_url_value}, avatar_url: {avatar_url_value}")
                
                # Check if img_url has a valid value (not None, not empty string, not "null")
                if img_url_value is not None and str(img_url_value).strip() and str(img_url_value).strip().lower() not in ["null", "none", ""]:
                    profile_data["avatar_url"] = img_url_value
                    # Keep img_url in the data for debugging/frontend use
                    profile_data["img_url"] = img_url_value
                    print(f"✅ [get_user_profile] Using img_url for avatar_url: {img_url_value[:80] if len(str(img_url_value)) > 80 else img_url_value}...")
                    logger.info(f"✅ Using img_url for avatar_url: {img_url_value[:80] if len(str(img_url_value)) > 80 else img_url_value}...")
                elif avatar_url_value is not None and str(avatar_url_value).strip() and str(avatar_url_value).strip().lower() not in ["null", "none", ""]:
                    print(f"⚠️ [get_user_profile] No valid img_url, keeping existing avatar_url: {avatar_url_value[:80] if len(str(avatar_url_value)) > 80 else avatar_url_value}...")
                    logger.info(f"⚠️ No valid img_url, keeping existing avatar_url: {avatar_url_value[:80] if len(str(avatar_url_value)) > 80 else avatar_url_value}...")
                else:
                    print(f"⚠️ [get_user_profile] No img_url or avatar_url in database for user {user_id}")
                    print(f"   img_url_value: {repr(img_url_value)}, avatar_url_value: {repr(avatar_url_value)}")
                    logger.warning(f"⚠️ No img_url or avatar_url in database for user {user_id}")
                    
                    # Try to get avatar from Supabase Storage as fallback
                    print(f"🔄 [get_user_profile] Trying to get avatar from Supabase Storage...")
                    try:
                        storage_avatar_url = await self.get_avatar_signed_url(user_id)
                        if storage_avatar_url:
                            print(f"✅ [get_user_profile] Found avatar in Storage, using it: {storage_avatar_url[:80]}...")
                            profile_data["avatar_url"] = storage_avatar_url
                            profile_data["img_url"] = storage_avatar_url
                        else:
                            print(f"⚠️ [get_user_profile] No avatar found in Storage either")
                            profile_data["avatar_url"] = None
                            profile_data["img_url"] = None
                    except Exception as storage_error:
                        print(f"⚠️ [get_user_profile] Error getting avatar from Storage: {storage_error}")
                        profile_data["avatar_url"] = None
                        profile_data["img_url"] = None
            
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
            
            print(f"✅ [get_user_profile] Returning profile data: {len(profile_data)} fields")
            print(f"🔍 [get_user_profile] Final profile data keys: {list(profile_data.keys())}")
            print(f"🔍 [get_user_profile] Final avatar_url in return: {profile_data.get('avatar_url')}")
            print(f"🔍 [get_user_profile] Final img_url in return: {profile_data.get('img_url')}")
            logger.info(f"✅ Returning profile data: {len(profile_data)} fields")
            logger.info(f"🔍 Final profile data keys: {list(profile_data.keys())}")
            logger.info(f"🔍 Final avatar_url in return: {profile_data.get('avatar_url')}")
            logger.info(f"🔍 Final img_url in return: {profile_data.get('img_url')}")
            return profile_data if profile_data else {}
        except Exception as e:
            print(f"❌ [get_user_profile] ERROR: {e}")
            import traceback
            print(f"❌ [get_user_profile] Traceback: {traceback.format_exc()}")
            logger.error(f"❌ Supabase get user profile error: {e}")
            return {}  # Return empty dict instead of None
    
    async def get_avatar_signed_url(self, user_id: str) -> Optional[str]:
        """Get avatar URL from user_profiles table or Supabase Storage
        First checks database for img_url, then checks Supabase Storage avatars bucket"""
        try:
            print(f"🔍 [get_avatar_signed_url] Getting avatar for user_id: {user_id}")
            
            # Step 1: Check database for img_url first
            try:
                profile_response = self.client.table("user_profiles").select("img_url").eq("user_id", user_id).execute()
                
                if profile_response.data and len(profile_response.data) > 0:
                    img_url = profile_response.data[0].get("img_url")
                    if img_url and str(img_url).strip() and str(img_url).lower() not in ["null", "none", ""]:
                        print(f"✅ [get_avatar_signed_url] Found img_url in database: {img_url[:80] if len(str(img_url)) > 80 else img_url}")
                        logger.debug(f"Found img_url in user_profiles for user {user_id}")
                        return img_url
            except Exception as db_error:
                print(f"⚠️ [get_avatar_signed_url] Error checking database: {db_error}")
            
            print(f"⚠️ [get_avatar_signed_url] No img_url in database, checking Supabase Storage...")
            
            # Step 2: Check Supabase Storage for avatar files
            # Use service role client to avoid JWT expiration issues
            try:
                # Ensure we're using a fresh service role client for storage operations
                storage_client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_ROLE_KEY
                )
                storage = storage_client.storage.from_("avatars")
                
                image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg']
                
                # Try to list files in user's folder
                try:
                    files_response = storage.list(user_id)
                    files = files_response if files_response else []
                    
                    if files and len(files) > 0:
                        print(f"📂 [get_avatar_signed_url] Found {len(files)} files in folder {user_id}")
                        # Find image files (jpg, jpeg, png, webp, etc.)
                        for file_info in files:
                            if isinstance(file_info, dict):
                                file_name = file_info.get('name', '')
                                if any(file_name.lower().endswith(ext) for ext in image_extensions):
                                    # Generate signed URL for this file
                                    file_path = f"{user_id}/{file_name}"
                                    print(f"📸 [get_avatar_signed_url] Found avatar file: {file_path}")
                                    
                                    try:
                                        # Generate signed URL (expires in 1 hour = 3600 seconds)
                                        signed_url_response = storage.create_signed_url(file_path, 3600)
                                        
                                        # Handle different response formats
                                        if isinstance(signed_url_response, dict):
                                            signed_url = signed_url_response.get('signedURL') or signed_url_response.get('signed_url')
                                        elif isinstance(signed_url_response, str):
                                            signed_url = signed_url_response
                                        else:
                                            signed_url = None
                                        
                                        if signed_url:
                                            print(f"✅ [get_avatar_signed_url] Generated signed URL from Storage: {signed_url[:80]}...")
                                            return signed_url
                                        else:
                                            print(f"⚠️ [get_avatar_signed_url] Signed URL response format unexpected: {signed_url_response}")
                                    except Exception as url_error:
                                        print(f"⚠️ [get_avatar_signed_url] Error generating signed URL: {url_error}")
                                        logger.warning(f"Error generating signed URL for {file_path}: {url_error}")
                except Exception as list_error:
                    print(f"⚠️ [get_avatar_signed_url] Error listing files in folder {user_id}: {list_error}")
                
                # If no files in user folder, try listing root and searching
                print(f"🔍 [get_avatar_signed_url] No files in {user_id} folder, checking root...")
                try:
                    root_files_response = storage.list("")
                    root_files = root_files_response if root_files_response else []
                    
                    if root_files:
                        # Search for files that might match user_id
                        for file_info in root_files:
                            if isinstance(file_info, dict):
                                file_name = file_info.get('name', '')
                                if user_id in file_name and any(file_name.lower().endswith(ext) for ext in image_extensions):
                                    print(f"📸 [get_avatar_signed_url] Found potential avatar in root: {file_name}")
                                    try:
                                        signed_url_response = storage.create_signed_url(file_name, 3600)
                                        
                                        # Handle different response formats
                                        if isinstance(signed_url_response, dict):
                                            signed_url = signed_url_response.get('signedURL') or signed_url_response.get('signed_url')
                                        elif isinstance(signed_url_response, str):
                                            signed_url = signed_url_response
                                        else:
                                            signed_url = None
                                        
                                        if signed_url:
                                            print(f"✅ [get_avatar_signed_url] Generated signed URL from Storage root: {signed_url[:80]}...")
                                            return signed_url
                                    except Exception as url_error:
                                        print(f"⚠️ [get_avatar_signed_url] Error generating signed URL for root file: {url_error}")
                except Exception as root_list_error:
                    print(f"⚠️ [get_avatar_signed_url] Error listing root files: {root_list_error}")
                
            except Exception as storage_error:
                error_str = str(storage_error)
                print(f"⚠️ [get_avatar_signed_url] Error checking Supabase Storage: {storage_error}")
                logger.warning(f"Error checking Supabase Storage for user {user_id}: {storage_error}")
                
                # If JWT expired error, try recreating client
                if "JWT expired" in error_str or "PGRST303" in error_str:
                    print(f"🔄 [get_avatar_signed_url] JWT expired, recreating client...")
                    try:
                        fresh_client = create_client(
                            settings.SUPABASE_URL,
                            settings.SUPABASE_SERVICE_ROLE_KEY
                        )
                        storage = fresh_client.storage.from_("avatars")
                        # Retry once with fresh client
                        print(f"🔄 [get_avatar_signed_url] Retrying with fresh client...")
                    except Exception as retry_error:
                        print(f"❌ [get_avatar_signed_url] Retry failed: {retry_error}")
            
            print(f"❌ [get_avatar_signed_url] No avatar found in database or storage for user {user_id}")
            logger.debug(f"No img_url found in user_profiles or Supabase Storage for user {user_id}")
            return None
            
        except Exception as e:
            print(f"❌ [get_avatar_signed_url] ERROR: {e}")
            import traceback
            print(f"❌ [get_avatar_signed_url] Traceback: {traceback.format_exc()}")
            logger.error(f"❌ Error getting avatar URL for user {user_id}: {e}")
            if settings.DEBUG:
                logger.debug(f"Traceback: {traceback.format_exc()}")
            return None
    
    async def update_user_profile(self, user_id: str, profile: Dict[str, Any], user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update user profile in Supabase database"""
        try:
            logger.info(f"💾 Updating user profile for user_id: {user_id}")
            logger.info(f"📝 Profile data: {profile}")
            
            # Always use service role client to avoid token expiration issues
            client = self.client
            
            # Map avatar_url to img_url for consistency with the database column name
            profile_update = profile.copy()
            if "avatar_url" in profile_update and profile_update["avatar_url"]:
                profile_update["img_url"] = profile_update.pop("avatar_url")
                logger.info(f"📸 Mapped avatar_url to img_url: {profile_update.get('img_url')}")
            
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
                    **profile_update,  # Use profile_update which has img_url mapped from avatar_url
                    "updated_at": "now()"
                }).eq("user_id", user_id).execute()
            else:
                # Profile doesn't exist, create it
                logger.info("✨ Profile doesn't exist, creating new...")
                response = client.table("user_profiles").insert({
                    "user_id": user_id,
                    **profile_update,  # Use profile_update which has img_url mapped from avatar_url
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
        """Update user password using Supabase Auth - try user session first, then admin API"""
        try:
            logger.info(f"🔐 Updating password for user_id: {user_id}")
            logger.info(f"📝 Using Supabase URL: {settings.SUPABASE_URL}")
            logger.info(f"📝 Service role key present: {bool(settings.SUPABASE_SERVICE_ROLE_KEY)}")
            logger.info(f"📝 User token present: {bool(user_token)}")
            
            # Method 1: Try using user's session to update their own password (most secure)
            # Users can update their own passwords using their session token
            if user_token:
                try:
                    logger.info("📝 Attempting to update password using user's session (update_user)")
                    
                    # Create a client with user's token
                    from supabase import create_client
                    user_client = create_client(
                        settings.SUPABASE_URL,
                        settings.SUPABASE_ANON_KEY
                    )
                    
                    # Try to use REST API with user's access token directly
                    # This is the recommended approach - users can update their own passwords
                    # The /auth/v1/user endpoint allows users to update their own info
                    try:
                        logger.info("📝 Attempting password update via user's own API endpoint (/auth/v1/user)")
                        url = f"{settings.SUPABASE_URL}/auth/v1/user"
                        headers = {
                            "apikey": settings.SUPABASE_ANON_KEY,
                            "Authorization": f"Bearer {user_token}",
                            "Content-Type": "application/json"
                        }
                        payload = {
                            "password": new_password
                        }
                        
                        logger.info(f"📝 Making PUT request to: {url}")
                        logger.info(f"📝 Headers: apikey present: {bool(headers['apikey'])}, Authorization present: {bool(headers['Authorization'])}")
                        
                        async with httpx.AsyncClient() as client:
                            response = await client.put(url, json=payload, headers=headers, timeout=30.0)
                            
                            logger.info(f"📝 User API endpoint response status: {response.status_code}")
                            
                            if response.status_code >= 200 and response.status_code < 300:
                                logger.info("✅ Password updated successfully using user's own API endpoint")
                                return {"user_id": user_id, "success": True}
                            elif response.status_code >= 400:
                                try:
                                    error_body = response.json()
                                    logger.error(f"❌ User API endpoint error response (JSON): {error_body}")
                                    error_msg = error_body.get("message") or error_body.get("error_description") or error_body.get("error") or str(error_body)
                                    logger.warning(f"⚠️ User API endpoint failed: {error_msg}")
                                    
                                    # Log more details
                                    if "hint" in error_body:
                                        logger.error(f"❌ Error hint: {error_body['hint']}")
                                    if "details" in error_body:
                                        logger.error(f"❌ Error details: {error_body['details']}")
                                    
                                    raise Exception(f"User API endpoint failed: {error_msg}")
                                except Exception as json_error:
                                    error_text = response.text
                                    logger.error(f"❌ User API endpoint error response (text): {error_text}")
                                    logger.warning(f"⚠️ User API endpoint failed (text): {error_text}, JSON parse error: {json_error}")
                                    raise Exception(f"User API endpoint failed: {error_text}")
                            else:
                                raise Exception(f"Unexpected response status: {response.status_code}")
                                
                    except Exception as user_api_error:
                        error_str = str(user_api_error)
                        logger.warning(f"⚠️ User API endpoint method failed: {error_str}")
                        logger.info("📝 Continuing to try admin API methods...")
                        # Continue to admin API methods - don't raise here
                        pass
                        
                except Exception as user_method_error:
                    logger.info(f"⚠️ User session method failed: {user_method_error}, trying admin API")
                    # Continue to admin API methods
            
            # Method 2: Try Python client admin method
            try:
                logger.info("📝 Attempting to update password using Python client admin.update_user_by_id")
                logger.info(f"📝 User ID: {user_id}")
                logger.info(f"📝 Password length: {len(new_password)}")
                
                # Verify we can get the user first (to ensure permissions work)
                try:
                    test_user = self.client.auth.admin.get_user_by_id(user_id)
                    if test_user and hasattr(test_user, 'user') and test_user.user:
                        logger.info(f"✅ Can access user via admin API - user email: {test_user.user.email}")
                    else:
                        logger.warning("⚠️ Could not retrieve user info via admin API")
                except Exception as test_error:
                    logger.warning(f"⚠️ Could not verify user access via admin API: {test_error}")
                
                update_response = self.client.auth.admin.update_user_by_id(
                    user_id,
                    {"password": new_password}
                )
                
                # Check if update was successful
                if update_response and hasattr(update_response, 'user') and update_response.user:
                    logger.info("✅ Password updated successfully using Python admin client")
                    return {"user_id": user_id, "success": True}
                elif update_response:
                    # Some responses might not have a user object but still succeed
                    logger.info("✅ Password update response received from Python admin client")
                    return {"user_id": user_id, "success": True}
                else:
                    logger.warning("⚠️ Python admin client returned None, trying REST API")
                    raise Exception("Python admin client returned None")
                    
            except Exception as python_error:
                error_str = str(python_error)
                logger.warning(f"⚠️ Python admin client method failed: {error_str}")
                logger.warning(f"   Error type: {type(python_error).__name__}")
                
                # Check if it's a permission error
                if "not allowed" in error_str.lower() or "forbidden" in error_str.lower() or "permission" in error_str.lower():
                    logger.error("❌ Python client reports permission issue. This might indicate:")
                    logger.error("   1. Service role key doesn't have admin permissions")
                    logger.error("   2. Supabase project configuration issue")
                    logger.error("   3. Password updates may be disabled in Supabase settings")
                
                # Method 3: Fallback to REST API
                logger.info("📝 Attempting to update password using REST API")
                url = f"{settings.SUPABASE_URL}/auth/v1/admin/users/{user_id}"
                headers = {
                    "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "password": new_password
                }
                
                logger.info(f"📝 Making PUT request to: {url}")
                
                async with httpx.AsyncClient() as client:
                    response = await client.put(url, json=payload, headers=headers, timeout=30.0)
                    
                    # Always log the response status and body for debugging
                    logger.info(f"📝 Response status: {response.status_code}")
                    
                    if response.status_code >= 400:
                        try:
                            error_body = response.json()
                            logger.error(f"❌ Supabase REST API error response (JSON): {error_body}")
                            error_msg = error_body.get("message") or error_body.get("error_description") or error_body.get("error") or str(error_body)
                            
                            # Log more details
                            logger.error(f"❌ Error message: {error_msg}")
                            if "hint" in error_body:
                                logger.error(f"❌ Error hint: {error_body['hint']}")
                            if "details" in error_body:
                                logger.error(f"❌ Error details: {error_body['details']}")
                                
                        except Exception as json_error:
                            error_text = response.text
                            logger.error(f"❌ Supabase REST API error response (text): {error_text}")
                            logger.error(f"❌ Could not parse error as JSON: {json_error}")
                            error_msg = error_text
                        
                        raise httpx.HTTPStatusError(
                            f"Password update failed: {error_msg}",
                            request=response.request,
                            response=response
                        )
                    
                    # Success - parse response
                    try:
                        result = response.json()
                        logger.info(f"✅ Password updated successfully via REST API. Response: {result}")
                        return {"user_id": user_id, "success": True}
                    except:
                        logger.info("✅ Password updated successfully via REST API (no JSON response body)")
                        return {"user_id": user_id, "success": True}
                        
        except httpx.HTTPStatusError as e:
            # HTTP error with response
            error_msg = str(e)
            try:
                error_body = e.response.json()
                error_msg = error_body.get("message") or error_body.get("error_description") or error_body.get("error") or str(error_body)
                logger.error(f"❌ Supabase update password HTTP error: {error_msg}, status: {e.response.status_code}")
                
                # Provide more context
                if "not allowed" in error_msg.lower() or "forbidden" in error_msg.lower():
                    logger.error("⚠️ 'User not allowed' error - possible causes:")
                    logger.error("   1. Service role key doesn't have admin permissions")
                    logger.error("   2. User account might be disabled or restricted")
                    logger.error("   3. Supabase project configuration issue")
                    logger.error("   4. Password updates may be disabled in Authentication > Settings")
                    logger.error("   5. Check if 'Enable password updates' is enabled in Supabase dashboard")
                    
            except:
                error_text = e.response.text if hasattr(e, 'response') else str(e)
                logger.error(f"❌ Supabase update password HTTP error (text): {error_text}, status: {e.response.status_code if hasattr(e, 'response') else 'unknown'}")
                error_msg = error_text
            
            # Re-raise with clearer message
            raise Exception(f"Password update failed: {error_msg}")
        except Exception as e:
            logger.error(f"❌ Supabase update password error: {e}")
            logger.error(f"Error type: {type(e)}")
            if hasattr(e, '__dict__'):
                logger.error(f"Error attributes: {e.__dict__}")
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
                
                # Check for errors before raising
                if verify_response.status_code != 200:
                    error_text = verify_response.text
                    logger.error(f"❌ MFA verify failed with status {verify_response.status_code}: {error_text}")
                    
                    # Try to parse error message
                    try:
                        error_json = verify_response.json()
                        error_msg = error_json.get("message", error_json.get("error_description", "MFA verification failed"))
                        raise Exception(f"MFA verification failed: {error_msg}")
                    except:
                        raise Exception(f"MFA verification failed: {error_text}")
                
                verify_response.raise_for_status()
                verify_result = verify_response.json()
                
                logger.info("✅ MFA verification successful during login")
                
                # The verify result should contain the session tokens with AAL2
                # If no new tokens, use the existing ones (they're now at AAL2)
                return {
                    "access_token": verify_result.get("access_token") or verify_result.get("session", {}).get("access_token") or access_token,
                    "refresh_token": verify_result.get("refresh_token") or verify_result.get("session", {}).get("refresh_token"),
                    "expires_in": verify_result.get("expires_in") or verify_result.get("session", {}).get("expires_in", 3600)
                }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Verify MFA for login error: {error_msg}")
            logger.error(f"Error type: {type(e)}")
            # Re-raise with clear message
            if "422" in error_msg or "Unprocessable" in error_msg or "Invalid" in error_msg:
                raise Exception("Invalid verification code. Please check your authenticator app and try again.")
            raise

# Global instance
supabase_service = SupabaseService() 