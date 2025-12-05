from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.models.ai_analysis import AIAnalysisHistory
from typing import Optional, List
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

class AIAnalysisHistoryCRUD:
    """CRUD operations for AI Analysis History"""
    
    def get_by_user_and_type(self, db: Session, user_id: int, analysis_type_id: int) -> Optional[AIAnalysisHistory]:
        """Get the latest AI analysis history for a user and analysis type"""
        return db.query(AIAnalysisHistory).filter(
            and_(
                AIAnalysisHistory.user_id == user_id,
                AIAnalysisHistory.analysis_type_id == analysis_type_id,
                AIAnalysisHistory.is_active == True
            )
        ).order_by(desc(AIAnalysisHistory.last_generated_at)).first()
    
    def create(self, db: Session, user_id: int, analysis_type_id: int, 
               health_record_count: int, health_record_updated_at: Optional[datetime] = None,
               analysis_content: Optional[str] = None, analysis_language: Optional[str] = None) -> AIAnalysisHistory:
        """Create a new AI analysis history record"""
        try:
            # Deactivate any existing records for this user and analysis type
            existing_records = db.query(AIAnalysisHistory).filter(
                and_(
                    AIAnalysisHistory.user_id == user_id,
                    AIAnalysisHistory.analysis_type_id == analysis_type_id,
                    AIAnalysisHistory.is_active == True
                )
            ).all()
            
            for record in existing_records:
                record.is_active = False
            
            # Create new record
            new_record = AIAnalysisHistory(
                user_id=user_id,
                analysis_type_id=analysis_type_id,
                last_generated_at=datetime.now(timezone.utc),
                last_health_record_count=health_record_count,
                last_health_record_updated_at=health_record_updated_at,
                analysis_content=analysis_content,
                analysis_language=analysis_language or 'en',
                is_active=True
            )
            
            db.add(new_record)
            db.commit()
            db.refresh(new_record)
            
            return new_record
            
        except Exception as e:
            logger.error(f"Failed to create AI analysis history: {e}")
            db.rollback()
            raise
    
    def update(self, db: Session, record_id: int, health_record_count: int,
               health_record_updated_at: Optional[datetime] = None,
               analysis_content: Optional[str] = None) -> Optional[AIAnalysisHistory]:
        """Update an existing AI analysis history record"""
        try:
            record = db.query(AIAnalysisHistory).filter(AIAnalysisHistory.id == record_id).first()
            if not record:
                return None
            
            record.last_generated_at = datetime.now(timezone.utc)
            record.last_health_record_count = health_record_count
            if health_record_updated_at:
                record.last_health_record_updated_at = health_record_updated_at
            if analysis_content:
                record.analysis_content = analysis_content
            
            db.commit()
            db.refresh(record)
            
            return record
            
        except Exception as e:
            logger.error(f"Failed to update AI analysis history: {e}")
            db.rollback()
            return None
    
    def should_generate_analysis(self, db: Session, user_id: int, analysis_type_id: int,
                                current_health_record_count: int,
                                latest_health_record_updated_at: Optional[datetime] = None,
                                force_check: bool = False) -> tuple[bool, str]:
        """
        Determine if AI analysis should be generated based on the 5-day rule and new information
        
        Args:
            force_check: If True, always regenerate when there are new records (for "Check for Updates" button)
                        If False, apply 5-day rule for automatic page loads
        
        Returns:
            tuple[bool, str]: (should_generate, reason)
        """
        try:
            # Get the latest analysis history
            latest_analysis = self.get_by_user_and_type(db, user_id, analysis_type_id)
            
            if not latest_analysis:
                return True, "No previous analysis found"
            
            # Check if there are new records (count increased)
            has_new_records = current_health_record_count > latest_analysis.last_health_record_count
            
            # Check if health records were updated since last analysis (by timestamp)
            has_updated_records = False
            if latest_health_record_updated_at and latest_analysis.last_health_record_updated_at:
                # Ensure both datetimes have the same timezone info
                if latest_health_record_updated_at.tzinfo is None:
                    latest_health_record_updated_at = latest_health_record_updated_at.replace(tzinfo=latest_analysis.last_health_record_updated_at.tzinfo)
                elif latest_analysis.last_health_record_updated_at.tzinfo is None:
                    latest_analysis.last_health_record_updated_at = latest_analysis.last_health_record_updated_at.replace(tzinfo=latest_health_record_updated_at.tzinfo)
                has_updated_records = latest_health_record_updated_at > latest_analysis.last_health_record_updated_at
            
            # If there's new information (either new records OR updated records)
            if has_new_records or has_updated_records:
                # For "Check for Updates" button: always regenerate when there are new records
                if force_check:
                    reasons = []
                    if has_new_records:
                        reasons.append(f"new records ({current_health_record_count} vs {latest_analysis.last_health_record_count})")
                    if has_updated_records:
                        reasons.append("updated records")
                    return True, f"Has {' + '.join(reasons)}"
                else:
                    # For automatic page loads: check 5-day rule even with new records
                    now = datetime.now(timezone.utc)
                    time_diff = now - latest_analysis.last_generated_at
                    days_since_last = time_diff.days
                    
                    if days_since_last < 5:
                        if days_since_last == 0:
                            # Less than a day - show hours and minutes
                            hours = time_diff.seconds // 3600
                            minutes = (time_diff.seconds % 3600) // 60
                            if hours > 0:
                                time_str = f"{hours}h {minutes}m"
                            else:
                                time_str = f"{minutes}m"
                            return False, f"Last analysis was {time_str} ago (less than 5 days)"
                        else:
                            return False, f"Last analysis was {days_since_last} days ago (less than 5 days)"
                    else:
                        # More than 5 days and has new information
                        reasons = []
                        if has_new_records:
                            reasons.append(f"new records ({current_health_record_count} vs {latest_analysis.last_health_record_count})")
                        if has_updated_records:
                            reasons.append("updated records")
                        return True, f"More than 5 days ({days_since_last}) and has {' + '.join(reasons)}"
            else:
                # No new information - for "Check for Updates" button, don't regenerate if no new records
                if force_check:
                    return False, "No new records found since last analysis"
            
            # No new information - check 5-day rule
            now = datetime.now(timezone.utc)
            time_diff = now - latest_analysis.last_generated_at
            days_since_last = time_diff.days
            
            if days_since_last < 5:
                if days_since_last == 0:
                    # Less than a day - show hours and minutes
                    hours = time_diff.seconds // 3600
                    minutes = (time_diff.seconds % 3600) // 60
                    if hours > 0:
                        time_str = f"{hours}h {minutes}m"
                    else:
                        time_str = f"{minutes}m"
                    return False, f"Last analysis was {time_str} ago (less than 5 days)"
                else:
                    return False, f"Last analysis was {days_since_last} days ago (less than 5 days)"
            
            # More than 5 days and no new information
            return False, f"No new information since last analysis ({days_since_last} days ago)"
            
        except Exception as e:
            logger.error(f"Error checking if analysis should be generated: {e}")
            return True, f"Error occurred: {str(e)}"
    
    def get_analysis_history(self, db: Session, user_id: int, analysis_type_id: int, limit: int = 10) -> List[AIAnalysisHistory]:
        """Get analysis history for a user"""
        return db.query(AIAnalysisHistory).filter(
            and_(
                AIAnalysisHistory.user_id == user_id,
                AIAnalysisHistory.analysis_type_id == analysis_type_id
            )
        ).order_by(desc(AIAnalysisHistory.last_generated_at)).limit(limit).all()

# Create instance
ai_analysis_history_crud = AIAnalysisHistoryCRUD()
