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
from app.models.user import User
from app.schemas.user import Token, UserResponse, UserProfile, UserRegistration
from app.crud.user import get_user_by_supabase_id
import logging
from typing import Optional

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
    
    # Extract user ID from the JWT token
    user_id = extract_user_id_from_token(token)
    return user_id

@router.post("/register", response_model=UserResponse)
async def register(registration_data: UserRegistration, db: Session = Depends(get_db)):
    """Register a new user with Supabase"""
    try:
        # Register user with Supabase
        supabase_response = await supabase_service.sign_up(
            email=registration_data.email,
            password=registration_data.password,
            user_metadata={
                "full_name": registration_data.full_name,
                "role": "patient"  # Default role for new users
            }
        )
        
        if not supabase_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to register user with Supabase"
            )
        
        # Extract profile data for Supabase storage
        profile_data = {
            "email": registration_data.email,  # Store email in profile for easy access
            "full_name": registration_data.full_name,
            "date_of_birth": registration_data.date_of_birth,
            "phone_number": registration_data.phone_number,
            "phone_country_code": registration_data.phone_country_code,
            "address": registration_data.address,
            "avatar_url": registration_data.avatar_url,
            "role": registration_data.role.value.lower() if registration_data.role else "patient",
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
        
        # Store personal data in Supabase (secure)
        await supabase_service.store_user_profile(
            user_id=supabase_response.user.id,
            profile={k: v for k, v in profile_data.items() if v is not None}
        )
        
        # Create minimal internal user record for application linkage
        db_user = User(
            supabase_user_id=supabase_response.user.id,  # Link to Supabase
            email=registration_data.email,  # For lookups only
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

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login user with Supabase and return access token"""
    try:
        # Authenticate with Supabase
        supabase_response = await supabase_service.sign_in(
            email=form_data.username,
            password=form_data.password
        )
        
        if not supabase_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
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
        
        # Return Supabase session tokens
        return {
            "access_token": supabase_response.session.access_token,
            "refresh_token": supabase_response.session.refresh_token,
            "token_type": "bearer",
            "expires_in": supabase_response.session.expires_in
        }
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        
        # Check for specific error types and return appropriate messages
        error_message = str(e).lower()
        
        if "invalid credentials" in error_message or "incorrect password" in error_message:
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
    try:
        # Extract token from authorization header
        user_token = authorization.replace("Bearer ", "") if authorization else None
        
        # Get personal data from Supabase
        profile_data = await supabase_service.get_user_profile(current_user_id, user_token)
        
        # Handle case where profile data is None or empty
        if not profile_data:
            # Return empty profile if no data exists
            return UserProfile()
        
        return UserProfile(**profile_data)
    except Exception as e:
        logger.error(f"Get profile error: {e}")
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
    try:
        # Extract token from authorization header
        user_token = authorization.replace("Bearer ", "") if authorization else None
        
        # Update personal data in Supabase
        updated_profile = await supabase_service.update_user_profile(
            user_id=current_user_id,
            profile=profile_data.dict(exclude_none=True),
            user_token=user_token
        )
        
        # Handle case where updated profile is None
        if not updated_profile:
            # Return the original profile data if update failed
            return profile_data
        
        return UserProfile(**updated_profile)
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
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
        db_user = get_user_by_supabase_id(db, supabase_user_id=user_info['id'])
        return db_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        ) 