from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.aws_service import aws_service
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.schemas.message import MessageAttachment

router = APIRouter()

@router.post("/upload-file", response_model=MessageAttachment)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a file to S3 and return attachment metadata"""
    try:
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
        
        # Upload file using aws_service
        upload_result = aws_service.upload_message_attachment(
            file_data=file_content,
            file_name=file.filename,
            content_type=file.content_type,
            user_id=current_user.id
        )
        
        # Return attachment metadata
        return MessageAttachment(
            id=0,  # Will be set when saved to database
            message_id=0,  # Will be set when message is created
            file_name=upload_result['file_name'],
            original_file_name=upload_result['original_file_name'],
            file_type=upload_result['file_type'],
            file_size=upload_result['file_size'],
            file_extension=upload_result['file_extension'],
            s3_bucket=upload_result['s3_bucket'],
            s3_key=upload_result['s3_key'],
            s3_url=upload_result['s3_url'],
            uploaded_by=upload_result['uploaded_by'],
            created_at=datetime.utcnow(),  # Set current datetime
            updated_at=None
        )
        
    except Exception as e:
        print(f"❌ File upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")
