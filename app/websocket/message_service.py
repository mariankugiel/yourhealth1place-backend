from typing import Dict, List, Any, Optional
from fastapi import WebSocket
import json
import asyncio
from datetime import datetime
from app.models.message import Message, Conversation
from app.schemas.message import WebSocketMessageEvent, WebSocketMessageData
from app.websocket.connection_manager import manager

class MessageWebSocketService:
    def __init__(self):
        # Use the global connection manager instead of maintaining separate connections
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, user_id: int, connection_id: str):
        """Accept a WebSocket connection and store it"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connection_id": connection_id,
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow()
        }
        
        # Send connection confirmation
        await self.send_to_connection(websocket, {
            "type": "connection_established",
            "data": {
                "connection_id": connection_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        })

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        metadata = self.connection_metadata.get(websocket)
        if metadata:
            user_id = metadata["user_id"]
            if user_id in self.active_connections:
                self.active_connections[user_id].remove(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            del self.connection_metadata[websocket]

    async def send_to_user(self, user_id: int, message: Dict[str, Any]):
        """Send a message to all connections for a specific user using global connection manager"""
        try:
            await manager.send_personal_message(message, user_id)
        except Exception as e:
            print(f"Error sending message to user {user_id}: {e}")
            raise

    async def send_to_connection(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            print(f"Error sending message to WebSocket: {e}")
            raise

    async def broadcast_new_message(self, message: Message, conversation: Conversation):
        """Broadcast a new message to the conversation participants"""
        print(f"📡 Broadcasting message {message.id} to conversation {conversation.id}")
        print(f"📡 Conversation user_id: {conversation.user_id}, contact_id: {conversation.contact_id}")
        print(f"📡 Message sender_id: {message.sender_id}")
        
        # Get active connections from global manager
        online_users = await manager.get_online_users()
        print(f"📡 Online users: {online_users}")
        
        # Get message attachments from database
        attachments = []
        print(f"📡 Message has attachments attribute: {hasattr(message, 'attachments')}")
        if hasattr(message, 'attachments') and message.attachments:
            print(f"📡 Message attachments count: {len(message.attachments)}")
            for attachment in message.attachments:
                print(f"📡 Processing attachment: {attachment.file_name}")
                attachments.append({
                    "id": attachment.id,
                    "message_id": attachment.message_id,
                    "file_name": attachment.file_name,
                    "original_file_name": attachment.original_file_name,
                    "file_type": attachment.file_type,
                    "file_size": attachment.file_size,
                    "file_extension": attachment.file_extension,
                    "s3_bucket": attachment.s3_bucket,
                    "s3_key": attachment.s3_key,
                    "s3_url": attachment.s3_url,
                    "uploaded_by": attachment.uploaded_by,
                    "created_at": attachment.created_at.isoformat(),
                    "updated_at": attachment.updated_at.isoformat() if attachment.updated_at else None
                })
        else:
            print(f"📡 No attachments found for message {message.id}")
        
        # Create simplified message data (avoiding relationship issues)
        message_data = {
            "type": "new_message",
            "data": {
                "conversation_id": conversation.id,
                "message": {
                    "id": message.id,
                    "conversation_id": message.conversation_id,
                    "sender_id": message.sender_id,  # Use sender_id directly
                    "content": message.content,
                    "message_type": message.message_type.value,
                    "priority": message.priority.value,
                    "status": message.status.value,
                    "message_metadata": message.message_metadata,
                    "attachments": attachments,  # Add attachments
                    "file_attachments": attachments,  # Also add as file_attachments for compatibility
                    "created_at": message.created_at.isoformat(),
                    "updated_at": message.updated_at.isoformat() if message.updated_at else None,
                    "read_at": message.read_at.isoformat() if message.read_at else None
                },
                "current_user_id": conversation.user_id,  # Add current user ID for frontend
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        # Determine who should receive the message (not the sender)
        recipients = []
        
        # Add conversation owner if they're not the sender
        if conversation.user_id != message.sender_id and conversation.user_id in online_users:
            recipients.append(conversation.user_id)
            print(f"📡 Adding conversation owner as recipient: {conversation.user_id}")
        
        # Add contact if they're not the sender
        if conversation.contact_id != message.sender_id and conversation.contact_id in online_users:
            recipients.append(conversation.contact_id)
            print(f"📡 Adding contact as recipient: {conversation.contact_id}")
        
        # Send to all recipients (excluding sender)
        for recipient_id in recipients:
            print(f"📡 Sending message to recipient: {recipient_id}")
            await self.send_to_user(recipient_id, message_data)
        
        print(f"📡 Message sent to {len(recipients)} recipients (excluding sender {message.sender_id})")

    async def broadcast_message_read(self, message_id: int, conversation_id: int, user_id: int):
        """Broadcast that a message was read"""
        # Send to all participants in the conversation
        # This would need to be implemented based on your conversation structure
        await self.send_to_user(user_id, {
            "type": "message_read",
            "data": {
                "message_id": message_id,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        })

    async def broadcast_conversation_updated(self, conversation_id: int, user_id: int, update_type: str, data: Dict[str, Any]):
        """Broadcast conversation updates (archived, pinned, etc.)"""
        await self.send_to_user(user_id, {
            "type": "conversation_updated",
            "data": {
                "conversation_id": conversation_id,
                "update_type": update_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
        })

    async def broadcast_typing_start(self, conversation_id: int, user_id: int, sender_name: str):
        """Broadcast typing start indicator"""
        await self.send_to_user(user_id, {
            "type": "typing_start",
            "data": {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "sender_name": sender_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        })

    async def broadcast_typing_stop(self, conversation_id: int, user_id: int):
        """Broadcast typing stop indicator"""
        await self.send_to_user(user_id, {
            "type": "typing_stop",
            "data": {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        })

    async def broadcast_medication_reminder(self, user_id: int, medication_data: Dict[str, Any]):
        """Broadcast medication reminder to user"""
        await self.send_to_user(user_id, {
            "type": "medication_reminder",
            "data": {
                "medication_id": medication_data.get("medication_id"),
                "medication_name": medication_data.get("medication_name"),
                "dosage": medication_data.get("dosage"),
                "scheduled_time": medication_data.get("scheduled_time"),
                "action_required": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        })

    async def broadcast_appointment_reminder(self, user_id: int, appointment_data: Dict[str, Any]):
        """Broadcast appointment reminder to user"""
        await self.send_to_user(user_id, {
            "type": "appointment_reminder",
            "data": {
                "appointment_id": appointment_data.get("appointment_id"),
                "appointment_date": appointment_data.get("appointment_date"),
                "doctor_name": appointment_data.get("doctor_name"),
                "location": appointment_data.get("location"),
                "action_required": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        })

    async def broadcast_lab_results(self, user_id: int, lab_data: Dict[str, Any]):
        """Broadcast lab results to user"""
        await self.send_to_user(user_id, {
            "type": "lab_results",
            "data": {
                "lab_result_id": lab_data.get("lab_result_id"),
                "test_name": lab_data.get("test_name"),
                "result_date": lab_data.get("result_date"),
                "is_abnormal": lab_data.get("is_abnormal", False),
                "action_required": lab_data.get("is_abnormal", False),
                "timestamp": datetime.utcnow().isoformat()
            }
        })

    async def broadcast_system_announcement(self, user_ids: List[int], announcement_data: Dict[str, Any]):
        """Broadcast system announcement to multiple users"""
        for user_id in user_ids:
            await self.send_to_user(user_id, {
                "type": "system_announcement",
                "data": {
                    "title": announcement_data.get("title"),
                    "content": announcement_data.get("content"),
                    "priority": announcement_data.get("priority", "normal"),
                    "action_required": announcement_data.get("action_required", False),
                    "timestamp": datetime.utcnow().isoformat()
                }
            })

    async def handle_ping(self, websocket: WebSocket):
        """Handle ping from client"""
        metadata = self.connection_metadata.get(websocket)
        if metadata:
            metadata["last_ping"] = datetime.utcnow()
            await self.send_to_connection(websocket, {
                "type": "pong",
                "data": {
                    "timestamp": datetime.utcnow().isoformat()
                }
            })

    async def handle_typing(self, websocket: WebSocket, conversation_id: int, typing: bool):
        """Handle typing indicators"""
        metadata = self.connection_metadata.get(websocket)
        if metadata:
            user_id = metadata["user_id"]
            if typing:
                await self.broadcast_typing_start(conversation_id, user_id, metadata.get("sender_name", "User"))
            else:
                await self.broadcast_typing_stop(conversation_id, user_id)

    def get_user_connections(self, user_id: int) -> List[WebSocket]:
        """Get all active connections for a user"""
        return self.active_connections.get(user_id, [])

    def get_connection_count(self, user_id: int) -> int:
        """Get the number of active connections for a user"""
        return len(self.active_connections.get(user_id, []))

    def is_user_online(self, user_id: int) -> bool:
        """Check if a user has any active connections"""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0

    async def cleanup_stale_connections(self):
        """Clean up stale connections (called periodically)"""
        current_time = datetime.utcnow()
        stale_connections = []
        
        for websocket, metadata in self.connection_metadata.items():
            # Consider connection stale if no ping for 5 minutes
            if (current_time - metadata["last_ping"]).total_seconds() > 300:
                stale_connections.append(websocket)
        
        for websocket in stale_connections:
            await self.disconnect(websocket)

# Global instance
message_websocket_service = MessageWebSocketService()
