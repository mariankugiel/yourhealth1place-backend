from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.aws_service import aws_service
from app.models.user import User
from app.models.patient import Patient
from app.models.health_record import HealthRecord
from app.schemas.health_record import HealthRecordCreate, HealthRecordUpdate, HealthRecordResponse
from app.api.v1.endpoints.auth import get_current_user
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=HealthRecordResponse)
async def create_health_record(
    health_record: HealthRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new health record with sensitive data stored in AWS S3"""
    try:
        # Get patient for current user
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient profile not found"
            )
        
        # Store sensitive health data in AWS S3
        sensitive_data = {
            "vital_signs": {
                "blood_pressure_systolic": health_record.blood_pressure_systolic,
                "blood_pressure_diastolic": health_record.blood_pressure_diastolic,
                "heart_rate": health_record.heart_rate,
                "temperature": health_record.temperature,
                "respiratory_rate": health_record.respiratory_rate,
                "oxygen_saturation": health_record.oxygen_saturation,
                "weight": health_record.weight,
                "height": health_record.height,
                "bmi": health_record.bmi
            },
            "lab_results": {
                "glucose_level": health_record.glucose_level,
                "cholesterol_total": health_record.cholesterol_total,
                "cholesterol_hdl": health_record.cholesterol_hdl,
                "cholesterol_ldl": health_record.cholesterol_ldl,
                "triglycerides": health_record.triglycerides,
                "hemoglobin": health_record.hemoglobin,
                "white_blood_cells": health_record.white_blood_cells,
                "platelets": health_record.platelets
            },
            "notes": {
                "notes": health_record.notes,
                "doctor_notes": health_record.doctor_notes
            }
        }
        
        # Store in AWS S3
        aws_file_id = await aws_service.store_health_data(
            user_id=current_user.internal_user_id,
            data_type=health_record.record_type,
            data=sensitive_data
        )
        
        # Create metadata record in database
        db_health_record = HealthRecord(
            patient_id=patient.id,
            record_date=health_record.record_date,
            record_type=health_record.record_type,
            aws_file_id=aws_file_id,
            is_abnormal=health_record.is_abnormal,
            requires_follow_up=health_record.requires_follow_up,
            recorded_by=current_user.id
        )
        
        db.add(db_health_record)
        db.commit()
        db.refresh(db_health_record)
        
        return HealthRecordResponse(
            id=db_health_record.id,
            patient_id=db_health_record.patient_id,
            record_date=db_health_record.record_date,
            record_type=db_health_record.record_type,
            aws_file_id=db_health_record.aws_file_id,
            is_abnormal=db_health_record.is_abnormal,
            requires_follow_up=db_health_record.requires_follow_up,
            recorded_by=db_health_record.recorded_by,
            created_at=db_health_record.created_at,
            updated_at=db_health_record.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create health record: {str(e)}"
        )

@router.get("/", response_model=List[HealthRecordResponse])
async def read_health_records(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get health records metadata for current user"""
    try:
        # Get patient for current user
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient profile not found"
            )
        
        # Get metadata from database
        health_records = db.query(HealthRecord).filter(
            HealthRecord.patient_id == patient.id
        ).offset(skip).limit(limit).all()
        
        return [
            HealthRecordResponse(
                id=record.id,
                patient_id=record.patient_id,
                record_date=record.record_date,
                record_type=record.record_type,
                aws_file_id=record.aws_file_id,
                is_abnormal=record.is_abnormal,
                requires_follow_up=record.requires_follow_up,
                recorded_by=record.recorded_by,
                created_at=record.created_at,
                updated_at=record.updated_at
            )
            for record in health_records
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve health records: {str(e)}"
        )

@router.get("/{record_id}", response_model=dict)
async def read_health_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific health record with sensitive data from AWS S3"""
    try:
        # Get patient for current user
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient profile not found"
            )
        
        # Get metadata from database
        health_record = db.query(HealthRecord).filter(
            HealthRecord.id == record_id,
            HealthRecord.patient_id == patient.id
        ).first()
        
        if not health_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health record not found"
            )
        
        # Retrieve sensitive data from AWS S3
        sensitive_data = await aws_service.retrieve_health_data(
            user_id=current_user.internal_user_id,
            data_type=health_record.record_type,
            file_id=health_record.aws_file_id
        )
        
        if not sensitive_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health record data not found in storage"
            )
        
        # Combine metadata with sensitive data
        return {
            "id": health_record.id,
            "patient_id": health_record.patient_id,
            "record_date": health_record.record_date,
            "record_type": health_record.record_type,
            "is_abnormal": health_record.is_abnormal,
            "requires_follow_up": health_record.requires_follow_up,
            "recorded_by": health_record.recorded_by,
            "created_at": health_record.created_at,
            "updated_at": health_record.updated_at,
            "sensitive_data": sensitive_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve health record: {str(e)}"
        )

@router.put("/{record_id}", response_model=HealthRecordResponse)
async def update_health_record(
    record_id: int,
    health_record: HealthRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update health record metadata (sensitive data updates handled separately)"""
    try:
        # Get patient for current user
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient profile not found"
            )
        
        # Get existing record
        db_health_record = db.query(HealthRecord).filter(
            HealthRecord.id == record_id,
            HealthRecord.patient_id == patient.id
        ).first()
        
        if not db_health_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health record not found"
            )
        
        # Update only metadata fields
        if health_record.is_abnormal is not None:
            db_health_record.is_abnormal = health_record.is_abnormal
        if health_record.requires_follow_up is not None:
            db_health_record.requires_follow_up = health_record.requires_follow_up
        
        db.commit()
        db.refresh(db_health_record)
        
        return HealthRecordResponse(
            id=db_health_record.id,
            patient_id=db_health_record.patient_id,
            record_date=db_health_record.record_date,
            record_type=db_health_record.record_type,
            aws_file_id=db_health_record.aws_file_id,
            is_abnormal=db_health_record.is_abnormal,
            requires_follow_up=db_health_record.requires_follow_up,
            recorded_by=db_health_record.recorded_by,
            created_at=db_health_record.created_at,
            updated_at=db_health_record.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update health record: {str(e)}"
        )

@router.delete("/{record_id}")
async def delete_health_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete health record and associated AWS S3 data"""
    try:
        # Get patient for current user
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient profile not found"
            )
        
        # Get existing record
        db_health_record = db.query(HealthRecord).filter(
            HealthRecord.id == record_id,
            HealthRecord.patient_id == patient.id
        ).first()
        
        if not db_health_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health record not found"
            )
        
        # Delete from AWS S3
        success = await aws_service.delete_health_data(
            user_id=current_user.internal_user_id,
            data_type=db_health_record.record_type,
            file_id=db_health_record.aws_file_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete health record data from storage"
            )
        
        # Delete metadata from database
        db.delete(db_health_record)
        db.commit()
        
        return {"message": "Health record deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete health record: {str(e)}"
        ) 