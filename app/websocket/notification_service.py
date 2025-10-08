"""
WebSocket Notification Service
Integrates with the medication reminder system to send real-time notifications
"""
import json
import asyncio
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.notification import Notification, NotificationType, NotificationStatus
from app.models.websocket_connection import WebSocketConnection
from app.websocket.connection_manager import manager
import logging

logger = logging.getLogger(__name__)

class WebSocketNotificationService:
    """Service for sending real-time notifications via WebSocket"""
    
    @staticmethod
    async def send_medication_reminder(notification: Notification, db: Session):
        """Send medication reminder notification via WebSocket"""
        try:
            # Check if user has active WebSocket connections
            active_connections = db.query(WebSocketConnection).filter(
                WebSocketConnection.user_id == notification.user_id,
                WebSocketConnection.is_active == True
            ).all()
            
            if not active_connections:
                logger.info(f"No active WebSocket connections for user {notification.user_id}")
                return False
            
            # Create notification message
            notification_message = {
                "type": "medication_reminder",
                "data": {
                    "notification_id": notification.id,
                    "title": notification.title,
                    "message": notification.message,
                    "priority": notification.priority.value if notification.priority else "normal",
                    "medication_id": notification.medication_id,
                    "timestamp": notification.created_at.isoformat() if notification.created_at else None,
                    "metadata": notification.data or {}
                }
            }
            
            # Send to all user's active connections
            sent_count = 0
            for connection in active_connections:
                success = await manager.send_to_connection(
                    notification_message, 
                    connection.connection_id
                )
                if success:
                    sent_count += 1
            
            logger.info(f"Sent medication reminder to {sent_count}/{len(active_connections)} connections for user {notification.user_id}")
            return sent_count > 0
            
        except Exception as e:
            logger.error(f"Failed to send medication reminder via WebSocket: {e}")
            return False
    
    @staticmethod
    async def send_general_notification(notification: Notification, db: Session):
        """Send general notification via WebSocket"""
        try:
            # Check if user has active WebSocket connections
            active_connections = db.query(WebSocketConnection).filter(
                WebSocketConnection.user_id == notification.user_id,
                WebSocketConnection.is_active == True
            ).all()
            
            if not active_connections:
                logger.info(f"No active WebSocket connections for user {notification.user_id}")
                return False
            
            # Create notification message
            notification_message = {
                "type": "notification",
                "data": {
                    "notification_id": notification.id,
                    "notification_type": notification.notification_type.value,
                    "title": notification.title,
                    "message": notification.message,
                    "priority": notification.priority.value if notification.priority else "normal",
                    "timestamp": notification.created_at.isoformat() if notification.created_at else None,
                    "metadata": notification.data or {}
                }
            }
            
            # Send to all user's active connections
            sent_count = 0
            for connection in active_connections:
                success = await manager.send_to_connection(
                    notification_message, 
                    connection.connection_id
                )
                if success:
                    sent_count += 1
            
            logger.info(f"Sent notification to {sent_count}/{len(active_connections)} connections for user {notification.user_id}")
            return sent_count > 0
            
        except Exception as e:
            logger.error(f"Failed to send notification via WebSocket: {e}")
            return False
    
    @staticmethod
    async def send_system_announcement(message: str, target_user_ids: Optional[list] = None):
        """Send system announcement to specific users or all users"""
        try:
            announcement_message = {
                "type": "system_announcement",
                "data": {
                    "message": message,
                    "timestamp": asyncio.get_event_loop().time()
                }
            }
            
            if target_user_ids:
                # Send to specific users
                for user_id in target_user_ids:
                    await manager.send_personal_message(announcement_message, user_id)
            else:
                # Broadcast to all users
                await manager.broadcast_to_all(announcement_message)
            
            logger.info(f"Sent system announcement to {len(target_user_ids) if target_user_ids else 'all'} users")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send system announcement: {e}")
            return False
    
    @staticmethod
    async def send_user_status_update(user_id: int, status: str):
        """Send user status update to relevant users"""
        try:
            status_message = {
                "type": "user_status_update",
                "data": {
                    "user_id": user_id,
                    "status": status,
                    "timestamp": asyncio.get_event_loop().time()
                }
            }
            
            # Broadcast to all users (in a real app, you might want to send only to friends/contacts)
            await manager.broadcast_to_all(status_message)
            
            logger.info(f"Sent user status update for user {user_id}: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send user status update: {e}")
            return False
    
    @staticmethod
    async def get_user_connection_info(user_id: int, db: Session) -> Dict[str, Any]:
        """Get information about user's WebSocket connections"""
        try:
            # Get active connections from database
            active_connections = db.query(WebSocketConnection).filter(
                WebSocketConnection.user_id == user_id,
                WebSocketConnection.is_active == True
            ).all()
            
            # Get connection info from manager
            connection_count = await manager.get_user_connection_count(user_id)
            status = await manager.get_user_status(user_id)
            
            return {
                "user_id": user_id,
                "status": status,
                "connection_count": connection_count,
                "active_connections": [
                    {
                        "connection_id": conn.connection_id,
                        "connected_at": conn.connected_at.isoformat() if conn.connected_at else None
                    }
                    for conn in active_connections
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get user connection info: {e}")
            return {
                "user_id": user_id,
                "status": "unknown",
                "connection_count": 0,
                "active_connections": []
            }

# Global service instance
websocket_notification_service = WebSocketNotificationService()

