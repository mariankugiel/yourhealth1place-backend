from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    # Personal data will be stored in Supabase, not in this schema

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None

# Schema for personal data (stored in Supabase)
class UserProfile(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None  # ISO format string
    phone_number: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    gender: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    current_medications: Optional[dict] = None
    emergency_medical_info: Optional[str] = None
    
    # Onboarding-related fields
    onboarding_completed: Optional[bool] = None
    onboarding_skipped: Optional[bool] = None
    onboarding_skipped_at: Optional[str] = None  # ISO format string
    onboarding_completed_at: Optional[str] = None  # ISO format string
    is_new_user: Optional[bool] = None

# Combined schema for registration
class UserRegistration(BaseModel):
    # User authentication data
    email: EmailStr
    password: str
    
    # Personal profile data
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None  # ISO format string
    phone_number: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    gender: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    current_medications: Optional[dict] = None
    emergency_medical_info: Optional[str] = None 