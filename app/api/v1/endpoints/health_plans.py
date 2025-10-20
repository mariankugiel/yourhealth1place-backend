from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict, Any
from decimal import Decimal

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.health_tasks import router as health_tasks_router
from app.models.health_plans import Goal, HealthTask, TaskCompletion
from app.models.health_record import HealthRecord
from app.models.user import User

router = APIRouter()

# Include health tasks router
router.include_router(health_tasks_router, tags=["health-tasks"])


def calculate_progress(current_value: float, target_value: float, target_operator: str, baseline_value: float = None) -> int:
    """
    Calculate progress percentage for health goals
    
    Args:
        current_value: Current metric value
        target_value: Target value for the goal
        target_operator: "below" or "above"
        baseline_value: Starting value when goal was created
    
    Returns:
        Progress percentage (0-100)
    """
    if not current_value or not target_value:
        return 0
    
    if target_operator == "below":
        # Goal is to achieve a value below the target
        if current_value <= target_value:
            # Goal achieved or exceeded
            return 100
        else:
            # Calculate progress based on how much we've moved toward the target
            if baseline_value:
                total_distance = baseline_value - target_value
                current_distance = current_value - target_value
                progress = max(0, min(100, (total_distance - current_distance) / total_distance * 100))
                return int(progress)
            else:
                # Estimate baseline if not provided
                estimated_baseline = current_value + (current_value - target_value)
                total_distance = estimated_baseline - target_value
                current_distance = current_value - target_value
                progress = max(0, min(100, (total_distance - current_distance) / total_distance * 100))
                return int(progress)
    
    elif target_operator == "above":
        # Goal is to achieve a value above the target
        if current_value >= target_value:
            # Goal achieved or exceeded
            return 100
        else:
            # Calculate progress based on how much we've moved toward the target
            if baseline_value:
                total_distance = target_value - baseline_value
                current_distance = target_value - current_value
                progress = max(0, min(100, (total_distance - current_distance) / total_distance * 100))
                return int(progress)
            else:
                # Estimate baseline if not provided
                estimated_baseline = max(0, current_value - (target_value - current_value))
                total_distance = target_value - estimated_baseline
                current_distance = target_value - current_value
                progress = max(0, min(100, (total_distance - current_distance) / total_distance * 100))
                return int(progress)
    
    # Default case (should not happen with current implementation)
    return 0


@router.get("/health-goals", response_model=List[Dict[str, Any]])
async def get_health_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all health goals for the current user"""
    try:
        # Validate that the user exists and has an ID
        if not current_user or not current_user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user authentication"
            )
        
        goals = db.query(Goal).filter(Goal.created_by == current_user.id).order_by(desc(Goal.created_at)).all()
        
        goal_list = []
        for goal in goals:
            # Get the latest health record for this goal's metric
            current_value = None
            current_numeric_value = None
            if goal.connected_metric_id:
                latest_record = db.query(HealthRecord).filter(
                    HealthRecord.metric_id == goal.connected_metric_id,
                    HealthRecord.created_by == current_user.id
                ).order_by(desc(HealthRecord.recorded_at)).first()
                
                if latest_record:
                    # Get unit from the metric relationship
                    unit = latest_record.metric.default_unit if latest_record.metric else None
                    current_value = {
                        "value": latest_record.value,
                        "status": latest_record.status,
                        "unit": unit
                    }
                    current_numeric_value = float(latest_record.value) if latest_record.value else None
            
            # Calculate progress if we have the necessary values
            progress = 0
            if current_numeric_value and goal.target_value and goal.target_operator:
                progress = calculate_progress(
                    current_numeric_value,
                    float(goal.target_value),
                    goal.target_operator,
                    float(goal.baseline_value) if goal.baseline_value else None
                )
                
                # Update the goal's progress in the database
                goal.current_value = Decimal(str(current_numeric_value))
                goal.progress_percentage = progress
            
            goal_list.append({
                "id": goal.id,
                "name": goal.name,
                "target": {
                    "operator": goal.target_operator,
                    "value": float(goal.target_value) if goal.target_value else None
                },
                "current": current_value,
                "baseline_value": float(goal.baseline_value) if goal.baseline_value else None,
                "progress": progress,
                "start_date": goal.start_date.isoformat() if goal.start_date else None,
                "end_date": goal.end_date.isoformat() if goal.end_date else None,
                "created_at": goal.created_at.isoformat(),
                "metric_id": goal.connected_metric_id
            })
        
        # Commit progress updates
        db.commit()
        
        return goal_list
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve health goals: {str(e)}"
        )


@router.post("/health-goals", status_code=status.HTTP_201_CREATED)
async def create_health_goal(
    goal_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new health goal"""
    try:
        if not current_user or not current_user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user authentication"
            )
        
        # Parse target data
        target_data = goal_data.get("target", {})
        target_operator = target_data.get("operator", "equal")
        target_value = target_data.get("value")
        
        # Get baseline value from current metric value if available
        baseline_value = None
        if goal_data.get("metric_id"):
            latest_record = db.query(HealthRecord).filter(
                HealthRecord.metric_id == goal_data.get("metric_id"),
                HealthRecord.created_by == current_user.id
            ).order_by(desc(HealthRecord.recorded_at)).first()
            
            if latest_record:
                baseline_value = Decimal(str(latest_record.value))
        
        # Create new goal
        new_goal = Goal(
            name=goal_data.get("name"),
            connected_metric_id=goal_data.get("metric_id"),
            target_operator=target_operator,
            target_value=Decimal(str(target_value)) if target_value else None,
            baseline_value=baseline_value,
            start_date=goal_data.get("start_date"),
            end_date=goal_data.get("end_date"),
            created_by=current_user.id,
            updated_by=current_user.id
        )
        
        db.add(new_goal)
        db.commit()
        db.refresh(new_goal)
        
        return {
            "id": new_goal.id,
            "name": new_goal.name,
            "target": {
                "operator": new_goal.target_operator,
                "value": float(new_goal.target_value) if new_goal.target_value else None
            },
            "baseline_value": float(new_goal.baseline_value) if new_goal.baseline_value else None,
            "progress": 0,  # New goals start with 0 progress
            "start_date": new_goal.start_date.isoformat() if new_goal.start_date else None,
            "end_date": new_goal.end_date.isoformat() if new_goal.end_date else None,
            "created_at": new_goal.created_at.isoformat(),
            "metric_id": new_goal.connected_metric_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create health goal: {str(e)}"
        )


@router.put("/health-goals/{goal_id}")
async def update_health_goal(
    goal_id: int,
    goal_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a health goal"""
    try:
        if not current_user or not current_user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user authentication"
            )
        
        goal = db.query(Goal).filter(
            Goal.id == goal_id,
            Goal.created_by == current_user.id
        ).first()
        
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health goal not found"
            )
        
        # Update goal fields
        if "name" in goal_data:
            goal.name = goal_data["name"]
        if "metric_id" in goal_data:
            goal.connected_metric_id = goal_data["metric_id"]
        if "target" in goal_data:
            target_data = goal_data["target"]
            if "operator" in target_data:
                goal.target_operator = target_data["operator"]
            if "value" in target_data:
                goal.target_value = Decimal(str(target_data["value"])) if target_data["value"] else None
        if "start_date" in goal_data:
            goal.start_date = goal_data["start_date"]
        if "end_date" in goal_data:
            goal.end_date = goal_data["end_date"]
        
        goal.updated_by = current_user.id
        
        db.commit()
        db.refresh(goal)
        
        return {
            "id": goal.id,
            "name": goal.name,
            "target": {
                "operator": goal.target_operator,
                "value": float(goal.target_value) if goal.target_value else None
            },
            "baseline_value": float(goal.baseline_value) if goal.baseline_value else None,
            "progress": goal.progress_percentage or 0,
            "start_date": goal.start_date.isoformat() if goal.start_date else None,
            "end_date": goal.end_date.isoformat() if goal.end_date else None,
            "created_at": goal.created_at.isoformat(),
            "metric_id": goal.connected_metric_id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update health goal: {str(e)}"
        )


@router.delete("/health-goals/{goal_id}")
async def delete_health_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a health goal"""
    try:
        if not current_user or not current_user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user authentication"
            )
        
        goal = db.query(Goal).filter(
            Goal.id == goal_id,
            Goal.created_by == current_user.id
        ).first()
        
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health goal not found"
            )
        
        db.delete(goal)
        db.commit()
        
        return {"message": "Health goal deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete health goal: {str(e)}"
        )


@router.post("/health-goals/{goal_id}/update-progress")
async def update_goal_progress(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update progress for a specific health goal"""
    try:
        if not current_user or not current_user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user authentication"
            )
        
        goal = db.query(Goal).filter(
            Goal.id == goal_id,
            Goal.created_by == current_user.id
        ).first()
        
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health goal not found"
            )
        
        # Get the latest health record for this goal's metric
        current_numeric_value = None
        if goal.connected_metric_id:
            latest_record = db.query(HealthRecord).filter(
                HealthRecord.metric_id == goal.connected_metric_id,
                HealthRecord.created_by == current_user.id
            ).order_by(desc(HealthRecord.recorded_at)).first()
            
            if latest_record:
                current_numeric_value = float(latest_record.value) if latest_record.value else None
        
        # Calculate progress if we have the necessary values
        progress = 0
        if current_numeric_value and goal.target_value and goal.target_operator:
            progress = calculate_progress(
                current_numeric_value,
                float(goal.target_value),
                goal.target_operator,
                float(goal.baseline_value) if goal.baseline_value else None
            )
            
            # Update the goal's progress in the database
            goal.current_value = Decimal(str(current_numeric_value))
            goal.progress_percentage = progress
            goal.updated_by = current_user.id
        
        db.commit()
        db.refresh(goal)
        
        return {
            "id": goal.id,
            "progress": progress,
            "current_value": float(goal.current_value) if goal.current_value else None,
            "updated_at": goal.updated_at.isoformat() if goal.updated_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update goal progress: {str(e)}"
        )