from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.crud.message import MessageCRUD
from app.schemas.message import (
    Message, MessageCreate, MessageUpdate, Conversation, ConversationCreate, ConversationUpdate,
    SendMessageRequest, SendMessageResponse, MessagesResponse, ConversationMessagesResponse,
    MessageFilters, MessageSearchParams, MessageSearchResponse, UnreadCountResponse,
    MessageStatsResponse, MessageActionCreate, MessageAction
)
from app.models.message import MessageType, MessagePriority, MessageStatus
from app.models.user import User

router = APIRouter()

@router.get("/conversations", response_model=MessagesResponse)
async def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    message_types: Optional[str] = Query(None, description="Comma-separated message types"),
    priorities: Optional[str] = Query(None, description="Comma-separated priorities"),
    statuses: Optional[str] = Query(None, description="Comma-separated statuses"),
    has_unread: Optional[bool] = Query(None, description="Filter by unread status"),
    has_action_required: Optional[bool] = Query(None, description="Filter by action required status")
):
    """Get conversations for the current user"""
    # Build filters from query parameters
    filters = MessageFilters()
    if message_types:
        filters.message_types = [MessageType(t) for t in message_types.split(',')]
    if priorities:
        filters.priorities = [MessagePriority(p) for p in priorities.split(',')]
    if statuses:
        filters.statuses = [MessageStatus(s) for s in statuses.split(',')]
    if has_unread is not None:
        filters.has_unread = has_unread
    if has_action_required is not None:
        filters.has_action_required = has_action_required
    
    message_crud = MessageCRUD()
    conversations = message_crud.get_conversations_by_user(db, current_user.id, filters)
    
    # Calculate unread count
    unread_count = message_crud.get_unread_count(db, current_user.id)
    
    return MessagesResponse(
        conversations=conversations,
        total_count=len(conversations),
        unread_count=unread_count["count"],
        has_more=False  # Implement pagination if needed
    )

@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific conversation"""
    message_crud = MessageCRUD()
    conversation = message_crud.get_conversation(db, conversation_id)
    
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation

@router.get("/conversations/{conversation_id}/messages", response_model=ConversationMessagesResponse)
async def get_conversation_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get messages for a conversation"""
    message_crud = MessageCRUD()
    
    # Verify conversation belongs to user
    conversation = message_crud.get_conversation(db, conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = message_crud.get_messages_by_conversation(db, conversation_id, page, limit)
    
    return ConversationMessagesResponse(
        messages=messages,
        has_more=len(messages) == limit
    )

@router.post("/send", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a new message"""
    message_crud = MessageCRUD()
    
    # Create message data
    message_data = MessageCreate(
        conversation_id=request.conversation_id,
        content=request.content,
        message_type=request.message_type,
        priority=request.priority,
        message_metadata=request.message_metadata
    )
    
    # Create or get conversation
    if request.conversation_id:
        conversation = message_crud.get_conversation(db, request.conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        if not request.recipient_id:
            raise HTTPException(status_code=400, detail="Recipient ID required for new conversation")
        
        # Create new conversation
        conversation_data = ConversationCreate(
            contact_id=request.recipient_id,
            contact_name="",  # Will be filled from contact
            contact_role="",
            contact_avatar="",
            contact_type="user"
        )
        conversation = message_crud.create_conversation(db, conversation_data, current_user.id)
        message_data.conversation_id = conversation.id
    
    # Create message
    message = message_crud.create_message(db, message_data, current_user.id)
    
    return SendMessageResponse(
        message=message,
        conversation=conversation
    )

@router.post("/conversations/{conversation_id}/mark-read")
async def mark_conversation_as_read(
    conversation_id: int,
    message_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark messages in a conversation as read"""
    message_crud = MessageCRUD()
    
    # Verify conversation belongs to user
    conversation = message_crud.get_conversation(db, conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    count = message_crud.mark_messages_as_read(db, conversation_id, message_ids)
    
    return {"marked_count": count}

@router.post("/messages/{message_id}/mark-read")
async def mark_message_as_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a specific message as read"""
    message_crud = MessageCRUD()
    
    # Verify message belongs to user
    message = message_crud.get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    conversation = message_crud.get_conversation(db, message.conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Message not found")
    
    success = message_crud.mark_message_as_read(db, message_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to mark message as read")
    
    return {"success": True}

@router.post("/conversations/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive a conversation"""
    message_crud = MessageCRUD()
    
    # Verify conversation belongs to user
    conversation = message_crud.get_conversation(db, conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    success = message_crud.archive_conversation(db, conversation_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to archive conversation")
    
    return {"success": True}

@router.post("/conversations/{conversation_id}/pin")
async def toggle_conversation_pin(
    conversation_id: int,
    pinned: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle conversation pin status"""
    message_crud = MessageCRUD()
    
    # Verify conversation belongs to user
    conversation = message_crud.get_conversation(db, conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    success = message_crud.toggle_conversation_pin(db, conversation_id, pinned)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to toggle pin")
    
    return {"success": True}

@router.post("/search", response_model=MessageSearchResponse)
async def search_messages(
    search_params: MessageSearchParams,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search messages"""
    message_crud = MessageCRUD()
    messages = message_crud.search_messages(db, current_user.id, search_params)
    
    return MessageSearchResponse(
        messages=messages,
        total_count=len(messages)
    )

@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get unread message count"""
    message_crud = MessageCRUD()
    unread_data = message_crud.get_unread_count(db, current_user.id)
    
    return UnreadCountResponse(
        count=unread_data["count"],
        by_type=unread_data["by_type"]
    )

@router.get("/stats", response_model=MessageStatsResponse)
async def get_message_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get message statistics"""
    message_crud = MessageCRUD()
    stats = message_crud.get_message_stats(db, current_user.id)
    
    return MessageStatsResponse(**stats)

@router.post("/conversations", response_model=Conversation)
async def create_conversation(
    conversation_data: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation"""
    message_crud = MessageCRUD()
    conversation = message_crud.create_conversation(db, conversation_data, current_user.id)
    
    return conversation

@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a message"""
    message_crud = MessageCRUD()
    
    # Verify message belongs to user
    message = message_crud.get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    conversation = message_crud.get_conversation(db, message.conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Message not found")
    
    success = message_crud.delete_message(db, message_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete message")
    
    return {"success": True}

@router.get("/contacts")
async def get_available_contacts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available contacts for new messages"""
    message_crud = MessageCRUD()
    contacts = message_crud.get_available_contacts(db, current_user.id)
    
    return [
        {
            "id": contact.id,
            "name": contact.full_name or contact.email,
            "role": contact.role,
            "avatar": contact.avatar_url,
            "is_online": False  # Implement online status if needed
        }
        for contact in contacts
    ]

# Message action endpoints
@router.post("/messages/{message_id}/medication-action")
async def handle_medication_action(
    message_id: int,
    action: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Handle medication reminder actions"""
    if action not in ["taken", "snooze"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    message_crud = MessageCRUD()
    
    # Verify message belongs to user
    message = message_crud.get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    conversation = message_crud.get_conversation(db, message.conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Create action record
    action_data = {"action": action, "timestamp": datetime.utcnow().isoformat()}
    message_crud.create_message_action(db, message_id, current_user.id, action, action_data)
    
    return {"success": True, "action": action}

@router.post("/messages/{message_id}/appointment-action")
async def handle_appointment_action(
    message_id: int,
    action: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Handle appointment reminder actions"""
    if action not in ["confirm", "reschedule", "cancel"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    message_crud = MessageCRUD()
    
    # Verify message belongs to user
    message = message_crud.get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    conversation = message_crud.get_conversation(db, message.conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Create action record
    action_data = {"action": action, "timestamp": datetime.utcnow().isoformat()}
    message_crud.create_message_action(db, message_id, current_user.id, action, action_data)
    
    return {"success": True, "action": action}