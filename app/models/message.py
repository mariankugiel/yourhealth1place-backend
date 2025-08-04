from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class MessageType(str, enum.Enum):
    GENERAL = "general"
    APPOINTMENT = "appointment"
    MEDICATION = "medication"
    TEST_RESULTS = "test_results"
    EMERGENCY = "emergency"
    REMINDER = "reminder"

class MessageStatus(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    ARCHIVED = "archived"

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.GENERAL)
    status = Column(Enum(MessageStatus), default=MessageStatus.SENT)
    
    # Related entities
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=True)
    health_record_id = Column(Integer, ForeignKey("health_records.id"), nullable=True)
    
    # Message metadata
    is_urgent = Column(Boolean, default=False)
    is_encrypted = Column(Boolean, default=True)
    read_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id])
    recipient = relationship("User", foreign_keys=[recipient_id])
    appointment = relationship("Appointment")
    medication = relationship("Medication")
    health_record = relationship("HealthRecord")
    
    def __repr__(self):
        return f"<Message(id={self.id}, subject='{self.subject}', sender_id={self.sender_id})>" 