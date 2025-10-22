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

@router.get("/health")
async def health_check():
    """Health check endpoint for messages API"""
    return {"status": "healthy", "service": "messages"}

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
    
    # Convert database messages to schema format
    from app.schemas.message import Message as MessageSchema, MessageSender
    from app.models.message import SenderType
    
    formatted_messages = []
    for message in messages:
        # Create MessageSender from message data
        sender = MessageSender(
            id=str(message.sender_id),
            name=message.sender_name or "Unknown",
            role=message.sender_role or "Unknown",
            avatar=message.sender_avatar,
            type=message.sender_type
        )
        
        # Create Message schema object
        formatted_message = MessageSchema(
            id=message.id,
            conversation_id=message.conversation_id,
            sender=sender,
            content=message.content,
            message_type=message.message_type,
            priority=message.priority,
            status=message.status,
            created_at=message.created_at,
            updated_at=message.updated_at,
            read_at=message.read_at,
            message_metadata=message.message_metadata
        )
        formatted_messages.append(formatted_message)
    
    return ConversationMessagesResponse(
        messages=formatted_messages,
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
    print(f"💬 Message created: {message.id} from user {current_user.id} to conversation {conversation.id}")
    
    # Broadcast message via WebSocket to both conversations
    from app.websocket.message_service import message_websocket_service
    
    # Broadcast to sender's conversation
    print(f"💬 Broadcasting to sender's conversation: {conversation.id}")
    await message_websocket_service.broadcast_new_message(message, conversation)
    
    # Also broadcast to recipient's conversation if it exists
    recipient_conversation = message_crud.get_conversation_by_users(db, conversation.contact_id, current_user.id)
    if recipient_conversation:
        print(f"💬 Broadcasting to recipient's conversation: {recipient_conversation.id}")
        await message_websocket_service.broadcast_new_message(message, recipient_conversation)
    else:
        print(f"💬 No recipient conversation found for contact_id: {conversation.contact_id}")
    
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
    
    # If there's an initial message, broadcast it via WebSocket
    if conversation_data.initial_message:
        from app.websocket.message_service import message_websocket_service
        
        # Get the conversation messages to find the initial message
        messages = message_crud.get_messages_by_conversation(db, conversation.id, page=1, limit=1)
        if messages:
            initial_message = messages[0]
            await message_websocket_service.broadcast_new_message(initial_message, conversation)
            
            # Also broadcast to the recipient if it's an existing conversation
            # For new conversations, the CRUD method already creates both sides
            # For existing conversations, we need to broadcast to the recipient
            if conversation.contact_id != current_user.id:
                # Get the recipient's conversation
                recipient_conversation = message_crud.get_conversation_by_users(db, conversation.contact_id, current_user.id)
                if recipient_conversation:
                    # Get the message from the recipient's conversation
                    recipient_messages = message_crud.get_messages_by_conversation(db, recipient_conversation.id, page=1, limit=1)
                    if recipient_messages:
                        recipient_message = recipient_messages[0]
                        await message_websocket_service.broadcast_new_message(recipient_message, recipient_conversation)
    
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

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a conversation and all its messages"""
    message_crud = MessageCRUD()
    
    # Verify conversation belongs to user
    conversation = message_crud.get_conversation(db, conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    success = message_crud.delete_conversation(db, conversation_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete conversation")
    
    return {"success": True}

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

@router.get("/contacts")
async def get_available_contacts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = Query(None, description="Search query for filtering contacts"),
    offset: int = Query(0, ge=0, description="Number of contacts to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of contacts to return")
):
    """Get available contacts for messaging (doctors, healthcare team, support staff) with pagination"""
    try:
        from app.core.supabase_client import supabase_service
        from app.websocket.connection_manager import manager
        from datetime import date
        
        # Query all active users except current user and exclude superusers
        contacts_query = db.query(User).filter(
            User.id != current_user.id,     # Exclude current user
            User.is_active == True,          # Only active users
            User.is_superuser == False       # Exclude superusers (admins)
        )
        
        # Apply search filter if provided (search by email)
        if search and search.strip():
            search_term = f"%{search.strip().lower()}%"
            contacts_query = contacts_query.filter(
                User.email.ilike(search_term)
            )
        
        # Apply pagination and order by email
        contacts = contacts_query.order_by(User.email).offset(offset).limit(limit).all()
        
        # Get online users list once for efficiency
        online_users = await manager.get_online_users()
        
        # Format response with profile data from Supabase
        result = []
        for contact in contacts:
            try:
                # Fetch user profile from Supabase
                profile = {}
                if contact.supabase_user_id:
                    try:
                        profile = await supabase_service.get_user_profile(contact.supabase_user_id) or {}
                    except Exception as e:
                        print(f"Failed to fetch profile for user {contact.id}: {e}")
                        profile = {}
                
                # Extract profile data
                full_name = profile.get("full_name", "")
                
                # Build display name
                if full_name and full_name.strip():
                    display_name = full_name.strip()
                    # Try to split full name into first and last
                    name_parts = full_name.strip().split()
                    first_name = name_parts[0] if name_parts else ""
                    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                else:
                    # Fallback to email
                    email_parts = contact.email.split('@')
                    display_name = email_parts[0].replace('.', ' ').replace('_', ' ').title()
                    first_name = email_parts[0].split('.')[0].title() if '.' in email_parts[0] else email_parts[0].title()
                    last_name = ""
                
                # Determine role from profile or default
                role_display = profile.get("role", "Healthcare Provider")
                if not role_display or role_display.strip() == "":
                    role_display = "Healthcare Provider"
                
                # Check if user is online using WebSocket status
                is_online = contact.id in online_users
                
                result.append({
                    "id": str(contact.id),
                    "name": display_name,
                    "firstName": first_name,
                    "lastName": last_name,
                    "role": role_display,
                    "avatar": None,
                    "isOnline": is_online,  # ✅ Real-time WebSocket status
                    "specialty": None
                })
            except Exception as e:
                print(f"Error processing contact {contact.id}: {e}")
                # Add contact with fallback data
                email_parts = contact.email.split('@')
                display_name = email_parts[0].replace('.', ' ').replace('_', ' ').title()
                result.append({
                    "id": str(contact.id),
                    "name": display_name,
                    "firstName": email_parts[0].split('.')[0].title() if '.' in email_parts[0] else email_parts[0].title(),
                    "lastName": "",
                    "role": "Healthcare Provider",
                    "avatar": None,
                    "isOnline": contact.id in online_users,
                    "specialty": None
                })
        
        return result
        
    except Exception as e:
        import traceback
        print(f"Error fetching contacts: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch contacts: {str(e)}"
        )