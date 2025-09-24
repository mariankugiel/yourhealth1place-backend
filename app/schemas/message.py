from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.message import MessageType, MessageStatus

class MessageBase(BaseModel):
    sender_id: int
    receiver_id: int  # Changed from recipient_id to match model
    content: str
    message_type: MessageType = MessageType.TEXT
    category: str = "GENERAL"
    appointment_id: Optional[int] = None
    health_plan_id: Optional[int] = None
    task_id: Optional[int] = None
    goal_id: Optional[int] = None

class MessageCreate(MessageBase):
    pass

class MessageUpdate(BaseModel):
    content: Optional[str] = None
    message_type: Optional[MessageType] = None
    category: Optional[str] = None
    status: Optional[MessageStatus] = None
    appointment_id: Optional[int] = None
    health_plan_id: Optional[int] = None
    task_id: Optional[int] = None
    goal_id: Optional[int] = None
    read_at: Optional[datetime] = None

class MessageResponse(MessageBase):
    id: int
    status: MessageStatus
    read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    has_attachments: bool = False
    attachment_count: int = 0

    class Config:
        from_attributes = True 