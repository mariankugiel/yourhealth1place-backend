from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import UserRole

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: Optional[UserRole] = UserRole.PATIENT
    # Personal data will be stored in Supabase, not in this schema

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
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
    email: Optional[str] = None
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None  # ISO format string
    phone_country_code: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    avatar_url: Optional[str] = None  # User profile picture URL
    role: Optional[str] = None  # User role: patient, doctor, admin
    emergency_contact_name: Optional[str] = None
    emergency_contact_country_code: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    waist_diameter: Optional[float] = None
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
    role: Optional[UserRole] = UserRole.PATIENT
    
    # Personal profile data
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None  # ISO format string
    phone_number: Optional[str] = None
    phone_country_code: Optional[str] = None  # Country code for phone number
    address: Optional[str] = None
    avatar_url: Optional[str] = None  # User profile picture URL
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    waist_diameter: Optional[float] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    current_medications: Optional[dict] = None
    emergency_medical_info: Optional[str] = None 