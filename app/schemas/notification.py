from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.notification import NotificationType, NotificationStatus

class NotificationBase(BaseModel):
    notification_type: NotificationType
    title: str
    message: str
    medication_id: Optional[int] = None
    appointment_id: Optional[int] = None
    data: Optional[Dict[str, Any]] = None

class NotificationCreate(NotificationBase):
    user_id: int

class NotificationUpdate(BaseModel):
    status: Optional[NotificationStatus] = None
    read_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    status: NotificationStatus
    read_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    display_until: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NotificationWithMedication(NotificationResponse):
    medication_name: Optional[str] = None
    medication_dosage: Optional[str] = None
