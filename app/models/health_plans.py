from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class HealthPlan(Base):
    __tablename__ = "health_plans"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Doctor who created the plan
    title = Column(String(200), nullable=False)
    description = Column(Text)
    plan_type = Column(String(50), nullable=False)  # "treatment", "prevention", "rehabilitation", "lifestyle"
    is_template = Column(Boolean, default=False)  # Can be assigned to multiple patients
    status = Column(String(50), nullable=False, default="DRAFT")  # "DRAFT", "ACTIVE", "INACTIVE"
    priority = Column(String(20), default="MEDIUM")  # "LOW", "MEDIUM", "HIGH", "URGENT"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Usually same as doctor_id
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    doctor = relationship("User", foreign_keys=[doctor_id], backref="created_health_plans")
    assignments = relationship("HealthPlanAssignment", back_populates="health_plan")
    goals = relationship("Goal", back_populates="health_plan")
    recommendations = relationship("HealthPlanRecommendation", back_populates="health_plan")
    appointments = relationship("Appointment", back_populates="health_plan")
    tasks = relationship("Task", back_populates="health_plan")
    plan_progress = relationship("HealthPlanProgress", back_populates="health_plan")

class HealthPlanAssignment(Base):
    __tablename__ = "health_plan_assignments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    health_plan_id = Column(Integer, ForeignKey("health_plans.id"), nullable=False)  # Link to doctor's plan
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Patient assigned to this plan
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Doctor who assigned the plan
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    status = Column(String(50), nullable=False, default="ACTIVE")  # "ACTIVE", "COMPLETED", "PAUSED", "CANCELLED"
    notes = Column(Text)  # Doctor's notes for this specific patient
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    health_plan = relationship("HealthPlan", back_populates="assignments")
    patient = relationship("User", foreign_keys=[patient_id], backref="health_plan_assignments")
    assigned_by_professional = relationship("User", foreign_keys=[assigned_by], backref="assigned_health_plans")

class Goal(Base):
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    goal_type = Column(String(50), nullable=False)  # "numeric", "boolean", "frequency", "duration"
    target_value = Column(JSON, nullable=False)  # {value: 70, unit: "kg"} or {frequency: "daily", count: 3}
    current_value = Column(JSON)  # Current progress
    progress_percentage = Column(Integer, default=0)
    status = Column(String(50), nullable=False, default="ACTIVE")  # "ACTIVE", "COMPLETED", "FAILED"
    priority = Column(String(20), default="MEDIUM")
    due_date = Column(Date)
    auto_track = Column(Boolean, default=True)  # Auto-update from health records
    metric_id = Column(Integer, ForeignKey("health_record_metrics.id"))  # Link to health_record_metrics for auto-tracking
    
    # Goal Ownership
    owner_type = Column(String(20), nullable=False)  # "doctor", "patient"
    owner_id = Column(Integer, nullable=False)  # doctor_id or patient_id
    health_plan_id = Column(Integer, ForeignKey("health_plans.id"))  # Link to doctor's plan (if doctor-created)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    health_plan = relationship("HealthPlan", back_populates="goals")
    metric = relationship("HealthRecordMetric", back_populates="goals")
    tracking = relationship("GoalTracking", back_populates="goal")
    tracking_details = relationship("GoalTrackingDetail", back_populates="goal")
    tasks = relationship("Task", back_populates="goal")

class GoalTracking(Base):
    __tablename__ = "goal_tracking"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tracking_date = Column(Date, nullable=False)  # The date being tracked
    target_count = Column(Integer, nullable=False)  # How many times should be done (e.g., 3)
    completed_count = Column(Integer, default=0)  # How many times actually done
    status = Column(String(50), nullable=False, default="PENDING")  # "PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"
    notes = Column(Text)  # Any notes for this day
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    goal = relationship("Goal", back_populates="tracking")
    patient = relationship("User", foreign_keys=[patient_id], backref="goal_tracking")
    details = relationship("GoalTrackingDetail", back_populates="goal_tracking")

class GoalTrackingDetail(Base):
    __tablename__ = "goal_tracking_details"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    goal_tracking_id = Column(Integer, ForeignKey("goal_tracking.id"), nullable=False)  # Link to goal_tracking
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    measurement_time = Column(DateTime, nullable=False)  # When this specific measurement was taken
    measurement_value = Column(JSON)  # The actual measurement value
    health_record_id = Column(Integer, ForeignKey("health_records.id"))  # Link to health_records if applicable
    notes = Column(Text)  # Any notes about this measurement
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Who recorded this measurement
    
    # Relationships
    goal_tracking = relationship("GoalTracking", back_populates="details")
    goal = relationship("Goal", back_populates="tracking_details")
    patient = relationship("User", foreign_keys=[patient_id], backref="goal_tracking_details")
    health_record = relationship("HealthRecord", back_populates="goal_tracking_details")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    task_type = Column(String(50), nullable=False)  # "medication", "exercise", "diet", "appointment", "measurement"
    frequency = Column(String(20), nullable=False)  # "once", "daily", "weekly", "monthly"
    total_count = Column(Integer, nullable=False)  # Total times to complete
    completed_count = Column(Integer, default=0)
    target_value = Column(JSON)  # {dosage: "10mg", frequency: "twice_daily"}
    due_date = Column(Date)
    status = Column(String(50), nullable=False, default="PENDING")  # "PENDING", "IN_PROGRESS", "COMPLETED", "SKIPPED"
    
    # Task Ownership
    owner_type = Column(String(20), nullable=False)  # "doctor", "patient"
    owner_id = Column(Integer, nullable=False)  # doctor_id or patient_id
    goal_id = Column(Integer, ForeignKey("goals.id"))  # Optional link to specific goal
    health_plan_id = Column(Integer, ForeignKey("health_plans.id"))  # Link to doctor's plan (if doctor-created)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    goal = relationship("Goal", back_populates="tasks")
    health_plan = relationship("HealthPlan", back_populates="tasks")
    tracking = relationship("TaskTracking", back_populates="task")
    tracking_details = relationship("TaskTrackingDetail", back_populates="task")

class TaskTracking(Base):
    __tablename__ = "task_tracking"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tracking_date = Column(Date, nullable=False)  # The date being tracked
    target_count = Column(Integer, nullable=False)  # How many times should be done today
    completed_count = Column(Integer, default=0)  # How many times actually done today
    status = Column(String(50), nullable=False, default="PENDING")  # "PENDING", "IN_PROGRESS", "COMPLETED", "FAILED", "SKIPPED"
    notes = Column(Text)  # Any notes for this day
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    task = relationship("Task", back_populates="tracking")
    patient = relationship("User", foreign_keys=[patient_id], backref="task_tracking")
    details = relationship("TaskTrackingDetail", back_populates="task_tracking")

class TaskTrackingDetail(Base):
    __tablename__ = "task_tracking_details"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_tracking_id = Column(Integer, ForeignKey("task_tracking.id"), nullable=False)  # Link to task_tracking
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    completion_time = Column(DateTime, nullable=False)  # When this specific task was completed
    completion_value = Column(JSON)  # Any data about the completion (e.g., actual dosage taken)
    health_record_id = Column(Integer, ForeignKey("health_records.id"))  # Link to health_records if applicable
    notes = Column(Text)  # Any notes about this completion
    skipped_reason = Column(Text)  # If task was skipped, why?
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Who marked this as completed
    
    # Relationships
    task_tracking = relationship("TaskTracking", back_populates="details")
    task = relationship("Task", back_populates="tracking_details")
    patient = relationship("User", foreign_keys=[patient_id], backref="task_tracking_details")
    health_record = relationship("HealthRecord", back_populates="task_tracking_details")

class HealthPlanRecommendation(Base):
    __tablename__ = "health_plan_recommendations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    health_plan_id = Column(Integer, ForeignKey("health_plans.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    recommendation_type = Column(String(50), nullable=False)  # "lifestyle", "medication", "exercise", "diet", "monitoring"
    priority = Column(String(20), default="MEDIUM")
    source = Column(String(100))  # "doctor", "ai", "guidelines"
    is_implemented = Column(Boolean, default=False)
    implementation_date = Column(Date)
    effectiveness_rating = Column(Integer)  # 1-5 scale
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    health_plan = relationship("HealthPlan", back_populates="recommendations") 