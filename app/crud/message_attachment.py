from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.message_document import MessageDocument
from app.schemas.message import MessageAttachmentCreate, MessageAttachment

class MessageAttachmentCRUD:
    def __init__(self):
        pass

    def create_attachment(self, db: Session, attachment_data: MessageAttachmentCreate, message_id: int, uploaded_by: int) -> MessageDocument:
        """Create a new message attachment"""
        attachment = MessageDocument(
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
        
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        return attachment

    def get_attachments_by_message(self, db: Session, message_id: int) -> List[MessageDocument]:
        """Get all attachments for a specific message"""
        return db.query(MessageDocument).filter(MessageDocument.message_id == message_id).all()

    def get_attachment(self, db: Session, attachment_id: int) -> Optional[MessageDocument]:
        """Get a specific attachment by ID"""
        return db.query(MessageDocument).filter(MessageDocument.id == attachment_id).first()

    def delete_attachment(self, db: Session, attachment_id: int) -> bool:
        """Delete an attachment"""
        attachment = self.get_attachment(db, attachment_id)
        if not attachment:
            return False
        
        db.delete(attachment)
        db.commit()
        return True

    def delete_attachments_by_message(self, db: Session, message_id: int) -> int:
        """Delete all attachments for a specific message"""
        attachments = self.get_attachments_by_message(db, message_id)
        count = len(attachments)
        for attachment in attachments:
            db.delete(attachment)
        db.commit()
        return count
