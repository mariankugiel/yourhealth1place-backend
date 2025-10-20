from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import logging

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.health_plans import HealthTask, TaskCompletion

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health-tasks", response_model=List[Dict[str, Any]])
async def get_health_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all health tasks for the current user"""
    try:
        if not current_user or not current_user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user authentication"
            )
        
        # Query tasks with metric information
        tasks = db.query(HealthTask).filter(
            HealthTask.created_by == current_user.id
        ).order_by(desc(HealthTask.created_at)).all()
        
        task_list = []
        for task in tasks:
            # Get metric information if metric_id exists
            metric_data = None
            if task.metric_id:
                from app.models.health_record import HealthRecordMetric
                metric = db.query(HealthRecordMetric).filter(
                    HealthRecordMetric.id == task.metric_id
                ).first()
                if metric:
                    metric_data = {
                        "id": metric.id,
                        "name": metric.name,
                        "display_name": metric.display_name,
                        "default_unit": metric.default_unit
                    }
            
            task_data = {
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "frequency": task.frequency,
                "target_days": task.target_days,
                "time_of_day": task.time_of_day,
                "goal_id": task.goal_id,
                "metric_id": task.metric_id,
                "metric": metric_data,  # Add metric information
                "target_operator": getattr(task, 'target_operator', None),
                "target_value": getattr(task, 'target_value', None),
                "target_unit": getattr(task, 'target_unit', None),
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                "created_by": task.created_by,
                "updated_by": task.updated_by
            }
            task_list.append(task_data)
        
        return task_list
    except Exception as e:
        logger.error(f"Failed to get health tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get health tasks: {str(e)}"
        )


@router.post("/health-tasks", response_model=Dict[str, Any])
async def create_health_task(
    task_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new health task"""
    try:
        if not current_user or not current_user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user authentication"
            )
        
        # Extract and validate task data
        name = task_data.get("name")
        frequency = task_data.get("frequency")
        time_of_day = task_data.get("time_of_day")
        target_days = task_data.get("target_days")
        goal_id = task_data.get("goal_id")
        metric_id = task_data.get("metric_id")
        target_operator = task_data.get("target_operator")
        target_value = task_data.get("target_value")
        target_unit = task_data.get("target_unit")
        
        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task name is required"
            )
        
        if not frequency:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task frequency is required"
            )
        
        if frequency not in ["daily", "weekly", "monthly"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Frequency must be 'daily', 'weekly', or 'monthly'"
            )
        
        # Create new task
        new_task = HealthTask(
            name=name,
            description=task_data.get("description"),
            frequency=frequency,
            target_days=target_days,
            time_of_day=time_of_day,
            goal_id=goal_id,
            metric_id=metric_id,
            created_by=current_user.id
        )
        
        # Add target fields if they exist
        if target_operator:
            setattr(new_task, 'target_operator', target_operator)
        if target_value:
            setattr(new_task, 'target_value', target_value)
        if target_unit:
            setattr(new_task, 'target_unit', target_unit)
        
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        return {
            "id": new_task.id,
            "name": new_task.name,
            "description": new_task.description,
            "frequency": new_task.frequency,
            "target_days": new_task.target_days,
            "time_of_day": new_task.time_of_day,
            "goal_id": new_task.goal_id,
            "metric_id": new_task.metric_id,
            "target_operator": getattr(new_task, 'target_operator', None),
            "target_value": getattr(new_task, 'target_value', None),
            "target_unit": getattr(new_task, 'target_unit', None),
            "created_at": new_task.created_at.isoformat() if new_task.created_at else None
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create health task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create health task: {str(e)}"
        )


@router.put("/health-tasks/{task_id}", response_model=Dict[str, Any])
async def update_health_task(
    task_id: int,
    task_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a health task"""
    try:
        if not current_user or not current_user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user authentication"
            )
        
        task = db.query(HealthTask).filter(
            HealthTask.id == task_id,
            HealthTask.created_by == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health task not found"
            )
        
        # Update task fields
        if "name" in task_data:
            task.name = task_data["name"]
        if "description" in task_data:
            task.description = task_data["description"]
        if "frequency" in task_data:
            task.frequency = task_data["frequency"]
        if "target_days" in task_data:
            task.target_days = task_data["target_days"]
        if "time_of_day" in task_data:
            task.time_of_day = task_data["time_of_day"]
        if "goal_id" in task_data:
            task.goal_id = task_data["goal_id"]
        if "metric_id" in task_data:
            task.metric_id = task_data["metric_id"]
        if "target_operator" in task_data:
            setattr(task, 'target_operator', task_data["target_operator"])
        if "target_value" in task_data:
            setattr(task, 'target_value', task_data["target_value"])
        if "target_unit" in task_data:
            setattr(task, 'target_unit', task_data["target_unit"])
        
        task.updated_by = current_user.id
        
        db.commit()
        db.refresh(task)
        
        return {
            "id": task.id,
            "name": task.name,
            "description": task.description,
            "frequency": task.frequency,
            "target_days": task.target_days,
            "time_of_day": task.time_of_day,
            "goal_id": task.goal_id,
            "metric_id": task.metric_id,
            "target_operator": getattr(task, 'target_operator', None),
            "target_value": getattr(task, 'target_value', None),
            "target_unit": getattr(task, 'target_unit', None),
            "updated_at": task.updated_at.isoformat() if task.updated_at else None
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update health task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update health task: {str(e)}"
        )


@router.delete("/health-tasks/{task_id}")
async def delete_health_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a health task"""
    try:
        if not current_user or not current_user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user authentication"
            )
        
        task = db.query(HealthTask).filter(
            HealthTask.id == task_id,
            HealthTask.created_by == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health task not found"
            )
        
        # Delete all task completion entries for this task
        db.query(TaskCompletion).filter(
            TaskCompletion.task_id == task_id,
            TaskCompletion.user_id == current_user.id
        ).delete()
        
        # Delete the task itself
        db.delete(task)
        db.commit()
        
        return {"message": "Health task deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete health task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete health task: {str(e)}"
        )


@router.get("/health-tasks/{task_id}/completions", response_model=List[Dict[str, Any]])
async def get_task_completions(
    task_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get task completions for a specific task"""
    try:
        if not current_user or not current_user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user authentication"
            )
        
        # Verify task belongs to user
        task = db.query(HealthTask).filter(
            HealthTask.id == task_id,
            HealthTask.created_by == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health task not found"
            )
        
        # Build query
        query = db.query(TaskCompletion).filter(
            TaskCompletion.task_id == task_id,
            TaskCompletion.user_id == current_user.id
        )
        
        if start_date:
            query = query.filter(TaskCompletion.completion_date >= datetime.strptime(start_date, "%Y-%m-%d").date())
        if end_date:
            query = query.filter(TaskCompletion.completion_date <= datetime.strptime(end_date, "%Y-%m-%d").date())
        
        completions = query.order_by(TaskCompletion.completion_date.desc()).all()
        
        completion_list = []
        for completion in completions:
            completion_data = {
                "id": completion.id,
                "task_id": completion.task_id,
                "user_id": completion.user_id,
                "completion_date": completion.completion_date.isoformat() if completion.completion_date else None,
                "completed": completion.completed,
                "notes": completion.notes,
                "created_at": completion.created_at.isoformat() if completion.created_at else None,
                "updated_at": completion.updated_at.isoformat() if completion.updated_at else None
            }
            completion_list.append(completion_data)
        
        return completion_list
        
    except Exception as e:
        logger.error(f"Failed to get task completions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task completions: {str(e)}"
        )


@router.post("/health-tasks/{task_id}/completions", response_model=Dict[str, Any])
async def create_task_completion(
    task_id: int,
    completion_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or update a task completion"""
    try:
        if not current_user or not current_user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user authentication"
            )
        
        # Verify task belongs to user
        task = db.query(HealthTask).filter(
            HealthTask.id == task_id,
            HealthTask.created_by == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health task not found"
            )
        
        completion_date = completion_data.get("completion_date")
        completed = completion_data.get("completed", True)
        notes = completion_data.get("notes")
        
        if not completion_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Completion date is required"
            )
        
        # Check if completion already exists for this date
        existing_completion = db.query(TaskCompletion).filter(
            TaskCompletion.task_id == task_id,
            TaskCompletion.user_id == current_user.id,
            TaskCompletion.completion_date == datetime.strptime(completion_date, "%Y-%m-%d").date()
        ).first()
        
        if existing_completion:
            # Update existing completion
            existing_completion.completed = completed
            if notes is not None:
                existing_completion.notes = notes
            db.commit()
            db.refresh(existing_completion)
            
            return {
                "id": existing_completion.id,
                "task_id": existing_completion.task_id,
                "user_id": existing_completion.user_id,
                "completion_date": existing_completion.completion_date.isoformat() if existing_completion.completion_date else None,
                "completed": existing_completion.completed,
                "notes": existing_completion.notes,
                "updated_at": existing_completion.updated_at.isoformat() if existing_completion.updated_at else None
            }
        else:
            # Create new completion
            new_completion = TaskCompletion(
                task_id=task_id,
                user_id=current_user.id,
                completion_date=datetime.strptime(completion_date, "%Y-%m-%d").date(),
                completed=completed,
                notes=notes
            )
            
            db.add(new_completion)
            db.commit()
            db.refresh(new_completion)
            
            return {
                "id": new_completion.id,
                "task_id": new_completion.task_id,
                "user_id": new_completion.user_id,
                "completion_date": new_completion.completion_date.isoformat() if new_completion.completion_date else None,
                "completed": new_completion.completed,
                "notes": new_completion.notes,
                "created_at": new_completion.created_at.isoformat() if new_completion.created_at else None
            }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create task completion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task completion: {str(e)}"
        )


@router.post("/health-tasks/{task_id}/completions/bulk", response_model=Dict[str, Any])
async def bulk_update_task_completions(
    task_id: int,
    bulk_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bulk update task completions"""
    try:
        if not current_user or not current_user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user authentication"
            )
        
        # Verify task belongs to user
        task = db.query(HealthTask).filter(
            HealthTask.id == task_id,
            HealthTask.created_by == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health task not found"
            )
        
        completions = bulk_data.get("completions", [])
        if not completions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Completions data is required"
            )
        
        updated_count = 0
        created_count = 0
        
        for completion_data in completions:
            completion_date = completion_data.get("completion_date")
            completed = completion_data.get("completed", True)
            notes = completion_data.get("notes")
            
            if not completion_date:
                continue
            
            # Check if completion already exists
            existing_completion = db.query(TaskCompletion).filter(
                TaskCompletion.task_id == task_id,
                TaskCompletion.user_id == current_user.id,
                TaskCompletion.completion_date == datetime.strptime(completion_date, "%Y-%m-%d").date()
            ).first()
            
            if existing_completion:
                # Update existing
                existing_completion.completed = completed
                if notes is not None:
                    existing_completion.notes = notes
                updated_count += 1
            else:
                # Create new
                new_completion = TaskCompletion(
                    task_id=task_id,
                    user_id=current_user.id,
                    completion_date=datetime.strptime(completion_date, "%Y-%m-%d").date(),
                    completed=completed,
                    notes=notes
                )
                db.add(new_completion)
                created_count += 1
        
        db.commit()
        
        return {
            "message": "Bulk update completed successfully",
            "updated": updated_count,
            "created": created_count,
            "total": updated_count + created_count
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to bulk update task completions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update task completions: {str(e)}"
        )


@router.get("/health-tasks/{task_id}/stats", response_model=Dict[str, Any])
async def get_task_completion_stats(
    task_id: int,
    period: str = "week",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get task completion statistics"""
    try:
        if not current_user or not current_user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user authentication"
            )
        
        # Verify task belongs to user
        task = db.query(HealthTask).filter(
            HealthTask.id == task_id,
            HealthTask.created_by == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health task not found"
            )
        
        # Calculate date range based on period
        today = date.today()
        if period == "week":
            start_date = today.replace(day=today.day - 6)  # Last 7 days
            total_days = 7
        elif period == "month":
            start_date = today.replace(day=1)  # First day of current month
            total_days = today.day
        elif period == "year":
            start_date = today.replace(month=1, day=1)  # First day of current year
            total_days = today.timetuple().tm_yday
        else:
            start_date = today.replace(day=today.day - 6)
            total_days = 7
        
        # Get completed days
        completed_completions = db.query(TaskCompletion).filter(
            TaskCompletion.task_id == task_id,
            TaskCompletion.user_id == current_user.id,
            TaskCompletion.completion_date >= start_date,
            TaskCompletion.completion_date <= today,
            TaskCompletion.completed == True
        ).all()
        
        completed_days = len(completed_completions)
        completion_rate = (completed_days / total_days * 100) if total_days > 0 else 0
        
        # Calculate streak
        streak = 0
        last_completed = None
        if completed_completions:
            # Sort by date descending
            sorted_completions = sorted(completed_completions, key=lambda x: x.completion_date, reverse=True)
            last_completed = sorted_completions[0].completion_date.isoformat()
            
            # Calculate streak from today backwards
            current_date = today
            for completion in sorted_completions:
                if completion.completion_date == current_date:
                    streak += 1
                    current_date = current_date.replace(day=current_date.day - 1)
                else:
                    break
        
        return {
            "total_days": total_days,
            "completed_days": completed_days,
            "completion_rate": round(completion_rate, 2),
            "streak": streak,
            "last_completed": last_completed
        }
        
    except Exception as e:
        logger.error(f"Failed to get task completion stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task completion stats: {str(e)}"
        )
