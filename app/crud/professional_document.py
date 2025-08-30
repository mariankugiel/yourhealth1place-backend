from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.models.professional_documents import (
    ProfessionalDocument,
    ProfessionalDocumentAssignment,
    ProfessionalDocumentCategory
)
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.professional import Professional
from app.schemas.professional_document import (
    ProfessionalDocumentCreate,
    ProfessionalDocumentUpdate,
    DocumentAssignmentCreate,
    DocumentAssignmentUpdate,
    PatientDataForDocument,
    CreateDocumentFromTemplate
)

class ProfessionalDocumentCRUD:
    
    # Document CRUD operations
    def create_document(
        self, 
        db: Session, 
        document_data: ProfessionalDocumentCreate,
        professional_id: int,
        created_by: int
    ) -> ProfessionalDocument:
        """Create a new document (can be a template)"""
        db_document = ProfessionalDocument(
            professional_id=professional_id,
            category_id=document_data.category_id,
            title=document_data.title,
            description=document_data.description,
            file_name=document_data.file_name,
            original_file_name=document_data.original_file_name,
            file_type=document_data.file_type,
            file_size=document_data.file_size,
            file_extension=document_data.file_extension,
            s3_url=document_data.s3_url,
            s3_key=document_data.s3_key,
            is_template=document_data.is_template,
            tags=document_data.tags,
            metadata=document_data.metadata,
            created_by=created_by
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        return db_document
    
    def get_document(self, db: Session, document_id: int) -> Optional[ProfessionalDocument]:
        return db.query(ProfessionalDocument).filter(
            ProfessionalDocument.id == document_id
        ).first()
    
    def get_documents_by_professional(
        self, 
        db: Session, 
        professional_id: int,
        is_template: Optional[bool] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[ProfessionalDocument]:
        query = db.query(ProfessionalDocument).filter(
            ProfessionalDocument.professional_id == professional_id
        )
        
        if is_template is not None:
            query = query.filter(ProfessionalDocument.is_template == is_template)
        
        return query.offset(skip).limit(limit).all()
    
    def get_templates_by_professional(
        self,
        db: Session,
        professional_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[ProfessionalDocument]:
        """Get all templates for a professional"""
        return self.get_documents_by_professional(
            db, professional_id, is_template=True, skip=skip, limit=limit
        )
    
    def update_document(
        self, 
        db: Session, 
        document_id: int,
        document_data: ProfessionalDocumentUpdate,
        updated_by: int
    ) -> Optional[ProfessionalDocument]:
        db_document = self.get_document(db, document_id)
        if not db_document:
            return None
        
        update_data = document_data.dict(exclude_unset=True)
        update_data["updated_by"] = updated_by
        update_data["updated_at"] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(db_document, field, value)
        
        db.commit()
        db.refresh(db_document)
        return db_document
    
    def create_document_from_template(
        self,
        db: Session,
        template_data: CreateDocumentFromTemplate,
        professional_id: int,
        created_by: int
    ) -> ProfessionalDocument:
        """
        Create a new document from an existing template
        This is the key function for your workflow!
        """
        # Get the template document
        template = self.get_document(db, template_data.template_document_id)
        if not template or not template.is_template:
            raise ValueError("Template document not found or not marked as template")
        
        # Get appointment details
        appointment = db.query(Appointment).filter(Appointment.id == template_data.appointment_id).first()
        if not appointment:
            raise ValueError("Appointment not found")
        
        # Get patient details
        patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
        if not patient:
            raise ValueError("Patient not found")
        
        # Create new document based on template
        new_document_data = ProfessionalDocumentCreate(
            category_id=template.category_id,
            title=template_data.new_title,
            description=f"Created from template: {template.title}",
            file_name=f"{template.file_name}_{uuid.uuid4().hex[:8]}",
            original_file_name=template.original_file_name,
            file_type=template.file_type,
            file_size=template.file_size,
            file_extension=template.file_extension,
            s3_url=template.s3_url,  # This would be updated with new file
            s3_key=template.s3_key,  # This would be updated with new file
            is_template=False,  # New document is not a template
            tags=template.tags,
            metadata={
                "source_template_id": template.id,
                "appointment_id": template_data.appointment_id,
                "patient_data": template_data.patient_data.dict(),
                "custom_variables": template_data.custom_variables or {},
                "created_from_template": True
            }
        )
        
        # TODO: Here you would process the template file with patient data
        # and create a new file with filled information
        # For now, we'll create the document record
        
        return self.create_document(
            db, new_document_data, professional_id, created_by
        )
    
    # Document Assignment CRUD operations
    def create_document_assignment(
        self,
        db: Session,
        assignment_data: DocumentAssignmentCreate,
        created_by: int
    ) -> ProfessionalDocumentAssignment:
        db_assignment = ProfessionalDocumentAssignment(
            appointment_id=assignment_data.appointment_id,
            document_id=assignment_data.document_id,
            assignment_type=assignment_data.assignment_type,
            assignment_notes=assignment_data.assignment_notes,
            is_required=assignment_data.is_required,
            created_by=created_by
        )
        db.add(db_assignment)
        db.commit()
        db.refresh(db_assignment)
        return db_assignment
    
    def get_document_assignments_by_appointment(
        self,
        db: Session,
        appointment_id: int
    ) -> List[ProfessionalDocumentAssignment]:
        return db.query(ProfessionalDocumentAssignment).filter(
            ProfessionalDocumentAssignment.appointment_id == appointment_id
        ).all()
    
    def update_document_assignment(
        self,
        db: Session,
        assignment_id: int,
        assignment_data: DocumentAssignmentUpdate,
        updated_by: int
    ) -> Optional[ProfessionalDocumentAssignment]:
        db_assignment = db.query(ProfessionalDocumentAssignment).filter(
            ProfessionalDocumentAssignment.id == assignment_id
        ).first()
        
        if not db_assignment:
            return None
        
        update_data = assignment_data.dict(exclude_unset=True)
        update_data["updated_by"] = updated_by
        update_data["updated_at"] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(db_assignment, field, value)
        
        db.commit()
        db.refresh(db_assignment)
        return db_assignment
    
    def get_appointment_document_summary(
        self,
        db: Session,
        appointment_id: int
    ) -> Dict[str, Any]:
        """Get a summary of all documents for an appointment"""
        assignments = self.get_document_assignments_by_appointment(db, appointment_id)
        
        total_documents = len(assignments)
        completed_documents = len([a for a in assignments if a.is_completed])
        pending_documents = total_documents - completed_documents
        
        document_types = list(set([a.assignment_type for a in assignments]))
        
        # Get the actual documents
        document_ids = [a.document_id for a in assignments]
        documents = db.query(ProfessionalDocument).filter(
            ProfessionalDocument.id.in_(document_ids)
        ).all() if document_ids else []
        
        return {
            "appointment_id": appointment_id,
            "total_documents": total_documents,
            "completed_documents": completed_documents,
            "pending_documents": pending_documents,
            "document_types": document_types,
            "assignments": assignments,
            "documents": documents
        }

# Create a singleton instance
professional_document_crud = ProfessionalDocumentCRUD()
