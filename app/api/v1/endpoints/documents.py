from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.crud.document import (
    document_crud, document_permission_crud, document_share_crud,
    lab_document_crud, imaging_document_crud, health_record_permission_crud
)
from app.schemas.document import (
    DocumentCreate, DocumentUpdate, DocumentResponse, DocumentWithDetails,
    DocumentPermissionCreate, DocumentPermissionUpdate, DocumentPermissionResponse,
    DocumentShareCreate, DocumentShareUpdate, DocumentShareResponse,
    LabDocumentCreate, LabDocumentUpdate, LabDocumentResponse,
    ImagingDocumentCreate, ImagingDocumentUpdate, ImagingDocumentResponse,
    PrescriptionDocumentCreate, PrescriptionDocumentUpdate, PrescriptionDocumentResponse,
    HealthRecordPermissionCreate, HealthRecordPermissionUpdate, HealthRecordPermissionResponse,
    DocumentSearchResult, DocumentPermissionSummary, DocumentShareSummary
)
from app.models.user import User
from app.models.documents import DocumentCategory, DocumentStatus, PermissionLevel, ShareType

router = APIRouter()

# ============================================================================
# DOCUMENT ENDPOINTS
# ============================================================================

@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document(
    document_data: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new document"""
    # Check if user is creating document for themselves or has permission
    if document_data.owner_id != current_user.id:
        # TODO: Add permission check for creating documents for others
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create documents for other users"
        )
    
    return document_crud.create(db, document_data, current_user.id)

@router.get("/{document_id}", response_model=DocumentWithDetails)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a document by ID with all details"""
    document = document_crud.get_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user can view this document
    if not document_crud._can_view(db, document_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this document"
        )
    
    # TODO: Add logic to fetch related data (permissions, shares, specialized docs)
    return document

@router.get("/", response_model=List[DocumentResponse])
def get_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[DocumentCategory] = None,
    document_type: Optional[str] = None,
    owner_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get documents with optional filtering"""
    if owner_id:
        # If requesting specific owner's documents, check permissions
        if owner_id != current_user.id:
            # TODO: Add permission check for viewing other users' documents
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view other users' documents"
            )
        return document_crud.get_by_owner(db, owner_id, skip, limit)
    
    if category:
        return document_crud.get_by_category(db, category, skip, limit)
    
    if document_type:
        return document_crud.get_by_type(db, document_type, skip, limit)
    
    # Default: get user's own documents
    return document_crud.get_by_owner(db, current_user.id, skip, limit)

@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: int,
    document_data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a document"""
    document = document_crud.update(db, document_id, document_data, current_user.id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or not authorized to edit"
        )
    return document

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document (soft delete)"""
    success = document_crud.delete(db, document_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or not authorized to delete"
        )

@router.post("/{document_id}/archive", response_model=DocumentResponse)
def archive_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive a document"""
    success = document_crud.archive(db, document_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or not authorized to archive"
        )
    
    return document_crud.get_by_id(db, document_id)

@router.get("/search/", response_model=DocumentSearchResult)
def search_documents(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search documents by title, description, or tags"""
    documents = document_crud.search_documents(db, q, current_user.id, skip, limit)
    # TODO: Implement proper pagination with total count
    return DocumentSearchResult(
        documents=documents,
        total=len(documents),
        skip=skip,
        limit=limit
    )

# ============================================================================
# DOCUMENT PERMISSION ENDPOINTS
# ============================================================================

@router.post("/{document_id}/permissions", response_model=DocumentPermissionResponse, status_code=status.HTTP_201_CREATED)
def create_document_permission(
    document_id: int,
    permission_data: DocumentPermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new document permission"""
    # Check if user can grant permissions for this document
    document = document_crud.get_by_id(db, document_id)
    if not document or document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or not authorized to grant permissions"
        )
    
    return document_permission_crud.create(db, permission_data, current_user.id)

@router.get("/{document_id}/permissions", response_model=List[DocumentPermissionResponse])
def get_document_permissions(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all permissions for a document"""
    # Check if user can view permissions for this document
    document = document_crud.get_by_id(db, document_id)
    if not document or document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or not authorized to view permissions"
        )
    
    return document_permission_crud.get_by_document(db, document_id)

@router.put("/permissions/{permission_id}", response_model=DocumentPermissionResponse)
def update_document_permission(
    permission_id: int,
    permission_data: DocumentPermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a document permission"""
    permission = document_permission_crud.update_permission(
        db, permission_id, permission_data, current_user.id
    )
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found or not authorized to update"
        )
    return permission

@router.delete("/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_document_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revoke a document permission"""
    success = document_permission_crud.revoke_permission(db, permission_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found or not authorized to revoke"
        )

# ============================================================================
# DOCUMENT SHARE ENDPOINTS
# ============================================================================

@router.post("/{document_id}/shares", response_model=DocumentShareResponse, status_code=status.HTTP_201_CREATED)
def create_document_share(
    document_id: int,
    share_data: DocumentShareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new document share"""
    # Check if user can share this document
    document = document_crud.get_by_id(db, document_id)
    if not document or document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or not authorized to share"
        )
    
    return document_share_crud.create(db, share_data, current_user.id)

@router.get("/{document_id}/shares", response_model=List[DocumentShareResponse])
def get_document_shares(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all shares for a document"""
    # Check if user can view shares for this document
    document = document_crud.get_by_id(db, document_id)
    if not document or document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or not authorized to view shares"
        )
    
    return document_share_crud.get_by_document(db, document_id)

@router.get("/shared/{share_token}", response_model=DocumentWithDetails)
def get_shared_document(
    share_token: str,
    db: Session = Depends(get_db)
):
    """Get a document via public share token"""
    share = document_share_crud.get_by_token(db, share_token)
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found or expired"
        )
    
    document = document_crud.get_by_id(db, share.document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # TODO: Add logic to fetch related data
    return document

@router.delete("/shares/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_document_share(
    share_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revoke a document share"""
    success = document_share_crud.revoke_share(db, share_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found or not authorized to revoke"
        )

# ============================================================================
# SPECIALIZED DOCUMENT ENDPOINTS
# ============================================================================

@router.post("/{document_id}/lab", response_model=LabDocumentResponse, status_code=status.HTTP_201_CREATED)
def create_lab_document(
    document_id: int,
    lab_data: LabDocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new lab document"""
    # Check if user can create lab documents for this document
    document = document_crud.get_by_id(db, document_id)
    if not document or document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or not authorized to create lab document"
        )
    
    return lab_document_crud.create(db, document_id, lab_data.dict())

@router.put("/lab/{lab_document_id}", response_model=LabDocumentResponse)
def update_lab_document(
    lab_document_id: int,
    lab_data: LabDocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a lab document"""
    # TODO: Implement update logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Update lab document not yet implemented"
    )

@router.post("/{document_id}/imaging", response_model=ImagingDocumentResponse, status_code=status.HTTP_201_CREATED)
def create_imaging_document(
    document_id: int,
    imaging_data: ImagingDocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new imaging document"""
    # Check if user can create imaging documents for this document
    document = document_crud.get_by_id(db, document_id)
    if not document or document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or not authorized to create imaging document"
        )
    
    return imaging_document_crud.create(db, document_id, imaging_data.dict())

@router.post("/{document_id}/prescription", response_model=PrescriptionDocumentResponse, status_code=status.HTTP_201_CREATED)
def create_prescription_document(
    document_id: int,
    prescription_data: PrescriptionDocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new prescription document"""
    # Check if user can create prescription documents for this document
    document = document_crud.get_by_id(db, document_id)
    if not document or document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or not authorized to create prescription document"
        )
    
    # TODO: Implement prescription document creation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Create prescription document not yet implemented"
    )

# ============================================================================
# HEALTH RECORD PERMISSION ENDPOINTS
# ============================================================================

@router.post("/health-records/permissions", response_model=HealthRecordPermissionResponse, status_code=status.HTTP_201_CREATED)
def create_health_record_permission(
    permission_data: HealthRecordPermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create health record permissions for a professional to access patient data"""
    # Check if current user is the patient or has permission to grant access
    if permission_data.patient_id != current_user.id:
        # TODO: Add permission check for granting health record access
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to grant health record permissions for other patients"
        )
    
    return health_record_permission_crud.create(
        db, 
        permission_data.patient_id, 
        permission_data.professional_id, 
        permission_data.dict(exclude={'patient_id', 'professional_id'}),
        current_user.id
    )

@router.get("/health-records/permissions/patient/{patient_id}", response_model=List[HealthRecordPermissionResponse])
def get_patient_health_record_permissions(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all health record permissions for a patient"""
    # Check if current user is the patient or has permission to view
    if patient_id != current_user.id:
        # TODO: Add permission check for viewing other patients' permissions
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view other patients' health record permissions"
        )
    
    return health_record_permission_crud.get_by_patient(db, patient_id)

@router.get("/health-records/permissions/professional/{professional_id}", response_model=List[HealthRecordPermissionResponse])
def get_professional_health_record_permissions(
    professional_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all health record permissions for a professional"""
    # Check if current user is the professional or has permission to view
    if professional_id != current_user.id:
        # TODO: Add permission check for viewing other professionals' permissions
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view other professionals' health record permissions"
        )
    
    return health_record_permission_crud.get_by_professional(db, professional_id)

@router.put("/health-records/permissions/{permission_id}", response_model=HealthRecordPermissionResponse)
def update_health_record_permission(
    permission_id: int,
    permission_data: HealthRecordPermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update health record permissions"""
    permission = health_record_permission_crud.update_permissions(
        db, permission_id, permission_data.dict(exclude_unset=True), current_user.id
    )
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found or not authorized to update"
        )
    return permission

@router.delete("/health-records/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_health_record_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revoke health record permissions"""
    success = health_record_permission_crud.revoke_permissions(db, permission_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found or not authorized to revoke"
        )
