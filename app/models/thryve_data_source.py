from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class ThryveDataSource(Base):
    __tablename__ = "thryve_data_sources"
    
    id = Column(Integer, primary_key=True, index=True)  # Matches Thryve data source ID
    name = Column(String(255), nullable=False, index=True)
    data_source_type = Column(String(50))  # "Web" or "Native"
    retrieval_method = Column(String(50))  # "Ping", "Bulk", "SDK"
    historic_data = Column(Boolean)  # yes/no
    shared_oauth_client = Column(String(10))  # "yes", "no", "n.a."
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ThryveDataSource(id={self.id}, name='{self.name}', type='{self.data_source_type}')>"

