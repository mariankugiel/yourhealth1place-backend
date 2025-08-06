from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.patient_insight import PatientInsight, InsightType
from app.schemas.patient_insight import PatientInsightCreate, PatientInsightUpdate

class PatientInsightCRUD:
    
    def create(self, db: Session, insight_data: PatientInsightCreate) -> PatientInsight:
        """Create a new patient insight"""
        db_insight = PatientInsight(**insight_data.dict())
        db.add(db_insight)
        db.commit()
        db.refresh(db_insight)
        return db_insight
    
    def get_by_id(self, db: Session, insight_id: int) -> Optional[PatientInsight]:
        """Get patient insight by ID"""
        return db.query(PatientInsight).filter(PatientInsight.id == insight_id).first()
    
    def get_all(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        professional_id: Optional[int] = None,
        patient_id: Optional[int] = None,
        insight_type: Optional[str] = None,
        category: Optional[str] = None,
        is_read: Optional[bool] = None,
        requires_action: Optional[bool] = None
    ) -> List[PatientInsight]:
        """Get all patient insights with optional filters"""
        query = db.query(PatientInsight)
        
        if professional_id:
            query = query.filter(PatientInsight.professional_id == professional_id)
        if patient_id:
            query = query.filter(PatientInsight.patient_id == patient_id)
        if insight_type:
            query = query.filter(PatientInsight.insight_type == insight_type)
        if category:
            query = query.filter(PatientInsight.category == category)
        if is_read is not None:
            query = query.filter(PatientInsight.is_read == is_read)
        if requires_action is not None:
            query = query.filter(PatientInsight.requires_action == requires_action)
            
        return query.offset(skip).limit(limit).all()
    
    def get_by_professional(
        self, 
        db: Session, 
        professional_id: int,
        skip: int = 0,
        limit: int = 100,
        insight_type: Optional[str] = None,
        is_read: Optional[bool] = None
    ) -> List[PatientInsight]:
        """Get insights by professional"""
        query = db.query(PatientInsight).filter(PatientInsight.professional_id == professional_id)
        
        if insight_type:
            query = query.filter(PatientInsight.insight_type == insight_type)
        if is_read is not None:
            query = query.filter(PatientInsight.is_read == is_read)
            
        return query.offset(skip).limit(limit).all()
    
    def get_by_patient(
        self, 
        db: Session, 
        patient_id: int,
        skip: int = 0,
        limit: int = 100,
        insight_type: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[PatientInsight]:
        """Get insights by patient"""
        query = db.query(PatientInsight).filter(PatientInsight.patient_id == patient_id)
        
        if insight_type:
            query = query.filter(PatientInsight.insight_type == insight_type)
        if category:
            query = query.filter(PatientInsight.category == category)
            
        return query.offset(skip).limit(limit).all()
    
    def update(
        self, 
        db: Session, 
        insight_id: int, 
        insight_data: PatientInsightUpdate
    ) -> Optional[PatientInsight]:
        """Update patient insight"""
        db_insight = self.get_by_id(db, insight_id)
        if not db_insight:
            return None
            
        update_data = insight_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_insight, field, value)
            
        db_insight.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_insight)
        return db_insight
    
    def acknowledge(
        self, 
        db: Session, 
        insight_id: int, 
        action_taken: Optional[str] = None
    ) -> Optional[PatientInsight]:
        """Acknowledge a patient insight"""
        db_insight = self.get_by_id(db, insight_id)
        if not db_insight:
            return None
            
        db_insight.is_acknowledged = True
        db_insight.acknowledged_at = datetime.utcnow()
        if action_taken:
            db_insight.action_taken = action_taken
        db_insight.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_insight)
        return db_insight
    
    def resolve(
        self, 
        db: Session, 
        insight_id: int
    ) -> Optional[PatientInsight]:
        """Resolve a patient insight"""
        db_insight = self.get_by_id(db, insight_id)
        if not db_insight:
            return None
            
        db_insight.resolved_at = datetime.utcnow()
        db_insight.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_insight)
        return db_insight
    
    def delete(self, db: Session, insight_id: int) -> bool:
        """Delete patient insight"""
        db_insight = self.get_by_id(db, insight_id)
        if not db_insight:
            return False
            
        db.delete(db_insight)
        db.commit()
        return True
    
    def get_unread_by_professional(
        self, 
        db: Session, 
        professional_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[PatientInsight]:
        """Get unread insights for a professional"""
        return db.query(PatientInsight).filter(
            and_(
                PatientInsight.professional_id == professional_id,
                PatientInsight.is_read == False
            )
        ).offset(skip).limit(limit).all()
    
    def get_urgent_by_professional(
        self, 
        db: Session, 
        professional_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[PatientInsight]:
        """Get urgent insights for a professional"""
        return db.query(PatientInsight).filter(
            and_(
                PatientInsight.professional_id == professional_id,
                PatientInsight.insight_type == InsightType.URGENT
            )
        ).offset(skip).limit(limit).all()
    
    def mark_as_read(
        self, 
        db: Session, 
        insight_id: int
    ) -> Optional[PatientInsight]:
        """Mark insight as read"""
        db_insight = self.get_by_id(db, insight_id)
        if not db_insight:
            return None
            
        db_insight.is_read = True
        db_insight.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_insight)
        return db_insight
    
    def get_insights_summary(
        self, 
        db: Session, 
        professional_id: int
    ) -> Dict[str, Any]:
        """Get insights summary for a professional"""
        total_insights = db.query(PatientInsight).filter(
            PatientInsight.professional_id == professional_id
        ).count()
        
        unread_insights = db.query(PatientInsight).filter(
            and_(
                PatientInsight.professional_id == professional_id,
                PatientInsight.is_read == False
            )
        ).count()
        
        urgent_insights = db.query(PatientInsight).filter(
            and_(
                PatientInsight.professional_id == professional_id,
                PatientInsight.insight_type == InsightType.URGENT
            )
        ).count()
        
        return {
            "total_insights": total_insights,
            "unread_insights": unread_insights,
            "urgent_insights": urgent_insights
        }

patient_insight_crud = PatientInsightCRUD() 