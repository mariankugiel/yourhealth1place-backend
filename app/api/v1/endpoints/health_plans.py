from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.crud.health_plan import health_plan_crud
from app.schemas.health_plan import (
    HealthPlan, 
    HealthPlanCreate, 
    HealthPlanUpdate, 
    HealthPlanList,
    HealthPlanWithRelations
)
from app.core.security import get_current_user

router = APIRouter()

@router.post("/", response_model=HealthPlan, status_code=status.HTTP_201_CREATED)
def create_health_plan(
    health_plan_data: HealthPlanCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new health plan"""
    # Verify that the professional exists and belongs to current user
    professional = professional_crud.get_by_user_id(db, current_user.id)
    if not professional or professional.id != health_plan_data.professional_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create health plans for this professional"
        )
    
    return health_plan_crud.create(db, health_plan_data)

@router.get("/", response_model=HealthPlanList)
def get_health_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    professional_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    status: Optional[str] = None,
    plan_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get health plans with optional filters"""
    health_plans = health_plan_crud.get_all(
        db, skip, limit, professional_id, patient_id, status, plan_type
    )
    
    total = len(health_plans)  # In a real app, you'd get total count separately
    
    return HealthPlanList(
        health_plans=health_plans,
        total=total,
        page=skip // limit + 1,
        size=limit
    )

@router.get("/{health_plan_id}", response_model=HealthPlanWithRelations)
def get_health_plan(
    health_plan_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get health plan by ID"""
    health_plan = health_plan_crud.get_by_id(db, health_plan_id)
    if not health_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health plan not found"
        )
    return health_plan

@router.put("/{health_plan_id}", response_model=HealthPlan)
def update_health_plan(
    health_plan_id: int,
    health_plan_data: HealthPlanUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update health plan"""
    # Verify that the health plan belongs to the current professional
    health_plan = health_plan_crud.get_by_id(db, health_plan_id)
    if not health_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health plan not found"
        )
    
    professional = professional_crud.get_by_user_id(db, current_user.id)
    if not professional or health_plan.professional_id != professional.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this health plan"
        )
    
    updated_health_plan = health_plan_crud.update(db, health_plan_id, health_plan_data)
    if not updated_health_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health plan not found"
        )
    return updated_health_plan

@router.delete("/{health_plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_health_plan(
    health_plan_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete health plan"""
    # Verify that the health plan belongs to the current professional
    health_plan = health_plan_crud.get_by_id(db, health_plan_id)
    if not health_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health plan not found"
        )
    
    professional = professional_crud.get_by_user_id(db, current_user.id)
    if not professional or health_plan.professional_id != professional.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this health plan"
        )
    
    success = health_plan_crud.delete(db, health_plan_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health plan not found"
        )

@router.get("/professional/{professional_id}", response_model=List[HealthPlan])
def get_health_plans_by_professional(
    professional_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get health plans by professional"""
    return health_plan_crud.get_by_professional(db, professional_id, skip, limit, status)

@router.get("/patient/{patient_id}", response_model=List[HealthPlan])
def get_health_plans_by_patient(
    patient_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get health plans by patient"""
    return health_plan_crud.get_by_patient(db, patient_id, skip, limit, status)

@router.put("/{health_plan_id}/status")
def update_health_plan_status(
    health_plan_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update health plan status"""
    # Verify that the health plan belongs to the current professional
    health_plan = health_plan_crud.get_by_id(db, health_plan_id)
    if not health_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health plan not found"
        )
    
    professional = professional_crud.get_by_user_id(db, current_user.id)
    if not professional or health_plan.professional_id != professional.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this health plan"
        )
    
    updated_health_plan = health_plan_crud.update_status(db, health_plan_id, status)
    if not updated_health_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health plan not found"
        )
    return {"message": "Health plan status updated successfully"}

@router.get("/{health_plan_id}/progress")
def get_health_plan_progress(
    health_plan_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get health plan progress"""
    health_plan = health_plan_crud.get_by_id(db, health_plan_id)
    if not health_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health plan not found"
        )
    
    progress = health_plan_crud.get_progress(db, health_plan_id)
    return {
        "health_plan_id": health_plan_id,
        "progress_percentage": health_plan.progress_percentage,
        "milestones": progress
    } 