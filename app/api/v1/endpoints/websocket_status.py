"""
WebSocket Status Endpoints
API endpoints for checking user online status and WebSocket connection info
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_user
from app.websocket.connection_manager import manager
from app.websocket.notification_service import websocket_notification_service

router = APIRouter()

@router.get("/status")
async def get_user_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current user's WebSocket connection status"""
    try:
        status = await manager.get_user_status(current_user.id)
        connection_count = await manager.get_user_connection_count(current_user.id)
        
        return {
            "user_id": current_user.id,
            "status": status,
            "connection_count": connection_count,
            "is_online": status == "online"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user status: {str(e)}"
        )

@router.get("/connections")
async def get_user_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed information about user's WebSocket connections"""
    try:
        connection_info = await websocket_notification_service.get_user_connection_info(
            current_user.id, db
        )
        return connection_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get connection info: {str(e)}"
        )

@router.get("/online-users")
async def get_online_users(
    current_user: User = Depends(get_current_user)
) -> Dict[str, List[int]]:
    """Get list of all online users"""
    try:
        online_users = await manager.get_online_users()
        return {
            "online_users": online_users,
            "total_count": len(online_users)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get online users: {str(e)}"
        )

@router.get("/status/{user_id}")
async def get_specific_user_status(
    user_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get status of a specific user"""
    try:
        status = await manager.get_user_status(user_id)
        connection_count = await manager.get_user_connection_count(user_id)
        
        return {
            "user_id": user_id,
            "status": status,
            "connection_count": connection_count,
            "is_online": status == "online"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user status: {str(e)}"
        )

@router.post("/test-notification")
async def send_test_notification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Send a test notification to current user via WebSocket"""
    try:
        from app.models.notification import Notification, NotificationType, NotificationPriority
        
        # Create test notification
        test_notification = Notification(
            user_id=current_user.id,
            notification_type=NotificationType.SYSTEM_MESSAGE,
            title="🧪 Test Notification",
            message="This is a test notification sent via WebSocket",
            priority=NotificationPriority.NORMAL,
            status="pending"
        )
        db.add(test_notification)
        db.commit()
        db.refresh(test_notification)
        
        # Send via WebSocket
        sent = await websocket_notification_service.send_general_notification(test_notification, db)
        
        if sent:
            return {"message": "Test notification sent successfully via WebSocket"}
        else:
            return {"message": "Test notification created but no active WebSocket connections found"}
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test notification: {str(e)}"
        )

