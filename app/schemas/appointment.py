from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.appointment import AppointmentStatus, AppointmentType as AppointmentTypeEnum

class AppointmentBase(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_date: datetime
    duration_minutes: int = 30
    appointment_type: AppointmentTypeEnum
    reason: Optional[str] = None
    symptoms: Optional[str] = None
    is_urgent: bool = False

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    appointment_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    appointment_type: Optional[AppointmentTypeEnum] = None
    status: Optional[AppointmentStatus] = None
    reason: Optional[str] = None
    symptoms: Optional[str] = None
    notes: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    prescription: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    is_urgent: Optional[bool] = None

class AppointmentResponse(AppointmentBase):
    id: int
    status: AppointmentStatus
    notes: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    prescription: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 


# New schemas for Acuity integration
class AcuityEmbedResponse(BaseModel):
    """Response model for Acuity embed URL"""
    embed_url: str
    iframe_src: str
    owner_id: str
    calendar_id: Optional[str] = None


class VideoRoomResponse(BaseModel):
    """Response model for Daily.co video room"""
    room_url: str
    room_name: str
    patient_token: str
    professional_token: Optional[str] = None


class AcuityWebhookPayload(BaseModel):
    """Acuity webhook payload structure"""
    id: str
    calendarID: str
    appointmentTypeID: Optional[int] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    datetime: Optional[str] = None
    timezone: Optional[str] = None
    notes: Optional[str] = None
    canceled: Optional[bool] = False
    calendarTimezone: Optional[str] = None
    canClientCancel: Optional[bool] = True
    canClientReschedule: Optional[bool] = True


class AppointmentBookRequest(BaseModel):
    """Request model for booking appointment via Acuity API"""
    calendar_id: str
    appointment_type_id: int = 0
    datetime: str  # ISO format with timezone
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    appointment_type: str  # "virtual", "in-person", or "phone"
    location: Optional[str] = None  # Required for in-person
    note: Optional[str] = None
    timezone: Optional[str] = None 


class AppointmentRescheduleRequest(BaseModel):
    """Request model for rescheduling an appointment via Acuity API"""
    appointment_date: datetime
    calendar_id: Optional[str] = None
    timezone: Optional[str] = None
    note: Optional[str] = None
    appointment_type: Optional[str] = None