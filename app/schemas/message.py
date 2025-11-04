from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.message import MessageType, MessagePriority, MessageStatus, SenderType

# Base schemas
class MessageSenderBase(BaseModel):
    id: str
    name: str
    role: str
    avatar: Optional[str] = None
    type: SenderType

class MessageSender(MessageSenderBase):
    pass

# Message attachment schemas
class MessageAttachmentBase(BaseModel):
    file_name: str
    original_file_name: str
    file_type: str
    file_size: int
    file_extension: str
    s3_bucket: str
    s3_key: str
    s3_url: Optional[str] = None

class MessageAttachmentCreate(MessageAttachmentBase):
    pass

class MessageAttachment(MessageAttachmentBase):
    id: int
    message_id: int
    uploaded_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    content: str
    message_type: MessageType = MessageType.GENERAL
    priority: MessagePriority = MessagePriority.NORMAL
    message_metadata: Optional[Dict[str, Any]] = None

class MessageCreate(MessageBase):
    conversation_id: Optional[int] = None
    recipient_id: Optional[int] = None

class MessageUpdate(BaseModel):
    content: Optional[str] = None
    message_metadata: Optional[Dict[str, Any]] = None

class Message(MessageBase):
    id: int
    conversation_id: int
    sender_id: int  # Simplified: just sender ID, no full sender object
    attachments: Optional[List[MessageAttachment]] = None  # Add attachments
    status: MessageStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Conversation schemas
class ConversationBase(BaseModel):
    tags: Optional[List[str]] = None

class ConversationCreate(ConversationBase):
    contact_id: int
    initial_message: Optional[str] = None

# Frontend request schema for creating conversations
class CreateConversationRequest(BaseModel):
    recipientId: str  # Frontend sends this as recipientId
    initialMessage: Optional[str] = None  # Frontend sends this as initialMessage

class ConversationUpdate(BaseModel):
    is_archived: Optional[bool] = None
    is_pinned: Optional[bool] = None
    tags: Optional[List[str]] = None

class Conversation(ConversationBase):
    id: int
    user_id: int
    contact_id: int
    contact_supabase_user_id: Optional[str] = None  # Supabase UUID for direct bucket access
    contact_name: Optional[str] = None  # Fetched from Supabase
    contact_role: Optional[str] = None  # Fetched from Supabase
    contact_avatar: Optional[str] = None  # Fetched from Supabase
    contact_initials: Optional[str] = None  # Generated initials for fallback avatar
    current_user_name: Optional[str] = None  # Current user's name
    current_user_role: Optional[str] = None  # Current user's role
    current_user_avatar: Optional[str] = None  # Current user's avatar
    current_user_initials: Optional[str] = None  # Current user's initials
    is_archived: bool
    is_pinned: bool
    unread_count: int = 0
    lastMessage: Optional[Message] = None
    lastMessageTime: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Message action schemas
class MessageActionCreate(BaseModel):
    action_type: str
    action_data: Optional[Dict[str, Any]] = None

class MessageAction(BaseModel):
    id: int
    message_id: int
    user_id: int
    action_type: str
    action_data: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

# API request/response schemas
class SendMessageRequest(BaseModel):
    conversation_id: Optional[int] = None
    recipient_id: Optional[int] = None
    content: str
    message_type: MessageType = MessageType.GENERAL
    priority: MessagePriority = MessagePriority.NORMAL
    attachments: Optional[List[MessageAttachmentCreate]] = None  # Add attachments support
    message_metadata: Optional[Dict[str, Any]] = None

class SendMessageResponse(BaseModel):
    message: Message
    conversation: Conversation

class MessagesResponse(BaseModel):
    conversations: List[Conversation]
    total_count: int
    unread_count: int
    has_more: bool

class ConversationMessagesResponse(BaseModel):
    messages: List[Message]
    has_more: bool

class MessageFilters(BaseModel):
    message_types: Optional[List[MessageType]] = None
    priorities: Optional[List[MessagePriority]] = None
    statuses: Optional[List[MessageStatus]] = None
    date_range: Optional[Dict[str, str]] = None
    sender_ids: Optional[List[int]] = None
    has_unread: Optional[bool] = None
    has_action_required: Optional[bool] = None

class MessageSearchParams(BaseModel):
    query: str
    filters: Optional[MessageFilters] = None
    sort_by: str = "timestamp"
    sort_order: str = "desc"

class MessageSearchResponse(BaseModel):
    messages: List[Message]
    total_count: int

class UnreadCountResponse(BaseModel):
    count: int
    by_type: Dict[str, int]

class MessageStatsResponse(BaseModel):
    total_messages: int
    unread_messages: int
    messages_by_type: Dict[str, int]
    messages_by_priority: Dict[str, int]
    recent_activity: List[Dict[str, Any]]

# WebSocket message schemas
class WebSocketMessageEvent(BaseModel):
    type: str  # new_message, message_read, conversation_updated, typing_start, typing_stop
    data: Dict[str, Any]

class WebSocketMessageData(BaseModel):
    conversation_id: int
    message: Optional[Message] = None
    user_id: Optional[int] = None
    timestamp: datetime

# Medication reminder specific schemas
class MedicationReminderMetadata(BaseModel):
    medication_id: int
    medication_name: str
    dosage: str
    scheduled_time: datetime
    action_required: bool = True
    action_url: Optional[str] = None
    action_text: Optional[str] = None

class AppointmentReminderMetadata(BaseModel):
    appointment_id: str
    appointment_date: datetime
    doctor_name: str
    location: str
    action_required: bool = True
    action_url: Optional[str] = None
    action_text: Optional[str] = None

class LabResultsMetadata(BaseModel):
    lab_result_id: str
    test_name: str
    result_date: datetime
    is_abnormal: bool
    action_required: bool
    action_url: Optional[str] = None
    action_text: Optional[str] = None

class HealthPlanSupportMetadata(BaseModel):
    support_ticket_id: Optional[str] = None
    category: str  # billing, coverage, claims, general
    action_required: Optional[bool] = None
    action_url: Optional[str] = None
    action_text: Optional[str] = None

# Response schemas
class MessagesResponse(BaseModel):
    conversations: List[Conversation]
    total_count: int
    unread_count: int
    has_more: bool
    current_user_id: int  # Add actual database user ID for frontend