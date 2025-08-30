from datetime import timedelta
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.supabase_client import supabase_service
from app.models.user import User
from app.schemas.user import Token, UserResponse, UserProfile, UserRegistration
from app.crud.user import get_user_by_supabase_id
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

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
            "full_name": registration_data.full_name,
            "date_of_birth": registration_data.date_of_birth,
            "phone_number": registration_data.phone_number,
            "address": registration_data.address,
            "emergency_contact_name": registration_data.emergency_contact_name,
            "emergency_contact_phone": registration_data.emergency_contact_phone,
            "gender": registration_data.gender,
            "blood_type": registration_data.blood_type,
            "allergies": registration_data.allergies,
            "current_medications": registration_data.current_medications,
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
            is_superuser=db_user.is_superuser,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at
        )
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login failed"
        )

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(current_user_id: str = Depends(oauth2_scheme)):
    """Get user profile from Supabase"""
    try:
        # Get personal data from Supabase
        profile_data = await supabase_service.get_user_profile(current_user_id)
        
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
    current_user_id: str = Depends(oauth2_scheme)
):
    """Update user profile in Supabase"""
    try:
        # Update personal data in Supabase
        updated_profile = await supabase_service.update_user_profile(
            user_id=current_user_id,
            profile=profile_data.dict(exclude_none=True)
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

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get current authenticated user from Supabase token"""
    try:
        # Verify token with Supabase
        # This would require implementing token verification with Supabase
        # For now, returning a placeholder implementation
        
        # In production, you would:
        # 1. Verify the JWT token with Supabase
        # 2. Extract user ID from token
        # 3. Get user from database
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Token verification to be implemented with Supabase"
        )
        
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        ) 