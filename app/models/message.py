from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class MessageType(str, enum.Enum):
    HEALTH_PLAN_SUPPORT = "health_plan_support"
    MEDICATION_REMINDER = "medication_reminder"
    APPOINTMENT_REMINDER = "appointment_reminder"
    LAB_RESULTS = "lab_results"
    DOCTOR_MESSAGE = "doctor_message"
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    PRESCRIPTION_UPDATE = "prescription_update"
    INSURANCE_UPDATE = "insurance_update"
    GENERAL = "general"

class MessagePriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class MessageStatus(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

class SenderType(str, enum.Enum):
    USER = "user"
    DOCTOR = "doctor"
    ADMIN = "admin"
    SYSTEM = "system"

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender_name = Column(String(255), nullable=False)
    sender_role = Column(String(100), nullable=False)
    sender_type = Column(Enum(SenderType), nullable=False, default=SenderType.USER)
    sender_avatar = Column(String(500), nullable=True)
    
    content = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), nullable=False, default=MessageType.GENERAL)
    priority = Column(Enum(MessagePriority), nullable=False, default=MessagePriority.NORMAL)
    status = Column(Enum(MessageStatus), nullable=False, default=MessageStatus.SENT)
    
    # Metadata for message-specific data
    message_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    documents = relationship("Document", back_populates="message")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contact_name = Column(String(255), nullable=False)
    contact_role = Column(String(100), nullable=False)
    contact_avatar = Column(String(500), nullable=True)
    contact_type = Column(Enum(SenderType), nullable=False, default=SenderType.USER)
    
    # Conversation metadata
    is_archived = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    tags = Column(JSON, nullable=True)  # Array of tag strings
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_message_time = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    contact = relationship("User", foreign_keys=[contact_id])
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class MessageDeliveryLog(Base):
    __tablename__ = "message_delivery_logs"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    delivery_method = Column(String(50), nullable=False)  # websocket, email, sms, push
    status = Column(String(50), nullable=False)  # sent, delivered, failed
    error_message = Column(Text, nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    message = relationship("Message")

class MessageAction(Base):
    __tablename__ = "message_actions"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action_type = Column(String(50), nullable=False)  # taken, snooze, confirm, reschedule, etc.
    action_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    message = relationship("Message")
    user = relationship("User", foreign_keys=[user_id])