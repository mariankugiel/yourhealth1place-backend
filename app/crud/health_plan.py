from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.health_plan import HealthPlan, PlanStatus
from app.schemas.health_plan import HealthPlanCreate, HealthPlanUpdate

class HealthPlanCRUD:
    
    def create(self, db: Session, health_plan_data: HealthPlanCreate) -> HealthPlan:
        """Create a new health plan"""
        db_health_plan = HealthPlan(**health_plan_data.dict())
        db.add(db_health_plan)
        db.commit()
        db.refresh(db_health_plan)
        return db_health_plan
    
    def get_by_id(self, db: Session, health_plan_id: int) -> Optional[HealthPlan]:
        """Get health plan by ID"""
        return db.query(HealthPlan).filter(HealthPlan.id == health_plan_id).first()
    
    def get_all(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        professional_id: Optional[int] = None,
        patient_id: Optional[int] = None,
        status: Optional[str] = None,
        plan_type: Optional[str] = None
    ) -> List[HealthPlan]:
        """Get all health plans with optional filters"""
        query = db.query(HealthPlan)
        
        if professional_id:
            query = query.filter(HealthPlan.professional_id == professional_id)
        if patient_id:
            query = query.filter(HealthPlan.patient_id == patient_id)
        if status:
            query = query.filter(HealthPlan.status == status)
        if plan_type:
            query = query.filter(HealthPlan.plan_type == plan_type)
            
        return query.offset(skip).limit(limit).all()
    
    def get_by_professional(
        self, 
        db: Session, 
        professional_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[HealthPlan]:
        """Get health plans by professional"""
        query = db.query(HealthPlan).filter(HealthPlan.professional_id == professional_id)
        
        if status:
            query = query.filter(HealthPlan.status == status)
            
        return query.offset(skip).limit(limit).all()
    
    def get_by_patient(
        self, 
        db: Session, 
        patient_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[HealthPlan]:
        """Get health plans by patient"""
        query = db.query(HealthPlan).filter(HealthPlan.patient_id == patient_id)
        
        if status:
            query = query.filter(HealthPlan.status == status)
            
        return query.offset(skip).limit(limit).all()
    
    def update(
        self, 
        db: Session, 
        health_plan_id: int, 
        health_plan_data: HealthPlanUpdate
    ) -> Optional[HealthPlan]:
        """Update health plan"""
        db_health_plan = self.get_by_id(db, health_plan_id)
        if not db_health_plan:
            return None
            
        update_data = health_plan_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_health_plan, field, value)
            
        db_health_plan.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_health_plan)
        return db_health_plan
    
    def update_status(
        self, 
        db: Session, 
        health_plan_id: int, 
        status: str
    ) -> Optional[HealthPlan]:
        """Update health plan status"""
        db_health_plan = self.get_by_id(db, health_plan_id)
        if not db_health_plan:
            return None
            
        db_health_plan.status = status
        db_health_plan.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_health_plan)
        return db_health_plan
    
    def delete(self, db: Session, health_plan_id: int) -> bool:
        """Delete health plan"""
        db_health_plan = self.get_by_id(db, health_plan_id)
        if not db_health_plan:
            return False
            
        db.delete(db_health_plan)
        db.commit()
        return True
    
    def get_progress(self, db: Session, health_plan_id: int) -> List[Dict[str, Any]]:
        """Get health plan progress milestones"""
        # This would typically query the HealthPlanProgress table
        # For now, returning a basic structure
        return [
            {
                "milestone_id": "1",
                "title": "Initial Assessment",
                "status": "completed",
                "completion_percentage": 100,
                "due_date": "2025-01-15",
                "completed_date": "2025-01-10"
            },
            {
                "milestone_id": "2",
                "title": "Treatment Plan Review",
                "status": "in_progress",
                "completion_percentage": 60,
                "due_date": "2025-02-01",
                "completed_date": None
            }
        ]
    
    def search_health_plans(
        self, 
        db: Session, 
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[HealthPlan]:
        """Search health plans by title, description, or target condition"""
        return db.query(HealthPlan).filter(
            or_(
                HealthPlan.title.ilike(f"%{search_term}%"),
                HealthPlan.description.ilike(f"%{search_term}%"),
                HealthPlan.target_condition.ilike(f"%{search_term}%")
            )
        ).offset(skip).limit(limit).all()
    
    def get_active_plans_count(self, db: Session, professional_id: int) -> int:
        """Get count of active health plans for a professional"""
        return db.query(HealthPlan).filter(
            and_(
                HealthPlan.professional_id == professional_id,
                HealthPlan.status == PlanStatus.ACTIVE
            )
        ).count()
    
    def get_completed_plans_count(self, db: Session, professional_id: int) -> int:
        """Get count of completed health plans for a professional"""
        return db.query(HealthPlan).filter(
            and_(
                HealthPlan.professional_id == professional_id,
                HealthPlan.status == PlanStatus.COMPLETED
            )
        ).count()

health_plan_crud = HealthPlanCRUD() 