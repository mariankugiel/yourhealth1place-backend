from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
import json

from app.core.database import get_db
from app.core.supabase_client import supabase_client
from app.core.dynamodb_service import dynamodb_service
from app.core.aws_service import aws_service
from app.models.user import User
from app.models.health_record import HealthRecord
from app.schemas.health_record import HealthRecordCreate, HealthRecordResponse, HealthRecordList

router = APIRouter()

@router.post("/health-records", response_model=HealthRecordResponse)
async def create_health_record(
    health_data: HealthRecordCreate,
    current_user: User = Depends(supabase_client.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new health record with sensitive data stored in DynamoDB
    """
    try:
        # Store sensitive health data in DynamoDB
        dynamodb_record_id = await dynamodb_service.store_health_data(
            internal_user_id=current_user.internal_user_id,
            data_type=health_data.record_type,
            data=health_data.sensitive_data
        )
        
        # Create metadata record in PostgreSQL
        db_health_record = HealthRecord(
            patient_id=health_data.patient_id,
            record_date=health_data.record_date,
            record_type=health_data.record_type,
            dynamodb_record_id=dynamodb_record_id,
            is_abnormal=health_data.is_abnormal,
            requires_follow_up=health_data.requires_follow_up,
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
            dynamodb_record_id=db_health_record.dynamodb_record_id,
            is_abnormal=db_health_record.is_abnormal,
            requires_follow_up=db_health_record.requires_follow_up,
            created_at=db_health_record.created_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create health record: {str(e)}")

@router.get("/health-records/{record_id}", response_model=Dict[str, Any])
async def get_health_record(
    record_id: int,
    current_user: User = Depends(supabase_client.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve health record with sensitive data from DynamoDB
    """
    try:
        # Get metadata from PostgreSQL
        db_health_record = db.query(HealthRecord).filter(
            HealthRecord.id == record_id
        ).first()
        
        if not db_health_record:
            raise HTTPException(status_code=404, detail="Health record not found")
        
        # Retrieve sensitive data from DynamoDB
        sensitive_data = await dynamodb_service.retrieve_health_data(
            internal_user_id=current_user.internal_user_id,
            data_type=db_health_record.record_type,
            record_id=db_health_record.dynamodb_record_id
        )
        
        if not sensitive_data:
            raise HTTPException(status_code=404, detail="Sensitive data not found")
        
        # Combine metadata with sensitive data
        return {
            "id": db_health_record.id,
            "patient_id": db_health_record.patient_id,
            "record_date": db_health_record.record_date,
            "record_type": db_health_record.record_type,
            "is_abnormal": db_health_record.is_abnormal,
            "requires_follow_up": db_health_record.requires_follow_up,
            "created_at": db_health_record.created_at,
            "sensitive_data": sensitive_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve health record: {str(e)}")

@router.get("/health-records", response_model=List[HealthRecordList])
async def list_health_records(
    record_type: str = None,
    current_user: User = Depends(supabase_client.get_current_user),
    db: Session = Depends(get_db)
):
    """
    List health records (metadata only, no sensitive data)
    """
    try:
        # Get metadata from PostgreSQL
        query = db.query(HealthRecord)
        
        if record_type:
            query = query.filter(HealthRecord.record_type == record_type)
        
        db_health_records = query.all()
        
        # Return metadata only (no sensitive data)
        return [
            HealthRecordList(
                id=record.id,
                patient_id=record.patient_id,
                record_date=record.record_date,
                record_type=record.record_type,
                is_abnormal=record.is_abnormal,
                requires_follow_up=record.requires_follow_up,
                created_at=record.created_at
            )
            for record in db_health_records
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list health records: {str(e)}")

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(supabase_client.get_current_user)
):
    """
    Upload a document to S3 (for lab reports, images, etc.)
    """
    try:
        # Read file data
        file_data = await file.read()
        
        # Store document in S3
        file_id = await aws_service.store_document(
            internal_user_id=current_user.internal_user_id,
            file_data=file_data,
            file_name=file.filename,
            content_type=file.content_type
        )
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "message": "Document uploaded successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

@router.get("/documents/{file_id}")
async def download_document(
    file_id: str,
    current_user: User = Depends(supabase_client.get_current_user)
):
    """
    Download a document from S3
    """
    try:
        # Retrieve document from S3
        document_data = await aws_service.retrieve_document(
            internal_user_id=current_user.internal_user_id,
            file_id=file_id
        )
        
        if not document_data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Return file data
        from fastapi.responses import Response
        return Response(
            content=document_data['file_data'],
            media_type=document_data['content_type'],
            headers={
                "Content-Disposition": f"attachment; filename={document_data['original_filename']}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download document: {str(e)}") 