from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.crud.patient_insight import patient_insight_crud
from app.schemas.patient_insight import (
    PatientInsight, 
    PatientInsightCreate, 
    PatientInsightUpdate, 
    PatientInsightList
)
from app.core.security import get_current_user

router = APIRouter()

@router.post("/", response_model=PatientInsight, status_code=status.HTTP_201_CREATED)
def create_patient_insight(
    insight_data: PatientInsightCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new patient insight"""
    # Verify that the professional exists and belongs to current user
    professional = professional_crud.get_by_user_id(db, current_user.id)
    if not professional or professional.id != insight_data.professional_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create insights for this professional"
        )
    
    return patient_insight_crud.create(db, insight_data)

@router.get("/", response_model=PatientInsightList)
def get_patient_insights(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    professional_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    insight_type: Optional[str] = None,
    category: Optional[str] = None,
    is_read: Optional[bool] = None,
    requires_action: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get patient insights with optional filters"""
    insights = patient_insight_crud.get_all(
        db, skip, limit, professional_id, patient_id, insight_type, category, is_read, requires_action
    )
    
    total = len(insights)  # In a real app, you'd get total count separately
    
    return PatientInsightList(
        insights=insights,
        total=total,
        page=skip // limit + 1,
        size=limit
    )

@router.get("/{insight_id}", response_model=PatientInsight)
def get_patient_insight(
    insight_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get patient insight by ID"""
    insight = patient_insight_crud.get_by_id(db, insight_id)
    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient insight not found"
        )
    return insight

@router.put("/{insight_id}", response_model=PatientInsight)
def update_patient_insight(
    insight_id: int,
    insight_data: PatientInsightUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update patient insight"""
    # Verify that the insight belongs to the current professional
    insight = patient_insight_crud.get_by_id(db, insight_id)
    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient insight not found"
        )
    
    professional = professional_crud.get_by_user_id(db, current_user.id)
    if not professional or insight.professional_id != professional.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this insight"
        )
    
    updated_insight = patient_insight_crud.update(db, insight_id, insight_data)
    if not updated_insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient insight not found"
        )
    return updated_insight

@router.delete("/{insight_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient_insight(
    insight_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete patient insight"""
    # Verify that the insight belongs to the current professional
    insight = patient_insight_crud.get_by_id(db, insight_id)
    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient insight not found"
        )
    
    professional = professional_crud.get_by_user_id(db, current_user.id)
    if not professional or insight.professional_id != professional.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this insight"
        )
    
    success = patient_insight_crud.delete(db, insight_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient insight not found"
        )

@router.get("/professional/{professional_id}", response_model=List[PatientInsight])
def get_insights_by_professional(
    professional_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    insight_type: Optional[str] = None,
    is_read: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get insights by professional"""
    return patient_insight_crud.get_by_professional(db, professional_id, skip, limit, insight_type, is_read)

@router.get("/patient/{patient_id}", response_model=List[PatientInsight])
def get_insights_by_patient(
    patient_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    insight_type: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get insights by patient"""
    return patient_insight_crud.get_by_patient(db, patient_id, skip, limit, insight_type, category)

@router.put("/{insight_id}/acknowledge")
def acknowledge_insight(
    insight_id: int,
    action_taken: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Acknowledge a patient insight"""
    # Verify that the insight belongs to the current professional
    insight = patient_insight_crud.get_by_id(db, insight_id)
    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient insight not found"
        )
    
    professional = professional_crud.get_by_user_id(db, current_user.id)
    if not professional or insight.professional_id != professional.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to acknowledge this insight"
        )
    
    updated_insight = patient_insight_crud.acknowledge(db, insight_id, action_taken)
    if not updated_insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient insight not found"
        )
    return {"message": "Insight acknowledged successfully"}

@router.put("/{insight_id}/resolve")
def resolve_insight(
    insight_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Resolve a patient insight"""
    # Verify that the insight belongs to the current professional
    insight = patient_insight_crud.get_by_id(db, insight_id)
    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient insight not found"
        )
    
    professional = professional_crud.get_by_user_id(db, current_user.id)
    if not professional or insight.professional_id != professional.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to resolve this insight"
        )
    
    updated_insight = patient_insight_crud.resolve(db, insight_id)
    if not updated_insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient insight not found"
        )
    return {"message": "Insight resolved successfully"}

@router.get("/professional/{professional_id}/unread", response_model=List[PatientInsight])
def get_unread_insights(
    professional_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get unread insights for a professional"""
    return patient_insight_crud.get_unread_by_professional(db, professional_id, skip, limit)

@router.get("/professional/{professional_id}/urgent", response_model=List[PatientInsight])
def get_urgent_insights(
    professional_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get urgent insights for a professional"""
    return patient_insight_crud.get_urgent_by_professional(db, professional_id, skip, limit) 