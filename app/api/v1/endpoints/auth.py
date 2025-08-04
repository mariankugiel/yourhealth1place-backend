from datetime import timedelta
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.supabase_client import supabase_service
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse
from app.crud.user import create_user, get_user_by_supabase_id
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with Supabase"""
    try:
        # Register user with Supabase
        supabase_response = await supabase_service.sign_up(
            email=user_data.email,
            password=user_data.password,
            user_metadata={
                "full_name": user_data.full_name,
                "role": user_data.role or "patient"
            }
        )
        
        if not supabase_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to register user with Supabase"
            )
        
        # Create internal user record for linkage
        internal_user_id = str(uuid.uuid4())
        db_user = User(
            supabase_user_id=supabase_response.user.id,
            internal_user_id=internal_user_id,
            role=user_data.role or "patient"
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Store personal info in Supabase
        await supabase_service.store_personal_info(
            user_id=supabase_response.user.id,
            personal_info={
                "full_name": user_data.full_name,
                "phone": user_data.phone,
                "date_of_birth": user_data.date_of_birth.isoformat() if user_data.date_of_birth else None,
                "address": user_data.address,
                "emergency_contact": user_data.emergency_contact,
                "emergency_phone": user_data.emergency_phone
            }
        )
        
        return UserResponse(
            id=db_user.id,
            email=user_data.email,
            full_name=user_data.full_name,
            role=db_user.role,
            is_active=db_user.is_active
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
        
        # Get internal user record
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
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user 