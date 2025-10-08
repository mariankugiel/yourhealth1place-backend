from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class DeliveryChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    WEBSOCKET = "websocket"
    WEB_PUSH = "web_push"

class DeliveryStatus(str, enum.Enum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    REJECTED = "rejected"

class NotificationDeliveryLog(Base):
    __tablename__ = "notification_delivery_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Delivery Details
    channel = Column(SQLEnum(DeliveryChannel), nullable=False, index=True)
    status = Column(SQLEnum(DeliveryStatus), nullable=False, index=True)
    
    # Target Info
    target_address = Column(String(255))  # email, phone, connection_id, subscription_id
    
    # SQS Message Info
    sqs_message_id = Column(String(255))
    sqs_receipt_handle = Column(Text)
    
    # Provider Response
    provider_message_id = Column(String(255))  # SES MessageId, SNS MessageId, etc.
    provider_response = Column(Text)  # Full response from provider
    
    # Error Info
    error_message = Column(Text)
    error_code = Column(String(100))
    
    # Retry Info
    attempt_number = Column(Integer, default=1)
    max_attempts = Column(Integer, default=3)
    
    # Timestamps
    queued_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    failed_at = Column(DateTime(timezone=True))
    
    # Relationships
    notification = relationship("Notification", backref="delivery_logs")
    user = relationship("User", backref="notification_delivery_logs")
    
    def __repr__(self):
        return f"<NotificationDeliveryLog(id={self.id}, notification_id={self.notification_id}, channel={self.channel}, status={self.status})>"

