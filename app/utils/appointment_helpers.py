from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.documents import Document, DocumentCategory
from app.models.appointment import Appointment

def create_appointment_document(
    db: Session,
    appointment_id: int,
    file_data: Dict[str, Any],
    user_id: int
) -> Document:
    """
    Create a document for an appointment using the Document system
    
    Args:
        db: Database session
        appointment_id: ID of the appointment to attach to
        file_data: Dictionary containing file information
        user_id: ID of the user creating the document
    
    Returns:
        Document: The created appointment document
    """
    # Create document with appointment document flag
    document = Document(
        title=file_data.get('title', file_data.get('file_name', 'Appointment Document')),
        description=file_data.get('description', 'Document for appointment'),
        category=DocumentCategory.APPOINTMENT_DOCUMENT,
        document_type=file_data.get('document_type', 'appointment'),
        file_name=file_data['file_name'],
        original_file_name=file_data.get('original_file_name', file_data['file_name']),
        file_type=file_data['file_type'],
        file_size=file_data['file_size'],
        file_extension=file_data.get('file_extension', ''),
        s3_bucket=file_data['s3_bucket'],
        s3_key=file_data['s3_key'],
        s3_url=file_data.get('s3_url'),
        owner_id=user_id,
        owner_type='user',
        appointment_id=appointment_id,
        is_appointment_document=True,
        created_by=user_id,
        updated_by=user_id
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return document

def get_appointment_documents(
    db: Session,
    appointment_id: int
) -> List[Document]:
    """
    Get all documents for a specific appointment
    
    Args:
        db: Database session
        appointment_id: ID of the appointment
    
    Returns:
        List[Document]: List of appointment documents
    """
    return db.query(Document).filter(
        Document.appointment_id == appointment_id,
        Document.is_appointment_document == True,
        Document.status != 'deleted'
    ).all()

def remove_appointment_document(
    db: Session,
    document_id: int,
    user_id: int
) -> bool:
    """
    Remove a document from an appointment (soft delete)
    
    Args:
        db: Database session
        document_id: ID of the document to remove
        user_id: ID of the user removing the document
    
    Returns:
        bool: True if successful, False otherwise
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.is_appointment_document == True
    ).first()
    
    if not document:
        return False
    
    # Check if user has permission to remove
    if document.owner_id != user_id:
        return False
    
    # Soft delete the document
    document.status = 'deleted'
    document.updated_by = user_id
    
    db.commit()
    return True

def update_appointment_document(
    db: Session,
    document_id: int,
    update_data: Dict[str, Any],
    user_id: int
) -> Optional[Document]:
    """
    Update an appointment document
    
    Args:
        db: Database session
        document_id: ID of the document to update
        update_data: Dictionary containing fields to update
        user_id: ID of the user updating the document
    
    Returns:
        Document: The updated document, or None if failed
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.is_appointment_document == True
    ).first()
    
    if not document:
        return None
    
    # Check if user has permission to update
    if document.owner_id != user_id:
        return None
    
    # Update allowed fields
    allowed_fields = ['title', 'description', 'tags', 'custom_metadata']
    for field, value in update_data.items():
        if field in allowed_fields and hasattr(document, field):
            setattr(document, field, value)
    
    document.updated_by = user_id
    
    db.commit()
    db.refresh(document)
    return document

def get_appointment_document_summary(
    db: Session,
    appointment_id: int
) -> Dict[str, Any]:
    """
    Get a summary of appointment documents
    
    Args:
        db: Database session
        appointment_id: ID of the appointment
    
    Returns:
        Dict: Summary of documents including count, types, and total size
    """
    documents = get_appointment_documents(db, appointment_id)
    
    if not documents:
        return {
            'count': 0,
            'total_size': 0,
            'types': [],
            'documents': []
        }
    
    total_size = sum(doc.file_size for doc in documents)
    types = list(set(doc.file_type for doc in documents))
    
    return {
        'count': len(documents),
        'total_size': total_size,
        'types': types,
        'documents': [
            {
                'id': doc.id,
                'title': doc.title,
                'file_name': doc.file_name,
                'file_type': doc.file_type,
                'file_size': doc.file_size,
                's3_url': doc.s3_url,
                'category': doc.category.value if doc.category else None
            } for doc in documents
        ]
    }

def share_appointment_document(
    db: Session,
    document_id: int,
    shared_with_id: int,
    permission_level: str,
    shared_by: int,
    expires_at: Optional[str] = None
) -> bool:
    """
    Share an appointment document with another user
    
    Args:
        db: Database session
        document_id: ID of the document to share
        shared_with_id: ID of the user to share with
        permission_level: Permission level (VIEW, DOWNLOAD, EDIT, etc.)
        shared_by: ID of the user sharing the document
        expires_at: Optional expiration date
    
    Returns:
        bool: True if successful, False otherwise
    """
    from app.models.documents import DocumentShare, ShareType, PermissionLevel
    
    # Create document share
    share = DocumentShare(
        document_id=document_id,
        share_type=ShareType.USER,
        shared_by=shared_by,
        shared_with_id=shared_with_id,
        permission_level=PermissionLevel(permission_level),
        expires_at=expires_at
    )
    
    db.add(share)
    db.commit()
    return True
