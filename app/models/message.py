from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class MessageType(str, enum.Enum):
    GENERAL = "GENERAL"
    TEXT = "TEXT"
    # File types are now handled by Document system
    # IMAGE, FILE, AUDIO, VIDEO removed - use Document.category instead

class MessageStatus(str, enum.Enum):
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    READ = "READ"
    FAILED = "FAILED"

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Message Participants
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # User ID of sender (can be system user for notifications)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # User ID of receiver
    
    # Message Details
    message_type = Column(String(20), nullable=False, default="TEXT")  # "TEXT", "IMAGE", "FILE", "AUDIO", "VIDEO"
    content = Column(Text, nullable=False)  # Message content or file description
    
    # Message Category
    category = Column(String(50), nullable=False, default="GENERAL")  # "GENERAL", "APPOINTMENT", "MEDICATION_REMINDER", "HEALTH_PLAN", "SYSTEM_NOTIFICATION", "EMERGENCY"
    
    # Message Status
    status = Column(String(20), nullable=False, default="SENT")  # "SENT", "DELIVERED", "READ", "FAILED"
    read_at = Column(DateTime)  # When message was read
    
    # Related Context
    appointment_id = Column(Integer, ForeignKey("appointments.id"))  # Link to appointment if message is appointment-related
    health_plan_id = Column(Integer, ForeignKey("health_plans.id"))  # Link to health plan if message is plan-related
    task_id = Column(Integer, ForeignKey("tasks.id"))  # Link to task if message is task-related
    goal_id = Column(Integer, ForeignKey("goals.id"))  # Link to goal if message is goal-related
    
    # External Integration
    external_message_id = Column(String(255))  # ID from external messaging service if applicable
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], backref="received_messages")
    appointment = relationship("Appointment", backref="messages")
    health_plan = relationship("HealthPlan", back_populates="messages")
    task = relationship("Task", back_populates="messages")
    goal = relationship("Goal", back_populates="messages")
    documents = relationship("Document", back_populates="message")
    
    # Helper methods for document management
    def has_attachments(self) -> bool:
        """Check if message has any document attachments"""
        return len(self.documents) > 0
    
    def get_attachments(self):
        """Get all document attachments for this message"""
        return [doc for doc in self.documents if doc.is_message_attachment]
    
    def get_attachment_count(self) -> int:
        """Get count of document attachments"""
        return len(self.get_attachments())

 