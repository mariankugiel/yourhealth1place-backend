from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.appointment import Appointment

class AppointmentCRUD:
    
    def get_appointment(self, db: Session, appointment_id: int) -> Optional[Appointment]:
        """Get appointment by ID"""
        return db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    def get_by_patient(self, db: Session, patient_id: int) -> List[Appointment]:
        """Get all appointments for a patient"""
        return db.query(Appointment).filter(Appointment.patient_id == patient_id).all()

appointment_crud = AppointmentCRUD()
