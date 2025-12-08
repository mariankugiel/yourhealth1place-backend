"""
Helper functions for applying translations to entities
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.services.translation_service import translation_service
from app.utils.user_language import get_user_language_from_cache
import logging

logger = logging.getLogger(__name__)


async def apply_translations_to_section(
    db: Session,
    section: Dict[str, Any],
    user_id: int,
    target_language: Optional[str] = None,
    request: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Apply translations to a section dictionary
    
    Args:
        db: Database session
        section: Section dictionary with id, display_name, description, etc.
        user_id: User ID to get language preference
        target_language: Optional target language (if None, gets from cached user profile)
        request: Optional FastAPI Request object (deprecated, kept for backward compatibility)
    
    Returns:
        Section dictionary with translated fields
    """
    try:
        # Get user's language preference from cache
        if target_language is None:
            target_language = await get_user_language_from_cache(user_id, db)
        
        # If English, return as-is (no translation needed)
        if target_language == 'en':
            return section
        
        section_id = section.get('id')
        if not section_id:
            return section
        
        # Get source_language from section (defaults to 'en' for backward compatibility)
        source_language = section.get('source_language', 'en')
        
        # Only translate if source and target languages are different
        if source_language == target_language:
            return section
        
        # Translate display_name
        display_name = section.get('display_name', '')
        if display_name:
            section['display_name'] = translation_service.get_translated_content(
                db=db,
                entity_type='health_record_sections',
                entity_id=section_id,
                field_name='display_name',
                original_text=display_name,
                target_language=target_language,
                source_language=source_language
            )
        
        # Translate description
        description = section.get('description')
        if description:
            section['description'] = translation_service.get_translated_content(
                db=db,
                entity_type='health_record_sections',
                entity_id=section_id,
                field_name='description',
                original_text=description,
                target_language=target_language,
                source_language=source_language
            )
        
        return section
        
    except Exception as e:
        logger.error(f"Failed to apply translations to section: {e}")
        return section  # Return original on error


async def apply_translations_to_metric(
    db: Session,
    metric: Dict[str, Any],
    user_id: int,
    target_language: Optional[str] = None,
    request: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Apply translations to a metric dictionary
    
    Args:
        db: Database session
        metric: Metric dictionary with id, display_name, description, etc.
        user_id: User ID to get language preference
        target_language: Optional target language (if None, gets from cached user profile)
        request: Optional FastAPI Request object (deprecated, kept for backward compatibility)
    
    Returns:
        Metric dictionary with translated fields
    """
    try:
        # Get user's language preference from cache
        if target_language is None:
            target_language = await get_user_language_from_cache(user_id, db)
        
        # If English, return as-is
        if target_language == 'en':
            return metric
        
        metric_id = metric.get('id')
        if not metric_id:
            return metric
        
        # Get source_language from metric (defaults to 'en' for backward compatibility)
        source_language = metric.get('source_language', 'en')
        
        # Only translate if source and target languages are different
        if source_language == target_language:
            return metric
        
        # Translate display_name
        display_name = metric.get('display_name', '')
        if display_name:
            metric['display_name'] = translation_service.get_translated_content(
                db=db,
                entity_type='health_record_metrics',
                entity_id=metric_id,
                field_name='display_name',
                original_text=display_name,
                target_language=target_language,
                source_language=source_language
            )
        
        # Translate description
        description = metric.get('description')
        if description:
            metric['description'] = translation_service.get_translated_content(
                db=db,
                entity_type='health_record_metrics',
                entity_id=metric_id,
                field_name='description',
                original_text=description,
                target_language=target_language,
                source_language=source_language
            )
        
        return metric
        
    except Exception as e:
        logger.error(f"Failed to apply translations to metric: {e}")
        return metric  # Return original on error


async def apply_translations_to_sections_with_metrics(
    db: Session,
    sections: List[Dict[str, Any]],
    user_id: int,
    target_language: Optional[str] = None,
    request: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """
    Apply translations to a list of sections with their metrics
    
    Args:
        db: Database session
        sections: List of section dictionaries with nested metrics
        user_id: User ID to get language preference
        target_language: Optional target language (if None, gets from cached user profile)
        request: Optional FastAPI Request object (deprecated, kept for backward compatibility)
    
    Returns:
        List of sections with translated fields
    """
    try:
        # Get user's language preference from cache
        if target_language is None:
            target_language = await get_user_language_from_cache(user_id, db)
        
        translated_sections = []
        for section in sections:
            # Translate section fields
            translated_section = await apply_translations_to_section(
                db, section, user_id, target_language, request
            )
            
            # Translate metrics within section
            metrics = section.get('metrics', [])
            translated_metrics = []
            for metric in metrics:
                translated_metric = await apply_translations_to_metric(
                    db, metric, user_id, target_language, request
                )
                translated_metrics.append(translated_metric)
            
            translated_section['metrics'] = translated_metrics
            translated_sections.append(translated_section)
        
        return translated_sections
        
    except Exception as e:
        logger.error(f"Failed to apply translations to sections: {e}")
        return sections  # Return original on error


async def apply_translations_to_medical_condition(
    db: Session,
    condition: Dict[str, Any],
    user_id: int,
    target_language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Apply translations to a medical condition dictionary
    
    Args:
        db: Database session
        condition: Condition dictionary with id, condition_name, description, treatment_plan, source_language
        user_id: User ID to get language preference
        target_language: Optional target language
    
    Returns:
        Condition dictionary with translated fields
    """
    try:
        if target_language is None:
            target_language = await get_user_language_from_cache(user_id, db)
        
        logger.info(f"🌐 [Medical Condition Translation] User {user_id}, Target: {target_language}, Condition ID: {condition.get('id')}")
        
        # Get source_language from condition dict (defaults to 'en' for backward compatibility)
        source_language = condition.get('source_language', 'en')
        
        logger.info(f"🌐 [Medical Condition Translation] Source: {source_language}, Target: {target_language}")
        
        # Only translate if source and target languages are different
        if source_language == target_language:
            logger.debug(f"🌐 [Medical Condition Translation] Source and target match ({source_language}), skipping translation")
            return condition
        
        condition_id = condition.get('id')
        if not condition_id:
            return condition
        
        # Get current version from condition dict
        current_version = condition.get('version', 1)
        
        # Translate condition_name
        condition_name = condition.get('condition_name', '')
        if condition_name:
            condition['condition_name'] = translation_service.get_translated_content(
                db=db,
                entity_type='medical_conditions',
                entity_id=condition_id,
                field_name='condition_name',
                original_text=condition_name,
                target_language=target_language,
                source_language=source_language,
                current_entry_version=current_version
            )
        
        # Translate description
        description = condition.get('description')
        if description:
            condition['description'] = translation_service.get_translated_content(
                db=db,
                entity_type='medical_conditions',
                entity_id=condition_id,
                field_name='description',
                original_text=description,
                target_language=target_language,
                source_language=source_language,
                current_entry_version=current_version
            )
        
        # Translate treatment_plan
        treatment_plan = condition.get('treatment_plan')
        if treatment_plan:
            condition['treatment_plan'] = translation_service.get_translated_content(
                db=db,
                entity_type='medical_conditions',
                entity_id=condition_id,
                field_name='treatment_plan',
                original_text=treatment_plan,
                target_language=target_language,
                source_language=source_language,
                current_entry_version=current_version
            )
        
        return condition
        
    except Exception as e:
        logger.error(f"Failed to apply translations to medical condition: {e}")
        return condition


async def apply_translations_to_family_history(
    db: Session,
    history: Dict[str, Any],
    user_id: int,
    target_language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Apply translations to a family medical history dictionary
    
    Args:
        db: Database session
        history: History dictionary with id, cause_of_death, chronic_diseases, source_language, etc.
        user_id: User ID to get language preference
        target_language: Optional target language
    
    Returns:
        History dictionary with translated fields
    """
    try:
        if target_language is None:
            target_language = await get_user_language_from_cache(user_id, db)
        
        # Get source_language from history dict (defaults to 'en' for backward compatibility)
        source_language = history.get('source_language', 'en')
        
        # Only translate if source and target languages are different
        if source_language == target_language:
            return history
        
        history_id = history.get('id')
        if not history_id:
            return history
        
        # Get current version from history dict
        current_version = history.get('version', 1)
        
        # Translate cause_of_death
        cause_of_death = history.get('cause_of_death')
        if cause_of_death:
            history['cause_of_death'] = translation_service.get_translated_content(
                db=db,
                entity_type='family_medical_history',
                entity_id=history_id,
                field_name='cause_of_death',
                original_text=cause_of_death,
                target_language=target_language,
                source_language=source_language,
                current_entry_version=current_version
            )
        
        # Translate chronic_diseases JSON array
        chronic_diseases = history.get('chronic_diseases')
        if chronic_diseases and isinstance(chronic_diseases, list):
            translated_diseases = translation_service.translate_json_array(
                chronic_diseases,
                target_language,
                source_language='en',
                fields_to_translate=['disease', 'comments']
            )
            # Store translated version (we'll need to handle this specially)
            # For now, we'll translate in-place
            for i, disease in enumerate(chronic_diseases):
                if 'disease' in disease and disease['disease']:
                    disease['disease'] = translation_service.get_translated_content(
                        db=db,
                        entity_type='family_medical_history',
                        entity_id=history_id,
                        field_name=f'chronic_diseases[{i}].disease',
                        original_text=disease['disease'],
                        target_language=target_language,
                        source_language=source_language,
                        current_entry_version=current_version
                    )
                if 'comments' in disease and disease['comments']:
                    disease['comments'] = translation_service.get_translated_content(
                        db=db,
                        entity_type='family_medical_history',
                        entity_id=history_id,
                        field_name=f'chronic_diseases[{i}].comments',
                        original_text=disease['comments'],
                        target_language=target_language,
                        source_language=source_language,
                        current_entry_version=current_version
                    )
        
        # Translate legacy fields
        condition_name = history.get('condition_name')
        if condition_name:
            history['condition_name'] = translation_service.get_translated_content(
                db=db,
                entity_type='family_medical_history',
                entity_id=history_id,
                field_name='condition_name',
                original_text=condition_name,
                target_language=target_language,
                source_language=source_language,
                current_entry_version=current_version
            )
        
        description = history.get('description')
        if description:
            history['description'] = translation_service.get_translated_content(
                db=db,
                entity_type='family_medical_history',
                entity_id=history_id,
                field_name='description',
                original_text=description,
                target_language=target_language,
                source_language=source_language,
                current_entry_version=current_version
            )
        
        outcome = history.get('outcome')
        if outcome:
            history['outcome'] = translation_service.get_translated_content(
                db=db,
                entity_type='family_medical_history',
                entity_id=history_id,
                field_name='outcome',
                original_text=outcome,
                target_language=target_language,
                source_language=source_language,
                current_entry_version=current_version
            )
        
        return history
        
    except Exception as e:
        logger.error(f"Failed to apply translations to family history: {e}")
        return history


async def apply_translations_to_imaging_document(
    db: Session,
    image: Dict[str, Any],
    user_id: int,
    target_language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Apply translations to an imaging document dictionary
    
    Args:
        db: Database session
        image: Image dictionary with id, body_part, conclusions, interpretation, notes
        user_id: User ID to get language preference
        target_language: Optional target language
    
    Returns:
        Image dictionary with translated fields
    """
    try:
        if target_language is None:
            target_language = await get_user_language_from_cache(user_id, db)
        
        if target_language == 'en':
            return image
        
        image_id = image.get('id')
        if not image_id:
            return image
        
        # Translate body_part
        body_part = image.get('body_part', '')
        if body_part:
            image['body_part'] = translation_service.get_translated_content(
                db=db,
                entity_type='health_record_doc_exam',
                entity_id=image_id,
                field_name='body_part',
                original_text=body_part,
                target_language=target_language,
                source_language='en'
            )
        
        # Translate conclusions
        conclusions = image.get('conclusions')
        if conclusions:
            image['conclusions'] = translation_service.get_translated_content(
                db=db,
                entity_type='health_record_doc_exam',
                entity_id=image_id,
                field_name='conclusions',
                original_text=conclusions,
                target_language=target_language,
                source_language='en'
            )
        
        # Translate interpretation
        interpretation = image.get('interpretation')
        if interpretation:
            image['interpretation'] = translation_service.get_translated_content(
                db=db,
                entity_type='health_record_doc_exam',
                entity_id=image_id,
                field_name='interpretation',
                original_text=interpretation,
                target_language=target_language,
                source_language='en'
            )
        
        # Translate notes
        notes = image.get('notes')
        if notes:
            image['notes'] = translation_service.get_translated_content(
                db=db,
                entity_type='health_record_doc_exam',
                entity_id=image_id,
                field_name='notes',
                original_text=notes,
                target_language=target_language,
                source_language='en'
            )
        
        return image
        
    except Exception as e:
        logger.error(f"Failed to apply translations to imaging document: {e}")
        return image


async def apply_translations_to_section_template(
    db: Session,
    section_template: Dict[str, Any],
    user_id: int,
    target_language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Apply translations to a section template dictionary
    
    Args:
        db: Database session
        section_template: Template dictionary with id, display_name, description, source_language
        user_id: User ID to get language preference
        target_language: Optional target language (if None, gets from user profile)
    
    Returns:
        Template dictionary with translated fields
    """
    try:
        # Get user's language preference
        if target_language is None:
            target_language = await get_user_language_from_cache(user_id, db)
        
        # Get template's source language
        source_language = section_template.get('source_language', 'en')
        
        # If target matches source, return as-is (no translation needed)
        if target_language == source_language:
            return section_template
        
        section_template_id = section_template.get('id')
        if not section_template_id:
            return section_template
        
        # Translate display_name
        display_name = section_template.get('display_name', '')
        if display_name:
            section_template['display_name'] = translation_service.get_translated_content(
                db=db,
                entity_type='health_record_section_template',
                entity_id=section_template_id,
                field_name='display_name',
                original_text=display_name,
                target_language=target_language,
                source_language=source_language
            )
        
        # Translate description
        description = section_template.get('description')
        if description:
            section_template['description'] = translation_service.get_translated_content(
                db=db,
                entity_type='health_record_section_template',
                entity_id=section_template_id,
                field_name='description',
                original_text=description,
                target_language=target_language,
                source_language=source_language
            )
        
        return section_template
        
    except Exception as e:
        logger.error(f"Failed to apply translations to section template: {e}")
        return section_template  # Return original on error


async def apply_translations_to_metric_template(
    db: Session,
    metric_template: Dict[str, Any],
    user_id: int,
    target_language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Apply translations to a metric template dictionary
    
    Args:
        db: Database session
        metric_template: Template dictionary with id, display_name, description, default_unit, source_language
        user_id: User ID to get language preference
        target_language: Optional target language (if None, gets from user profile)
    
    Returns:
        Template dictionary with translated fields
    """
    try:
        # Get user's language preference
        if target_language is None:
            target_language = await get_user_language_from_cache(user_id, db)
        
        # Get template's source language
        source_language = metric_template.get('source_language', 'en')
        
        # If target matches source, return as-is
        if target_language == source_language:
            return metric_template
        
        metric_template_id = metric_template.get('id')
        if not metric_template_id:
            return metric_template
        
        # Translate display_name
        display_name = metric_template.get('display_name', '')
        if display_name:
            metric_template['display_name'] = translation_service.get_translated_content(
                db=db,
                entity_type='health_record_metric_template',
                entity_id=metric_template_id,
                field_name='display_name',
                original_text=display_name,
                target_language=target_language,
                source_language=source_language
            )
        
        # Translate description
        description = metric_template.get('description')
        if description:
            metric_template['description'] = translation_service.get_translated_content(
                db=db,
                entity_type='health_record_metric_template',
                entity_id=metric_template_id,
                field_name='description',
                original_text=description,
                target_language=target_language,
                source_language=source_language
            )
        
        # Translate default_unit
        default_unit = metric_template.get('default_unit')
        if default_unit:
            metric_template['default_unit'] = translation_service.get_translated_content(
                db=db,
                entity_type='health_record_metric_template',
                entity_id=metric_template_id,
                field_name='default_unit',
                original_text=default_unit,
                target_language=target_language,
                source_language=source_language
            )
        
        return metric_template
        
    except Exception as e:
        logger.error(f"Failed to apply translations to metric template: {e}")
        return metric_template  # Return original on error


async def apply_translations_to_surgery_hospitalization(
    db: Session,
    surgery: Dict[str, Any],
    user_id: int,
    target_language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Apply translations to a surgery/hospitalization dictionary
    
    Args:
        db: Database session
        surgery: Surgery/hospitalization dictionary with id, name, reason, treatment, body_area, notes, source_language
        user_id: User ID to get language preference
        target_language: Optional target language
    
    Returns:
        Surgery/hospitalization dictionary with translated fields
    """
    try:
        if target_language is None:
            target_language = await get_user_language_from_cache(user_id, db)
        
        # Get source_language from surgery dict (defaults to 'en' for backward compatibility)
        source_language = surgery.get('source_language', 'en')
        
        # Only translate if source and target languages are different
        if source_language == target_language:
            return surgery
        
        surgery_id = surgery.get('id')
        if not surgery_id:
            return surgery
        
        # Get current version from surgery dict
        current_version = surgery.get('version', 1)
        
        # Translate name
        name = surgery.get('name', '')
        if name:
            surgery['name'] = translation_service.get_translated_content(
                db=db,
                entity_type='surgeries_hospitalizations',
                entity_id=surgery_id,
                field_name='name',
                original_text=name,
                target_language=target_language,
                source_language=source_language,
                current_entry_version=current_version
            )
        
        # Translate reason
        reason = surgery.get('reason')
        if reason:
            surgery['reason'] = translation_service.get_translated_content(
                db=db,
                entity_type='surgeries_hospitalizations',
                entity_id=surgery_id,
                field_name='reason',
                original_text=reason,
                target_language=target_language,
                source_language=source_language,
                current_entry_version=current_version
            )
        
        # Translate treatment
        treatment = surgery.get('treatment')
        if treatment:
            surgery['treatment'] = translation_service.get_translated_content(
                db=db,
                entity_type='surgeries_hospitalizations',
                entity_id=surgery_id,
                field_name='treatment',
                original_text=treatment,
                target_language=target_language,
                source_language=source_language,
                current_entry_version=current_version
            )
        
        # Translate body_area
        body_area = surgery.get('body_area')
        if body_area:
            surgery['body_area'] = translation_service.get_translated_content(
                db=db,
                entity_type='surgeries_hospitalizations',
                entity_id=surgery_id,
                field_name='body_area',
                original_text=body_area,
                target_language=target_language,
                source_language=source_language,
                current_entry_version=current_version
            )
        
        # Translate notes
        notes = surgery.get('notes')
        if notes:
            surgery['notes'] = translation_service.get_translated_content(
                db=db,
                entity_type='surgeries_hospitalizations',
                entity_id=surgery_id,
                field_name='notes',
                original_text=notes,
                target_language=target_language,
                source_language=source_language,
                current_entry_version=current_version
            )
        
        return surgery
        
    except Exception as e:
        logger.error(f"Failed to apply translations to surgery/hospitalization: {e}")
        return surgery  # Return original on error

