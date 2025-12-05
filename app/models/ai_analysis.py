from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class AIAnalysisHistory(Base):
    """Track AI analysis generation history for users"""
    __tablename__ = "ai_analysis_history"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    analysis_type_id = Column(Integer, nullable=False)  # 1 = health records analysis
    last_generated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_health_record_count = Column(Integer, nullable=False, default=0)  # Track number of health records when last generated
    last_health_record_updated_at = Column(DateTime(timezone=True), nullable=True)  # Track when last health record was updated
    analysis_content = Column(Text, nullable=True)  # Store the last generated analysis
    analysis_language = Column(String(10), nullable=True, default='en')  # Language the analysis was generated in ('en', 'es', 'pt')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="ai_analysis_history")
    
    def __repr__(self):
        return f"<AIAnalysisHistory(user_id={self.user_id}, last_generated_at={self.last_generated_at})>"
