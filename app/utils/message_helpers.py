from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.documents import Document, DocumentCategory
from app.models.message import Message

def create_message_attachment(
    db: Session,
    message_id: int,
    file_data: Dict[str, Any],
    user_id: int
) -> Document:
    """
    Create a document attachment for a message using the Document system
    
    Args:
        db: Database session
        message_id: ID of the message to attach to
        file_data: Dictionary containing file information
        user_id: ID of the user creating the attachment
    
    Returns:
        Document: The created document attachment
    """
    # Create document with message attachment flag
    document = Document(
        title=file_data.get('title', file_data.get('file_name', 'Message Attachment')),
        description=file_data.get('description', 'File attached to message'),
        category=DocumentCategory.MESSAGE_ATTACHMENT,
        document_type=file_data.get('document_type', 'attachment'),
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
        message_id=message_id,
        is_message_attachment=True,
        created_by=user_id,
        updated_by=user_id
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return document

def get_message_attachments(
    db: Session,
    message_id: int
) -> List[Document]:
    """
    Get all document attachments for a specific message
    
    Args:
        db: Database session
        message_id: ID of the message
    
    Returns:
        List[Document]: List of document attachments
    """
    return db.query(Document).filter(
        Document.message_id == message_id,
        Document.is_message_attachment == True,
        Document.status != 'deleted'
    ).all()

def remove_message_attachment(
    db: Session,
    document_id: int,
    user_id: int
) -> bool:
    """
    Remove a document attachment from a message (soft delete)
    
    Args:
        db: Database session
        document_id: ID of the document to remove
        user_id: ID of the user removing the attachment
    
    Returns:
        bool: True if successful, False otherwise
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.is_message_attachment == True
    ).first()
    
    if not document:
        return False
    
    # Check if user has permission to remove
    if document.owner_id != user_id:
        return False
    
    # Soft delete the attachment
    document.status = 'deleted'
    document.updated_by = user_id
    
    db.commit()
    return True

def update_message_attachment(
    db: Session,
    document_id: int,
    update_data: Dict[str, Any],
    user_id: int
) -> Optional[Document]:
    """
    Update a message attachment document
    
    Args:
        db: Database session
        document_id: ID of the document to update
        update_data: Dictionary containing fields to update
        user_id: ID of the user updating the attachment
    
    Returns:
        Document: The updated document, or None if failed
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.is_message_attachment == True
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

def get_message_attachment_summary(
    db: Session,
    message_id: int
) -> Dict[str, Any]:
    """
    Get a summary of message attachments
    
    Args:
        db: Database session
        message_id: ID of the message
    
    Returns:
        Dict: Summary of attachments including count, types, and total size
    """
    attachments = get_message_attachments(db, message_id)
    
    if not attachments:
        return {
            'count': 0,
            'total_size': 0,
            'types': [],
            'attachments': []
        }
    
    total_size = sum(doc.file_size for doc in attachments)
    types = list(set(doc.file_type for doc in attachments))
    
    return {
        'count': len(attachments),
        'total_size': total_size,
        'types': types,
        'attachments': [
            {
                'id': doc.id,
                'title': doc.title,
                'file_name': doc.file_name,
                'file_type': doc.file_type,
                'file_size': doc.file_size,
                's3_url': doc.s3_url
            } for doc in attachments
        ]
    }
