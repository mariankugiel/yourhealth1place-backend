from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class NotificationType(str, enum.Enum):
    MEDICATION_REMINDER = "medication_reminder"
    APPOINTMENT_REMINDER = "appointment_reminder"
    HEALTH_ALERT = "health_alert"
    SYSTEM_MESSAGE = "system_message"
    ADMIN_INSTRUCTION = "admin_instruction"

class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    DISMISSED = "dismissed"

class NotificationPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Notification Content
    notification_type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Priority
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL)
    
    # Related Entity
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    
    # Metadata
    data = Column(JSON)  # Additional data: {dosage, medication_name, etc}
    
    # Status
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING, index=True)
    
    # Timestamps
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)  # When to send (UTC)
    sent_at = Column(DateTime(timezone=True))  # When sent to queue
    delivered_at = Column(DateTime(timezone=True))  # When delivered to user
    read_at = Column(DateTime(timezone=True))  # When user read it
    failed_at = Column(DateTime(timezone=True))  # When delivery failed
    
    # Error tracking
    error_message = Column(Text)  # Error details if failed
    retry_count = Column(Integer, default=0)  # Number of retry attempts
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="notifications")
    medication = relationship("Medication", backref="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.notification_type}, user_id={self.user_id}, status={self.status})>"

