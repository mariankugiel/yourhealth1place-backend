from sqlalchemy import Column, Integer, String, Text, DateTime, func, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class Translation(Base):
    """Store translations for user-generated and system-generated content"""
    __tablename__ = "translations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Entity identification
    entity_type = Column(String(50), nullable=False, index=True)  # e.g., 'health_record_sections', 'medications'
    entity_id = Column(Integer, nullable=False, index=True)  # ID from the original table
    
    # Field and language
    field_name = Column(String(50), nullable=False)  # e.g., 'display_name', 'description', 'name'
    language = Column(String(10), nullable=False)  # 'en', 'es', 'pt'
    
    # Translation content
    translated_text = Column(Text, nullable=False)  # The translated content
    
    # Metadata
    source_language = Column(String(10), nullable=True)  # Original language (usually 'en')
    content_version = Column(Integer, nullable=True)  # Version of source content when translation was created/updated
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Unique constraint: one translation per entity+field+language combination
    __table_args__ = (
        UniqueConstraint('entity_type', 'entity_id', 'field_name', 'language', 
                        name='uq_translations_entity_field_language'),
        Index('idx_translations_lookup', 'entity_type', 'entity_id', 'field_name', 'language'),
        Index('idx_translations_entity', 'entity_type', 'entity_id'),
        Index('idx_translations_language', 'language'),
    )
    
    def __repr__(self):
        return f"<Translation(entity_type='{self.entity_type}', entity_id={self.entity_id}, field='{self.field_name}', lang='{self.language}')>"


