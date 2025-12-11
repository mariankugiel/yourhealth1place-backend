from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class ThryveDailyEpoch(str, enum.Enum):
    DAILY = "Daily"
    EPOCH = "Epoch"


class ThryveDataType(Base):
    __tablename__ = "thryve_data_types"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    data_type_id = Column(Integer, nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(255))  # Can be comma-separated, e.g., "Activity,Workouts"
    # Use PostgreSQL native enum with values_callable to use enum VALUES ("Daily", "Epoch")
    # instead of enum NAMES ("DAILY", "EPOCH")
    # By default, SQLAlchemy uses enum member names, but we need the values to match PostgreSQL
    type = Column(
        Enum(
            ThryveDailyEpoch,
            name='thryvedailyepoch',
            values_callable=lambda x: [e.value for e in x],  # Use enum values, not names
            create_constraint=True
        ),
        nullable=False,
        index=True
    )  # Daily or Epoch
    description = Column(Text)
    unit = Column(String(100), nullable=True)
    value_type = Column(String(50))  # LONG, DOUBLE, BOOLEAN, STRING, DATE, JSON
    platform_support = Column(JSON)  # Store which platforms support this as JSONB
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    admin_metrics = relationship("HealthRecordMetricTemplate", back_populates="thryve_data_type")
    
    def __repr__(self):
        return f"<ThryveDataType(id={self.id}, data_type_id={self.data_type_id}, name='{self.name}', type='{self.type}')>"

