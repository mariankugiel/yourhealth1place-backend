from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Header
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime
import json
import os

from app.core.database import get_db
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.notification import (
    NotificationResponse,
    NotificationUpdate,
    NotificationWithMedication
)
from app.crud.notification import notification_crud
from app.models.notification import NotificationStatus

router = APIRouter()

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        print(f"✅ User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        print(f"❌ User {user_id} disconnected")
    
    async def send_notification(self, user_id: int, message: dict):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                    print(f"📤 Sent notification to user {user_id}")
                except Exception as e:
                    print(f"❌ Failed to send to user {user_id}: {e}")
                    # Remove broken connection
                    if connection in self.active_connections[user_id]:
                        self.active_connections[user_id].remove(connection)

manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_notifications(websocket: WebSocket, user_id: int):
    """WebSocket endpoint for real-time notifications"""
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and handle ping/pong
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("action") == "ping":
                    await websocket.send_json({"action": "pong"})
            except json.JSONDecodeError:
                # Handle plain text ping
                if data == "ping":
                    await websocket.send_json({"action": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket, user_id)

@router.get("/", response_model=List[NotificationWithMedication])
async def get_notifications(
    status: Optional[NotificationStatus] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notifications for the current user"""
    notifications = notification_crud.get_user_notifications(
        db=db,
        user_id=current_user.id,
        status=status,
        limit=limit,
        offset=offset
    )
    
    # Add medication details
    result = []
    for notification in notifications:
        notification_dict = {
            "id": notification.id,
            "user_id": notification.user_id,
            "notification_type": notification.notification_type,
            "title": notification.title,
            "message": notification.message,
            "medication_id": notification.medication_id,
            "appointment_id": notification.appointment_id,
            "data": notification.data,
            "status": notification.status,
            "read_at": notification.read_at,
            "delivered_at": notification.delivered_at,
            "display_until": notification.display_until,
            "created_at": notification.created_at,
            "updated_at": notification.updated_at,
            "medication_name": notification.medication.medication_name if notification.medication else None,
            "medication_dosage": getattr(notification.medication, 'dosage', None) if notification.medication else None
        }
        result.append(notification_dict)
    
    return result

@router.get("/unread/count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get count of unread notifications"""
    count = notification_crud.get_unread_count(db=db, user_id=current_user.id)
    return {"count": count}

@router.patch("/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read"""
    success = notification_crud.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return {"message": "Notification marked as read"}

@router.patch("/{notification_id}/dismiss", status_code=status.HTTP_200_OK)
async def dismiss_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dismiss a notification"""
    update_data = NotificationUpdate(status=NotificationStatus.DISMISSED)
    updated_notification = notification_crud.update_notification(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id,
        update_data=update_data
    )
    
    if not updated_notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return {"message": "Notification dismissed"}

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a notification"""
    notification = notification_crud.get_notification(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    db.delete(notification)
    db.commit()

@router.post("/mark-all-read", status_code=status.HTTP_200_OK)
async def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read for the current user"""
    # Get all unread notifications
    unread_notifications = notification_crud.get_user_notifications(
        db=db,
        user_id=current_user.id,
        status=NotificationStatus.UNREAD
    )
    
    # Mark each as read
    for notification in unread_notifications:
        notification.status = NotificationStatus.READ
        notification.read_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": f"Marked {len(unread_notifications)} notifications as read"}

# Webhook endpoint for receiving notifications from Lambda
@router.post("/webhook/lambda")
async def lambda_webhook(
    request: dict,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Receive notification from Lambda and send to connected users via WebSocket"""
    try:
        # Verify Lambda authentication
        expected_token = os.getenv("LAMBDA_WEBHOOK_TOKEN", "your-lambda-webhook-token")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header"
            )
        
        token = authorization.split(" ")[1]
        if token != expected_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook token"
            )
        
        notification_data = request.get("notification_data", {})
        user_id = notification_data.get("user_id")
        
        if user_id:
            # Send to connected WebSocket clients
            await manager.send_notification(user_id, notification_data)
            
            # Mark notification as delivered
            notification_id = notification_data.get("notification_id")
            if notification_id:
                notification_crud.mark_as_delivered(db, notification_id)
            
            return {"message": "Notification sent", "user_id": user_id}
        
        return {"message": "No user_id provided"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing Lambda webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process notification"
        )

# Legacy SNS webhook endpoint (keep for backward compatibility)
@router.post("/webhook/sns")
async def sns_webhook(
    request: dict,
    db: Session = Depends(get_db)
):
    """Receive notification from SNS and send to connected users via WebSocket"""
    try:
        message_type = request.get("Type")
        
        if message_type == "SubscriptionConfirmation":
            # Confirm SNS subscription (only happens once)
            return {"message": "Subscription confirmation received"}
        
        if message_type == "Notification":
            message_data = json.loads(request.get("Message", "{}"))
            user_id = message_data.get("user_id")
            
            if user_id:
                # Send to connected WebSocket clients
                await manager.send_notification(user_id, message_data)
                
                # Mark notification as delivered
                notification_id = message_data.get("notification_id")
                if notification_id:
                    notification_crud.mark_as_delivered(db, notification_id)
                
                return {"message": "Notification sent"}
        
        return {"message": "Unknown message type"}
        
    except Exception as e:
        print(f"Error processing SNS webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process notification"
        )
