from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.message import Message

class MessageCRUD:
    """CRUD operations for messages"""
    
    def get_by_user(self, db: Session, user_id: int, limit: int = 50) -> List[Message]:
        """Get messages for a specific user"""
        return db.query(Message).filter(
            Message.user_id == user_id
        ).limit(limit).all()
    
    def get_by_id(self, db: Session, message_id: int) -> Optional[Message]:
        """Get message by ID"""
        return db.query(Message).filter(Message.id == message_id).first()
    
    def create(self, db: Session, message_data: dict) -> Message:
        """Create a new message"""
        message = Message(**message_data)
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    
    def update(self, db: Session, message_id: int, message_data: dict) -> Optional[Message]:
        """Update a message"""
        message = self.get_by_id(db, message_id)
        if not message:
            return None
        
        for field, value in message_data.items():
            if hasattr(message, field):
                setattr(message, field, value)
        
        db.commit()
        db.refresh(message)
        return message
    
    def delete(self, db: Session, message_id: int) -> bool:
        """Delete a message"""
        message = self.get_by_id(db, message_id)
        if not message:
            return False
        
        db.delete(message)
        db.commit()
        return True

# Create instance
message_crud = MessageCRUD()
