from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.notification import Notification, NotificationType, NotificationStatus
from app.schemas.notification import NotificationCreate, NotificationUpdate

class NotificationCRUD:
    
    def create_notification(self, db: Session, notification: NotificationCreate) -> Notification:
        """Create a new notification"""
        db_notification = Notification(
            user_id=notification.user_id,
            notification_type=notification.notification_type,
            title=notification.title,
            message=notification.message,
            medication_id=notification.medication_id,
            appointment_id=notification.appointment_id,
            data=notification.data,
            status=NotificationStatus.UNREAD
        )
        
        db.add(db_notification)
        db.commit()
        db.refresh(db_notification)
        return db_notification
    
    def get_notification(self, db: Session, notification_id: int, user_id: int) -> Optional[Notification]:
        """Get a specific notification by ID"""
        return db.query(Notification).filter(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        ).first()
    
    def get_user_notifications(
        self, 
        db: Session, 
        user_id: int, 
        status: Optional[NotificationStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """Get notifications for a user with optional filtering"""
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        if status:
            query = query.filter(Notification.status == status)
        
        return query.order_by(desc(Notification.created_at)).offset(offset).limit(limit).all()
    
    def get_unread_count(self, db: Session, user_id: int) -> int:
        """Get count of unread notifications for a user"""
        return db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.status == NotificationStatus.UNREAD
            )
        ).count()
    
    def mark_as_read(self, db: Session, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read"""
        notification = self.get_notification(db, notification_id, user_id)
        if not notification:
            return False
        
        notification.status = NotificationStatus.READ
        notification.read_at = datetime.utcnow()
        db.commit()
        return True
    
    def mark_as_delivered(self, db: Session, notification_id: int) -> bool:
        """Mark a notification as delivered"""
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            return False
        
        notification.delivered_at = datetime.utcnow()
        db.commit()
        return True
    
    def update_notification(self, db: Session, notification_id: int, user_id: int, update_data: NotificationUpdate) -> Optional[Notification]:
        """Update a notification"""
        notification = self.get_notification(db, notification_id, user_id)
        if not notification:
            return None
        
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(notification, field, value)
        
        db.commit()
        db.refresh(notification)
        return notification
    
    def delete_old_notifications(self, db: Session, days_old: int = 30) -> int:
        """Delete old read notifications"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        deleted_count = db.query(Notification).filter(
            and_(
                Notification.status == NotificationStatus.READ,
                Notification.created_at < cutoff_date
            )
        ).delete()
        
        db.commit()
        return deleted_count
    
    def create_medication_reminder_notification(
        self,
        db: Session,
        user_id: int,
        medication_id: int,
        medication_name: str,
        dosage: str,
        frequency: str
    ) -> Notification:
        """Create a medication reminder notification"""
        notification_data = {
            "medication_id": medication_id,
            "medication_name": medication_name,
            "dosage": dosage,
            "frequency": frequency,
            "reminder_time": datetime.utcnow().isoformat()
        }
        
        notification = NotificationCreate(
            user_id=user_id,
            notification_type=NotificationType.MEDICATION_REMINDER,
            title=f"Time to take {medication_name}",
            message=f"Remember to take your {medication_name} ({dosage})",
            medication_id=medication_id,
            data=notification_data
        )
        
        return self.create_notification(db, notification)

# Create instance
notification_crud = NotificationCRUD()
