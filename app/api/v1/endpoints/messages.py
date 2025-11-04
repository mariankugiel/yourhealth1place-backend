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
    MessageStatsResponse, MessageActionCreate, MessageAction, CreateConversationRequest
)
from app.models.message import MessageType, MessagePriority, MessageStatus, SenderType
from app.models.user import User, UserRole

def get_initials(name: str) -> str:
    """Generate initials from a full name"""
    if not name or name == "Unknown":
        return "U"
    
    # Split by space and get first letter of each word
    words = name.strip().split()
    if len(words) == 1:
        # Single word, take first two characters
        return words[0][:2].upper()
    else:
        # Multiple words, take first letter of each word (max 2)
        return ''.join([word[0] for word in words[:2]]).upper()

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
    
    # Fetch contact information from Supabase for each conversation
    from app.core.supabase_client import supabase_service
    import asyncio
    
    # Get current user's profile information (only once)
    current_user_profile = None
    try:
        current_user_db = db.query(User).filter(User.id == current_user.id).first()
        if current_user_db and current_user_db.supabase_user_id:
            current_user_profile = await supabase_service.get_user_profile(current_user_db.supabase_user_id)
    except Exception as e:
        print(f"⚠️ Failed to fetch current user profile: {e}")
    
    # First, collect all contact user IDs synchronously (fast DB queries)
    conversation_contacts = {}
    for conversation in conversations:
        if conversation.user_id == current_user.id:
            contact_id = conversation.contact_id
        else:
            contact_id = conversation.user_id
        conversation_contacts[conversation.id] = contact_id
    
    # Get all contact users in one query (more efficient)
    contact_ids = list(conversation_contacts.values())
    contact_users = {user.id: user for user in db.query(User).filter(User.id.in_(contact_ids)).all()}
    
    # Prepare profile fetch tasks to run in parallel (only async Supabase calls)
    async def fetch_contact_profile(conversation_id, contact_id):
        """Fetch profile data for a single conversation's contact"""
        try:
            print(f"🔄 [fetch_contact_profile] Starting for conversation {conversation_id}, contact_id {contact_id}")
            contact_user = contact_users.get(contact_id)
            if not contact_user or not contact_user.supabase_user_id:
                print(f"❌ [fetch_contact_profile] No Supabase user ID found for contact_id {contact_id}")
                raise ValueError(f"No Supabase user ID found for contact_id {contact_id}")
            
            print(f"🔄 [fetch_contact_profile] Calling get_user_profile for supabase_user_id: {contact_user.supabase_user_id}")
            # Fetch profile from Supabase using supabase_user_id
            contact_profile = await supabase_service.get_user_profile(contact_user.supabase_user_id)
            print(f"🔄 [fetch_contact_profile] Received profile from get_user_profile: {contact_profile is not None}")
            
            # Debug logging to see what we got from get_user_profile
            print(f"🔍 Contact {contact_id} (supabase_user_id: {contact_user.supabase_user_id})")
            print(f"   Profile keys: {list(contact_profile.keys()) if contact_profile else 'None'}")
            print(f"   img_url in profile: {contact_profile.get('img_url') if contact_profile else 'N/A'}")
            print(f"   avatar_url in profile: {contact_profile.get('avatar_url') if contact_profile else 'N/A'}")
            
            # Get avatar URL - prioritize img_url from profile (already a signed URL stored in database)
            # Only generate new signed URL if img_url doesn't exist in database
            avatar_url = contact_profile.get('avatar_url') if contact_profile else None  # This is img_url mapped from get_user_profile
            print(f"   Extracted avatar_url: {avatar_url}")
            
            if not avatar_url:
                print(f"   ⚠️ No avatar_url from profile, trying get_avatar_signed_url...")
                # Fallback: Generate signed URL from Supabase Storage if img_url not in database
                avatar_url = await supabase_service.get_avatar_signed_url(contact_user.supabase_user_id)
                print(f"   Fallback avatar_url result: {avatar_url}")
            else:
                print(f"   ✅ Using avatar_url from profile")
            
            # Return profile data including the Supabase UUID
            return {
                'conversation_id': conversation_id,
                'contact_id': contact_id,
                'contact_supabase_user_id': contact_profile.get('supabase_user_id') or contact_user.supabase_user_id,
                'contact_name': contact_profile.get('full_name', 'Unknown'),
                'contact_role': contact_profile.get('role', 'PATIENT'),
                'contact_avatar': avatar_url,  # Use img_url from profile if available, otherwise generated URL
                'contact_initials': get_initials(contact_profile.get('full_name', 'Unknown'))
            }
        except Exception as e:
            print(f"⚠️ Failed to fetch contact profile for conversation {conversation_id}: {e}")
            # Return fallback values
            return {
                'conversation_id': conversation_id,
                'contact_id': contact_id,
                'contact_supabase_user_id': None,
                'contact_name': "Unknown",
                'contact_role': "PATIENT",
                'contact_avatar': None,
                'contact_initials': "U"
            }
    
    # Fetch all profiles in parallel (only the async Supabase calls)
    profile_tasks = [
        fetch_contact_profile(conv.id, conversation_contacts[conv.id]) 
        for conv in conversations
    ]
    profile_results = await asyncio.gather(*profile_tasks, return_exceptions=True)
    
    # Create a map of conversation_id -> profile data for quick lookup
    profile_map = {}
    for result in profile_results:
        if isinstance(result, Exception):
            print(f"⚠️ Error fetching profile: {result}")
            continue
        profile_map[result['conversation_id']] = result
    
    # Apply profile data to conversations
    for conversation in conversations:
        profile_data = profile_map.get(conversation.id, {})
        conversation.contact_name = profile_data.get('contact_name', 'Unknown')
        conversation.contact_role = profile_data.get('contact_role', 'PATIENT')
        conversation.contact_avatar = profile_data.get('contact_avatar')
        conversation.contact_id = profile_data.get('contact_id', conversation_contacts.get(conversation.id))
        conversation.contact_supabase_user_id = profile_data.get('contact_supabase_user_id')
        conversation.contact_initials = profile_data.get('contact_initials', 'U')
        
        # Add current user information to conversation
        if current_user_profile:
            # Get current user's avatar URL - prioritize img_url from profile (already a signed URL)
            current_user_avatar_url = current_user_profile.get('avatar_url')  # This is img_url mapped from get_user_profile
            if not current_user_avatar_url and current_user_db and current_user_db.supabase_user_id:
                # Fallback: Generate signed URL from Supabase Storage if img_url not in database
                current_user_avatar_url = await supabase_service.get_avatar_signed_url(current_user_db.supabase_user_id)
            
            conversation.current_user_name = current_user_profile.get('full_name', 'Unknown')
            conversation.current_user_role = current_user_profile.get('role', 'PATIENT')
            conversation.current_user_avatar = current_user_avatar_url
            conversation.current_user_initials = get_initials(current_user_profile.get('full_name', 'Unknown'))
        else:
            conversation.current_user_name = "Unknown"
            conversation.current_user_role = "PATIENT"
            conversation.current_user_avatar = None
            conversation.current_user_initials = "U"
    
    # Calculate unread count
    unread_count = message_crud.get_unread_count(db, current_user.id)
    
    return MessagesResponse(
        conversations=conversations,
        total_count=len(conversations),
        unread_count=unread_count["count"],
        has_more=False,  # Implement pagination if needed
        current_user_id=current_user.id  # Add actual database user ID
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
    
    # Verify conversation belongs to user (check both user_id and contact_id)
    conversation = message_crud.get_conversation(db, conversation_id)
    if not conversation or (conversation.user_id != current_user.id and conversation.contact_id != current_user.id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = message_crud.get_messages_by_conversation(db, conversation_id, page, limit)
    
    # Convert database messages to schema format
    from app.schemas.message import Message as MessageSchema, MessageSender, MessageAttachment
    from app.models.message import SenderType
    from app.crud.message_document import MessageDocumentCRUD
    
    formatted_messages = []
    document_crud = MessageDocumentCRUD()
    
    for message in messages:
        # Get attachments for this message
        attachments = document_crud.get_documents_by_message(db, message.id)
        formatted_attachments = []
        for attachment in attachments:
            formatted_attachments.append(MessageAttachment(
                id=attachment.id,
                message_id=attachment.message_id,
                file_name=attachment.file_name,
                original_file_name=attachment.original_file_name,
                file_type=attachment.file_type,
                file_size=attachment.file_size,
                file_extension=attachment.file_extension,
                s3_bucket=attachment.s3_bucket,
                s3_key=attachment.s3_key,
                s3_url=attachment.s3_url,
                uploaded_by=attachment.uploaded_by,
                created_at=attachment.created_at,
                updated_at=attachment.updated_at
            ))
        
        # Create simplified Message schema object
        formatted_message = MessageSchema(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_id=message.sender_id,  # Just sender ID, no full sender object
            attachments=formatted_attachments if formatted_attachments else None,
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
    print(f"💬 Send message endpoint called by user {current_user.id}")
    print(f"💬 Request data: {request}")
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
            contact_id=request.recipient_id
        )
        conversation = message_crud.create_conversation(db, conversation_data, current_user.id)
        message_data.conversation_id = conversation.id
    
    # Create message for sender's conversation with attachments
    message = message_crud.create_message(db, message_data, current_user.id, request.attachments)
    print(f"💬 Message created: {message.id} from user {current_user.id} to conversation {conversation.id}")
    
    # Also create message for recipient's conversation if it exists
    recipient_conversation = message_crud.get_conversation_by_users(db, conversation.contact_id, current_user.id)
    recipient_message = None
    if recipient_conversation:
        # Create message for recipient's conversation
        recipient_message_data = MessageCreate(
            conversation_id=recipient_conversation.id,
            content=message_data.content,
            message_type=message_data.message_type,
            priority=message_data.priority,
            message_metadata=message_data.message_metadata
        )
        recipient_message = message_crud.create_message(db, recipient_message_data, current_user.id)
        print(f"💬 Recipient message created: {recipient_message.id} in conversation {recipient_conversation.id}")
    else:
        print(f"💬 No recipient conversation found for contact_id: {conversation.contact_id}")
    
    # Broadcast message via WebSocket to both conversations
    from app.websocket.message_service import message_websocket_service
    
    # Broadcast to sender's conversation
    print(f"💬 Broadcasting to sender's conversation: {conversation.id}")
    await message_websocket_service.broadcast_new_message(message, conversation)
    
    # Broadcast to recipient's conversation if it exists
    if recipient_conversation and recipient_message:
        print(f"💬 Broadcasting to recipient's conversation: {recipient_conversation.id}")
        await message_websocket_service.broadcast_new_message(recipient_message, recipient_conversation)
    
    # Convert SQLAlchemy Message to Pydantic Message schema
    from app.schemas.message import Message as MessageSchema, MessageSender
    
    # Fetch sender information from User relationship
    sender_name = "Unknown"
    sender_role = "Unknown" 
    sender_avatar = None
    
    if message.sender:
        sender_name = message.sender.email or "Unknown"
        # Get role and avatar from Supabase if available
        try:
            from app.core.supabase_client import supabase_service
            profile = await supabase_service.get_user_profile(message.sender.supabase_user_id)
            sender_role = profile.get('role', 'Patient')
            # Prioritize img_url from profile (already a signed URL stored in database)
            sender_avatar = profile.get('avatar_url')  # This is img_url mapped from get_user_profile
            if not sender_avatar and message.sender.supabase_user_id:
                # Fallback: Generate signed URL from Supabase Storage if img_url not in database
                sender_avatar = await supabase_service.get_avatar_signed_url(message.sender.supabase_user_id)
        except Exception:
            sender_role = "Patient"  # Default role
            sender_avatar = None
    
    sender = MessageSender(
        id=str(message.sender_id),
        name=sender_name,
        role=sender_role,
        avatar=sender_avatar,
        type="user"  # Default type since we removed sender_type
    )
    
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
    
    return SendMessageResponse(
        message=formatted_message,
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
    request: CreateConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation"""
    from app.core.supabase_client import supabase_service
    
    message_crud = MessageCRUD()
    
    # Convert recipientId to integer
    try:
        contact_id = int(request.recipientId)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid recipient ID format")
    
    # Create conversation data
    conversation_data = ConversationCreate(
        contact_id=contact_id,
        initial_message=request.initialMessage
    )
    
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
            User.role != UserRole.ADMIN       # Exclude admins
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