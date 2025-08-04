from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.message import MessageType, MessageStatus

class MessageBase(BaseModel):
    sender_id: int
    recipient_id: int
    subject: str
    content: str
    message_type: MessageType = MessageType.GENERAL
    appointment_id: Optional[int] = None
    medication_id: Optional[int] = None
    health_record_id: Optional[int] = None
    is_urgent: bool = False

class MessageCreate(MessageBase):
    pass

class MessageUpdate(BaseModel):
    subject: Optional[str] = None
    content: Optional[str] = None
    message_type: Optional[MessageType] = None
    status: Optional[MessageStatus] = None
    appointment_id: Optional[int] = None
    medication_id: Optional[int] = None
    health_record_id: Optional[int] = None
    is_urgent: Optional[bool] = None
    read_at: Optional[datetime] = None

class MessageResponse(MessageBase):
    id: int
    status: MessageStatus
    is_encrypted: bool
    read_at: Optional[datetime] = None
    sent_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 