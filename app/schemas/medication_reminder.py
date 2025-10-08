from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import time, datetime
from app.models.medication_reminder import ReminderStatus

class MedicationReminderBase(BaseModel):
    medication_id: int
    reminder_time: time
    days_of_week: List[str] = Field(..., description="List of days: ['monday', 'tuesday', ...]. Reminder repeats every week on these days.")
    enabled: bool = Field(default=True)

class MedicationReminderCreate(MedicationReminderBase):
    """
    Create medication reminder.
    
    Note: 
    - user_timezone is NOT sent from frontend
    - Backend will use user.timezone from user profile (Supabase)
    - If user.timezone is None, UTC will be used as fallback
    - days_of_week creates a WEEKLY recurring reminder
    """
    pass

class MedicationReminderUpdate(BaseModel):
    reminder_time: Optional[time] = None
    days_of_week: Optional[List[str]] = None
    enabled: Optional[bool] = None
    status: Optional[ReminderStatus] = None

class MedicationReminderResponse(MedicationReminderBase):
    id: int
    user_id: int
    user_timezone: str
    next_scheduled_at: Optional[datetime] = None
    last_sent_at: Optional[datetime] = None
    status: ReminderStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MedicationReminderWithMedication(MedicationReminderResponse):
    medication_name: Optional[str] = None
