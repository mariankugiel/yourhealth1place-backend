from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class WebSocketConnection(Base):
    __tablename__ = "websocket_connections"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    connection_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Connection metadata
    user_agent = Column(String(500))
    ip_address = Column(String(50))
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    connected_at = Column(DateTime(timezone=True), server_default=func.now())
    last_ping_at = Column(DateTime(timezone=True))
    disconnected_at = Column(DateTime(timezone=True))
    
    # TTL for cleanup (in seconds, for DynamoDB-style expiration)
    ttl = Column(Integer)  # Unix timestamp for expiration
    
    # Relationships
    user = relationship("User", backref="websocket_connections")
    
    def __repr__(self):
        return f"<WebSocketConnection(connection_id={self.connection_id}, user_id={self.user_id}, active={self.is_active})>"

