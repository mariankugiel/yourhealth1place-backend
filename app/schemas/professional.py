from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    PATIENT = "patient"
    PROFESSIONAL = "professional"

class ProfessionalBase(BaseModel):
    first_name: str
    last_name: str
    title: Optional[str] = None
    specialty: Optional[str] = None
    license_number: Optional[str] = None
    medical_board: Optional[str] = None
    phone: Optional[str] = None
    office_address: Optional[str] = None
    office_hours: Optional[Dict[str, Any]] = None
    education: Optional[List[Dict[str, Any]]] = None
    certifications: Optional[List[str]] = None
    experience_years: Optional[int] = None
    languages: Optional[List[str]] = None
    consultation_types: Optional[List[str]] = None
    consultation_duration: Optional[int] = 30
    consultation_fee: Optional[int] = None
    is_available: bool = True
    availability_schedule: Optional[Dict[str, Any]] = None
    is_verified: bool = False
    is_active: bool = True

class ProfessionalCreate(ProfessionalBase):
    email: EmailStr
    user_id: int

class ProfessionalUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    specialty: Optional[str] = None
    license_number: Optional[str] = None
    medical_board: Optional[str] = None
    phone: Optional[str] = None
    office_address: Optional[str] = None
    office_hours: Optional[Dict[str, Any]] = None
    education: Optional[List[Dict[str, Any]]] = None
    certifications: Optional[List[str]] = None
    experience_years: Optional[int] = None
    languages: Optional[List[str]] = None
    consultation_types: Optional[List[str]] = None
    consultation_duration: Optional[int] = None
    consultation_fee: Optional[int] = None
    is_available: Optional[bool] = None
    availability_schedule: Optional[Dict[str, Any]] = None
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None

class Professional(ProfessionalBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProfessionalWithUser(Professional):
    user: Optional[Dict[str, Any]] = None

class ProfessionalList(BaseModel):
    professionals: List[Professional]
    total: int
    page: int
    size: int 