from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.models.professional import Professional
from app.models.user import User
from app.schemas.professional import ProfessionalCreate, ProfessionalUpdate

class ProfessionalCRUD:
    
    def create(self, db: Session, professional_data: ProfessionalCreate) -> Professional:
        """Create a new professional"""
        db_professional = Professional(**professional_data.dict())
        db.add(db_professional)
        db.commit()
        db.refresh(db_professional)
        return db_professional
    
    def get_by_id(self, db: Session, professional_id: int) -> Optional[Professional]:
        """Get professional by ID"""
        return db.query(Professional).filter(Professional.id == professional_id).first()
    
    def get_by_user_id(self, db: Session, user_id: int) -> Optional[Professional]:
        """Get professional by user ID"""
        return db.query(Professional).filter(Professional.user_id == user_id).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[Professional]:
        """Get professional by email"""
        return db.query(Professional).join(User).filter(User.email == email).first()
    
    def get_by_license(self, db: Session, license_number: str) -> Optional[Professional]:
        """Get professional by license number"""
        return db.query(Professional).filter(Professional.license_number == license_number).first()
    
    def get_all(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        specialty: Optional[str] = None,
        is_available: Optional[bool] = None,
        is_verified: Optional[bool] = None
    ) -> List[Professional]:
        """Get all professionals with optional filters"""
        query = db.query(Professional)
        
        if specialty:
            query = query.filter(Professional.specialty == specialty)
        if is_available is not None:
            query = query.filter(Professional.is_available == is_available)
        if is_verified is not None:
            query = query.filter(Professional.is_verified == is_verified)
            
        return query.offset(skip).limit(limit).all()
    
    def update(
        self, 
        db: Session, 
        professional_id: int, 
        professional_data: ProfessionalUpdate
    ) -> Optional[Professional]:
        """Update professional"""
        db_professional = self.get_by_id(db, professional_id)
        if not db_professional:
            return None
            
        update_data = professional_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_professional, field, value)
            
        db_professional.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_professional)
        return db_professional
    
    def delete(self, db: Session, professional_id: int) -> bool:
        """Delete professional"""
        db_professional = self.get_by_id(db, professional_id)
        if not db_professional:
            return False
            
        db.delete(db_professional)
        db.commit()
        return True
    
    def get_available_professionals(
        self, 
        db: Session, 
        specialty: Optional[str] = None,
        consultation_type: Optional[str] = None
    ) -> List[Professional]:
        """Get available professionals for appointments"""
        query = db.query(Professional).filter(
            and_(
                Professional.is_available == True,
                Professional.is_active == True
            )
        )
        
        if specialty:
            query = query.filter(Professional.specialty == specialty)
        if consultation_type:
            query = query.filter(Professional.consultation_types.contains([consultation_type]))
            
        return query.all()
    
    def get_professional_statistics(
        self, 
        db: Session, 
        professional_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get professional statistics for a date range"""
        # This would typically query multiple tables for comprehensive stats
        # For now, returning a basic structure
        return {
            "professional_id": professional_id,
            "period_start": start_date,
            "period_end": end_date,
            "total_appointments": 0,
            "completed_appointments": 0,
            "total_patients": 0,
            "revenue": 0.0
        }
    
    def search_professionals(
        self, 
        db: Session, 
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Professional]:
        """Search professionals by name, specialty, or license"""
        return db.query(Professional).filter(
            or_(
                Professional.first_name.ilike(f"%{search_term}%"),
                Professional.last_name.ilike(f"%{search_term}%"),
                Professional.specialty.ilike(f"%{search_term}%"),
                Professional.license_number.ilike(f"%{search_term}%")
            )
        ).offset(skip).limit(limit).all()
    
    def get_professionals_by_specialty(
        self, 
        db: Session, 
        specialty: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Professional]:
        """Get professionals by specialty"""
        return db.query(Professional).filter(
            and_(
                Professional.specialty == specialty,
                Professional.is_active == True
            )
        ).offset(skip).limit(limit).all()
    
    def update_availability(
        self, 
        db: Session, 
        professional_id: int, 
        is_available: bool,
        availability_schedule: Optional[Dict[str, Any]] = None
    ) -> Optional[Professional]:
        """Update professional availability"""
        db_professional = self.get_by_id(db, professional_id)
        if not db_professional:
            return None
            
        db_professional.is_available = is_available
        if availability_schedule:
            db_professional.availability_schedule = availability_schedule
        db_professional.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_professional)
        return db_professional

professional_crud = ProfessionalCRUD() 