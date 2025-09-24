from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.medication import Medication

class MedicationCRUD:
    """CRUD operations for medications"""
    
    def get_by_patient(self, db: Session, patient_id: int) -> List[Medication]:
        """Get all medications for a patient"""
        return db.query(Medication).filter(
            Medication.patient_id == patient_id
        ).all()
    
    def get_by_id(self, db: Session, medication_id: int) -> Optional[Medication]:
        """Get medication by ID"""
        return db.query(Medication).filter(Medication.id == medication_id).first()
    
    def create(self, db: Session, medication_data: dict) -> Medication:
        """Create a new medication"""
        medication = Medication(**medication_data)
        db.add(medication)
        db.commit()
        db.refresh(medication)
        return medication
    
    def update(self, db: Session, medication_id: int, medication_data: dict) -> Optional[Medication]:
        """Update a medication"""
        medication = self.get_by_id(db, medication_id)
        if not medication:
            return None
        
        for field, value in medication_data.items():
            if hasattr(medication, field):
                setattr(medication, field, value)
        
        db.commit()
        db.refresh(medication)
        return medication
    
    def delete(self, db: Session, medication_id: int) -> bool:
        """Delete a medication"""
        medication = self.get_by_id(db, medication_id)
        if not medication:
            return False
        
        db.delete(medication)
        db.commit()
        return True

# Create instance
medication_crud = MedicationCRUD()
