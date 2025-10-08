from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, time, timedelta
import pytz
from app.models.medication_reminder import MedicationReminder, ReminderStatus
from app.models.user import User
from app.schemas.medication_reminder import MedicationReminderCreate, MedicationReminderUpdate

class MedicationReminderCRUD:
    
    async def create_reminder(self, db: Session, reminder: MedicationReminderCreate, user_id: int) -> MedicationReminder:
        """
        Create a new medication reminder
        
        NOTE: user_timezone is NOT sent from frontend
        - Gets timezone from Supabase user profile
        - Falls back to UTC if timezone not found in Supabase
        """
        # Get user timezone from Supabase profile
        user = db.query(User).filter(User.id == user_id).first()
        user_timezone = "UTC"  # Default fallback
        
        if user and user.supabase_user_id:
            try:
                from app.core.supabase_client import supabase_service
                # Get timezone from Supabase user profile
                profile_data = await supabase_service.get_user_profile(user.supabase_user_id)
                user_timezone = profile_data.get("timezone", "UTC")
            except Exception as e:
                print(f"Warning: Could not get timezone from Supabase for user {user_id}: {e}")
                user_timezone = "UTC"
        
        db_reminder = MedicationReminder(
            medication_id=reminder.medication_id,
            user_id=user_id,
            reminder_time=reminder.reminder_time,
            user_timezone=user_timezone,  # From user profile, not frontend
            days_of_week=reminder.days_of_week,
            enabled=reminder.enabled,
            status=ReminderStatus.ACTIVE
        )
        
        # Calculate next scheduled time
        db_reminder.next_scheduled_at = self._calculate_next_scheduled_time(
            reminder.reminder_time,
            reminder.days_of_week,
            user_timezone
        )
        
        db.add(db_reminder)
        db.commit()
        db.refresh(db_reminder)
        return db_reminder
    
    def get_reminder(self, db: Session, reminder_id: int, user_id: int) -> Optional[MedicationReminder]:
        """Get a specific reminder by ID"""
        return db.query(MedicationReminder).filter(
            and_(
                MedicationReminder.id == reminder_id,
                MedicationReminder.user_id == user_id
            )
        ).first()
    
    def get_user_reminders(self, db: Session, user_id: int, medication_id: Optional[int] = None) -> List[MedicationReminder]:
        """Get all reminders for a user, optionally filtered by medication"""
        query = db.query(MedicationReminder).filter(
            and_(
                MedicationReminder.user_id == user_id,
                MedicationReminder.status != ReminderStatus.DELETED
            )
        )
        
        if medication_id:
            query = query.filter(MedicationReminder.medication_id == medication_id)
        
        return query.all()
    
    def get_due_reminders(self, db: Session, check_window_minutes: int = 5) -> List[MedicationReminder]:
        """Get reminders that are due within the next check_window_minutes"""
        now = datetime.utcnow()
        check_window = now + timedelta(minutes=check_window_minutes)
        
        return db.query(MedicationReminder).filter(
            and_(
                MedicationReminder.enabled == True,
                MedicationReminder.status == ReminderStatus.ACTIVE,
                MedicationReminder.next_scheduled_at <= check_window,
                MedicationReminder.next_scheduled_at > now
            )
        ).all()
    
    def update_reminder(self, db: Session, reminder_id: int, user_id: int, update_data: MedicationReminderUpdate) -> Optional[MedicationReminder]:
        """Update a reminder"""
        reminder = self.get_reminder(db, reminder_id, user_id)
        if not reminder:
            return None
        
        update_dict = update_data.dict(exclude_unset=True)
        
        # If time or days changed, recalculate next scheduled time
        if 'reminder_time' in update_dict or 'days_of_week' in update_dict:
            reminder_time = update_dict.get('reminder_time', reminder.reminder_time)
            days_of_week = update_dict.get('days_of_week', reminder.days_of_week)
            user_timezone = reminder.user_timezone
            
            reminder.next_scheduled_at = self._calculate_next_scheduled_time(
                reminder_time, days_of_week, user_timezone
            )
        
        for field, value in update_dict.items():
            setattr(reminder, field, value)
        
        db.commit()
        db.refresh(reminder)
        return reminder
    
    def delete_reminder(self, db: Session, reminder_id: int, user_id: int) -> bool:
        """Soft delete a reminder"""
        reminder = self.get_reminder(db, reminder_id, user_id)
        if not reminder:
            return False
        
        reminder.status = ReminderStatus.DELETED
        reminder.enabled = False
        db.commit()
        return True
    
    def mark_reminder_sent(self, db: Session, reminder_id: int) -> bool:
        """
        Mark a reminder as sent and calculate next occurrence
        
        NOTE: Weekly recurring reminders
        - If user selects "Monday", reminder repeats EVERY Monday
        - Next occurrence will be calculated for the next available day in days_of_week
        """
        reminder = db.query(MedicationReminder).filter(MedicationReminder.id == reminder_id).first()
        if not reminder:
            return False
        
        reminder.last_sent_at = datetime.utcnow()
        # Calculate next occurrence (next week on same day)
        reminder.next_scheduled_at = self._calculate_next_scheduled_time(
            reminder.reminder_time,
            reminder.days_of_week,
            reminder.user_timezone
        )
        
        db.commit()
        return True
    
    def _calculate_next_scheduled_time(self, reminder_time: time, days_of_week: List[str], user_timezone: str) -> Optional[datetime]:
        """
        Calculate the next UTC time when the reminder should be sent
        
        NOTE: Creates WEEKLY recurring reminders
        - If days_of_week = ["monday"], reminder repeats EVERY Monday
        - Checks next 7 days to find the next occurrence
        """
        try:
            user_tz = pytz.timezone(user_timezone)
            utc_tz = pytz.UTC
            
            # Get current time in user's timezone
            now_user_tz = datetime.now(user_tz)
            
            # Check next 7 days for a valid reminder time
            for i in range(7):
                check_date = now_user_tz + timedelta(days=i)
                day_name = check_date.strftime('%A').lower()
                
                if day_name in days_of_week:
                    # Create the reminder datetime for this day
                    reminder_datetime = user_tz.localize(
                        datetime.combine(check_date.date(), reminder_time)
                    )
                    
                    # Only use this if it's in the future
                    if reminder_datetime > now_user_tz:
                        # Convert to UTC
                        return reminder_datetime.astimezone(utc_tz).replace(tzinfo=None)
            
            return None
            
        except Exception as e:
            print(f"Error calculating next scheduled time: {e}")
            return None

# Create instance
medication_reminder_crud = MedicationReminderCRUD()
