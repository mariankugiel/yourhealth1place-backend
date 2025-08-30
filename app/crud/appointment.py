from sqlalchemy.orm import Session
from typing import Optional
from app.models.appointment import Appointment

class AppointmentCRUD:
    
    def get_appointment(self, db: Session, appointment_id: int) -> Optional[Appointment]:
        """Get appointment by ID"""
        return db.query(Appointment).filter(Appointment.id == appointment_id).first()

appointment_crud = AppointmentCRUD()
