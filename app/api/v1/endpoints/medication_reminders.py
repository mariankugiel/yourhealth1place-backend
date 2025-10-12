from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import boto3
import json
import os

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.medication_reminder import (
    MedicationReminderCreate,
    MedicationReminderUpdate,
    MedicationReminderResponse,
    MedicationReminderWithMedication
)
from app.crud.medication_reminder import medication_reminder_crud
from app.models.notification import Notification, NotificationType, NotificationStatus, NotificationPriority
from app.models.notification_channel import NotificationChannel
from app.models.websocket_connection import WebSocketConnection
from app.models.medication import Medication
from app.websocket.notification_service import websocket_notification_service

router = APIRouter()

# Initialize SQS client with explicit region
sqs_client = boto3.client('sqs', region_name=settings.AWS_REGION)

@router.post("/", response_model=MedicationReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_medication_reminder(
    reminder: MedicationReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new medication reminder"""
    try:
        db_reminder = await medication_reminder_crud.create_reminder(
            db=db,
            reminder=reminder,
            user_id=current_user.id
        )
        return db_reminder
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create reminder: {str(e)}"
        )

@router.get("/", response_model=List[MedicationReminderWithMedication])
async def get_medication_reminders(
    medication_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all medication reminders for the current user"""
    reminders = medication_reminder_crud.get_user_reminders(
        db=db,
        user_id=current_user.id,
        medication_id=medication_id
    )
    
    # Add medication details
    result = []
    for reminder in reminders:
        reminder_dict = {
            "id": reminder.id,
            "medication_id": reminder.medication_id,
            "user_id": reminder.user_id,
            "reminder_time": reminder.reminder_time,
            "user_timezone": reminder.user_timezone,
            "days_of_week": reminder.days_of_week,
            "enabled": reminder.enabled,
            "next_scheduled_at": reminder.next_scheduled_at,
            "last_sent_at": reminder.last_sent_at,
            "status": reminder.status,
            "created_at": reminder.created_at,
            "updated_at": reminder.updated_at,
            "medication_name": reminder.medication.medication_name if reminder.medication else None
        }
        result.append(reminder_dict)
    
    return result

@router.get("/{reminder_id}", response_model=MedicationReminderResponse)
async def get_medication_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific medication reminder"""
    reminder = medication_reminder_crud.get_reminder(
        db=db,
        reminder_id=reminder_id,
        user_id=current_user.id
    )
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    
    return reminder

@router.put("/{reminder_id}", response_model=MedicationReminderResponse)
async def update_medication_reminder(
    reminder_id: int,
    reminder_update: MedicationReminderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a medication reminder"""
    updated_reminder = medication_reminder_crud.update_reminder(
        db=db,
        reminder_id=reminder_id,
        user_id=current_user.id,
        update_data=reminder_update
    )
    
    if not updated_reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    
    return updated_reminder

@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medication_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a medication reminder"""
    success = medication_reminder_crud.delete_reminder(
        db=db,
        reminder_id=reminder_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )

@router.post("/{reminder_id}/toggle", response_model=MedicationReminderResponse)
async def toggle_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle a reminder on/off"""
    reminder = medication_reminder_crud.get_reminder(
        db=db,
        reminder_id=reminder_id,
        user_id=current_user.id
    )
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    
    # Toggle the enabled status
    update_data = MedicationReminderUpdate(enabled=not reminder.enabled)
    updated_reminder = medication_reminder_crud.update_reminder(
        db=db,
        reminder_id=reminder_id,
        user_id=current_user.id,
        update_data=update_data
    )
    
    return updated_reminder

@router.get("/medications/{medication_id}/reminders", response_model=List[MedicationReminderResponse])
async def get_medication_reminders_by_medication(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all reminders for a specific medication"""
    reminders = medication_reminder_crud.get_user_reminders(
        db=db,
        user_id=current_user.id,
        medication_id=medication_id
    )
    
    return reminders

# ============================================================================
# LAMBDA ENDPOINT - Called by EventBridge Dispatcher
# ============================================================================

@router.post("/check-due")
async def check_due_reminders(
    request: Dict[str, Any],
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Check for due medication reminders and send notifications
    
    Called by Lambda Dispatcher every 5 minutes
    Authorization: Bearer token (LAMBDA_API_TOKEN)
    
    NOTE: This endpoint is called by Lambda, not by users
    """
    
    # Verify Lambda authentication
    expected_token = os.getenv("LAMBDA_API_TOKEN", "your-lambda-webhook-token")
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
    
    print(f"🔔 Checking due reminders at {datetime.utcnow().isoformat()}")
    
    # Get due reminders
    check_window_minutes = request.get('check_window_minutes', 5)
    due_reminders = medication_reminder_crud.get_due_reminders(
        db=db,
        check_window_minutes=check_window_minutes
    )
    
    print(f"📋 Found {len(due_reminders)} due reminders")
    
    processed_count = 0
    
    for reminder in due_reminders:
        try:
            # Get medication details for dynamic message
            medication = db.query(Medication).filter(Medication.id == reminder.medication_id).first()
            if not medication:
                print(f"⚠️ Medication {reminder.medication_id} not found for reminder {reminder.id}")
                continue
            
            # Create dynamic notification message
            notification_title = f"💊 Time to take {medication.medication_name}"
            notification_message = f"It's time to take your {medication.medication_name}"
            
            # Create notification record
            notification = Notification(
                user_id=reminder.user_id,
                notification_type=NotificationType.MEDICATION_REMINDER,
                title=notification_title,
                message=notification_message,
                priority=NotificationPriority.NORMAL,
                medication_id=reminder.medication_id,
                scheduled_at=reminder.next_scheduled_at,
                status=NotificationStatus.PENDING,
                data={
                    "medication_name": medication.medication_name,
                    "medication_type": medication.medication_type.value,
                    "reminder_id": reminder.id,
                    "reminder_time": reminder.reminder_time.isoformat(),
                    "user_timezone": reminder.user_timezone
                }
            )
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            print(f"✅ Created notification {notification.id} for user {reminder.user_id}")
            
            # Get user details for email
            user = db.query(User).filter(User.id == reminder.user_id).first()
            if not user or not user.email:
                print(f"⚠️ User {reminder.user_id} has no email address")
                continue
            
            # Get user's notification preferences
            user_channels = db.query(NotificationChannel).filter(
                NotificationChannel.user_id == reminder.user_id
            ).first()
            
            email_sent = False
            
            # Send via Email (PRIMARY CHANNEL for medication reminders)
            if not user_channels or user_channels.email_enabled:
                try:
                    send_to_email_queue(
                        notification_id=notification.id,
                        user_id=reminder.user_id,
                        email_address=user.email,
                        title=notification_title,
                        message=notification_message,
                        priority=notification.priority.value,
                        metadata={
                            "medication_name": medication.medication_name,
                            "medication_type": medication.medication_type.value,
                            "dosage": medication.dosage,
                            "frequency": medication.frequency,
                            "reminder_id": reminder.id,
                            "reminder_time": reminder.reminder_time.isoformat(),
                            "user_timezone": reminder.user_timezone
                        }
                    )
                    email_sent = True
                    print(f"📧 Queued email reminder for user {reminder.user_id} ({user.email})")
                except Exception as e:
                    print(f"❌ Failed to queue email: {e}")
                    # Continue processing - we'll still mark as sent if email was queued
            
            # NOTE: WebSocket reminders are DISABLED for medication reminders
            # WebSocket is still used for messages and other real-time notifications
            # To re-enable, uncomment the code below:
            # 
            # if not user_channels or user_channels.websocket_enabled:
            #     websocket_sent = await websocket_notification_service.send_medication_reminder(notification, db)
            #     if websocket_sent:
            #         print(f"📡 Sent medication reminder via WebSocket to user {reminder.user_id}")
            
            # Update notification status
            if email_sent:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
                db.commit()
            else:
                print(f"⚠️ No notification channels available for user {reminder.user_id}")
                notification.status = NotificationStatus.FAILED
                db.commit()
                continue
            
            # Mark reminder as sent and calculate next occurrence
            medication_reminder_crud.mark_reminder_sent(db, reminder.id)
            
            processed_count += 1
            print(f"✅ Processed reminder {reminder.id} for user {reminder.user_id}")
            
        except Exception as e:
            print(f"❌ Error processing reminder {reminder.id}: {e}")
            db.rollback()
            continue
    
    return {
        "processed_count": processed_count,
        "total_due": len(due_reminders),
        "timestamp": datetime.utcnow().isoformat()
    }

def send_to_email_queue(notification_id: int, user_id: int, email_address: str,
                        title: str, message: str, priority: str, metadata: dict):
    """Send notification to Email SQS queue"""
    try:
        queue_url = os.environ.get('SQS_EMAIL_QUEUE_URL')
        if not queue_url:
            raise ValueError("SQS_EMAIL_QUEUE_URL environment variable not set")
        
        message_body = {
            'notification_id': notification_id,
            'user_id': user_id,
            'email_address': email_address,
            'title': title,
            'message': message,
            'priority': priority,
            'notification_type': 'medication_reminder',
            'metadata': metadata
        }
        
        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body),
            MessageGroupId=f"user-{user_id}",
            MessageDeduplicationId=f"notification-{notification_id}-{datetime.utcnow().isoformat()}"
        )
        
        print(f"📤 Sent to Email queue: notification {notification_id} for user {user_id}")
        print(f"   SQS MessageId: {response.get('MessageId')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to send to Email queue: {e}")
        raise

def send_to_websocket_queue(notification_id: int, user_id: int, connection_id: str, 
                             title: str, message: str, priority: str, 
                             notification_type: str, metadata: dict):
    """Send notification to WebSocket SQS queue"""
    try:
        queue_url = os.environ['SQS_WEBSOCKET_QUEUE_URL']
        
        message_body = {
            'notification_id': notification_id,
            'user_id': user_id,
            'connection_id': connection_id,
            'title': title,
            'message': message,
            'priority': priority,
            'notification_type': notification_type,
            'metadata': metadata
        }
        
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body),
            MessageGroupId=f"user-{user_id}",
            MessageDeduplicationId=f"notification-{notification_id}-{connection_id}"
        )
        
        print(f"📤 Sent to WebSocket queue: notification {notification_id} for connection {connection_id}")
        
    except Exception as e:
        print(f"❌ Failed to send to WebSocket queue: {e}")
        raise
