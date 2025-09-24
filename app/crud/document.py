from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from app.models.documents import (
    Document, DocumentShare, DocumentAccessLog,
    LabDocument, ImagingDocument, PrescriptionDocument,
    DocumentCategory, DocumentStatus, PermissionLevel, ShareType
)
from app.models.permissions import (
    DocumentPermission, HealthRecordPermission
)
from app.models.s3_storage import S3StorageInfo
from app.schemas.document import (
    DocumentCreate, DocumentUpdate, DocumentPermissionCreate,
    DocumentShareCreate, DocumentAccessLogCreate
)

# ============================================================================
# DOCUMENT CRUD OPERATIONS
# ============================================================================

class DocumentCRUD:
    """CRUD operations for documents"""
    
    def create(self, db: Session, document_data: DocumentCreate, user_id: int) -> Document:
        """Create a new document"""
        document = Document(
            **document_data.dict(),
            created_by=user_id,
            updated_by=user_id
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return document
    
    def get_by_id(self, db: Session, document_id: int) -> Optional[Document]:
        """Get document by ID"""
        return db.query(Document).filter(Document.id == document_id).first()
    
    def get_by_owner(self, db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[Document]:
        """Get documents owned by a specific user"""
        return db.query(Document).filter(
            Document.owner_id == owner_id,
            Document.status != DocumentStatus.DELETED
        ).offset(skip).limit(limit).all()
    
    def get_by_category(self, db: Session, category: DocumentCategory, skip: int = 0, limit: int = 100) -> List[Document]:
        """Get documents by category"""
        return db.query(Document).filter(
            Document.category == category,
            Document.status == DocumentStatus.ACTIVE
        ).offset(skip).limit(limit).all()
    
    def get_by_type(self, db: Session, document_type: str, skip: int = 0, limit: int = 100) -> List[Document]:
        """Get documents by specific type"""
        return db.query(Document).filter(
            Document.document_type == document_type,
            Document.status == DocumentStatus.ACTIVE
        ).offset(skip).limit(limit).all()
    
    def search_documents(self, db: Session, query: str, user_id: int, skip: int = 0, limit: int = 100) -> List[Document]:
        """Search documents by title, description, or tags"""
        search_filter = or_(
            Document.title.ilike(f"%{query}%"),
            Document.description.ilike(f"%{query}%"),
            Document.tags.contains([query])
        )
        
        # Get documents user owns or has permission to view
        owned_docs = db.query(Document.id).filter(Document.owner_id == user_id)
        permitted_docs = db.query(DocumentPermission.document_id).filter(
            DocumentPermission.user_id == user_id,
            DocumentPermission.can_view == True,
            DocumentPermission.is_active == True
        )
        
        return db.query(Document).filter(
            and_(
                search_filter,
                Document.status == DocumentStatus.ACTIVE,
                or_(
                    Document.id.in_(owned_docs),
                    Document.id.in_(permitted_docs)
                )
            )
        ).offset(skip).limit(limit).all()
    
    def update(self, db: Session, document_id: int, document_data: DocumentUpdate, user_id: int) -> Optional[Document]:
        """Update a document"""
        document = self.get_by_id(db, document_id)
        if not document:
            return None
        
        # Check if user has edit permission
        if not self._can_edit(db, document_id, user_id):
            return None
        
        for field, value in document_data.dict(exclude_unset=True).items():
            setattr(document, field, value)
        
        document.updated_by = user_id
        document.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(document)
        return document
    
    def delete(self, db: Session, document_id: int, user_id: int) -> bool:
        """Soft delete a document"""
        document = self.get_by_id(db, document_id)
        if not document:
            return False
        
        # Check if user has delete permission
        if not self._can_delete(db, document_id, user_id):
            return False
        
        document.status = DocumentStatus.DELETED
        document.updated_by = user_id
        document.updated_at = datetime.utcnow()
        
        db.commit()
        return True
    
    def archive(self, db: Session, document_id: int, user_id: int) -> bool:
        """Archive a document"""
        document = self.get_by_id(db, document_id)
        if not document:
            return False
        
        # Check if user has edit permission
        if not self._can_edit(db, document_id, user_id):
            return False
        
        document.status = DocumentStatus.ARCHIVED
        document.updated_by = user_id
        document.updated_at = datetime.utcnow()
        
        db.commit()
        return True
    
    def _can_view(self, db: Session, document_id: int, user_id: int) -> bool:
        """Check if user can view document"""
        document = self.get_by_id(db, document_id)
        if not document:
            return False
        
        # Owner can always view
        if document.owner_id == user_id:
            return True
        
        # Check permissions
        permission = db.query(DocumentPermission).filter(
            DocumentPermission.document_id == document_id,
            DocumentPermission.user_id == user_id,
            DocumentPermission.can_view == True,
            DocumentPermission.is_active == True
        ).first()
        
        return permission is not None
    
    def _can_edit(self, db: Session, document_id: int, user_id: int) -> bool:
        """Check if user can edit document"""
        document = self.get_by_id(db, document_id)
        if not document:
            return False
        
        # Owner can always edit
        if document.owner_id == user_id:
            return True
        
        # Check permissions
        permission = db.query(DocumentPermission).filter(
            DocumentPermission.document_id == document_id,
            DocumentPermission.user_id == user_id,
            DocumentPermission.can_edit == True,
            DocumentPermission.is_active == True
        ).first()
        
        return permission is not None
    
    def _can_delete(self, db: Session, document_id: int, user_id: int) -> bool:
        """Check if user can delete document"""
        document = self.get_by_id(db, document_id)
        if not document:
            return False
        
        # Only owner can delete
        return document.owner_id == user_id

# ============================================================================
# DOCUMENT PERMISSION CRUD OPERATIONS
# ============================================================================

class DocumentPermissionCRUD:
    """CRUD operations for document permissions"""
    
    def create(self, db: Session, permission_data: DocumentPermissionCreate, granter_id: int) -> DocumentPermission:
        """Create a new document permission"""
        permission = DocumentPermission(
            **permission_data.dict(),
            granted_by=granter_id
        )
        db.add(permission)
        db.commit()
        db.refresh(permission)
        return permission
    
    def get_by_document(self, db: Session, document_id: int) -> List[DocumentPermission]:
        """Get all permissions for a document"""
        return db.query(DocumentPermission).filter(
            DocumentPermission.document_id == document_id,
            DocumentPermission.is_active == True
        ).all()
    
    def get_by_user(self, db: Session, user_id: int) -> List[DocumentPermission]:
        """Get all permissions for a user"""
        return db.query(DocumentPermission).filter(
            DocumentPermission.user_id == user_id,
            DocumentPermission.is_active == True
        ).all()
    
    def update_permission(self, db: Session, permission_id: int, permission_data: DocumentPermissionCreate, updater_id: int) -> Optional[DocumentPermission]:
        """Update a document permission"""
        permission = db.query(DocumentPermission).filter(DocumentPermission.id == permission_id).first()
        if not permission:
            return None
        
        # Only granter or document owner can update permissions
        document = db.query(Document).filter(Document.id == permission.document_id).first()
        if not document or (permission.granted_by != updater_id and document.owner_id != updater_id):
            return None
        
        for field, value in permission_data.dict(exclude_unset=True).items():
            setattr(permission, field, value)
        
        permission.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(permission)
        return permission
    
    def revoke_permission(self, db: Session, permission_id: int, revoker_id: int) -> bool:
        """Revoke a document permission"""
        permission = db.query(DocumentPermission).filter(DocumentPermission.id == permission_id).first()
        if not permission:
            return False
        
        # Only granter or document owner can revoke permissions
        document = db.query(Document).filter(Document.id == permission.document_id).first()
        if not document or (permission.granted_by != revoker_id and document.owner_id != revoker_id):
            return False
        
        permission.is_active = False
        permission.updated_at = datetime.utcnow()
        
        db.commit()
        return True

# ============================================================================
# DOCUMENT SHARE CRUD OPERATIONS
# ============================================================================

class DocumentShareCRUD:
    """CRUD operations for document sharing"""
    
    def create(self, db: Session, share_data: DocumentShareCreate, sharer_id: int) -> DocumentShare:
        """Create a new document share"""
        # Generate unique share token for public links
        if share_data.share_type == ShareType.PUBLIC_LINK:
            share_data.share_token = str(uuid.uuid4())
            share_data.share_url = f"/shared/{share_data.share_token}"
        
        share = DocumentShare(
            **share_data.dict(),
            shared_by=sharer_id
        )
        db.add(share)
        db.commit()
        db.refresh(share)
        return share
    
    def get_by_document(self, db: Session, document_id: int) -> List[DocumentShare]:
        """Get all shares for a document"""
        return db.query(DocumentShare).filter(
            DocumentShare.document_id == document_id,
            DocumentShare.is_active == True
        ).all()
    
    def get_by_token(self, db: Session, share_token: str) -> Optional[DocumentShare]:
        """Get share by token (for public links)"""
        return db.query(DocumentShare).filter(
            DocumentShare.share_token == share_token,
            DocumentShare.is_active == True,
            or_(
                DocumentShare.expires_at.is_(None),
                DocumentShare.expires_at > datetime.utcnow()
            )
        ).first()
    
    def get_by_appointment(self, db: Session, appointment_id: int) -> List[DocumentShare]:
        """Get all document shares for an appointment"""
        return db.query(DocumentShare).filter(
            DocumentShare.appointment_id == appointment_id,
            DocumentShare.is_active == True
        ).all()
    
    def revoke_share(self, db: Session, share_id: int, revoker_id: int) -> bool:
        """Revoke a document share"""
        share = db.query(DocumentShare).filter(DocumentShare.id == share_id).first()
        if not share:
            return False
        
        # Only sharer or document owner can revoke shares
        document = db.query(Document).filter(Document.id == share.document_id).first()
        if not document or (share.shared_by != revoker_id and document.owner_id != revoker_id):
            return False
        
        share.is_active = False
        share.updated_at = datetime.utcnow()
        
        db.commit()
        return True

# ============================================================================
# SPECIALIZED DOCUMENT CRUD OPERATIONS
# ============================================================================

class LabDocumentCRUD:
    """CRUD operations for lab documents"""
    
    def create(self, db: Session, document_id: int, lab_data: Dict[str, Any]) -> LabDocument:
        """Create a new lab document"""
        lab_doc = LabDocument(
            document_id=document_id,
            **lab_data
        )
        db.add(lab_doc)
        db.commit()
        db.refresh(lab_doc)
        return lab_doc
    
    def get_by_document(self, db: Session, document_id: int) -> Optional[LabDocument]:
        """Get lab document by document ID"""
        return db.query(LabDocument).filter(LabDocument.document_id == document_id).first()
    
    def get_by_patient(self, db: Session, patient_id: int, skip: int = 0, limit: int = 100) -> List[LabDocument]:
        """Get lab documents for a patient"""
        return db.query(LabDocument).join(Document).filter(
            Document.owner_id == patient_id,
            Document.status == DocumentStatus.ACTIVE
        ).offset(skip).limit(limit).all()

class ImagingDocumentCRUD:
    """CRUD operations for imaging documents"""
    
    def create(self, db: Session, document_id: int, imaging_data: Dict[str, Any]) -> ImagingDocument:
        """Create a new imaging document"""
        imaging_doc = ImagingDocument(
            document_id=document_id,
            **imaging_data
        )
        db.add(imaging_doc)
        db.commit()
        db.refresh(imaging_doc)
        return imaging_doc
    
    def get_by_document(self, db: Session, document_id: int) -> Optional[ImagingDocument]:
        """Get imaging document by document ID"""
        return db.query(ImagingDocument).filter(ImagingDocument.document_id == document_id).first()
    
    def get_by_patient(self, db: Session, patient_id: int, skip: int = 0, limit: int = 100) -> List[ImagingDocument]:
        """Get imaging documents for a patient"""
        return db.query(ImagingDocument).join(Document).filter(
            Document.owner_id == patient_id,
            Document.status == DocumentStatus.ACTIVE
        ).offset(skip).limit(limit).all()

# ============================================================================
# HEALTH RECORD PERMISSION CRUD OPERATIONS
# ============================================================================

class HealthRecordPermissionCRUD:
    """CRUD operations for health record permissions"""
    
    def create(self, db: Session, patient_id: int, professional_id: int, permissions: Dict[str, bool], granter_id: int) -> HealthRecordPermission:
        """Create health record permissions for a professional to access patient data"""
        permission = HealthRecordPermission(
            patient_id=patient_id,
            professional_id=professional_id,
            granted_by=granter_id,
            **permissions
        )
        db.add(permission)
        db.commit()
        db.refresh(permission)
        return permission
    
    def get_by_patient(self, db: Session, patient_id: int) -> List[HealthRecordPermission]:
        """Get all health record permissions for a patient"""
        return db.query(HealthRecordPermission).filter(
            HealthRecordPermission.patient_id == patient_id,
            HealthRecordPermission.is_active == True
        ).all()
    
    def get_by_professional(self, db: Session, professional_id: int) -> List[HealthRecordPermission]:
        """Get all health record permissions for a professional"""
        return db.query(HealthRecordPermission).filter(
            HealthRecordPermission.professional_id == professional_id,
            HealthRecordPermission.is_active == True
        ).all()
    
    def get_permission(self, db: Session, patient_id: int, professional_id: int) -> Optional[HealthRecordPermission]:
        """Get specific health record permission"""
        return db.query(HealthRecordPermission).filter(
            HealthRecordPermission.patient_id == patient_id,
            HealthRecordPermission.professional_id == professional_id,
            HealthRecordPermission.is_active == True
        ).first()
    
    def update_permissions(self, db: Session, permission_id: int, permissions: Dict[str, bool], updater_id: int) -> Optional[HealthRecordPermission]:
        """Update health record permissions"""
        permission = db.query(HealthRecordPermission).filter(HealthRecordPermission.id == permission_id).first()
        if not permission:
            return None
        
        # Only patient or granter can update permissions
        if permission.patient_id != updater_id and permission.granted_by != updater_id:
            return None
        
        for field, value in permissions.items():
            if hasattr(permission, field):
                setattr(permission, field, value)
        
        permission.updated_at = datetime.utcnow()
        permission.updated_by = updater_id
        
        db.commit()
        db.refresh(permission)
        return permission
    
    def revoke_permissions(self, db: Session, permission_id: int, revoker_id: int) -> bool:
        """Revoke health record permissions"""
        permission = db.query(HealthRecordPermission).filter(HealthRecordPermission.id == permission_id).first()
        if not permission:
            return False
        
        # Only patient or granter can revoke permissions
        if permission.patient_id != revoker_id and permission.granted_by != revoker_id:
            return False
        
        permission.is_active = False
        permission.updated_at = datetime.utcnow()
        permission.updated_by = revoker_id
        
        db.commit()
        return True

# ============================================================================
# INSTANCES
# ============================================================================

document_crud = DocumentCRUD()
document_permission_crud = DocumentPermissionCRUD()
document_share_crud = DocumentShareCRUD()
lab_document_crud = LabDocumentCRUD()
imaging_document_crud = ImagingDocumentCRUD()
health_record_permission_crud = HealthRecordPermissionCRUD()
