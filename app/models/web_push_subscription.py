from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class WebPushSubscription(Base):
    __tablename__ = "web_push_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # VAPID Subscription Details
    endpoint = Column(Text, nullable=False, unique=True)
    p256dh_key = Column(Text, nullable=False)  # Public key for encryption
    auth_key = Column(Text, nullable=False)  # Authentication secret
    
    # Browser/Device Info
    user_agent = Column(String(500))
    browser = Column(String(100))  # Chrome, Firefox, Safari, etc.
    device_type = Column(String(50))  # desktop, mobile, tablet
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    subscribed_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True))
    unsubscribed_at = Column(DateTime(timezone=True))
    
    # Error tracking
    failed_attempts = Column(Integer, default=0)
    last_error = Column(Text)
    last_error_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", backref="web_push_subscriptions")
    
    def __repr__(self):
        return f"<WebPushSubscription(id={self.id}, user_id={self.user_id}, active={self.is_active})>"

