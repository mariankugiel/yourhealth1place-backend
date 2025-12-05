from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.translation import Translation
import logging

logger = logging.getLogger(__name__)


class TranslationCRUD:
    """CRUD operations for Translation model"""
    
    def get_translation(
        self,
        db: Session,
        entity_type: str,
        entity_id: int,
        field_name: str,
        language: str
    ) -> Optional[Translation]:
        """Get a specific translation"""
        try:
            return db.query(Translation).filter(
                and_(
                    Translation.entity_type == entity_type,
                    Translation.entity_id == entity_id,
                    Translation.field_name == field_name,
                    Translation.language == language
                )
            ).first()
        except Exception as e:
            logger.error(f"Failed to get translation: {e}")
            return None
    
    def get_entity_translations(
        self,
        db: Session,
        entity_type: str,
        entity_id: int,
        language: str
    ) -> List[Translation]:
        """Get all translations for a specific entity in a specific language"""
        try:
            return db.query(Translation).filter(
                and_(
                    Translation.entity_type == entity_type,
                    Translation.entity_id == entity_id,
                    Translation.language == language
                )
            ).all()
        except Exception as e:
            logger.error(f"Failed to get entity translations: {e}")
            return []
    
    def get_bulk_translations(
        self,
        db: Session,
        entity_type: str,
        entity_ids: List[int],
        field_names: List[str],
        language: str
    ) -> Dict[tuple, Translation]:
        """
        Get translations for multiple entities and fields in bulk.
        Returns a dictionary keyed by (entity_id, field_name) for fast lookup.
        """
        try:
            translations = db.query(Translation).filter(
                and_(
                    Translation.entity_type == entity_type,
                    Translation.entity_id.in_(entity_ids),
                    Translation.field_name.in_(field_names),
                    Translation.language == language
                )
            ).all()
            
            # Create lookup dictionary
            result = {}
            for trans in translations:
                key = (trans.entity_id, trans.field_name)
                result[key] = trans
            
            return result
        except Exception as e:
            logger.error(f"Failed to get bulk translations: {e}")
            return {}
    
    def create_translation(
        self,
        db: Session,
        entity_type: str,
        entity_id: int,
        field_name: str,
        language: str,
        translated_text: str,
        source_language: Optional[str] = None,
        content_version: Optional[int] = None
    ) -> Translation:
        """Create or update a translation"""
        try:
            # Check if translation already exists
            existing = self.get_translation(
                db, entity_type, entity_id, field_name, language
            )
            
            if existing:
                # Update existing translation
                existing.translated_text = translated_text
                existing.source_language = source_language or existing.source_language
                existing.content_version = content_version or existing.content_version
                existing.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(existing)
                return existing
            else:
                # Create new translation
                new_translation = Translation(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_name=field_name,
                    language=language,
                    translated_text=translated_text,
                    source_language=source_language,
                    content_version=content_version
                )
                db.add(new_translation)
                db.commit()
                db.refresh(new_translation)
                return new_translation
        except Exception as e:
            logger.error(f"Failed to create translation: {e}")
            db.rollback()
            raise
    
    def delete_translations(
        self,
        db: Session,
        entity_type: str,
        entity_id: int
    ) -> bool:
        """Delete all translations for a specific entity (when entity is deleted)"""
        try:
            deleted_count = db.query(Translation).filter(
                and_(
                    Translation.entity_type == entity_type,
                    Translation.entity_id == entity_id
                )
            ).delete()
            db.commit()
            logger.info(f"Deleted {deleted_count} translations for {entity_type}:{entity_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete translations: {e}")
            db.rollback()
            return False
    
    def delete_translation(
        self,
        db: Session,
        entity_type: str,
        entity_id: int,
        field_name: str,
        language: str
    ) -> bool:
        """Delete a specific translation"""
        try:
            deleted_count = db.query(Translation).filter(
                and_(
                    Translation.entity_type == entity_type,
                    Translation.entity_id == entity_id,
                    Translation.field_name == field_name,
                    Translation.language == language
                )
            ).delete()
            db.commit()
            return deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete translation: {e}")
            db.rollback()
            return False


# Create singleton instance
translation_crud = TranslationCRUD()

