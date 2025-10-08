from typing import Dict, List, Any, Optional
from fastapi import WebSocket
import json
import asyncio
from datetime import datetime
from app.models.message import Message, Conversation
from app.schemas.message import WebSocketMessageEvent, WebSocketMessageData

class MessageWebSocketService:
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Store connection metadata
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
        """Send a message to all connections for a specific user"""
        if user_id in self.active_connections:
            connections = self.active_connections[user_id].copy()
            for connection in connections:
                try:
                    await self.send_to_connection(connection, message)
                except Exception as e:
                    print(f"Error sending to connection: {e}")
                    await self.disconnect(connection)

    async def send_to_connection(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            print(f"Error sending message to WebSocket: {e}")
            raise

    async def broadcast_new_message(self, message: Message, conversation: Conversation):
        """Broadcast a new message to the conversation participants"""
        # Send to the recipient (user in the conversation)
        if conversation.user_id in self.active_connections:
            await self.send_to_user(conversation.user_id, {
                "type": "new_message",
                "data": {
                    "conversation_id": conversation.id,
                    "message": {
                        "id": message.id,
                        "conversation_id": message.conversation_id,
                        "sender": {
                            "id": str(message.sender_id),
                            "name": message.sender_name,
                            "role": message.sender_role,
                            "avatar": message.sender_avatar,
                            "type": message.sender_type.value
                        },
                        "content": message.content,
                        "message_type": message.message_type.value,
                        "priority": message.priority.value,
                        "status": message.status.value,
                        "metadata": message.message_metadata,
                        "created_at": message.created_at.isoformat(),
                        "updated_at": message.updated_at.isoformat() if message.updated_at else None,
                        "read_at": message.read_at.isoformat() if message.read_at else None
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            })

        # Send to the sender (if they have active connections)
        if message.sender_id in self.active_connections:
            await self.send_to_user(message.sender_id, {
                "type": "message_sent",
                "data": {
                    "conversation_id": conversation.id,
                    "message_id": message.id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            })

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
