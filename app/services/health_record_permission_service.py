from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.models.permissions import HealthRecordPermission
from app.models.user import User
from app.models.health_record import HealthRecord, MedicalCondition, FamilyMedicalHistory
from app.models.health_plans import HealthPlan
from app.models.medication import Medication
from app.models.appointment import Appointment
from app.models.message import Message
from app.models.documents import Document
from app.crud.health_record import health_record_crud
from app.crud.health_plan import health_plan_crud
from app.crud.medication import medication_crud
from app.crud.appointment import appointment_crud
from app.crud.message import message_crud
from app.crud.document import document_crud
import logging

logger = logging.getLogger(__name__)

class HealthRecordPermissionService:
    """Service for managing and checking health record permissions"""
    
    def check_health_record_access(
        self, 
        db: Session, 
        patient_id: int, 
        professional_id: int,
        access_type: str = "view"
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a professional has access to a patient's health records
        
        Args:
            db: Database session
            patient_id: ID of the patient
            professional_id: ID of the professional
            access_type: Type of access ("view", "edit", "download")
            
        Returns:
            Tuple[bool, Optional[str]]: (has_access, reason_if_denied)
        """
        try:
            # Check if there's an active permission record
            permission = db.query(HealthRecordPermission).filter(
                and_(
                    HealthRecordPermission.patient_id == patient_id,
                    HealthRecordPermission.professional_id == professional_id,
                    HealthRecordPermission.is_active == True
                )
            ).first()
            
            if not permission:
                return False, "No active permission record found"
            
            # Check if permission has expired
            if permission.expires_at and permission.expires_at < db.query(func.now()).scalar():
                return False, "Permission has expired"
            
            # Check specific access type
            if access_type == "view":
                if not permission.can_view_health_records:
                    return False, "No permission to view health records"
            elif access_type == "edit":
                # For now, only view permissions are implemented
                return False, "Edit permissions not yet implemented"
            elif access_type == "download":
                # For now, only view permissions are implemented
                return False, "Download permissions not yet implemented"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking health record access: {e}")
            return False, f"Error checking permissions: {str(e)}"
    
    def check_medical_history_access(
        self, 
        db: Session, 
        patient_id: int, 
        professional_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Check if professional can access patient's medical history"""
        try:
            permission = db.query(HealthRecordPermission).filter(
                and_(
                    HealthRecordPermission.patient_id == patient_id,
                    HealthRecordPermission.professional_id == professional_id,
                    HealthRecordPermission.is_active == True
                )
            ).first()
            
            if not permission:
                return False, "No active permission record found"
            
            if permission.expires_at and permission.expires_at < db.query(func.now()).scalar():
                return False, "Permission has expired"
            
            if not permission.can_view_medical_history:
                return False, "No permission to view medical history"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking medical history access: {e}")
            return False, f"Error checking permissions: {str(e)}"
    
    def check_health_plan_access(
        self, 
        db: Session, 
        patient_id: int, 
        professional_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Check if professional can access patient's health plans"""
        try:
            permission = db.query(HealthRecordPermission).filter(
                and_(
                    HealthRecordPermission.patient_id == patient_id,
                    HealthRecordPermission.professional_id == professional_id,
                    HealthRecordPermission.is_active == True
                )
            ).first()
            
            if not permission:
                return False, "No active permission record found"
            
            if permission.expires_at and permission.expires_at < db.query(func.now()).scalar():
                return False, "Permission has expired"
            
            if not permission.can_view_health_plans:
                return False, "No permission to view health plans"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking health plan access: {e}")
            return False, f"Error checking permissions: {str(e)}"
    
    def check_medication_access(
        self, 
        db: Session, 
        patient_id: int, 
        professional_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Check if professional can access patient's medications"""
        try:
            permission = db.query(HealthRecordPermission).filter(
                and_(
                    HealthRecordPermission.patient_id == patient_id,
                    HealthRecordPermission.professional_id == professional_id,
                    HealthRecordPermission.is_active == True
                )
            ).first()
            
            if not permission:
                return False, "No active permission record found"
            
            if permission.expires_at and permission.expires_at < db.query(func.now()).scalar():
                return False, "Permission has expired"
            
            if not permission.can_view_medications:
                return False, "No permission to view medications"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking medication access: {e}")
            return False, f"Error checking permissions: {str(e)}"
    
    def check_appointment_access(
        self, 
        db: Session, 
        patient_id: int, 
        professional_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Check if professional can access patient's appointments"""
        try:
            permission = db.query(HealthRecordPermission).filter(
                and_(
                    HealthRecordPermission.patient_id == patient_id,
                    HealthRecordPermission.professional_id == professional_id,
                    HealthRecordPermission.is_active == True
                )
            ).first()
            
            if not permission:
                return False, "No active permission record found"
            
            if permission.expires_at and permission.expires_at < db.query(func.now()).scalar():
                return False, "Permission has expired"
            
            if not permission.can_view_appointments:
                return False, "No permission to view appointments"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking appointment access: {e}")
            return False, f"Error checking permissions: {str(e)}"
    
    def check_message_access(
        self, 
        db: Session, 
        patient_id: int, 
        professional_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Check if professional can access patient's messages"""
        try:
            permission = db.query(HealthRecordPermission).filter(
                and_(
                    HealthRecordPermission.patient_id == patient_id,
                    HealthRecordPermission.professional_id == professional_id,
                    HealthRecordPermission.is_active == True
                )
            ).first()
            
            if not permission:
                return False, "No active permission record found"
            
            if permission.expires_at and permission.expires_at < db.query(func.now()).scalar():
                return False, "Permission has expired"
            
            if not permission.can_view_messages:
                return False, "No permission to view messages"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking message access: {e}")
            return False, f"Error checking permissions: {str(e)}"
    
    def check_lab_result_access(
        self, 
        db: Session, 
        patient_id: int, 
        professional_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Check if professional can access patient's lab results"""
        try:
            permission = db.query(HealthRecordPermission).filter(
                and_(
                    HealthRecordPermission.patient_id == patient_id,
                    HealthRecordPermission.professional_id == professional_id,
                    HealthRecordPermission.is_active == True
                )
            ).first()
            
            if not permission:
                return False, "No active permission record found"
            
            if permission.expires_at and permission.expires_at < db.query(func.now()).scalar():
                return False, "Permission has expired"
            
            if not permission.can_view_lab_results:
                return False, "No permission to view lab results"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking lab result access: {e}")
            return False, f"Error checking permissions: {str(e)}"
    
    def check_imaging_access(
        self, 
        db: Session, 
        patient_id: int, 
        professional_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Check if professional can access patient's imaging"""
        try:
            permission = db.query(HealthRecordPermission).filter(
                and_(
                    HealthRecordPermission.patient_id == patient_id,
                    HealthRecordPermission.professional_id == professional_id,
                    HealthRecordPermission.is_active == True
                )
            ).first()
            
            if not permission:
                return False, "No active permission record found"
            
            if permission.expires_at and permission.expires_at < db.query(func.now()).scalar():
                return False, "Permission has expired"
            
            if not permission.can_view_imaging:
                return False, "No permission to view imaging"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking imaging access: {e}")
            return False, f"Error checking permissions: {str(e)}"
    
    def get_patient_data_with_permissions(
        self, 
        db: Session, 
        patient_id: int, 
        professional_id: int
    ) -> Dict[str, Any]:
        """
        Get patient data based on granted permissions
        
        Args:
            db: Database session
            patient_id: ID of the patient
            professional_id: ID of the professional
            
        Returns:
            Dict containing available data based on permissions
        """
        try:
            permission = db.query(HealthRecordPermission).filter(
                and_(
                    HealthRecordPermission.patient_id == patient_id,
                    HealthRecordPermission.professional_id == professional_id,
                    HealthRecordPermission.is_active == True
                )
            ).first()
            
            if not permission:
                return {"error": "No active permission record found"}
            
            if permission.expires_at and permission.expires_at < db.query(func.now()).scalar():
                return {"error": "Permission has expired"}
            
            result = {
                "patient_id": patient_id,
                "professional_id": professional_id,
                "permission_granted_for": permission.granted_for,
                "expires_at": permission.expires_at,
                "data": {}
            }
            
            # Get health records if permitted
            if permission.can_view_health_records:
                health_records = health_record_crud.get_by_user(db, patient_id, limit=100)
                result["data"]["health_records"] = [
                    {
                        "id": record.id,
                        "section_id": record.section_id,
                        "metric_id": record.metric_id,
                        "value": record.value,
                        "status": record.status,
                        "recorded_at": record.recorded_at
                    } for record in health_records
                ]
            
            # Get medical conditions if permitted
            if permission.can_view_medical_history:
                medical_conditions = db.query(MedicalCondition).filter(
                    MedicalCondition.created_by == patient_id
                ).all()
                result["data"]["medical_conditions"] = [
                    {
                        "id": condition.id,
                        "condition_name": condition.condition_name,
                        "status": condition.status,
                        "severity": condition.severity,
                        "diagnosed_date": condition.diagnosed_date
                    } for condition in medical_conditions
                ]
            
            # Get health plans if permitted
            if permission.can_view_health_plans:
                health_plans = health_plan_crud.get_by_patient(db, patient_id)
                result["data"]["health_plans"] = [
                    {
                        "id": plan.id,
                        "name": plan.name,
                        "status": plan.status,
                        "start_date": plan.start_date,
                        "end_date": plan.end_date
                    } for plan in health_plans
                ]
            
            # Get medications if permitted
            if permission.can_view_medications:
                medications = medication_crud.get_by_patient(db, patient_id)
                result["data"]["medications"] = [
                    {
                        "id": med.id,
                        "name": med.name,
                        "dosage": med.dosage,
                        "frequency": med.frequency,
                        "status": med.status
                    } for med in medications
                ]
            
            # Get appointments if permitted
            if permission.can_view_appointments:
                appointments = appointment_crud.get_by_patient(db, patient_id)
                result["data"]["appointments"] = [
                    {
                        "id": apt.id,
                        "scheduled_at": apt.scheduled_at,
                        "status": apt.status,
                        "appointment_category": apt.appointment_category
                    } for apt in appointments
                ]
            
            # Get messages if permitted
            if permission.can_view_messages:
                messages = message_crud.get_by_user(db, patient_id, limit=50)
                result["data"]["messages"] = [
                    {
                        "id": msg.id,
                        "content": msg.content,
                        "message_type": msg.message_type,
                        "created_at": msg.created_at
                    } for msg in messages
                ]
            
            # Get lab results if permitted
            if permission.can_view_lab_results:
                lab_documents = document_crud.get_by_category(db, patient_id, "lab_results")
                result["data"]["lab_results"] = [
                    {
                        "id": doc.id,
                        "title": doc.title,
                        "file_name": doc.file_name,
                        "created_at": doc.created_at
                    } for doc in lab_documents
                ]
            
            # Get imaging if permitted
            if permission.can_view_imaging:
                imaging_documents = document_crud.get_by_category(db, patient_id, "imaging")
                result["data"]["imaging"] = [
                    {
                        "id": doc.id,
                        "title": doc.title,
                        "file_name": doc.file_name,
                        "created_at": doc.created_at
                    } for doc in imaging_documents
                ]
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting patient data with permissions: {e}")
            return {"error": f"Error retrieving patient data: {str(e)}"}
    
    def grant_temporary_access(
        self, 
        db: Session, 
        patient_id: int, 
        professional_id: int, 
        permissions: Dict[str, bool], 
        granter_id: int,
        granted_for: str = "consultation",
        expires_in_hours: int = 24
    ) -> Optional[HealthRecordPermission]:
        """
        Grant temporary access to health records for a specific purpose
        
        Args:
            db: Database session
            patient_id: ID of the patient
            professional_id: ID of the professional
            permissions: Dict of permission flags
            granter_id: ID of the user granting permissions
            granted_for: Context for the permission
            expires_in_hours: Hours until permission expires
            
        Returns:
            HealthRecordPermission or None if failed
        """
        try:
            from datetime import timedelta
            
            # Calculate expiration time
            expires_at = db.query(func.now()).scalar() + timedelta(hours=expires_in_hours)
            
            # Create or update permission
            existing_permission = db.query(HealthRecordPermission).filter(
                and_(
                    HealthRecordPermission.patient_id == patient_id,
                    HealthRecordPermission.professional_id == professional_id
                )
            ).first()
            
            if existing_permission:
                # Update existing permission
                existing_permission.can_view_health_records = permissions.get('can_view_health_records', False)
                existing_permission.can_view_medical_history = permissions.get('can_view_medical_history', False)
                existing_permission.can_view_health_plans = permissions.get('can_view_health_plans', False)
                existing_permission.can_view_medications = permissions.get('can_view_medications', False)
                existing_permission.can_view_appointments = permissions.get('can_view_appointments', False)
                existing_permission.can_view_messages = permissions.get('can_view_messages', False)
                existing_permission.can_view_lab_results = permissions.get('can_view_lab_results', False)
                existing_permission.can_view_imaging = permissions.get('can_view_imaging', False)
                existing_permission.granted_for = granted_for
                existing_permission.expires_at = expires_at
                existing_permission.is_active = True
                
                db.commit()
                db.refresh(existing_permission)
                return existing_permission
            else:
                # Create new permission
                new_permission = HealthRecordPermission(
                    patient_id=patient_id,
                    professional_id=professional_id,
                    can_view_health_records=permissions.get('can_view_health_records', False),
                    can_view_medical_history=permissions.get('can_view_medical_history', False),
                    can_view_health_plans=permissions.get('can_view_health_plans', False),
                    can_view_medications=permissions.get('can_view_medications', False),
                    can_view_appointments=permissions.get('can_view_appointments', False),
                    can_view_messages=permissions.get('can_view_messages', False),
                    can_view_lab_results=permissions.get('can_view_lab_results', False),
                    can_view_imaging=permissions.get('can_view_imaging', False),
                    granted_for=granted_for,
                    expires_at=expires_at,
                    granted_by=granter_id
                )
                
                db.add(new_permission)
                db.commit()
                db.refresh(new_permission)
                return new_permission
                
        except Exception as e:
            logger.error(f"Error granting temporary access: {e}")
            db.rollback()
            return None

# Create service instance
health_record_permission_service = HealthRecordPermissionService()
