from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.models.message import Message, Conversation, MessageDeliveryLog, MessageAction, MessageType, MessagePriority, MessageStatus, SenderType
from app.schemas.message import (
    MessageCreate, MessageUpdate, ConversationCreate, ConversationUpdate,
    MessageFilters, MessageSearchParams
)
from app.models.user import User

class MessageCRUD:
    def __init__(self):
        pass

    # Message CRUD operations
    def create_message(self, db: Session, message_data: MessageCreate, sender_id: int) -> Message:
        """Create a new message"""
        # Get sender information
        sender = db.query(User).filter(User.id == sender_id).first()
        if not sender:
            raise ValueError("Sender not found")

        # Create message
        message = Message(
            conversation_id=message_data.conversation_id,
            sender_id=sender_id,
            sender_name=sender.full_name or sender.email,
            sender_role=sender.role,
            sender_type=SenderType.USER,
            sender_avatar=sender.avatar_url,
            content=message_data.content,
            message_type=message_data.message_type,
            priority=message_data.priority,
            message_metadata=message_data.message_metadata
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        # Update conversation last message time
        if message_data.conversation_id:
            self._update_conversation_last_message(db, message_data.conversation_id)
        
        return message
    
    def get_message(self, db: Session, message_id: int) -> Optional[Message]:
        """Get a message by ID"""
        return db.query(Message).filter(Message.id == message_id).first()

    def get_messages_by_conversation(self, db: Session, conversation_id: int, page: int = 1, limit: int = 50) -> List[Message]:
        """Get messages for a conversation with pagination"""
        offset = (page - 1) * limit
        return (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(desc(Message.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def update_message(self, message_id: int, message_data: MessageUpdate) -> Optional[Message]:
        """Update a message"""
        message = self.get_message(message_id)
        if not message:
            return None
        
        update_data = message_data.dict(exclude_unset=True)
        for field, value in update_data.items():
                setattr(message, field, value)
        
        db.commit()
        db.refresh(message)
        return message
    
    def delete_message(self, db: Session, message_id: int) -> bool:
        """Delete a message"""
        message = self.get_message(db, message_id)
        if not message:
            return False
        
        db.delete(message)
        db.commit()
        return True

    def mark_message_as_read(self, db: Session, message_id: int) -> bool:
        """Mark a message as read"""
        message = self.get_message(db, message_id)
        if not message:
            return False
        
        message.status = MessageStatus.READ
        message.read_at = datetime.utcnow()
        db.commit()
        return True

    def mark_messages_as_read(self, db: Session, conversation_id: int, message_ids: Optional[List[int]] = None) -> int:
        """Mark messages as read in a conversation"""
        query = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.status != MessageStatus.READ
        )
        
        if message_ids:
            query = query.filter(Message.id.in_(message_ids))
        
        messages = query.all()
        count = 0
        for message in messages:
            message.status = MessageStatus.READ
            message.read_at = datetime.utcnow()
            count += 1
        
        db.commit()
        return count

    # Conversation CRUD operations
    def create_conversation(self, db: Session, conversation_data: ConversationCreate, user_id: int) -> Conversation:
        """Create a new conversation"""
        # Get contact information
        contact = db.query(User).filter(User.id == conversation_data.contact_id).first()
        if not contact:
            raise ValueError("Contact not found")

        conversation = Conversation(
            user_id=user_id,
            contact_id=conversation_data.contact_id,
            contact_name=contact.email,  # Use email since full_name may not exist
            contact_role="User",  # Default role
            contact_avatar=None,
            contact_type=SenderType.USER,
            tags=conversation_data.tags
        )
        
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    def get_conversation(self, db: Session, conversation_id: int) -> Optional[Conversation]:
        """Get a conversation by ID"""
        return (
            db.query(Conversation)
            .options(joinedload(Conversation.messages))
            .filter(Conversation.id == conversation_id)
            .first()
        )

    def get_conversations_by_user(self, db: Session, user_id: int, filters: Optional[MessageFilters] = None) -> List[Conversation]:
        """Get conversations for a user with optional filtering"""
        query = db.query(Conversation).filter(Conversation.user_id == user_id)
        
        if filters:
            if filters.has_unread:
                # This would need a subquery to count unread messages
                pass
            if filters.has_action_required:
                # This would need to check message metadata
                pass
        
        return query.order_by(desc(Conversation.last_message_time)).all()

    def update_conversation(self, db: Session, conversation_id: int, conversation_data: ConversationUpdate) -> Optional[Conversation]:
        """Update a conversation"""
        conversation = self.get_conversation(db, conversation_id)
        if not conversation:
            return None
        
        update_data = conversation_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(conversation, field, value)
        
        db.commit()
        db.refresh(conversation)
        return conversation

    def archive_conversation(self, db: Session, conversation_id: int) -> bool:
        """Archive a conversation"""
        conversation = self.get_conversation(db, conversation_id)
        if not conversation:
            return False
        
        conversation.is_archived = True
        db.commit()
        return True

    def toggle_conversation_pin(self, db: Session, conversation_id: int, pinned: bool) -> bool:
        """Toggle conversation pin status"""
        conversation = self.get_conversation(db, conversation_id)
        if not conversation:
            return False
        
        conversation.is_pinned = pinned
        db.commit()
        return True

    def get_unread_count(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get unread message count for a user"""
        # Count unread messages by type
        unread_by_type = (
            db.query(Message.message_type, func.count(Message.id))
            .join(Conversation)
            .filter(
                Conversation.user_id == user_id,
                Message.status != MessageStatus.READ
            )
            .group_by(Message.message_type)
            .all()
        )
        
        total_unread = sum(count for _, count in unread_by_type)
        by_type = {msg_type.value: count for msg_type, count in unread_by_type}
        
        return {
            "count": total_unread,
            "by_type": by_type
        }

    def search_messages(self, db: Session, user_id: int, search_params: MessageSearchParams) -> List[Message]:
        """Search messages for a user"""
        query = (
            db.query(Message)
            .join(Conversation)
            .filter(Conversation.user_id == user_id)
        )
        
        # Text search
        if search_params.query:
            query = query.filter(Message.content.ilike(f"%{search_params.query}%"))
        
        # Apply filters
        if search_params.filters:
            filters = search_params.filters
            if filters.message_types:
                query = query.filter(Message.message_type.in_(filters.message_types))
            if filters.priorities:
                query = query.filter(Message.priority.in_(filters.priorities))
            if filters.statuses:
                query = query.filter(Message.status.in_(filters.statuses))
            if filters.date_range:
                start_date = datetime.fromisoformat(filters.date_range["start"])
                end_date = datetime.fromisoformat(filters.date_range["end"])
                query = query.filter(
                    and_(
                        Message.created_at >= start_date,
                        Message.created_at <= end_date
                    )
                )
        
        # Apply sorting
        if search_params.sort_by == "timestamp":
            order_func = desc if search_params.sort_order == "desc" else asc
            query = query.order_by(order_func(Message.created_at))
        elif search_params.sort_by == "priority":
            order_func = desc if search_params.sort_order == "desc" else asc
            query = query.order_by(order_func(Message.priority))
        
        return query.all()

    def get_message_stats(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get message statistics for a user"""
        # Total messages
        total_messages = (
            db.query(func.count(Message.id))
            .join(Conversation)
            .filter(Conversation.user_id == user_id)
            .scalar()
        )
        
        # Unread messages
        unread_messages = (
            db.query(func.count(Message.id))
            .join(Conversation)
            .filter(
                Conversation.user_id == user_id,
                Message.status != MessageStatus.READ
            )
            .scalar()
        )
        
        # Messages by type
        messages_by_type = (
            db.query(Message.message_type, func.count(Message.id))
            .join(Conversation)
            .filter(Conversation.user_id == user_id)
            .group_by(Message.message_type)
            .all()
        )
        
        # Messages by priority
        messages_by_priority = (
            db.query(Message.priority, func.count(Message.id))
            .join(Conversation)
            .filter(Conversation.user_id == user_id)
            .group_by(Message.priority)
            .all()
        )
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_activity = (
            db.query(
                func.date(Message.created_at).label('date'),
                func.count(Message.id).label('count')
            )
            .join(Conversation)
            .filter(
                Conversation.user_id == user_id,
                Message.created_at >= thirty_days_ago
            )
            .group_by(func.date(Message.created_at))
            .order_by(func.date(Message.created_at))
            .all()
        )
        
        return {
            "total_messages": total_messages,
            "unread_messages": unread_messages,
            "messages_by_type": {msg_type.value: count for msg_type, count in messages_by_type},
            "messages_by_priority": {priority.value: count for priority, count in messages_by_priority},
            "recent_activity": [{"date": str(date), "count": count} for date, count in recent_activity]
        }

    def create_message_action(self, message_id: int, user_id: int, action_type: str, action_data: Optional[Dict[str, Any]] = None) -> MessageAction:
        """Create a message action (e.g., mark medication as taken)"""
        action = MessageAction(
            message_id=message_id,
            user_id=user_id,
            action_type=action_type,
            action_data=action_data
        )
        
        db.add(action)
        db.commit()
        db.refresh(action)
        return action

    def _update_conversation_last_message(self, db: Session, conversation_id: int):
        """Update conversation's last message time"""
        conversation = self.get_conversation(db, conversation_id)
        if conversation:
            conversation.last_message_time = datetime.utcnow()
            db.commit()

    def get_available_contacts(self, db: Session, user_id: int) -> List[User]:
        """Get available contacts for new messages"""
        # This would typically return doctors, admins, and other users the patient can message
        return (
            db.query(User)
            .filter(
                User.id != user_id,
                User.is_active == True,
                User.is_superuser == False
            )
            .all()
        )

# Create instance for dependency injection
message_crud = MessageCRUD()
