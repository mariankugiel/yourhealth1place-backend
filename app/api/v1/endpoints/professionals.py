from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.crud.professional import professional_crud
from app.schemas.professional import (
    Professional, 
    ProfessionalCreate, 
    ProfessionalUpdate, 
    ProfessionalList
)
from app.schemas.statistics import DashboardStatistics
from app.core.security import get_current_user

router = APIRouter()

@router.post("/", response_model=Professional, status_code=status.HTTP_201_CREATED)
def create_professional(
    professional_data: ProfessionalCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new professional profile"""
    # Check if user already has a professional profile
    existing_professional = professional_crud.get_by_user_id(db, professional_data.user_id)
    if existing_professional:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a professional profile"
        )
    
    # Check if license number already exists
    if professional_data.license_number:
        existing_license = professional_crud.get_by_license(db, professional_data.license_number)
        if existing_license:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="License number already registered"
            )
    
    return professional_crud.create(db, professional_data)

@router.get("/", response_model=ProfessionalList)
def get_professionals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    specialty: Optional[str] = None,
    is_available: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all professionals with optional filters"""
    if search:
        professionals = professional_crud.search_professionals(db, search, skip, limit)
    else:
        professionals = professional_crud.get_all(
            db, skip, limit, specialty, is_available, is_verified
        )
    
    total = len(professionals)  # In a real app, you'd get total count separately
    
    return ProfessionalList(
        professionals=professionals,
        total=total,
        page=skip // limit + 1,
        size=limit
    )

@router.get("/{professional_id}", response_model=Professional)
def get_professional(
    professional_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get professional by ID"""
    professional = professional_crud.get_by_id(db, professional_id)
    if not professional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional not found"
        )
    return professional

@router.get("/me/profile", response_model=Professional)
def get_my_professional_profile(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get current user's professional profile"""
    professional = professional_crud.get_by_user_id(db, current_user.id)
    if not professional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional profile not found"
        )
    return professional

@router.put("/me/profile", response_model=Professional)
def update_my_professional_profile(
    professional_data: ProfessionalUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update current user's professional profile"""
    professional = professional_crud.get_by_user_id(db, current_user.id)
    if not professional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional profile not found"
        )
    
    updated_professional = professional_crud.update(db, professional.id, professional_data)
    if not updated_professional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional not found"
        )
    return updated_professional

@router.put("/{professional_id}", response_model=Professional)
def update_professional(
    professional_id: int,
    professional_data: ProfessionalUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update professional profile"""
    updated_professional = professional_crud.update(db, professional_id, professional_data)
    if not updated_professional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional not found"
        )
    return updated_professional

@router.delete("/{professional_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_professional(
    professional_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete professional profile"""
    success = professional_crud.delete(db, professional_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional not found"
        )

@router.get("/available/", response_model=List[Professional])
def get_available_professionals(
    specialty: Optional[str] = None,
    consultation_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get available professionals for appointments"""
    return professional_crud.get_available_professionals(db, specialty, consultation_type)

@router.get("/specialty/{specialty}", response_model=List[Professional])
def get_professionals_by_specialty(
    specialty: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get professionals by specialty"""
    return professional_crud.get_professionals_by_specialty(db, specialty, skip, limit)

@router.put("/me/availability")
def update_my_availability(
    is_available: bool,
    availability_schedule: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update current user's availability"""
    professional = professional_crud.get_by_user_id(db, current_user.id)
    if not professional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional profile not found"
        )
    
    updated_professional = professional_crud.update_availability(
        db, professional.id, is_available, availability_schedule
    )
    if not updated_professional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional not found"
        )
    return {"message": "Availability updated successfully"}

@router.get("/me/dashboard", response_model=DashboardStatistics)
def get_my_dashboard_statistics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get dashboard statistics for current professional"""
    professional = professional_crud.get_by_user_id(db, current_user.id)
    if not professional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional profile not found"
        )
    
    # Get date range for statistics
    today = datetime.utcnow().date()
    start_of_month = today.replace(day=1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Get statistics for the current month
    stats = professional_crud.get_professional_statistics(
        db, professional.id, start_of_month, end_of_month
    )
    
    # For now, returning mock data - in a real app, you'd calculate these from actual data
    return DashboardStatistics(
        today_appointments=5,
        upcoming_appointments=12,
        total_patients=150,
        active_health_plans=25,
        pending_insights=8,
        monthly_revenue=8500.0,
        patient_satisfaction=4.8,
        consultation_completion_rate=0.95
    ) 