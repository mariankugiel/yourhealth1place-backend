from sqlalchemy import Column, Integer, String, DateTime, Time, Text, ForeignKey, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class ReminderStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    DELETED = "deleted"

class MedicationReminder(Base):
    __tablename__ = "medication_reminders"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Time Configuration (user's local time)
    reminder_time = Column(Time, nullable=False)  # e.g., 08:00:00 (local time)
    user_timezone = Column(String(50), nullable=False)  # e.g., "America/New_York"
    days_of_week = Column(JSON, nullable=False)  # ["monday", "tuesday", ...]
    
    # Next scheduled notification (pre-calculated in UTC)
    next_scheduled_at = Column(DateTime(timezone=True), index=True)
    last_sent_at = Column(DateTime(timezone=True))
    
    # Status
    status = Column(SQLEnum(ReminderStatus), nullable=False, default=ReminderStatus.ACTIVE, index=True)
    enabled = Column(Boolean, nullable=False, default=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    medication = relationship("Medication", backref="reminders")
    user = relationship("User", backref="medication_reminders")
    
    def __repr__(self):
        return f"<MedicationReminder(id={self.id}, user_id={self.user_id}, time={self.reminder_time})>"

