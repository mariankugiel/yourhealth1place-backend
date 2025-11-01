"""
WebSocket Connection Manager
Handles real-time connections, user status, and message broadcasting
"""
import json
import asyncio
from typing import Dict, List, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.websocket_connection import WebSocketConnection
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections and user status"""
    
    def __init__(self):
        # Active connections: {connection_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # User connections: {user_id: set of connection_ids}
        self.user_connections: Dict[int, Set[str]] = {}
        # Connection metadata: {connection_id: {"user_id": int, "connected_at": datetime}}
        self.connection_metadata: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: int) -> bool:
        """Accept a new WebSocket connection"""
        try:
            print(f"🔌 ConnectionManager: Accepting WebSocket for user {user_id}")
            await websocket.accept()
            
            # Store connection
            self.active_connections[connection_id] = websocket
            print(f"🔌 ConnectionManager: Stored connection {connection_id} for user {user_id}")
            
            # Track user connections
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            print(f"🔌 ConnectionManager: User {user_id} now has {len(self.user_connections[user_id])} connections")
            
            # Store metadata
            self.connection_metadata[connection_id] = {
                "user_id": user_id,
                "connected_at": asyncio.get_event_loop().time()
            }
            
            # Store in database
            await self._store_connection_in_db(connection_id, user_id)
            
            # Notify user is online
            await self._broadcast_user_status(user_id, "online")
            
            print(f"🔌 ConnectionManager: Successfully connected user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect user {user_id}: {e}")
            return False
    
    async def disconnect(self, connection_id: str):
        """Handle WebSocket disconnection"""
        try:
            if connection_id in self.connection_metadata:
                user_id = self.connection_metadata[connection_id]["user_id"]
                
                # Remove from active connections
                if connection_id in self.active_connections:
                    del self.active_connections[connection_id]
                
                # Remove from user connections
                if user_id in self.user_connections:
                    self.user_connections[user_id].discard(connection_id)
                    
                    # If user has no more connections, mark as offline
                    if not self.user_connections[user_id]:
                        del self.user_connections[user_id]
                        await self._broadcast_user_status(user_id, "offline")
                
                # Remove metadata
                del self.connection_metadata[connection_id]
                
                # Update database
                await self._remove_connection_from_db(connection_id)
                
                # User disconnected (logging removed for brevity)
                
        except Exception as e:
            logger.error(f"Error during disconnect for connection {connection_id}: {e}")
    
    async def send_personal_message(self, message: dict, user_id: int):
        """Send message to all connections of a specific user"""
        if user_id in self.user_connections:
            connections_to_remove = []
            
            for connection_id in self.user_connections[user_id]:
                try:
                    websocket = self.active_connections.get(connection_id)
                    if websocket:
                        await websocket.send_text(json.dumps(message))
                    else:
                        connections_to_remove.append(connection_id)
                except Exception as e:
                    # Connection failed, will be cleaned up
                    connections_to_remove.append(connection_id)
            
            # Clean up dead connections
            for connection_id in connections_to_remove:
                await self.disconnect(connection_id)
    
    async def send_to_connection(self, message: dict, connection_id: str):
        """Send message to a specific connection"""
        try:
            websocket = self.active_connections.get(connection_id)
            if websocket:
                await websocket.send_text(json.dumps(message))
                return True
            else:
                return False
        except Exception as e:
            return False
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected users"""
        connections_to_remove = []
        
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                # Connection failed, will be cleaned up
                connections_to_remove.append(connection_id)
        
        # Clean up dead connections
        for connection_id in connections_to_remove:
            await self.disconnect(connection_id)
    
    async def get_user_status(self, user_id: int) -> str:
        """Get online/offline status of a user"""
        return "online" if user_id in self.user_connections else "offline"
    
    async def get_online_users(self) -> List[int]:
        """Get list of all online user IDs"""
        online_users = list(self.user_connections.keys())
        print(f"🔌 ConnectionManager: Online users: {online_users}")
        print(f"🔌 ConnectionManager: User connections: {self.user_connections}")
        return online_users
    
    async def get_user_connection_count(self, user_id: int) -> int:
        """Get number of active connections for a user"""
        return len(self.user_connections.get(user_id, set()))
    
    async def _store_connection_in_db(self, connection_id: str, user_id: int):
        """Store connection in database"""
        try:
            # Get database session
            db = next(get_db())
            
            # Create or update connection record
            connection = db.query(WebSocketConnection).filter(
                WebSocketConnection.connection_id == connection_id
            ).first()
            
            if not connection:
                connection = WebSocketConnection(
                    connection_id=connection_id,
                    user_id=user_id,
                    is_active=True
                )
                db.add(connection)
            else:
                connection.is_active = True
            
            db.commit()
            db.close()
            
        except Exception as e:
            logger.error(f"Failed to store connection in database: {e}")
    
    async def _remove_connection_from_db(self, connection_id: str):
        """Remove connection from database"""
        try:
            # Get database session
            db = next(get_db())
            
            # Mark connection as inactive
            connection = db.query(WebSocketConnection).filter(
                WebSocketConnection.connection_id == connection_id
            ).first()
            
            if connection:
                connection.is_active = False
                db.commit()
            
            db.close()
            
        except Exception as e:
            logger.error(f"Failed to remove connection from database: {e}")
    
    async def _broadcast_user_status(self, user_id: int, status: str):
        """Broadcast user status change to relevant users"""
        try:
            # Get database session to find user's connections
            db = next(get_db())
            
            # Get user info
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                db.close()
                return
            
            # Create status message
            status_message = {
                "type": "user_status_change",
                "data": {
                    "user_id": user_id,
                    "status": status,
                    "timestamp": asyncio.get_event_loop().time()
                }
            }
            
            # Broadcast to all online users (for now)
            # In a real app, you might want to broadcast only to friends/contacts
            await self.broadcast_to_all(status_message)
            
            db.close()
            
        except Exception as e:
            logger.error(f"Failed to broadcast user status: {e}")

# Global connection manager instance
manager = ConnectionManager()

