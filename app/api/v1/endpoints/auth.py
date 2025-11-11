from datetime import timedelta
import uuid
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.supabase_client import supabase_service
from app.core.patient_token import generate_patient_token
from app.services.doctor_supabase_service import doctor_supabase_service
from app.models.user import User, UserRole
from app.models.permissions import HealthRecordPermission
from app.schemas.user import Token, LoginResponse, MFALoginVerifyRequest, UserResponse, UserProfile, UserRegistration, UserEmergency, UserNotifications, UserIntegrations, UserPrivacy, UserSharedAccess, UserAccessLogs, UserDataSharing, PasswordChange, MFAEnrollRequest, MFAEnrollResponse, MFAVerifyRequest, MFAFactor
from app.crud.user import get_user_by_supabase_id
from sqlalchemy import and_, func
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter()

# Custom authentication scheme for Supabase tokens
def extract_user_id_from_token(token: str) -> str:
    """Extract user ID from JWT token"""
    try:
        # Decode JWT token without verification (since it's already verified by Supabase)
        # We just need to extract the user ID
        decoded = jwt.decode(token, options={"verify_signature": False})
        user_id = decoded.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_supabase_token(authorization: Optional[str] = Header(None)) -> str:
    """Extract Supabase token from Authorization header and return the actual JWT token"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.replace("Bearer ", "")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Return the actual JWT token for Supabase authentication
    return token

async def get_user_id_from_token(authorization: Optional[str] = Header(None)) -> str:
    """Extract user ID from Authorization header JWT token"""
    logger.info(f"🔍 get_user_id_from_token called, authorization header: {authorization[:50] if authorization else 'None'}...")
    
    if not authorization:
        logger.error("❌ Authorization header missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not authorization.startswith("Bearer "):
        logger.error("❌ Invalid authorization header format")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.replace("Bearer ", "")
    if not token:
        logger.error("❌ Token missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user ID from the JWT token
    user_id = extract_user_id_from_token(token)
    logger.info(f"✅ Extracted user_id: {user_id}")
    return user_id

@router.post("/register", response_model=UserResponse)
async def register(registration_data: UserRegistration, db: Session = Depends(get_db)):
    """Register a new user with Supabase"""
    try:
        # Determine role from registration data
        user_role = registration_data.role if registration_data.role else UserRole.PATIENT
        role_str = user_role.value.lower()
        
        # Register user with Supabase
        supabase_response = await supabase_service.sign_up(
            email=registration_data.email,
            password=registration_data.password,
            user_metadata={
                "full_name": registration_data.full_name,
                "role": role_str  # Store role in user metadata
            }
        )
        
        if not supabase_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to register user with Supabase"
            )
        
        # Auto-confirm the user's email so they can log in immediately
        await supabase_service.confirm_user_email(supabase_response.user.id)
        
        # Extract profile data for Supabase storage
        profile_data = {
            "email": registration_data.email,  # Store email in profile for easy access
            "full_name": registration_data.full_name,
            "date_of_birth": registration_data.date_of_birth,
            "phone_number": registration_data.phone_number,
            "phone_country_code": registration_data.phone_country_code,
            "address": registration_data.address,
            "avatar_url": registration_data.avatar_url,
            "role": role_str,
            "timezone": registration_data.timezone,  # Save timezone to user_profiles
            "emergency_contact_name": registration_data.emergency_contact_name,
            "emergency_contact_phone": registration_data.emergency_contact_phone,
            "emergency_contact_relationship": registration_data.emergency_contact_relationship,
            "gender": registration_data.gender,
            "height": registration_data.height,
            "weight": registration_data.weight,
            "waist_diameter": registration_data.waist_diameter,
            "blood_type": registration_data.blood_type,
            "allergies": registration_data.allergies,
            "emergency_medical_info": registration_data.emergency_medical_info,
        }
        
        # Store profile data in appropriate table based on role
        if user_role == UserRole.DOCTOR:
            # Store doctor profile in doctor_profiles table
            doctor_profile_data = {
                "first_name": registration_data.full_name.split()[0] if registration_data.full_name else None,
                "last_name": " ".join(registration_data.full_name.split()[1:]) if registration_data.full_name and len(registration_data.full_name.split()) > 1 else None,
                "full_name": registration_data.full_name,
                "phone_number": registration_data.phone_number,
                "phone_country_code": registration_data.phone_country_code,
                "address": registration_data.address,
                "avatar_url": registration_data.avatar_url,
                "specialty": getattr(registration_data, 'specialty', None),  # If specialty field exists
            }
            await doctor_supabase_service.store_doctor_profile(
                user_id=supabase_response.user.id,
                profile={k: v for k, v in doctor_profile_data.items() if v is not None}
            )
        else:
            # Store patient profile in user_profiles table
            await supabase_service.store_user_profile(
                user_id=supabase_response.user.id,
                profile={k: v for k, v in profile_data.items() if v is not None}
            )
            
            # Create minimal internal user record for application linkage
            db_user = User(
                supabase_user_id=supabase_response.user.id,  # Link to Supabase
                email=registration_data.email,  # For lookups only
                role=user_role,  # Set role in User model
                is_active=True
            )
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            return UserResponse(
                id=db_user.id,
                email=registration_data.email,
                is_active=db_user.is_active,
                role=db_user.role,
                created_at=db_user.created_at,
                updated_at=db_user.updated_at
            )
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        
        # Check for specific error types and return appropriate messages
        error_message = str(e).lower()
        
        if "user already registered" in error_message or "email already exists" in error_message or "duplicate" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists. Please try logging in instead."
            )
        elif "invalid email" in error_message or "email format" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please enter a valid email address."
            )
        elif "password" in error_message and ("weak" in error_message or "short" in error_message):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters long."
            )
        elif "network" in error_message or "connection" in error_message:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to connect to authentication service. Please try again later."
            )
        else:
            # Generic error for unknown issues
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed. Please try again."
            )

@router.post("/reset-password")
async def reset_password(request_data: dict):
    """Send password reset email"""
    try:
        email = request_data.get("email")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required"
            )
        
        # Use Supabase to send password reset email
        await supabase_service.reset_password(email)
        
        return {"message": "Password reset email sent successfully"}
    except HTTPException:
        # Re-raise HTTP exceptions (like validation errors)
        raise
    except Exception as e:
        error_message = str(e).lower()
        
        # Handle specific error types
        if "rate limit" in error_message or "24 seconds" in error_message or "too many" in error_message:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many password reset requests. Please wait before trying again."
            )
        elif "invalid email" in error_message or "email not found" in error_message:
            # For security, don't reveal if email exists - return generic success
            return {"message": "If an account with that email exists, a password reset email has been sent"}
        else:
            # For other errors, log and return generic message for security
            logger.error(f"Password reset error: {e}")
            return {"message": "If an account with that email exists, a password reset email has been sent"}

@router.post("/oauth-profile", response_model=UserResponse)
async def create_oauth_profile(oauth_data: dict, db: Session = Depends(get_db), authorization: Optional[str] = Header(None)):
    """Create user profile for OAuth users (Google, GitHub, etc.)"""
    try:
        # Extract user ID from the JWT token in the request
        user_id = await get_user_id_from_token(authorization)
        
        # Check if user already exists in our database
        existing_user = get_user_by_supabase_id(db, user_id)
        if existing_user:
            # User already exists, return existing profile
            return UserResponse(
                id=existing_user.id,
                email=existing_user.email,
                is_active=existing_user.is_active,
                is_superuser=existing_user.is_superuser,
                created_at=existing_user.created_at,
                updated_at=existing_user.updated_at
            )
        
        # Create new user record in our database
        db_user = User(
            supabase_user_id=user_id,
            email=oauth_data.get("email"),
            is_active=True
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Store OAuth user data in Supabase user_profiles table
        profile_data = {
            "email": oauth_data.get("email"),
            "full_name": oauth_data.get("full_name"),
            "avatar_url": oauth_data.get("avatar_url"),
            "provider": oauth_data.get("provider"),
            "is_new_user": True,
            "onboarding_completed": False,
            "onboarding_skipped": False,
        }
        
        # Store profile in Supabase
        await supabase_service.store_user_profile(
            user_id=user_id,
            profile={k: v for k, v in profile_data.items() if v is not None}
        )
        
        return UserResponse(
            id=db_user.id,
            email=db_user.email,
            is_active=db_user.is_active,
            role=db_user.role,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at
        )
        
    except Exception as e:
        logger.error(f"OAuth profile creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create OAuth user profile"
        )

@router.post("/login", response_model=LoginResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login user with Supabase and return access token or MFA requirement"""
    try:
        # Authenticate with Supabase
        supabase_response = await supabase_service.sign_in(
            email=form_data.username,
            password=form_data.password
        )
        
        # Check if response has error
        if hasattr(supabase_response, 'error') and supabase_response.error:
            logger.error(f"Supabase sign_in error: {supabase_response.error}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not supabase_response or not hasattr(supabase_response, 'user') or not supabase_response.user:
            logger.error(f"Supabase sign_in failed - no user in response: {supabase_response}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if session exists
        if not hasattr(supabase_response, 'session') or not supabase_response.session:
            logger.error(f"Supabase sign_in failed - no session in response: {supabase_response}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed. Please try again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get internal user record by Supabase UID
        db_user = get_user_by_supabase_id(db, supabase_user_id=supabase_response.user.id)

        print(db_user)
        if not db_user or not db_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Check if user has MFA factors enrolled
        # Only require MFA if there are verified factors (2FA is actually enabled)
        try:
            factors = await supabase_service.list_mfa_factors(user_id=supabase_response.user.id)
            # Only look for verified factors - unverified factors don't require MFA
            verified_factors = [f for f in factors if f.get("status") == "verified"]
            
            # Only require MFA if there are verified factors
            if verified_factors and len(verified_factors) > 0:
                logger.info(f"User has {len(verified_factors)} verified MFA factor(s) - MFA required")
                # User has verified MFA factors - MFA verification is required
                # Store the temporary session for MFA verification
                # Return MFA requirement response
                return {
                    "mfa_required": True,
                    "factor_id": verified_factors[0].get("id"),
                    "user_id": supabase_response.user.id,
                    "access_token": supabase_response.session.access_token,  # Temporary token for MFA verification
                    "refresh_token": supabase_response.session.refresh_token,
                    "token_type": "bearer",
                    "expires_in": supabase_response.session.expires_in
                }
            else:
                logger.info(f"User has {len(factors) if factors else 0} MFA factor(s), but none are verified - MFA not required")
        except Exception as mfa_error:
            # If we can't check MFA factors, continue with normal login (don't require MFA)
            logger.warning(f"Could not check MFA factors: {mfa_error} - continuing without MFA requirement")
        
        # No MFA required - return normal token response
        return {
            "access_token": supabase_response.session.access_token,
            "refresh_token": supabase_response.session.refresh_token,
            "token_type": "bearer",
            "expires_in": supabase_response.session.expires_in,
            "mfa_required": False,
            "user_id": supabase_response.user.id  # Include user_id in response
        }
        
    except HTTPException:
        # Re-raise HTTPExceptions (like the ones we raise above)
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        logger.error(f"Login error type: {type(e)}")
        logger.error(f"Login error details: {str(e)}")
        
        # Check if it's a Supabase Auth error
        error_message = str(e).lower()
        error_str = str(e)
        
        # Check for Supabase Auth API errors
        if hasattr(e, 'message'):
            error_message = str(e.message).lower()
            error_str = str(e.message)
        elif hasattr(e, 'args') and len(e.args) > 0:
            error_str = str(e.args[0])
            error_message = error_str.lower()
        
        # Check for specific error types and return appropriate messages
        if "invalid credentials" in error_message or "incorrect password" in error_message or "invalid login credentials" in error_message:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password. Please check your credentials and try again."
            )
        elif "user not found" in error_message or "email not found" in error_message:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No account found with this email address. Please sign up first."
            )
        elif "email not confirmed" in error_message or "verify" in error_message:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please check your email and click the confirmation link before logging in."
            )
        elif "too many requests" in error_message or "rate limit" in error_message:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please wait a few minutes before trying again."
            )
        elif "network" in error_message or "connection" in error_message:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to connect to authentication service. Please try again later."
            )
        else:
            # Generic error for unknown issues
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Login failed. Please check your credentials and try again."
            )

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    current_user_id: str = Depends(get_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    """Get user profile from Supabase"""
    logger.info(f"📋 GET /profile endpoint called for user_id: {current_user_id}")
    try:
        # Extract token from authorization header
        user_token = authorization.replace("Bearer ", "") if authorization else None
        logger.info(f"🔑 Token extracted: {user_token[:50] if user_token else 'None'}...")
        
        # Get personal data from Supabase
        profile_data = await supabase_service.get_user_profile(current_user_id, user_token)
        logger.info(f"📦 Profile data retrieved: {len(profile_data) if profile_data else 0} fields")
        
        # Handle case where profile data is None or empty
        if not profile_data:
            # Return empty profile if no data exists
            logger.info("⚠️ No profile data found, returning empty UserProfile")
            return UserProfile()
        
        logger.info(f"✅ Returning profile with data")
        return UserProfile(**profile_data)
    except Exception as e:
        logger.error(f"❌ Get profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )

@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    profile_data: UserProfile, 
    current_user_id: str = Depends(get_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    """Update user profile in Supabase"""
    logger.info(f"💾 PUT /profile endpoint called for user_id: {current_user_id}")
    logger.info(f"📝 Profile data received: {profile_data.dict(exclude_none=True)}")
    try:
        # Extract token from authorization header
        user_token = authorization.replace("Bearer ", "") if authorization else None
        
        # Update personal data in Supabase
        updated_profile = await supabase_service.update_user_profile(
            user_id=current_user_id,
            profile=profile_data.dict(exclude_none=True),
            user_token=user_token
        )
        
        logger.info(f"📦 Updated profile received: {updated_profile}")
        
        # Handle case where updated profile is None
        if not updated_profile:
            # Return the original profile data if update failed
            logger.warning("⚠️ Update returned None, returning original profile data")
            return profile_data
        
        logger.info(f"✅ Successfully updated profile")
        return UserProfile(**updated_profile)
    except Exception as e:
        logger.error(f"❌ Update profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )

@router.get("/emergency", response_model=UserEmergency)
async def get_user_emergency(
    current_user_id: str = Depends(get_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    """Get user emergency data from Supabase"""
    logger.info(f"📋 GET /emergency endpoint called for user_id: {current_user_id}")
    try:
        # Extract token from authorization header
        user_token = authorization.replace("Bearer ", "") if authorization else None
        logger.info(f"🔑 Token extracted: {user_token[:50] if user_token else 'None'}...")
        
        # Get emergency data from Supabase
        emergency_data = await supabase_service.get_user_emergency(current_user_id, user_token)
        logger.info(f"📦 Emergency data retrieved: {len(emergency_data) if emergency_data else 0} fields")
        
        # Handle case where emergency data is None or empty
        if not emergency_data:
            # Return empty emergency if no data exists
            logger.info("⚠️ No emergency data found, returning empty UserEmergency")
            return UserEmergency()
        
        logger.info(f"✅ Returning emergency with data")
        return UserEmergency(**emergency_data)
    except Exception as e:
        logger.error(f"❌ Get emergency error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user emergency data"
        )

@router.put("/emergency", response_model=UserEmergency)
async def update_user_emergency(
    emergency_data: UserEmergency, 
    current_user_id: str = Depends(get_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    """Update user emergency data in Supabase"""
    logger.info(f"💾 PUT /emergency endpoint called for user_id: {current_user_id}")
    logger.info(f"📝 Emergency data received: {emergency_data.dict(exclude_none=True)}")
    try:
        # Extract token from authorization header
        user_token = authorization.replace("Bearer ", "") if authorization else None
        
        # Update emergency data in Supabase
        updated_emergency = await supabase_service.update_user_emergency(
            user_id=current_user_id,
            emergency=emergency_data.dict(exclude_none=True),
            user_token=user_token
        )
        
        logger.info(f"📦 Updated emergency received: {updated_emergency}")
        
        # Handle case where updated emergency is None
        if not updated_emergency:
            # Return the original emergency data if update failed
            logger.warning("⚠️ Update returned None, returning original emergency data")
            return emergency_data
        
        logger.info(f"✅ Successfully updated emergency")
        return UserEmergency(**updated_emergency)
    except Exception as e:
        logger.error(f"❌ Update emergency error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user emergency data"
        )

@router.get("/notifications", response_model=UserNotifications)
async def get_user_notifications(
    current_user_id: str = Depends(get_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    """Get user notification preferences from Supabase"""
    logger.info(f"📋 GET /notifications endpoint called for user_id: {current_user_id}")
    try:
        # Extract token from authorization header
        user_token = authorization.replace("Bearer ", "") if authorization else None
        logger.info(f"🔑 Token extracted: {user_token[:50] if user_token else 'None'}...")
        
        # Get notifications from Supabase
        notifications_data = await supabase_service.get_user_notifications(current_user_id, user_token)
        logger.info(f"📦 Notifications data retrieved: {len(notifications_data) if notifications_data else 0} fields")
        
        # Handle case where notifications data is None or empty
        if not notifications_data:
            # Return empty notifications if no data exists
            logger.info("⚠️ No notifications data found, returning empty UserNotifications")
            return UserNotifications()
        
        logger.info(f"✅ Returning notifications with data")
        return UserNotifications(**notifications_data)
    except Exception as e:
        logger.error(f"❌ Get notifications error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user notification preferences"
        )

@router.put("/notifications", response_model=UserNotifications)
async def update_user_notifications(
    notifications_data: UserNotifications, 
    current_user_id: str = Depends(get_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    """Update user notification preferences in Supabase"""
    logger.info(f"💾 PUT /notifications endpoint called for user_id: {current_user_id}")
    logger.info(f"📝 Notifications data received: {notifications_data.dict(exclude_none=True)}")
    try:
        # Extract token from authorization header
        user_token = authorization.replace("Bearer ", "") if authorization else None
        
        # Update notifications in Supabase
        updated_notifications = await supabase_service.update_user_notifications(
            user_id=current_user_id,
            notifications=notifications_data.dict(exclude_none=True),
            user_token=user_token
        )
        
        logger.info(f"📦 Updated notifications received: {updated_notifications}")
        
        # Handle case where updated notifications is None
        if not updated_notifications:
            # Return the original notifications data if update failed
            logger.warning("⚠️ Update returned None, returning original notifications data")
            return notifications_data
        
        logger.info(f"✅ Successfully updated notifications")
        return UserNotifications(**updated_notifications)
    except Exception as e:
        logger.error(f"❌ Update notifications error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user notification preferences"
        )

@router.get("/integrations", response_model=UserIntegrations)
async def get_user_integrations(
    current_user_id: str = Depends(get_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    """Get user integration preferences from Supabase"""
    logger.info(f"📋 GET /integrations endpoint called for user_id: {current_user_id}")
    try:
        user_token = authorization.replace("Bearer ", "") if authorization else None
        logger.info(f"🔑 Token extracted: {user_token[:50] if user_token else 'None'}...")
        
        integrations_data = await supabase_service.get_user_integrations(current_user_id, user_token)
        logger.info(f"📦 Integrations data retrieved: {len(integrations_data) if integrations_data else 0} fields")
        
        if not integrations_data:
            logger.info("⚠️ No integrations data found, returning empty UserIntegrations")
            return UserIntegrations()
        
        logger.info(f"✅ Returning integrations with data")
        return UserIntegrations(**integrations_data)
    except Exception as e:
        logger.error(f"❌ Get integrations error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user integrations"
        )

@router.put("/integrations", response_model=UserIntegrations)
async def update_user_integrations(
    integrations_data: UserIntegrations, 
    current_user_id: str = Depends(get_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    """Update user integration preferences in Supabase"""
    logger.info(f"💾 PUT /integrations endpoint called for user_id: {current_user_id}")
    logger.info(f"📝 Integrations data received: {integrations_data.dict(exclude_none=True)}")
    try:
        user_token = authorization.replace("Bearer ", "") if authorization else None
        
        updated_integrations = await supabase_service.update_user_integrations(
            user_id=current_user_id,
            integrations=integrations_data.dict(exclude_none=True),
            user_token=user_token
        )
        
        logger.info(f"📦 Updated integrations received: {updated_integrations}")
        
        if not updated_integrations:
            logger.warning("⚠️ Update returned None, returning original integrations data")
            return integrations_data
        
        logger.info(f"✅ Successfully updated integrations")
        return UserIntegrations(**updated_integrations)
    except Exception as e:
        logger.error(f"❌ Update integrations error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user integrations"
        )

@router.get("/privacy", response_model=UserPrivacy)
async def get_user_privacy(
    current_user_id: str = Depends(get_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    """Get user privacy preferences from Supabase"""
    logger.info(f"📋 GET /privacy endpoint called for user_id: {current_user_id}")
    try:
        user_token = authorization.replace("Bearer ", "") if authorization else None
        logger.info(f"🔑 Token extracted: {user_token[:50] if user_token else 'None'}...")
        
        privacy_data = await supabase_service.get_user_privacy(current_user_id, user_token)
        logger.info(f"📦 Privacy data retrieved: {len(privacy_data) if privacy_data else 0} fields")
        
        if not privacy_data:
            logger.info("⚠️ No privacy data found, returning empty UserPrivacy")
            return UserPrivacy()
        
        logger.info(f"✅ Returning privacy with data")
        return UserPrivacy(**privacy_data)
    except Exception as e:
        logger.error(f"❌ Get privacy error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user privacy settings"
        )

@router.put("/privacy", response_model=UserPrivacy)
async def update_user_privacy(
    privacy_data: UserPrivacy, 
    current_user_id: str = Depends(get_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    """Update user privacy preferences in Supabase"""
    logger.info(f"💾 PUT /privacy endpoint called for user_id: {current_user_id}")
    logger.info(f"📝 Privacy data received: {privacy_data.dict(exclude_none=True)}")
    try:
        user_token = authorization.replace("Bearer ", "") if authorization else None
        
        updated_privacy = await supabase_service.update_user_privacy(
            user_id=current_user_id,
            privacy=privacy_data.dict(exclude_none=True),
            user_token=user_token
        )
        
        logger.info(f"📦 Updated privacy received: {updated_privacy}")
        
        if not updated_privacy:
            logger.warning("⚠️ Update returned None, returning original privacy data")
            return privacy_data
        
        logger.info(f"✅ Successfully updated privacy")
        return UserPrivacy(**updated_privacy)
    except Exception as e:
        logger.error(f"❌ Update privacy error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user privacy settings"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token using Supabase refresh token"""
    try:
        # Use Supabase refresh token
        # Note: This would require implementing refresh token logic with Supabase
        # For now, returning a placeholder response
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Refresh token functionality to be implemented with Supabase"
        )
        
    except Exception as e:
        logger.error(f"Refresh token error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

async def get_current_user(token: str = Depends(get_supabase_token), db: Session = Depends(get_db)):
    """Get current authenticated user from Supabase token"""
    try:
        # Verify token with Supabase
        user_info = supabase_service.get_user_from_token(token)
        
        if not user_info or not user_info.get('id'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get internal user record by Supabase UID
        try:
            db_user = get_user_by_supabase_id(db, supabase_user_id=user_info['id'])
        except Exception as db_error:
            # Database connection error - log and return a mock user with Supabase info
            logger.warning(f"Database not available, using Supabase user info: {db_error}")
            # Create a mock user object from Supabase data
            class MockUser:
                def __init__(self, supabase_user_id: str, email: str):
                    self.id = None  # No internal DB ID
                    self.supabase_user_id = supabase_user_id
                    self.email = email
                    self.is_active = True
                    self.is_superuser = False
            
            # Extract email from Supabase user info
            email = user_info.get('email', 'unknown@example.com')
            db_user = MockUser(supabase_user_id=user_info['id'], email=email)
        
        return db_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@router.get("/profile/{patient_id}", response_model=UserProfile)
async def get_patient_profile(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get another patient's profile (requires permission to access)"""
    from app.core.patient_access import check_patient_access
    
    logger.info(f"📋 GET /profile/{patient_id} endpoint called by user_id: {current_user.id}")
    
    # Check if current user has permission to access this patient
    has_access, error_msg = await check_patient_access(
        db=db,
        patient_id=patient_id,
        current_user=current_user,
        permission_type="view_health_records"
    )
    
    if not has_access:
        logger.warning(f"❌ Access denied for patient {patient_id}: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_msg or "No permission to access this patient's data"
        )
    
    # Get patient from database
    patient_user = db.query(User).filter(User.id == patient_id).first()
    if not patient_user:
        logger.warning(f"❌ Patient not found: {patient_id}")
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get patient's profile from Supabase
    try:
        profile_data = await supabase_service.get_user_profile(patient_user.supabase_user_id)
        
        if not profile_data:
            logger.info(f"⚠️ No profile data found for patient {patient_id}, returning empty UserProfile")
            return UserProfile()
        
        logger.info(f"✅ Returning profile data for patient {patient_id}")
        return UserProfile(**profile_data)
    except Exception as e:
        logger.error(f"❌ Error getting patient profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get patient profile"
        )

@router.get("/shared-access", response_model=UserSharedAccess)
async def get_user_shared_access(
    current_user_id: str = Depends(get_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    """Get user shared access preferences from Supabase"""
    logger.info(f"📋 GET /shared-access endpoint called for user_id: {current_user_id}")
    try:
        user_token = authorization.replace("Bearer ", "") if authorization else None
        logger.info(f"🔑 Token extracted: {user_token[:50] if user_token else 'None'}...")
        
        shared_access_data = await supabase_service.get_user_shared_access(current_user_id, user_token)
        logger.info(f"📦 Shared access data retrieved: {len(shared_access_data) if shared_access_data else 0} fields")
        
        if not shared_access_data:
            logger.info("⚠️ No shared access data found, returning empty UserSharedAccess")
            return UserSharedAccess()
        
        logger.info(f"✅ Returning shared access with data")
        return UserSharedAccess(**shared_access_data)
    except Exception as e:
        logger.error(f"❌ Get shared access error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user shared access"
        )

@router.put("/shared-access", response_model=UserSharedAccess)
async def update_user_shared_access(
    shared_access_data: UserSharedAccess, 
    current_user_id: str = Depends(get_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    """Update user shared access preferences in Supabase"""
    logger.info(f"💾 PUT /shared-access endpoint called for user_id: {current_user_id}")
    logger.info(f"📝 Shared access data received: {shared_access_data.dict(exclude_none=True)}")
    try:
        user_token = authorization.replace("Bearer ", "") if authorization else None
        
        updated_shared_access = await supabase_service.update_user_shared_access(
            user_id=current_user_id,
            shared_access=shared_access_data.dict(exclude_none=True),
            user_token=user_token
        )
        
        logger.info(f"📦 Updated shared access received: {updated_shared_access}")
        
        if not updated_shared_access:
            logger.warning("⚠️ Update returned None, returning original shared access data")
            return shared_access_data
        
        logger.info(f"✅ Successfully updated shared access")
        return UserSharedAccess(**updated_shared_access)
    except Exception as e:
        logger.error(f"❌ Update shared access error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user shared access"
        )

@router.get("/access-logs", response_model=UserAccessLogs)
async def get_user_access_logs(
    current_user_id: str = Depends(get_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    """Get user access logs from Supabase"""
    logger.info(f"📋 GET /access-logs endpoint called for user_id: {current_user_id}")
    try:
        user_token = authorization.replace("Bearer ", "") if authorization else None
        logger.info(f"🔑 Token extracted: {user_token[:50] if user_token else 'None'}...")
        
        access_logs_data = await supabase_service.get_user_access_logs(current_user_id, user_token)
        logger.info(f"📦 Access logs data retrieved: {len(access_logs_data) if access_logs_data else 0} fields")
        
        if not access_logs_data:
            logger.info("⚠️ No access logs data found, returning empty UserAccessLogs")
            return UserAccessLogs()
        
        logger.info(f"✅ Returning access logs with data")
        return UserAccessLogs(**access_logs_data)
    except Exception as e:
        logger.error(f"❌ Get access logs error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user access logs"
        )

@router.put("/access-logs", response_model=UserAccessLogs)
async def update_user_access_logs(
    access_logs_data: UserAccessLogs, 
    current_user_id: str = Depends(get_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    """Update user access logs in Supabase"""
    logger.info(f"💾 PUT /access-logs endpoint called for user_id: {current_user_id}")
    logger.info(f"📝 Access logs data received: {access_logs_data.dict(exclude_none=True)}")
    try:
        user_token = authorization.replace("Bearer ", "") if authorization else None
        
        updated_access_logs = await supabase_service.update_user_access_logs(
            user_id=current_user_id,
            access_logs=access_logs_data.dict(exclude_none=True),
            user_token=user_token
        )
        
        logger.info(f"📦 Updated access logs received: {updated_access_logs}")
        
        if not updated_access_logs:
            logger.warning("⚠️ Update returned None, returning original access logs data")
            return access_logs_data
        
        logger.info(f"✅ Successfully updated access logs")
        return UserAccessLogs(**updated_access_logs)
    except Exception as e:
        logger.error(f"❌ Update access logs error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user access logs"
        )

@router.get("/data-sharing", response_model=UserDataSharing)
async def get_user_data_sharing(
    current_user_id: str = Depends(get_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    """Get user data sharing preferences from Supabase"""
    logger.info(f"📋 GET /data-sharing endpoint called for user_id: {current_user_id}")
    try:
        user_token = authorization.replace("Bearer ", "") if authorization else None
        logger.info(f"🔑 Token extracted: {user_token[:50] if user_token else 'None'}...")
        
        data_sharing_preferences = await supabase_service.get_user_data_sharing(current_user_id, user_token)
        logger.info(f"📦 Data sharing data retrieved: {len(data_sharing_preferences) if data_sharing_preferences else 0} fields")
        
        if not data_sharing_preferences:
            logger.info("⚠️ No data sharing data found, returning empty UserDataSharing")
            return UserDataSharing()
        
        logger.info(f"✅ Returning data sharing with data")
        return UserDataSharing(**data_sharing_preferences)
    except Exception as e:
        logger.error(f"❌ Get data sharing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user data sharing preferences"
        )

@router.put("/data-sharing", response_model=UserDataSharing)
async def update_user_data_sharing(
    data_sharing_data: UserDataSharing, 
    current_user_id: str = Depends(get_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    """Update user data sharing preferences in Supabase"""
    logger.info(f"💾 PUT /data-sharing endpoint called for user_id: {current_user_id}")
    logger.info(f"📝 Data sharing data received: {data_sharing_data.dict(exclude_none=True)}")
    try:
        user_token = authorization.replace("Bearer ", "") if authorization else None
        
        updated_data_sharing = await supabase_service.update_user_data_sharing(
            user_id=current_user_id,
            data_sharing=data_sharing_data.dict(exclude_none=True),
            user_token=user_token
        )
        
        logger.info(f"📦 Updated data sharing received: {updated_data_sharing}")
        
        if not updated_data_sharing:
            logger.warning("⚠️ Update returned None, returning original data sharing data")
            return data_sharing_data
        
        logger.info(f"✅ Successfully updated data sharing")
        return UserDataSharing(**updated_data_sharing)
    except Exception as e:
        logger.error(f"❌ Update data sharing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user data sharing preferences"
        )

@router.get("/accessible-patients")
async def get_accessible_patients(
    current_user_id: str = Depends(get_user_id_from_token),
    current_user_db: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """Get list of patients that current user has permission to access (including self)"""
    logger.info(f"📋 GET /accessible-patients endpoint called for user_id: {current_user_id}")
    try:
        from app.crud.user import get_user_by_email
        
        accessible_patients = []
        
        # Get current user's email
        current_user_email = current_user_db.email
        if not current_user_email:
            logger.warning("⚠️ Current user has no email address")
            return {"accessible_patients": []}
        
        # Add current user as first item with full permissions
        try:
            # Get current user's profile from Supabase
            current_user_profile = await supabase_service.get_user_profile(current_user_db.supabase_user_id)
            current_user_name = current_user_profile.get("full_name", current_user_db.email) if current_user_profile else current_user_db.email
        except Exception as e:
            logger.warning(f"Could not get current user profile: {e}")
            current_user_name = current_user_db.email
        
        # Add current user with full permissions
        accessible_patients.append({
            "patient_id": current_user_db.id,
            "patient_supabase_id": current_user_db.supabase_user_id,
            "patient_name": current_user_name,
            "patient_email": current_user_db.email,
            "patient_token": generate_patient_token(current_user_db.id),
            "permissions": {
                "can_view_health_records": True,
                "health_records_download": True,
                "can_view_medical_history": True,
                "can_view_health_plans": True,
                "can_view_medications": True,
                "can_view_appointments": True,
                "can_view_messages": True,
                "can_view_lab_results": True,
                "can_view_imaging": True,
            },
            "granted_for": "Self",
            "expires_at": None
        })
        logger.info(f"✅ Added current user ({current_user_db.id}) to accessible patients list")
        
        logger.info(f"🔍 Looking for permissions for email: {current_user_email}")
        
        # Get all user_shared_access records from Supabase
        # We need to check all users' shared_access records to see if current user's email is in them
        try:
            # Create a fresh client with service role key to avoid JWT expiration issues
            from supabase import create_client
            from app.core.config import settings
            
            fresh_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY
            )
            
            # Get all user_shared_access records
            all_shared_access = fresh_client.table("user_shared_access").select("*").execute()
            
            if all_shared_access.data:
                for shared_access_record in all_shared_access.data:
                    patient_supabase_id = shared_access_record.get("user_id")
                    if not patient_supabase_id:
                        continue
                    
                    # Check health_professionals
                    health_professionals = shared_access_record.get("health_professionals", [])
                    if isinstance(health_professionals, list):
                        for contact in health_professionals:
                            contact_email = contact.get("profile_email") or contact.get("email")
                            if contact_email and contact_email.lower() == current_user_email.lower():
                                # Found a match! This patient has granted access to current user
                                await _add_accessible_patient(
                                    accessible_patients,
                                    patient_supabase_id,
                                    contact,
                                    db,
                                    current_user_db.id
                                )
                    
                    # Check family_friends
                    family_friends = shared_access_record.get("family_friends", [])
                    if isinstance(family_friends, list):
                        for contact in family_friends:
                            contact_email = contact.get("profile_email") or contact.get("email")
                            if contact_email and contact_email.lower() == current_user_email.lower():
                                # Found a match! This patient has granted access to current user
                                await _add_accessible_patient(
                                    accessible_patients,
                                    patient_supabase_id,
                                    contact,
                                    db,
                                    current_user_db.id
                                )
        except Exception as e:
            error_str = str(e)
            # Check if it's a JWT expiration error
            if "JWT expired" in error_str or "PGRST303" in error_str:
                logger.error(f"❌ JWT expired error detected! Attempting to recreate client...")
                try:
                    # Recreate client one more time
                    from supabase import create_client
                    from app.core.config import settings
                    fresh_client = create_client(
                        settings.SUPABASE_URL,
                        settings.SUPABASE_SERVICE_ROLE_KEY
                    )
                    all_shared_access = fresh_client.table("user_shared_access").select("*").execute()
                    logger.info(f"✅ Query succeeded after recreating client")
                    
                    # Process the data again
                    if all_shared_access.data:
                        for shared_access_record in all_shared_access.data:
                            patient_supabase_id = shared_access_record.get("user_id")
                            if not patient_supabase_id:
                                continue
                            
                            # Check health_professionals
                            health_professionals = shared_access_record.get("health_professionals", [])
                            if isinstance(health_professionals, list):
                                for contact in health_professionals:
                                    contact_email = contact.get("profile_email") or contact.get("email")
                                    if contact_email and contact_email.lower() == current_user_email.lower():
                                        await _add_accessible_patient(
                                            accessible_patients,
                                            patient_supabase_id,
                                            contact,
                                            db
                                        )
                            
                            # Check family_friends
                            family_friends = shared_access_record.get("family_friends", [])
                            if isinstance(family_friends, list):
                                for contact in family_friends:
                                    contact_email = contact.get("profile_email") or contact.get("email")
                                    if contact_email and contact_email.lower() == current_user_email.lower():
                                        await _add_accessible_patient(
                                            accessible_patients,
                                            patient_supabase_id,
                                            contact,
                                            db
                                        )
                except Exception as retry_error:
                    logger.error(f"❌ Retry with fresh client also failed: {retry_error}")
            else:
                logger.error(f"❌ Error querying user_shared_access: {e}")
        
        # Also check PostgreSQL health_record_permissions table (for backward compatibility)
        try:
            permissions = db.query(HealthRecordPermission).filter(
                and_(
                    HealthRecordPermission.professional_id == current_user_db.id,
                    HealthRecordPermission.is_active == True
                )
            ).all()
            
            for perm in permissions:
                # Check if expired
                if perm.expires_at and perm.expires_at < db.query(func.now()).scalar():
                    continue
                
                # Get patient info
                patient = db.query(User).filter(User.id == perm.patient_id).first()
                if not patient:
                    continue
                
                # Skip if this is the current user (already added as first item)
                if patient.id == current_user_db.id:
                    continue
                
                # Check if we already added this patient
                if any(p["patient_id"] == patient.id for p in accessible_patients):
                    continue
                
                # Get patient profile from Supabase
                try:
                    patient_profile = await supabase_service.get_user_profile(patient.supabase_user_id)
                    patient_name = patient_profile.get("full_name", "Unknown")
                except Exception as e:
                    logger.warning(f"Could not get patient profile for {patient.supabase_user_id}: {e}")
                    patient_name = "Unknown"
                
                accessible_patients.append({
                    "patient_id": patient.id,
                    "patient_supabase_id": patient.supabase_user_id,
                    "patient_name": patient_name,
                    "patient_email": patient.email,
            "patient_token": generate_patient_token(patient.id),
                    "permissions": {
                        "can_view_health_records": perm.can_view_health_records,
                        "health_records_download": False,
                        "can_view_medical_history": perm.can_view_medical_history,
                        "can_view_health_plans": perm.can_view_health_plans,
                        "can_view_medications": perm.can_view_medications,
                        "can_view_appointments": perm.can_view_appointments,
                        "can_view_messages": perm.can_view_messages,
                        "can_view_lab_results": perm.can_view_lab_results,
                        "can_view_imaging": perm.can_view_imaging,
                    },
                    "granted_for": perm.granted_for,
                    "expires_at": perm.expires_at.isoformat() if perm.expires_at else None
                })
        except Exception as e:
            logger.error(f"❌ Error querying health_record_permissions: {e}")
        
        logger.info(f"✅ Returning {len(accessible_patients)} accessible patients")
        return {"accessible_patients": accessible_patients}
        
    except Exception as e:
        logger.error(f"❌ Get accessible patients error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get accessible patients"
        )

async def _add_accessible_patient(
    accessible_patients: list,
    patient_supabase_id: str,
    contact: dict,
    db: Session,
    current_user_id: Optional[int] = None
):
    """Helper function to add an accessible patient from user_shared_access contact"""
    try:
        # Get patient from database
        patient = db.query(User).filter(User.supabase_user_id == patient_supabase_id).first()
        if not patient:
            logger.warning(f"⚠️ Patient not found in database for supabase_id: {patient_supabase_id}")
            return
        
        # Skip if this is the current user (already added as first item)
        if current_user_id and patient.id == current_user_id:
            return
        
        # Check if already added
        if any(p["patient_id"] == patient.id for p in accessible_patients):
            return
        
        # Get patient profile
        try:
            patient_profile = await supabase_service.get_user_profile(patient_supabase_id)
            patient_name = patient_profile.get("full_name", contact.get("profile_fullname", "Unknown"))
        except Exception as e:
            logger.warning(f"Could not get patient profile: {e}")
            patient_name = contact.get("profile_fullname", "Unknown")
        
        # Map permissions from contact to our format
        permissions = {
            "can_view_health_records": contact.get("health_records_view", False),
            "health_records_download": contact.get("health_records_download", False),
            "can_view_medical_history": contact.get("medical_history_view", False),
            "can_view_health_plans": contact.get("health_plan_view", False),
            "can_view_medications": contact.get("medications_view", False),
            "can_view_appointments": contact.get("appointments_view", False),
            "can_view_messages": contact.get("messages_view", False),
            "can_view_lab_results": False,  # Not in contact format
            "can_view_imaging": False,  # Not in contact format
        }
        
        # Check expiration
        expires_at = None
        expires_str = contact.get("expires")
        if expires_str:
            try:
                expires_at = expires_str  # Keep as string, frontend will parse
            except:
                pass
        
        accessible_patients.append({
            "patient_id": patient.id,
            "patient_supabase_id": patient_supabase_id,
            "patient_name": patient_name,
            "patient_email": patient.email,
            "patient_token": generate_patient_token(patient.id),
            "permissions": permissions,
            "granted_for": contact.get("permissions_relationship", "shared_access"),
            "expires_at": expires_at
        })
    except Exception as e:
        logger.error(f"❌ Error adding accessible patient: {e}")

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user_id: str = Depends(get_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    """Change user password"""
    logger.info(f"🔐 POST /change-password endpoint called for user_id: {current_user_id}")
    try:
        # Extract token from authorization header
        user_token = authorization.replace("Bearer ", "") if authorization else None
        
        # Get user email - try from JWT token first, then from user profile
        email = None
        
        # Method 1: Try to get email from JWT token
        try:
            if user_token:
                decoded = jwt.decode(user_token, options={"verify_signature": False})
                email = decoded.get("email")
                if email:
                    logger.info(f"📧 Got email from JWT token: {email}")
        except Exception as jwt_error:
            logger.debug(f"Could not get email from JWT: {jwt_error}")
        
        # Method 2: Try to get email from user profile if not in JWT
        if not email:
            try:
                profile_data = await supabase_service.get_user_profile(current_user_id, user_token)
                if profile_data and profile_data.get("email"):
                    email = profile_data.get("email")
                    logger.info(f"📧 Got email from user profile: {email}")
            except Exception as profile_error:
                logger.warning(f"Could not get email from profile: {profile_error}")
        
        # Method 3: Fallback - try admin API (may fail if service role key doesn't have permissions)
        if not email:
            try:
                logger.info("📝 Attempting to get email from admin API (fallback)")
                user_response = supabase_service.client.auth.admin.get_user_by_id(current_user_id)
                if user_response and hasattr(user_response, 'user') and user_response.user:
                    email = user_response.user.email
                    if email:
                        logger.info(f"📧 Got email from admin API: {email}")
            except Exception as admin_error:
                logger.warning(f"Could not get email from admin API: {admin_error}")
                # Don't raise here - we'll try without email first
        
        # If we still don't have email, we can't verify the current password
        # But we can still try to update the password using the user's token
        if not email:
            logger.warning("⚠️ Could not retrieve user email - will attempt password update without email verification")
            # We'll skip password verification and go directly to password update
            # The password update endpoint should validate the user's session
        else:
            logger.info(f"📧 Verifying current password for email: {email}")
            
            # Verify current password by attempting to sign in
            # Note: If MFA is enabled, sign_in might return a response without session
            # but with mfa_required flag - in that case, password is still correct
            try:
                sign_in_response = await supabase_service.sign_in(email, password_data.current_password)
                
                # If sign in succeeds (no exception), password is correct
                logger.info("✅ Current password verified successfully")
            except Exception as sign_in_error:
                error_msg = str(sign_in_error).lower()
                full_error = str(sign_in_error)
                
                logger.info(f"🔍 Sign in error details: {full_error}")
                
                # If MFA is required, that means the password was correct
                # Check for MFA-related errors or codes
                is_mfa_error = (
                    "mfa" in error_msg or 
                    "multi-factor" in error_msg or 
                    "2fa" in error_msg or 
                    "two-factor" in error_msg or
                    "aal2" in error_msg
                )
                
                if is_mfa_error:
                    logger.info("✅ Password is correct (MFA required, which indicates valid credentials)")
                    # Password is correct, continue with password update
                else:
                    # Check if it's a specific invalid credentials error
                    if "invalid" in error_msg and ("credentials" in error_msg or "password" in error_msg or "login" in error_msg):
                        logger.warning(f"❌ Current password verification failed: {full_error}")
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Current password is incorrect"
                        )
                    else:
                        # Unknown error - log it but don't assume password is wrong
                        logger.error(f"❓ Unexpected error during password verification: {full_error}")
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Could not verify password: {full_error}"
                        )
        
        # Password is verified (either directly or via MFA requirement, or skipped if email not available)
        # Now update to new password
        logger.info(f"🔐 Attempting to update password for user: {current_user_id}")
        await supabase_service.update_password(current_user_id, password_data.new_password, user_token)
        
        logger.info(f"✅ Password changed successfully")
        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"❌ Change password error: {error_msg}")
        logger.error(f"❌ Error type: {error_type}")
        
        # Log full exception details if available
        if hasattr(e, '__dict__'):
            logger.error(f"❌ Error attributes: {e.__dict__}")
        
        # Import traceback for full stack trace
        import traceback
        logger.error(f"❌ Full traceback:\n{traceback.format_exc()}")
        
        # Extract more specific error message if available
        detail_message = error_msg
        if "User not allowed" in error_msg or "not allowed" in error_msg.lower():
            detail_message = "Password update failed: User not allowed. This may be due to Supabase project configuration or service role key permissions."
        elif "Failed to change password" in error_msg:
            detail_message = error_msg  # Already has context
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail_message
        )

@router.post("/mfa/enroll", response_model=MFAEnrollResponse)
async def enroll_mfa(
    enroll_data: MFAEnrollRequest,
    current_user_id: str = Depends(get_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    """Enroll user in TOTP MFA"""
    logger.info(f"🔐 POST /mfa/enroll endpoint called for user_id: {current_user_id}")
    try:
        # Extract token from authorization header
        user_token = authorization.replace("Bearer ", "") if authorization else None
        
        # Enroll in MFA
        result = await supabase_service.enroll_mfa_totp(
            user_id=current_user_id,
            friendly_name=enroll_data.friendly_name
        )
        
        logger.info(f"✅ MFA enrollment initiated")
        return MFAEnrollResponse(**result)
    except Exception as e:
        logger.error(f"❌ MFA enrollment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enroll in MFA"
        )

@router.post("/mfa/verify")
async def verify_mfa_enrollment(
    verify_data: MFAVerifyRequest,
    current_user_id: str = Depends(get_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    """Verify TOTP MFA code during enrollment"""
    logger.info(f"🔐 POST /mfa/verify endpoint called for user_id: {current_user_id}")
    try:
        # Extract token from authorization header
        user_token = authorization.replace("Bearer ", "") if authorization else None
        
        # Verify MFA
        result = await supabase_service.verify_mfa_totp(
            user_id=current_user_id,
            factor_id=verify_data.factor_id,
            code=verify_data.code
        )
        
        logger.info(f"✅ MFA verification successful")
        return {"message": "MFA verified successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ MFA verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify MFA code"
        )

@router.get("/mfa/factors", response_model=List[MFAFactor])
async def get_mfa_factors(
    current_user_id: str = Depends(get_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    """Get all MFA factors for a user"""
    logger.info(f"🔐 GET /mfa/factors endpoint called for user_id: {current_user_id}")
    try:
        # Extract token from authorization header
        user_token = authorization.replace("Bearer ", "") if authorization else None
        
        # Get MFA factors
        factors = await supabase_service.list_mfa_factors(user_id=current_user_id)
        
        logger.info(f"✅ Retrieved {len(factors)} MFA factors")
        return [MFAFactor(**factor) for factor in factors]
    except Exception as e:
        logger.error(f"❌ Get MFA factors error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get MFA factors"
        )

@router.delete("/mfa/factors/{factor_id}")
async def delete_mfa_factor(
    factor_id: str,
    current_user_id: str = Depends(get_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    """Remove an MFA factor"""
    logger.info(f"🔐 DELETE /mfa/factors/{factor_id} endpoint called for user_id: {current_user_id}")
    try:
        # Extract token from authorization header
        user_token = authorization.replace("Bearer ", "") if authorization else None
        
        # Unenroll MFA factor
        success = await supabase_service.unenroll_mfa_factor(
            user_id=current_user_id,
            factor_id=factor_id
        )
        
        if success:
            logger.info(f"✅ MFA factor unenrolled")
            return {"message": "MFA factor removed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove MFA factor"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete MFA factor error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove MFA factor"
        )

@router.post("/login/mfa/verify", response_model=Token)
async def verify_mfa_login(
    verify_request: MFALoginVerifyRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Verify MFA code during login and return final access token"""
    try:
        # Extract temporary access token from authorization header
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
            )
        
        token = authorization.replace("Bearer ", "")
        user_id_from_token = extract_user_id_from_token(token)
        
        # Validate code format (should be 6 digits)
        if not verify_request.code or len(verify_request.code) != 6 or not verify_request.code.isdigit():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code must be 6 digits",
            )
        
        # Verify MFA code using the temporary session
        verified_session = await supabase_service.verify_mfa_for_login(
            user_id=user_id_from_token,
            factor_id=verify_request.factor_id,
            code=verify_request.code,
            access_token=token
        )
        
        if not verified_session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid verification code. Please check your authenticator app and try again.",
            )
        
        # Return the verified session tokens
        return {
            "access_token": verified_session["access_token"],
            "refresh_token": verified_session["refresh_token"],
            "token_type": "bearer",
            "expires_in": verified_session.get("expires_in", 3600),
            "user_id": user_id_from_token  # Include user_id in response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ MFA login verification error: {e}")
        
        # Provide better error messages based on the error
        if "Invalid verification code" in error_msg or "Invalid" in error_msg or "422" in error_msg or "Unprocessable" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid verification code. Please check your authenticator app and ensure your device time is correct. Try entering a fresh code."
            )
        elif "challenge" in error_msg.lower() or "expired" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Verification code expired. Please try logging in again."
            )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MFA verification failed. Please try again."
        ) 