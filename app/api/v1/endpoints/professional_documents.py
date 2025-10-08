from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.crud.professional_document import professional_document_crud
from app.crud.appointment import appointment_crud
from app.schemas.professional_document import (
    ProfessionalDocumentCreate,
    ProfessionalDocumentUpdate,
    ProfessionalDocument,
    ProfessionalDocumentList,
    DocumentAssignmentCreate,
    DocumentAssignmentUpdate,
    DocumentAssignment,
    DocumentAssignmentList,
    CreateDocumentFromTemplate,
    AppointmentDocumentSummary,
    AppointmentWithDocuments
)
from app.models.user import User

router = APIRouter()

# Helper function to get current professional
async def get_current_professional(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    # Since professional data is now stored in Supabase user metadata,
    # we can use the current_user directly if they have professional role
    # TODO: Add role checking logic here based on Supabase user metadata
    return current_user

# Document Management Endpoints
@router.post("/documents/", response_model=ProfessionalDocument)
async def create_document(
    document_data: ProfessionalDocumentCreate,
    current_professional: User = Depends(get_current_professional),
    db: Session = Depends(get_db)
):
    """Create a new document (can be marked as template for reuse)"""
    return professional_document_crud.create_document(
        db, document_data, current_professional.id, current_professional.id
    )

@router.get("/documents/", response_model=ProfessionalDocumentList)
async def get_professional_documents(
    is_template: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    current_professional: User = Depends(get_current_professional),
    db: Session = Depends(get_db)
):
    """Get all documents for the current professional"""
    documents = professional_document_crud.get_documents_by_professional(
        db, current_professional.id, is_template=is_template, skip=skip, limit=limit
    )
    return ProfessionalDocumentList(
        documents=documents,
        total=len(documents),
        page=skip // limit + 1,
        size=limit
    )

@router.get("/documents/templates/", response_model=ProfessionalDocumentList)
async def get_professional_templates(
    skip: int = 0,
    limit: int = 100,
    current_professional: User = Depends(get_current_professional),
    db: Session = Depends(get_db)
):
    """Get all template documents for the current professional"""
    templates = professional_document_crud.get_templates_by_professional(
        db, current_professional.id, skip=skip, limit=limit
    )
    return ProfessionalDocumentList(
        documents=templates,
        total=len(templates),
        page=skip // limit + 1,
        size=limit
    )

@router.get("/documents/{document_id}", response_model=ProfessionalDocument)
async def get_document(
    document_id: int,
    current_professional: User = Depends(get_current_professional),
    db: Session = Depends(get_db)
):
    """Get a specific document"""
    document = professional_document_crud.get_document(db, document_id)
    if not document or document.professional_id != current_professional.id:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@router.put("/documents/{document_id}", response_model=ProfessionalDocument)
async def update_document(
    document_id: int,
    document_data: ProfessionalDocumentUpdate,
    current_professional: User = Depends(get_current_professional),
    db: Session = Depends(get_db)
):
    """Update a document (e.g., mark as template)"""
    document = professional_document_crud.get_document(db, document_id)
    if not document or document.professional_id != current_professional.id:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return professional_document_crud.update_document(
        db, document_id, document_data, current_professional.id
    )

# Key endpoint for your workflow - Create document from template
@router.post("/documents/create-from-template/", response_model=ProfessionalDocument)
async def create_document_from_template(
    template_data: CreateDocumentFromTemplate,
    current_professional: User = Depends(get_current_professional),
    db: Session = Depends(get_db)
):
    """
    Create a new document from an existing template with patient data
    This is the main workflow: Doctor uses template to create patient-specific document
    """
    # Verify the appointment belongs to the professional
    appointment = appointment_crud.get_appointment(db, template_data.appointment_id)
    if not appointment or appointment.professional_id != current_professional.id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    try:
        document = professional_document_crud.create_document_from_template(
            db,
            template_data,
            current_professional.id,
            current_professional.id
        )
        return document
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Document Assignment Endpoints
@router.post("/assignments/", response_model=DocumentAssignment)
async def create_document_assignment(
    assignment_data: DocumentAssignmentCreate,
    current_professional: User = Depends(get_current_professional),
    db: Session = Depends(get_db)
):
    """Assign a document to an appointment"""
    # Verify the appointment belongs to the professional
    appointment = appointment_crud.get_appointment(db, assignment_data.appointment_id)
    if not appointment or appointment.professional_id != current_professional.id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Verify the document belongs to the professional
    document = professional_document_crud.get_document(db, assignment_data.document_id)
    if not document or document.professional_id != current_professional.id:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return professional_document_crud.create_document_assignment(
        db, assignment_data, current_professional.id
    )

@router.get("/assignments/appointment/{appointment_id}", response_model=DocumentAssignmentList)
async def get_appointment_document_assignments(
    appointment_id: int,
    current_professional: User = Depends(get_current_professional),
    db: Session = Depends(get_db)
):
    """Get all document assignments for an appointment"""
    # Verify the appointment belongs to the professional
    appointment = appointment_crud.get_appointment(db, appointment_id)
    if not appointment or appointment.professional_id != current_professional.id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    assignments = professional_document_crud.get_document_assignments_by_appointment(
        db, appointment_id
    )
    
    return DocumentAssignmentList(
        assignments=assignments,
        total=len(assignments),
        page=1,
        size=len(assignments)
    )

@router.put("/assignments/{assignment_id}", response_model=DocumentAssignment)
async def update_document_assignment(
    assignment_id: int,
    assignment_data: DocumentAssignmentUpdate,
    current_professional: User = Depends(get_current_professional),
    db: Session = Depends(get_db)
):
    """Update a document assignment"""
    assignment = professional_document_crud.update_document_assignment(
        db, assignment_id, assignment_data, current_professional.id
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Document assignment not found")
    return assignment

# Appointment Document Summary Endpoints
@router.get("/appointments/{appointment_id}/summary", response_model=AppointmentDocumentSummary)
async def get_appointment_document_summary(
    appointment_id: int,
    current_professional: User = Depends(get_current_professional),
    db: Session = Depends(get_db)
):
    """Get a summary of all documents for an appointment"""
    # Verify the appointment belongs to the professional
    appointment = appointment_crud.get_appointment(db, appointment_id)
    if not appointment or appointment.professional_id != current_professional.id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    summary = professional_document_crud.get_appointment_document_summary(db, appointment_id)
    
    return AppointmentDocumentSummary(
        appointment_id=summary["appointment_id"],
        total_documents=summary["total_documents"],
        completed_documents=summary["completed_documents"],
        pending_documents=summary["pending_documents"],
        document_types=summary["document_types"]
    )

@router.get("/appointments/{appointment_id}/documents", response_model=AppointmentWithDocuments)
async def get_appointment_with_documents(
    appointment_id: int,
    current_professional: User = Depends(get_current_professional),
    db: Session = Depends(get_db)
):
    """Get appointment details with all associated documents"""
    # Verify the appointment belongs to the professional
    appointment = appointment_crud.get_appointment(db, appointment_id)
    if not appointment or appointment.professional_id != current_professional.id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    summary = professional_document_crud.get_appointment_document_summary(db, appointment_id)
    
    return AppointmentWithDocuments(
        appointment_id=appointment_id,
        patient_name=f"{appointment.patient.first_name} {appointment.patient.last_name}",
        professional_name=f"{appointment.professional.first_name} {appointment.professional.last_name}",
        appointment_date=appointment.scheduled_at,
        documents=summary["documents"],
        assignments=summary["assignments"]
    )

# File Upload Endpoint
@router.post("/documents/upload")
async def upload_document_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    is_template: bool = Form(False),
    category_id: int = Form(...),
    current_professional: User = Depends(get_current_professional),
    db: Session = Depends(get_db)
):
    """Upload a document file (can be marked as template)"""
    # TODO: Implement file upload to S3
    # For now, return a placeholder response
    
    document_data = ProfessionalDocumentCreate(
        category_id=category_id,
        title=title,
        description=description,
        is_template=is_template,
        file_name=file.filename,
        original_file_name=file.filename,
        file_type=file.content_type or "application/octet-stream",
        file_size=file.size or 0,
        file_extension=file.filename.split(".")[-1] if "." in file.filename else "",
        s3_url="",  # Will be set after S3 upload
        s3_key=""   # Will be set after S3 upload
    )
    
    document = professional_document_crud.create_document(
        db, document_data, current_professional.id, current_professional.id
    )
    
    return {
        "message": "Document uploaded successfully",
        "document_id": document.id,
        "filename": file.filename,
        "is_template": is_template
    }
