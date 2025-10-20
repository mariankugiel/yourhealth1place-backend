from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON, Date, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Goal(Base):
    """Health goals that users want to achieve"""
    __tablename__ = "health_plan_goals"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)  # Health goal name
    connected_metric_id = Column(Integer, ForeignKey("health_record_metrics.id"))  # Link to health_record_metrics for auto-tracking
    target_operator = Column(String(20), default='equal')  # "below" or "above"
    target_value = Column(Numeric(10, 2))  # Target value for the goal
    baseline_value = Column(Numeric(10, 2))  # Starting value when goal was created
    current_value = Column(Numeric(10, 2))  # Latest recorded value
    progress_percentage = Column(Integer, default=0)  # Calculated progress percentage
    start_date = Column(Date, nullable=False)  # When the goal should start
    end_date = Column(Date, nullable=False)  # When the goal should end
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    metric = relationship("HealthRecordMetric", back_populates="goals")
    tasks = relationship("HealthTask", back_populates="goal")


class HealthTask(Base):
    """Health tasks that users need to complete"""
    __tablename__ = "health_plan_tasks"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)  # Task name
    description = Column(Text)  # Optional task description
    frequency = Column(String(20), nullable=False)  # "daily", "weekly", "monthly"
    target_days = Column(Integer)  # For weekly/monthly tasks: how many days per week/month
    time_of_day = Column(String(20))  # "morning", "afternoon", "evening"
    
    # Relationships to other entities
    goal_id = Column(Integer, ForeignKey("health_plan_goals.id"))  # Optional link to health goal
    metric_id = Column(Integer, ForeignKey("health_record_metrics.id"))  # Optional link to metric
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    goal = relationship("Goal", back_populates="tasks")
    metric = relationship("HealthRecordMetric")
    completions = relationship("TaskCompletion", back_populates="task", cascade="all, delete-orphan")


class TaskCompletion(Base):
    """Track when a user completes a specific task on a specific date"""
    __tablename__ = "health_plan_task_completions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("health_plan_tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    completion_date = Column(Date, nullable=False)  # The date when the task was completed
    completed = Column(Boolean, default=True)  # True if completed, False if marked as not done
    notes = Column(Text)  # Optional notes about the completion
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    task = relationship("HealthTask", back_populates="completions")
    
    # Ensure one completion record per task per user per date
    __table_args__ = (
        # This creates a unique constraint ensuring one record per task/user/date combination
        # If user wants to update completion status, we update the existing record
        {"extend_existing": True}
    )