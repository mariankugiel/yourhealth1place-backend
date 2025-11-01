"""
WebSocket Endpoints
Handles WebSocket connections, authentication, and real-time communication
"""
import json
import uuid
import asyncio
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.routing import APIRouter
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.supabase_client import supabase_service
from app.models.user import User
from app.models.message import Message
from app.websocket.connection_manager import manager
from app.websocket.message_service import message_websocket_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

async def authenticate_websocket_user(token: str, db: Session) -> Optional[User]:
    """Authenticate user from WebSocket token"""
    try:
        # Verify token with Supabase
        user_info = supabase_service.get_user_from_token(token)
        if not user_info:
            return None
        
        # Get internal user record
        db_user = db.query(User).filter(
            User.supabase_user_id == user_info['id']
        ).first()
        
        return db_user
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        return None

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Main WebSocket endpoint for real-time communication
    
    Query Parameters:
    - token: Supabase JWT token for authentication
    """
    
    connection_id = str(uuid.uuid4())
    user = None
    print(f"🔌 WebSocket connection attempt: {connection_id}")
    print(f"🔌 Token provided: {token is not None}")
    
    try:
        # Authenticate user
        if not token:
            await websocket.close(code=1008, reason="Authentication token required")
            return
        
        user = await authenticate_websocket_user(token, db)
        if not user:
            await websocket.close(code=1008, reason="Invalid authentication token")
            return
        
        # Connect user
        connected = await manager.connect(websocket, connection_id, user.id)
        if not connected:
            await websocket.close(code=1011, reason="Failed to establish connection")
            return
        
        # Send welcome message
        welcome_message = {
            "type": "connection_established",
            "data": {
                "connection_id": connection_id,
                "user_id": user.id,
                "message": "Connected successfully"
            }
        }
        await websocket.send_text(json.dumps(welcome_message))
        
        # Handle incoming messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Process different message types
                await handle_websocket_message(websocket, connection_id, user, message, db)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                error_message = {
                    "type": "error",
                    "data": {"message": "Invalid JSON format"}
                }
                await websocket.send_text(json.dumps(error_message))
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                error_message = {
                    "type": "error",
                    "data": {"message": "Internal server error"}
                }
                await websocket.send_text(json.dumps(error_message))
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Clean up connection
        await manager.disconnect(connection_id)

async def handle_websocket_message(
    websocket: WebSocket, 
    connection_id: str, 
    user: User, 
    message: dict, 
    db: Session
):
    """Handle different types of WebSocket messages"""
    
    message_type = message.get("type")
    data = message.get("data", {})
    
    if message_type == "ping":
        # Respond to ping with pong
        pong_message = {
            "type": "pong",
            "data": {"timestamp": data.get("timestamp")}
        }
        await websocket.send_text(json.dumps(pong_message))
    
    elif message_type == "get_online_users":
        # Send list of online users
        online_users = await manager.get_online_users()
        response = {
            "type": "online_users",
            "data": {"users": online_users}
        }
        await websocket.send_text(json.dumps(response))
    
    elif message_type == "get_user_status":
        # Get status of specific user
        target_user_id = data.get("user_id")
        if target_user_id:
            status = await manager.get_user_status(target_user_id)
            response = {
                "type": "user_status",
                "data": {
                    "user_id": target_user_id,
                    "status": status
                }
            }
            await websocket.send_text(json.dumps(response))
    
    elif message_type == "send_message":
        # Handle direct messaging (foundation for chat system)
        conversation_id = data.get("conversation_id")
        target_user_id = data.get("target_user_id")
        message_content = data.get("message")
        message_type = data.get("message_type", "general")
        priority = data.get("priority", "normal")
        attachments = data.get("attachments", [])
        
        if conversation_id and message_content:
            await handle_websocket_message_send(user.id, conversation_id, message_content, message_type, priority, attachments, db)
    
    elif message_type == "typing":
        # Handle typing indicators
        target_user_id = data.get("target_user_id")
        is_typing = data.get("is_typing", False)
        
        if target_user_id:
            typing_message = {
                "type": "typing_indicator",
                "data": {
                    "from_user_id": user.id,
                    "is_typing": is_typing
                }
            }
            await manager.send_personal_message(typing_message, target_user_id)
    
    elif message_type == "message_typing":
        # Handle message typing indicators for conversations
        conversation_id = data.get("conversation_id")
        is_typing = data.get("is_typing", False)
        
        if conversation_id:
            print(f"🔤 Typing indicator: user {user.id} in conversation {conversation_id}, typing: {is_typing}")
            
            # Get conversation to find the other participant
            from app.crud.message import MessageCRUD
            message_crud = MessageCRUD()
            conversation = message_crud.get_conversation(db, conversation_id)
            
            if conversation:
                # Determine who should receive the typing indicator (not the sender)
                recipient_id = None
                if conversation.user_id != user.id:
                    recipient_id = conversation.user_id
                elif conversation.contact_id != user.id:
                    recipient_id = conversation.contact_id
                
                if recipient_id:
                    print(f"🔤 Sending typing indicator to user {recipient_id}")
                    typing_message = {
                        "type": "typing_indicator",
                        "data": {
                            "conversation_id": conversation_id,
                            "user_id": user.id,
                            "is_typing": is_typing
                        }
                    }
                    await manager.send_personal_message(typing_message, recipient_id)
                else:
                    print(f"🔤 No recipient found for typing indicator")
            else:
                print(f"🔤 Conversation {conversation_id} not found")
    
    elif message_type == "message_action":
        # Handle message actions (medication taken, appointment confirmed, etc.)
        message_id = data.get("message_id")
        action_type = data.get("action_type")
        action_data = data.get("action_data", {})
        
        if message_id and action_type:
            await handle_message_action(user.id, message_id, action_type, action_data, db)
    
    else:
        # Unknown message type
        error_message = {
            "type": "error",
            "data": {"message": f"Unknown message type: {message_type}"}
        }
        await websocket.send_text(json.dumps(error_message))

async def handle_websocket_message_send(
    sender_id: int, 
    conversation_id: int, 
    message_content: str, 
    message_type: str, 
    priority: str, 
    attachments: list, 
    db: Session
):
    """Handle WebSocket message sending with proper database storage and broadcasting"""
    try:
        from app.crud.message import MessageCRUD
        from app.schemas.message import MessageCreate, MessageAttachmentCreate
        from app.models.message import MessageType, MessagePriority
        
        print(f"🔍 WebSocket message send: sender_id={sender_id}, conversation_id={conversation_id}, content='{message_content}'")
        
        # Create message data
        message_data = MessageCreate(
            conversation_id=conversation_id,
            content=message_content,
            message_type=MessageType(message_type),
            priority=MessagePriority(priority),
            message_metadata={}
        )
        
        # Create attachment data if provided
        attachment_data = []
        if attachments:
            for attachment in attachments:
                attachment_data.append(MessageAttachmentCreate(
                    file_name=attachment.get("file_name", ""),
                    original_file_name=attachment.get("original_file_name", ""),
                    file_type=attachment.get("file_type", ""),
                    file_size=attachment.get("file_size", 0),
                    file_extension=attachment.get("file_extension", ""),
                    s3_bucket=attachment.get("s3_bucket", ""),
                    s3_key=attachment.get("s3_key", ""),
                    s3_url=attachment.get("s3_url", "")
                ))
        
        # Save message to database
        message_crud = MessageCRUD()
        message = message_crud.create_message(db, message_data, sender_id, attachment_data)
        print(f"✅ Message saved to database: {message.id}")
        
        # Load message with attachments for broadcasting
        from sqlalchemy.orm import joinedload
        message_with_attachments = db.query(Message).options(joinedload(Message.attachments)).filter(Message.id == message.id).first()
        
        # Get conversation for broadcasting
        conversation = message_crud.get_conversation(db, conversation_id)
        if not conversation:
            print(f"❌ Conversation not found: {conversation_id}")
            return
        
        print(f"📡 Broadcasting message to conversation participants")
        
        # Broadcast message using the message service
        await message_websocket_service.broadcast_new_message(message_with_attachments, conversation)
        
        print(f"✅ Message broadcasted successfully")
        
    except Exception as e:
        logger.error(f"Error handling WebSocket message send: {e}")
        print(f"❌ Error in WebSocket message send: {e}")
        import traceback
        traceback.print_exc()

async def handle_direct_message(sender_id: int, target_user_id: int, message_content: str, db: Session):
    """Handle direct messaging between users (legacy function - kept for compatibility)"""
    try:
        # Check if target user is online
        target_status = await manager.get_user_status(target_user_id)
        
        # Create message object
        message_data = {
            "type": "direct_message",
            "data": {
                "from_user_id": sender_id,
                "to_user_id": target_user_id,
                "message": message_content,
                "timestamp": asyncio.get_event_loop().time(),
                "delivery_status": "delivered" if target_status == "online" else "pending"
            }
        }
        
        # Send to target user if online
        if target_status == "online":
            await manager.send_personal_message(message_data, target_user_id)
        
        # Send confirmation to sender
        confirmation = {
            "type": "message_sent",
            "data": {
                "to_user_id": target_user_id,
                "message": message_content,
                "delivery_status": "delivered" if target_status == "online" else "pending"
            }
        }
        await manager.send_personal_message(confirmation, sender_id)
        
        # TODO: Store message in database for offline users
        # This would be implemented in a full messaging system
        
    except Exception as e:
        logger.error(f"Error handling direct message: {e}")

# Additional WebSocket endpoints for specific features

async def handle_message_action(user_id: int, message_id: int, action_type: str, action_data: dict, db: Session):
    """Handle message actions like medication taken, appointment confirmed, etc."""
    try:
        from app.crud.message import MessageCRUD
        
        message_crud = MessageCRUD(db)
        
        # Create the action record
        action = message_crud.create_message_action(message_id, user_id, action_type, action_data)
        
        # Update message metadata if needed
        message = message_crud.get_message(message_id)
        if message and message.message_metadata:
            message.message_metadata["action_completed"] = True
            message.message_metadata["action_taken"] = action_type
            message.message_metadata["action_timestamp"] = action.created_at.isoformat()
            db.commit()
        
        # Broadcast action to relevant users
        if message:
            conversation = message_crud.get_conversation(message.conversation_id)
            if conversation:
                await message_websocket_service.broadcast_message_read(
                    message_id, message.conversation_id, conversation.user_id
                )
        
        return action
    except Exception as e:
        logger.error(f"Error handling message action: {e}")
        raise

@router.websocket("/ws/notifications")
async def notification_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint specifically for notifications
    """
    connection_id = str(uuid.uuid4())
    user = None
    
    try:
        # Authenticate user
        if not token:
            await websocket.close(code=1008, reason="Authentication token required")
            return
        
        user = await authenticate_websocket_user(token, db)
        if not user:
            await websocket.close(code=1008, reason="Invalid authentication token")
            return
        
        # Connect user
        connected = await manager.connect(websocket, connection_id, user.id)
        if not connected:
            await websocket.close(code=1011, reason="Failed to establish connection")
            return
        
        # Send notification-specific welcome
        welcome_message = {
            "type": "notification_connection_established",
            "data": {
                "connection_id": connection_id,
                "user_id": user.id,
                "message": "Notification channel connected"
            }
        }
        await websocket.send_text(json.dumps(welcome_message))
        
        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle notification-specific messages
                if message.get("type") == "notification_acknowledged":
                    # Handle notification acknowledgment
                    notification_id = message.get("data", {}).get("notification_id")
                    if notification_id:
                        # TODO: Update notification status in database
                        pass
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Notification WebSocket error: {e}")
                break
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Notification WebSocket connection error: {e}")
    finally:
        await manager.disconnect(connection_id)

