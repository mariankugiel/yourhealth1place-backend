from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Date, Enum as SQLAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

# ============================================================================
# SURGERY & HOSPITALIZATION ENUMS
# ============================================================================

class ProcedureType(str, enum.Enum):
    SURGERY = "surgery"
    HOSPITALIZATION = "hospitalization"

class RecoveryStatus(str, enum.Enum):
    FULL_RECOVERY = "full_recovery"
    PARTIAL_RECOVERY = "partial_recovery"
    NO_RECOVERY = "no_recovery"

# ============================================================================
# SURGERY & HOSPITALIZATION MODELS
# ============================================================================

class SurgeryHospitalization(Base):
    __tablename__ = "surgeries_hospitalizations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    procedure_type = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    procedure_date = Column(Date, nullable=False)
    reason = Column(String(500))
    treatment = Column(String(500))
    body_area = Column(String(100))
    recovery_status = Column(String(50), nullable=False, default="full_recovery")
    notes = Column(Text)
    source_language = Column(String(10), nullable=False, default='en')  # Language of original content ('en', 'es', 'pt')
    version = Column(Integer, nullable=False, default=1)  # Content version for translation invalidation
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
