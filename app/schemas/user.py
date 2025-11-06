from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
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

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class MFAEnrollRequest(BaseModel):
    friendly_name: Optional[str] = "My Authenticator App"

class MFAEnrollResponse(BaseModel):
    id: str
    totp: Dict[str, Any]
    class Config:
        from_attributes = True

class MFAVerifyRequest(BaseModel):
    factor_id: str
    code: str

class MFAFactor(BaseModel):
    id: str
    type: str
    friendly_name: str
    status: str
    created_at: str
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class LoginResponse(BaseModel):
    """Response for login - can be either a token or MFA requirement"""
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = "bearer"
    expires_in: Optional[int] = None
    mfa_required: bool = False
    factor_id: Optional[str] = None
    user_id: Optional[str] = None

class MFALoginVerifyRequest(BaseModel):
    """Request to verify MFA during login"""
    factor_id: str
    code: str

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
    img_url: Optional[str] = None  # User profile picture URL (prioritized over avatar_url)
    avatar_url: Optional[str] = None  # User profile picture URL (fallback)
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
    theme: Optional[str] = None  # User theme preference: light or dark
    language: Optional[str] = None  # User language preference: en, es, pt
    timezone: Optional[str] = None  # User timezone preference
    
    # Onboarding-related fields
    onboarding_completed: Optional[bool] = None
    onboarding_skipped: Optional[bool] = None
    onboarding_skipped_at: Optional[str] = None  # ISO format string
    onboarding_completed_at: Optional[str] = None  # ISO format string
    is_new_user: Optional[bool] = None

# Schema for emergency data (stored in Supabase user_emergency table)
class UserEmergency(BaseModel):
    contacts: Optional[list[Dict[str, Any]]] = None  # JSON array of emergency contacts
    allergies: Optional[str] = None
    medications: Optional[str] = None  # Current medications and dosages
    health_problems: Optional[str] = None
    pregnancy_status: Optional[str] = None
    organ_donor: Optional[bool] = None
    
    class Config:
        from_attributes = True

# Schema for notification preferences (stored in Supabase user_notifications table)
class UserNotifications(BaseModel):
    appointment_hours_before: Optional[str] = None  # "1", "2", "4", "12", "24", "48"
    medication_minutes_before: Optional[str] = None  # "0", "5", "10", "15", "30", "60"
    tasks_reminder_time: Optional[str] = None  # "HH:MM" format
    email_appointments: Optional[bool] = None
    sms_appointments: Optional[bool] = None
    whatsapp_appointments: Optional[bool] = None
    push_appointments: Optional[bool] = None
    email_medications: Optional[bool] = None
    sms_medications: Optional[bool] = None
    whatsapp_medications: Optional[bool] = None
    push_medications: Optional[bool] = None
    email_tasks: Optional[bool] = None
    sms_tasks: Optional[bool] = None
    whatsapp_tasks: Optional[bool] = None
    push_tasks: Optional[bool] = None
    email_newsletter: Optional[bool] = None
    
    class Config:
        from_attributes = True

# Schema for wearable integrations (stored in Supabase user_integrations table)
class UserIntegrations(BaseModel):
    google_fit: Optional[bool] = None
    fitbit: Optional[bool] = None
    garmin: Optional[bool] = None
    apple_health: Optional[bool] = None
    withings: Optional[bool] = None
    oura: Optional[bool] = None
    
    class Config:
        from_attributes = True

# Schema for privacy preferences (stored in Supabase user_privacy table)
class UserPrivacy(BaseModel):
    share_anonymized_data: Optional[bool] = None
    share_analytics: Optional[bool] = None
    
    class Config:
        from_attributes = True

# Schema for shared access (stored in Supabase user_shared_access table)
class UserSharedAccess(BaseModel):
    health_professionals: Optional[list[Dict[str, Any]]] = None
    family_friends: Optional[list[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True

# Schema for access logs (stored in Supabase user_access_logs table)
class UserAccessLogs(BaseModel):
    logs: Optional[list[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True

# Schema for data sharing preferences (stored in Supabase user_data_sharing table)
class UserDataSharing(BaseModel):
    share_health_data: Optional[bool] = None
    share_with_other_providers: Optional[bool] = None
    share_with_researchers: Optional[bool] = None
    share_with_insurance: Optional[bool] = None
    
    class Config:
        from_attributes = True

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