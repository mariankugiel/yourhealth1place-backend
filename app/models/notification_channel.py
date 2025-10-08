from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class NotificationChannel(Base):
    __tablename__ = "notification_channels"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Channel Preferences
    email_enabled = Column(Boolean, default=True)
    email_address = Column(String(255))  # Can override user's primary email
    
    sms_enabled = Column(Boolean, default=False)
    phone_number = Column(String(20))  # E.164 format: +1234567890
    
    websocket_enabled = Column(Boolean, default=True)
    
    web_push_enabled = Column(Boolean, default=False)
    
    # Notification Type Preferences (JSON)
    # Example: {"medication_reminder": ["email", "websocket"], "admin_instruction": ["email", "websocket", "web_push"]}
    preferences = Column(JSON, default={})
    
    # Quiet Hours (JSON)
    # Example: {"start": "22:00", "end": "08:00", "timezone": "America/New_York"}
    quiet_hours = Column(JSON)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="notification_channel")
    
    def __repr__(self):
        return f"<NotificationChannel(user_id={self.user_id}, email={self.email_enabled}, sms={self.sms_enabled})>"

