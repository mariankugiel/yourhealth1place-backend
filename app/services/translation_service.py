import os
import json
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.translation import translation_crud

# Try to import OpenAI, fallback if not available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI package not installed. Translation service will use fallback mode.")

logger = logging.getLogger(__name__)


class TranslationService:
    """Service for translating user-generated and system-generated content"""
    
    def __init__(self):
        """Initialize the Translation Service with OpenAI client"""
        if OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
            try:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
                self.model = "gpt-4o-mini"  # Using GPT-4o-mini for cost efficiency
                self.openai_enabled = True
            except Exception as e:
                logging.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
                self.model = None
                self.openai_enabled = False
        else:
            self.client = None
            self.model = None
            self.openai_enabled = False
            logging.warning("OpenAI not available. Translation service will use fallback mode.")
    
    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: str = 'en'
    ) -> str:
        """
        Translate text from source language to target language using OpenAI
        
        Args:
            text: Text to translate
            target_language: Target language code ('en', 'es', 'pt')
            source_language: Source language code ('en', 'es', 'pt')
        
        Returns:
            Translated text, or original text if translation fails
        """
        if not text or not text.strip():
            return text
        
        # If source and target are the same, return original
        if source_language == target_language:
            return text
        
        # Language name mapping
        language_names = {
            'en': 'English',
            'es': 'Spanish',
            'pt': 'Portuguese'
        }
        
        source_name = language_names.get(source_language, 'English')
        target_name = language_names.get(target_language, 'English')
        
        if not self.openai_enabled:
            logger.warning("OpenAI not available, returning original text")
            return text
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional medical translator. Translate medical and health-related content accurately while preserving medical terminology and context. Maintain the same tone and style as the original text."
                    },
                    {
                        "role": "user",
                        "content": f"Translate the following text from {source_name} to {target_name}. Only return the translated text, nothing else:\n\n{text}"
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent translations
                max_tokens=1000
            )
            
            translated_text = response.choices[0].message.content.strip()
            logger.info(f"Successfully translated text from {source_language} to {target_language}")
            return translated_text
            
        except Exception as e:
            logger.error(f"Failed to translate text: {e}")
            return text  # Return original text on error
    
    def translate_json_array(
        self,
        json_array: List[Dict[str, Any]],
        target_language: str,
        source_language: str = 'en',
        fields_to_translate: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Translate specific fields in a JSON array structure
        
        Args:
            json_array: List of dictionaries to translate
            target_language: Target language code
            source_language: Source language code
            fields_to_translate: List of field names to translate (e.g., ['disease', 'comments'])
        
        Returns:
            Translated JSON array
        """
        if not json_array or not isinstance(json_array, list):
            return json_array
        
        if not fields_to_translate:
            return json_array
        
        translated_array = []
        for item in json_array:
            translated_item = item.copy()
            for field in fields_to_translate:
                if field in item and item[field]:
                    translated_item[field] = self.translate_text(
                        str(item[field]),
                        target_language,
                        source_language
                    )
            translated_array.append(translated_item)
        
        return translated_array
    
    def get_translated_content(
        self,
        db: Session,
        entity_type: str,
        entity_id: int,
        field_name: str,
        original_text: str,
        target_language: str,
        source_language: str = 'en',
        current_entry_version: Optional[int] = None
    ) -> str:
        """
        Get translated content, translating on-demand if not cached or if content version changed
        
        Args:
            db: Database session
            entity_type: Type of entity (e.g., 'health_record_sections')
            entity_id: ID of the entity
            field_name: Name of the field to translate
            original_text: Original text content
            target_language: Target language code
            source_language: Source language code
            current_entry_version: Current version of the source entry (for version checking)
        
        Returns:
            Translated text or original if translation fails
        """
        # If target is same as source, return original
        if target_language == source_language or not original_text:
            return original_text
        
        # Check if translation exists in database
        translation = translation_crud.get_translation(
            db, entity_type, entity_id, field_name, target_language
        )
        
        # If translation exists, check version
        if translation:
            # If current_entry_version is provided, compare with stored content_version
            if current_entry_version is not None:
                stored_version = translation.content_version
                
                # If versions match, use cached translation
                if stored_version is not None and stored_version == current_entry_version:
                    logger.debug(f"Using cached translation for {entity_type}:{entity_id}.{field_name} (version {current_entry_version})")
                    return translation.translated_text
                
                # Versions don't match or stored_version is None - need to re-translate
                if stored_version is not None:
                    logger.info(f"Content version changed for {entity_type}:{entity_id}.{field_name} (stored: {stored_version}, current: {current_entry_version}). Re-translating.")
                else:
                    logger.info(f"No content_version stored for {entity_type}:{entity_id}.{field_name}. Translating and storing version {current_entry_version}.")
            else:
                # No version provided - use cached translation (backward compatibility)
                return translation.translated_text
        
        # Translation not found or version mismatch - translate on-demand
        try:
            translated_text = self.translate_text(
                original_text,
                target_language,
                source_language
            )
            
            # Cache translation in database with content_version
            translation_crud.create_translation(
                db=db,
                entity_type=entity_type,
                entity_id=entity_id,
                field_name=field_name,
                language=target_language,
                translated_text=translated_text,
                source_language=source_language,
                content_version=current_entry_version
            )
            
            return translated_text
            
        except Exception as e:
            logger.error(f"Failed to translate and cache content: {e}")
            return original_text  # Return original on error
    
    def translate_entity_fields(
        self,
        db: Session,
        entity_type: str,
        entity_id: int,
        fields: Dict[str, str],
        target_language: str,
        source_language: str = 'en'
    ) -> Dict[str, str]:
        """
        Translate multiple fields of an entity
        
        Args:
            db: Database session
            entity_type: Type of entity
            entity_id: ID of the entity
            fields: Dictionary of field_name -> original_text
            target_language: Target language code
            source_language: Source language code
        
        Returns:
            Dictionary of field_name -> translated_text
        """
        translated_fields = {}
        
        for field_name, original_text in fields.items():
            if original_text:
                translated_fields[field_name] = self.get_translated_content(
                    db, entity_type, entity_id, field_name,
                    original_text, target_language, source_language
                )
            else:
                translated_fields[field_name] = original_text
        
        return translated_fields


# Create singleton instance
translation_service = TranslationService()


