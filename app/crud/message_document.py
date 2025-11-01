from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.message_document import MessageDocument
from app.schemas.message import MessageAttachmentCreate

class MessageDocumentCRUD:
    def __init__(self):
        pass

    def create_message_document(self, db: Session, message_id: int, attachment_data: MessageAttachmentCreate, uploaded_by: int) -> MessageDocument:
        """Create a new message document attachment"""
        document = MessageDocument(
            message_id=message_id,
            file_name=attachment_data.file_name,
            original_file_name=attachment_data.original_file_name,
            file_type=attachment_data.file_type,
            file_size=attachment_data.file_size,
            file_extension=attachment_data.file_extension,
            s3_bucket=attachment_data.s3_bucket,
            s3_key=attachment_data.s3_key,
            s3_url=attachment_data.s3_url,
            uploaded_by=uploaded_by
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        return document

    def get_documents_by_message(self, db: Session, message_id: int) -> List[MessageDocument]:
        """Get all document attachments for a specific message"""
        return db.query(MessageDocument).filter(MessageDocument.message_id == message_id).all()

    def get_document(self, db: Session, document_id: int) -> Optional[MessageDocument]:
        """Get a specific document by ID"""
        return db.query(MessageDocument).filter(MessageDocument.id == document_id).first()

    def delete_document(self, db: Session, document_id: int) -> bool:
        """Delete a document attachment"""
        document = self.get_document(db, document_id)
        if not document:
            return False
        
        db.delete(document)
        db.commit()
        return True

    def delete_documents_by_message(self, db: Session, message_id: int) -> int:
        """Delete all document attachments for a specific message"""
        documents = self.get_documents_by_message(db, message_id)
        count = len(documents)
        for document in documents:
            db.delete(document)
        db.commit()
        return count
