import os
import json
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.health_record import HealthRecord, HealthRecordMetric, HealthRecordSection, HealthRecordDocExam
from app.models.user import User
from app.crud.health_record import health_record_section_metric_crud, medical_condition_crud, family_medical_history_crud
from app.crud.medical_images import MedicalImageCRUD
from app.crud.ai_analysis import ai_analysis_history_crud
from app.core.supabase_client import supabase_service

# Try to import OpenAI, fallback if not available
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI package not installed. AI analysis will use fallback mode.")

logger = logging.getLogger(__name__)


class AIAnalysisService:
    def __init__(self):
        """Initialize the AI Analysis Service with OpenAI client"""
        if OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
            try:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
                self.model = "gpt-4o-mini"  # Using GPT-4o-mini for cost efficiency
                self.openai_enabled = True
                # Map health_record_type_id to assistant_id
                self.assistant_ids = {
                    1: settings.OPENAI_ASSISTANT_SUMMARY_ID,  # Summary/Analysis
                    2: settings.OPENAI_ASSISTANT_VITALS_ID,  # Vitals
                    3: settings.OPENAI_ASSISTANT_BODY_ID,  # Body Composition
                    4: settings.OPENAI_ASSISTANT_LIFESTYLE_ID,  # Lifestyle
                    5: settings.OPENAI_ASSISTANT_EXAMS_ID,  # Exams/Medical Images
                }
            except Exception as e:
                logging.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
                self.model = None
                self.openai_enabled = False
                self.assistant_ids = {}
        else:
            self.client = None
            self.model = None
            self.openai_enabled = False
            self.assistant_ids = {}
            logging.warning("OpenAI not available. AI analysis will use fallback mode.")
        
    async def analyze_health_data(
        self, 
        db: Session, 
        user_id: int, 
        health_record_type_id: int = 1,
        force_check: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze user's health data using GPT and return AI insights
        
        Args:
            db: Database session
            user_id: User ID to analyze
            health_record_type_id: Health record type ID (default: 1 for analysis)
            force_check: Force check for updates (for "Check for Updates" button)
            
        Returns:
            Dict containing AI analysis results
        """
        try:
            # Get user's health data
            health_data = await self._get_user_health_data(db, user_id, health_record_type_id)
            
            if not health_data:
                return {
                    "success": False,
                    "message": "No health data found for analysis",
                    "analysis": {
                        "areas_of_concern": [],
                        "positive_trends": [],
                        "recommendations": ["Please add some health data to get personalized AI insights."]
                    }
                }
            
            # Count actual health records (data points) and get latest update time
            current_health_record_count = 0
            latest_health_record_updated_at = None
            
            for section in health_data.get("sections", []):
                for metric in section.get("metrics", []):
                    data_points = metric.get("data_points", [])
                    current_health_record_count += len(data_points)
                    
                    for data_point in data_points:
                        if data_point.get("recorded_at"):
                            record_time = datetime.fromisoformat(data_point["recorded_at"].replace('Z', '+00:00'))
                            if not latest_health_record_updated_at or record_time > latest_health_record_updated_at:
                                latest_health_record_updated_at = record_time
            
            # If there are no actual health records (data points), don't generate analysis
            if current_health_record_count == 0:
                return {
                    "success": False,
                    "message": "No health records found for analysis",
                    "analysis": {
                        "areas_of_concern": [],
                        "positive_trends": [],
                        "recommendations": ["Please add some health records to get personalized AI insights."]
                    }
                }
            
            # Check if we should generate new analysis based on 5-day rule and force_check parameter
            should_generate, reason = ai_analysis_history_crud.should_generate_analysis(
                db, user_id, health_record_type_id, current_health_record_count, latest_health_record_updated_at, force_check=force_check
            )
                
            # Get user's language preference first
            from app.utils.user_language import get_user_language_from_cache
            user_language = await get_user_language_from_cache(user_id, db)
            
            if not should_generate:
                # Return the last analysis if available
                last_analysis = ai_analysis_history_crud.get_by_user_and_type(db, user_id, health_record_type_id)
                if last_analysis and last_analysis.analysis_content:
                    try:
                        cached_analysis = json.loads(last_analysis.analysis_content)
                        cached_language = getattr(last_analysis, 'analysis_language', 'en') or 'en'
                        
                        # Check if cached analysis language matches user's current language
                        if cached_language == user_language:
                            # Languages match - return cached analysis as-is
                            return {
                                "success": True,
                                "message": f"Using cached analysis ({reason})",
                                    "analysis": cached_analysis,
                                    "generated_at": last_analysis.last_generated_at.isoformat(),
                                    "cached": True,
                                    "reason": reason
                                }
                        else:
                            # Languages don't match - need to translate cached analysis
                            logger.info(f"Cached analysis is in {cached_language}, user wants {user_language}. Translating...")
                            from app.services.translation_service import translation_service
                            
                            # Translate the analysis content
                            translated_analysis = {}
                            
                            # Translate areas_of_concern
                            if 'areas_of_concern' in cached_analysis and isinstance(cached_analysis['areas_of_concern'], list):
                                translated_analysis['areas_of_concern'] = []
                                for i, concern in enumerate(cached_analysis['areas_of_concern']):
                                    if concern:
                                        translated_concern = translation_service.get_translated_content(
                                            db=db,
                                            entity_type='ai_analysis_history',
                                            entity_id=last_analysis.id,
                                            field_name=f'areas_of_concern[{i}]',
                                            original_text=str(concern),
                                            target_language=user_language,
                                            source_language=cached_language
                                        )
                                        translated_analysis['areas_of_concern'].append(translated_concern)
                            
                            # Translate positive_trends
                            if 'positive_trends' in cached_analysis and isinstance(cached_analysis['positive_trends'], list):
                                translated_analysis['positive_trends'] = []
                                for i, trend in enumerate(cached_analysis['positive_trends']):
                                    if trend:
                                        translated_trend = translation_service.get_translated_content(
                                            db=db,
                                            entity_type='ai_analysis_history',
                                            entity_id=last_analysis.id,
                                            field_name=f'positive_trends[{i}]',
                                            original_text=str(trend),
                                            target_language=user_language,
                                            source_language=cached_language
                                        )
                                        translated_analysis['positive_trends'].append(translated_trend)
                            
                            # Translate recommendations
                            if 'recommendations' in cached_analysis and isinstance(cached_analysis['recommendations'], list):
                                translated_analysis['recommendations'] = []
                                for i, recommendation in enumerate(cached_analysis['recommendations']):
                                    if recommendation:
                                        translated_rec = translation_service.get_translated_content(
                                            db=db,
                                            entity_type='ai_analysis_history',
                                            entity_id=last_analysis.id,
                                            field_name=f'recommendations[{i}]',
                                            original_text=str(recommendation),
                                            target_language=user_language,
                                            source_language=cached_language
                                        )
                                        translated_analysis['recommendations'].append(translated_rec)
                            
                            # Copy other fields as-is
                            for key in cached_analysis:
                                if key not in ['areas_of_concern', 'positive_trends', 'recommendations']:
                                    translated_analysis[key] = cached_analysis[key]
                            
                            return {
                                "success": True,
                                "message": f"Using cached analysis translated to {user_language} ({reason})",
                                "analysis": translated_analysis,
                            "generated_at": last_analysis.last_generated_at.isoformat(),
                            "cached": True,
                            "reason": reason
                        }
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse cached analysis for user {user_id}")
                else:
                    return {
                        "success": False,
                        "message": f"No analysis available ({reason})",
                        "analysis": {
                            "areas_of_concern": [],
                            "positive_trends": [],
                            "recommendations": ["Please add some health data to get personalized AI insights."]
                        }
                    }
            
            # Generate AI analysis using GPT in user's language (either forced or required by 5-day rule)
            ai_analysis_result = await self._generate_ai_analysis(health_data, health_record_type_id, user_id=user_id, target_language=user_language)
            ai_analysis = ai_analysis_result["analysis"]
            ai_success = ai_analysis_result["success"]
            
            if ai_success:
                
                # Save analysis to history with language
                try:
                    ai_analysis_history_crud.create(
                        db=db,
                        user_id=user_id,
                        analysis_type_id=health_record_type_id,
                        health_record_count=current_health_record_count,
                        health_record_updated_at=latest_health_record_updated_at,
                        analysis_content=json.dumps(ai_analysis),
                        analysis_language=user_language
                    )
                except Exception as e:
                    logger.error(f"Failed to save AI analysis history for user {user_id}: {e}")
                
                return {
                    "success": True,
                    "message": "AI analysis completed successfully",
                    "analysis": ai_analysis,
                    "generated_at": datetime.utcnow().isoformat(),
                    "data_summary": {
                        "total_sections": len(health_data.get("sections", [])),
                        "total_metrics": sum(len(section.get("metrics", [])) for section in health_data.get("sections", [])),
                        "total_data_points": sum(
                            len(metric.get("data_points", [])) 
                            for section in health_data.get("sections", []) 
                            for metric in section.get("metrics", [])
                        )
                    }
                }
            else:
                logger.warning(f"AI analysis failed for user {user_id}, using fallback analysis")
                return {
                    "success": False,
                    "message": ai_analysis_result["message"],
                    "analysis": ai_analysis,
                    "generated_at": datetime.utcnow().isoformat(),
                    "data_summary": {
                        "total_sections": len(health_data.get("sections", [])),
                        "total_metrics": sum(len(section.get("metrics", [])) for section in health_data.get("sections", [])),
                        "total_data_points": sum(
                            len(metric.get("data_points", [])) 
                            for section in health_data.get("sections", []) 
                            for metric in section.get("metrics", [])
                        )
                    }
                }
            
        except Exception as e:
            logger.error(f"Error in AI analysis for user {user_id}: {e}")
            return {
                "success": False,
                "message": f"AI analysis failed: {str(e)}",
                "analysis": {
                    "areas_of_concern": [],
                    "positive_trends": [],
                    "recommendations": ["Please try again later or contact support if the issue persists."]
                }
            }
    
    async def _get_user_context_data(
        self,
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        """Get user context data (age, sex, conditions, medications, family history) for AI analysis"""
        try:
            context = {
                "age": None,
                "sex": None,
                "current_conditions": [],
                "past_conditions": [],
                "family_history": [],
                "medications": []
            }
            
            # Get user from database to access supabase_user_id
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return context
            
            # Get user profile from Supabase
            if user.supabase_user_id:
                try:
                    profile = await supabase_service.get_user_profile(user.supabase_user_id)
                    if profile:
                        # Calculate age from date_of_birth
                        if profile.get("date_of_birth"):
                            try:
                                dob = datetime.fromisoformat(profile["date_of_birth"].replace("Z", "+00:00"))
                                today = datetime.utcnow()
                                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                                context["age"] = age
                            except (ValueError, TypeError):
                                pass
                        
                        # Get sex/gender
                        gender = profile.get("gender")
                        if gender:
                            context["sex"] = gender.capitalize()
                        
                        # Get medications
                        medications = profile.get("current_medications")
                        if medications:
                            med_list = []
                            if isinstance(medications, dict):
                                # Check if it's a dict with "medications" key containing array
                                if "medications" in medications and isinstance(medications["medications"], list):
                                    meds = medications["medications"]
                                    for med in meds:
                                        if isinstance(med, dict):
                                            drug_name = med.get("drugName", med.get("name", ""))
                                            dosage = med.get("dosage", "")
                                            frequency = med.get("frequency", "")
                                            if drug_name:
                                                med_str = drug_name
                                                if dosage:
                                                    med_str += f" {dosage}"
                                                if frequency:
                                                    med_str += f" {frequency}"
                                                med_list.append(med_str)
                            elif isinstance(medications, list):
                                # Direct list format
                                for med in medications:
                                    if isinstance(med, dict):
                                        drug_name = med.get("drugName", med.get("name", ""))
                                        dosage = med.get("dosage", "")
                                        frequency = med.get("frequency", "")
                                        if drug_name:
                                            med_str = drug_name
                                            if dosage:
                                                med_str += f" {dosage}"
                                            if frequency:
                                                med_str += f" {frequency}"
                                            med_list.append(med_str)
                            elif isinstance(medications, str):
                                # String format
                                if medications.strip():
                                    med_list.append(medications)
                            
                            if med_list:
                                context["medications"] = med_list
                except Exception as e:
                    logger.warning(f"Failed to fetch user profile from Supabase: {e}")
            
            # Get medical conditions
            try:
                conditions = medical_condition_crud.get_by_user(db, user_id, skip=0, limit=1000)
                for condition in conditions:
                    condition_str = condition.condition_name or ""
                    if condition.diagnosed_date:
                        condition_str += f" (Diagnosed: {condition.diagnosed_date.strftime('%Y-%m-%d')})"
                    
                    status = condition.status.value if hasattr(condition.status, 'value') else str(condition.status)
                    if status in ['current', 'active', 'ongoing']:
                        context["current_conditions"].append(condition_str)
                    elif status in ['past', 'resolved', 'inactive']:
                        context["past_conditions"].append(condition_str)
            except Exception as e:
                logger.warning(f"Failed to fetch medical conditions: {e}")
            
            # Get family history
            try:
                family_history = family_medical_history_crud.get_by_user(db, user_id, skip=0, limit=1000)
                for history in family_history:
                    relation = history.relation.value if hasattr(history.relation, 'value') else str(history.relation)
                    conditions_list = []
                    
                    # Use chronic_diseases if available
                    if history.chronic_diseases and isinstance(history.chronic_diseases, list):
                        for disease in history.chronic_diseases:
                            if isinstance(disease, dict):
                                disease_name = disease.get("disease", disease.get("condition", ""))
                                age_at_diagnosis = disease.get("age_at_diagnosis", disease.get("age_at_onset"))
                                if disease_name:
                                    if age_at_diagnosis:
                                        conditions_list.append(f"{disease_name} (Age at onset: {age_at_diagnosis})")
                                    else:
                                        conditions_list.append(disease_name)
                    # Fallback to legacy fields
                    elif history.condition_name:
                        condition_str = history.condition_name
                        if history.age_of_onset:
                            condition_str += f" (Age at onset: {history.age_of_onset})"
                        conditions_list.append(condition_str)
                    
                    if conditions_list:
                        context["family_history"].append(f"{relation}: {', '.join(conditions_list)}")
            except Exception as e:
                logger.warning(f"Failed to fetch family history: {e}")
            
            return context
        except Exception as e:
            logger.error(f"Error getting user context data: {e}")
            return {
                "age": None,
                "sex": None,
                "current_conditions": [],
                "past_conditions": [],
                "family_history": [],
                "medications": []
            }
    
    async def _get_user_health_data(
        self, 
        db: Session, 
        user_id: int, 
        health_record_type_id: int
    ) -> Dict[str, Any]:
        """Get user's health data for analysis"""
        try:
            # Handle medical images (type ID 5) differently
            if health_record_type_id == 5:
                return await self._get_medical_images_data(db, user_id)
            
            # Get sections with metrics and data points
            # We need to get ALL sections (both user-created and admin defaults) that have user's health records
            sections_data = health_record_section_metric_crud.get_all_sections_with_user_data(
                db, user_id, include_inactive=False, health_record_type_id=health_record_type_id
            )
            
            
            if not sections_data:
                return {}
            
            # Get user context data
            user_context = await self._get_user_context_data(db, user_id)
            
            # Structure the data for AI analysis
            health_data = {
                "user_id": user_id,
                "analysis_date": datetime.utcnow().isoformat(),
                "user_context": user_context,
                "sections": []
            }
            
            for section in sections_data:
                section_data = {
                    "section_name": section.get("display_name", section.get("name", "Unknown")),
                    "section_description": section.get("description", ""),
                    "metrics": []
                }
                
                metrics = section.get("metrics", [])
                for metric in metrics:
                    metric_data = {
                        "metric_name": metric.get("display_name", metric.get("name", "Unknown")),
                        "unit": metric.get("unit", ""),
                        "reference_range": metric.get("threshold", {}),
                        "latest_value": metric.get("latest_value"),
                        "latest_status": metric.get("latest_status", "unknown"),
                        "latest_recorded_at": metric.get("latest_recorded_at"),
                        "total_records": metric.get("total_records", 0),
                        "trend": metric.get("trend", "unknown"),
                        "data_points": []
                    }
                    
                    # Add ALL data points (no cutoff for AI analysis)
                    data_points = metric.get("data_points", [])
                    
                    for point in data_points:
                        try:
                            point_date = datetime.fromisoformat(point.get("recorded_at", "").replace("Z", "+00:00"))
                            metric_data["data_points"].append({
                                "value": point.get("value"),
                                "status": point.get("status", "normal"),
                                "recorded_at": point.get("recorded_at"),
                                "source": point.get("source", "manual")
                            })
                        except (ValueError, TypeError) as e:
                            continue
                    
                    # Sort data points by date
                    metric_data["data_points"].sort(
                        key=lambda x: x.get("recorded_at", ""), 
                        reverse=True
                    )
                    
                    section_data["metrics"].append(metric_data)
                
                health_data["sections"].append(section_data)
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error getting user health data: {e}")
            return {}
    
    def _format_user_prompt_for_assistant(
        self, 
        health_data: Dict[str, Any], 
        health_record_type_id: int,
        target_language: str = 'en'
    ) -> str:
        """Format user prompt for Assistants API (no system instructions, just data)"""
        # Language name mapping
        language_names = {
            'en': 'English',
            'es': 'Spanish',
            'pt': 'Portuguese'
        }
        target_language_name = language_names.get(target_language, 'English')
        
        # Get user context
        user_context = health_data.get('user_context', {})
        
        # Format age
        age_str = str(user_context.get('age')) if user_context.get('age') else "Not provided"
        
        # Format sex
        sex_str = user_context.get('sex') or "Not provided"
        
        # Format conditions
        current_conditions = user_context.get('current_conditions', [])
        past_conditions = user_context.get('past_conditions', [])
        conditions_str = ""
        if current_conditions or past_conditions:
            if current_conditions:
                conditions_str += f"Current Conditions: {', '.join(current_conditions)}"
            else:
                conditions_str += "Current Conditions: None reported"
            if past_conditions:
                conditions_str += f"\nPast Conditions: {', '.join(past_conditions)}"
            else:
                conditions_str += "\nPast Conditions: None reported"
        else:
            conditions_str = "Current Conditions: None reported\nPast Conditions: None reported"
        
        # Format family history
        family_history = user_context.get('family_history', [])
        family_history_str = ', '.join(family_history) if family_history else "None reported"
        
        # Format medications
        medications = user_context.get('medications', [])
        medications_str = ', '.join(medications) if medications else "None reported"
        
        # Handle different types of data
        if health_record_type_id == 5:  # Exams/Medical Images
            prompt = f"""Please analyze the following medical imaging data and provide a comprehensive summary focused on imaging findings and recommendations.
IMPORTANT: Provide your entire response in {target_language_name} language.

**Medical Imaging Data Summary:**
- Age: {age_str}
- Sex: {sex_str}
- [Current and Past Conditions and Family History]
  {conditions_str}
  Family History: {family_history_str}
- [Medication being taken]
  {medications_str}
- Analysis Date: {health_data.get('analysis_date', 'Unknown')}
- Total Image Types: {len(health_data.get('sections', []))}

**Detailed Medical Imaging Data:**

"""
            for section in health_data.get("sections", []):
                prompt += f"**Image Type: {section.get('section_name', 'Unknown')}**\n"
                if section.get('section_description'):
                    prompt += f"Description: {section.get('section_description')}\n"
                
                for metric in section.get("metrics", []):
                    prompt += f"\n- **{metric.get('metric_name', 'Unknown')}**\n"
                    prompt += f"  - Body Part: {metric.get('body_part', 'N/A')}\n"
                    prompt += f"  - Latest Findings: {metric.get('latest_value', 'N/A')}\n"
                    prompt += f"  - Status: {metric.get('latest_status', 'unknown')}\n"
                    prompt += f"  - Total Records: {metric.get('total_records', 0)}\n"
                    
                    # Add recent imaging data points (max 5 per type)
                    data_points = metric.get('data_points', [])[:5]
                    if data_points:
                        prompt += f"  - Recent Imaging Studies:\n"
                        for point in data_points:
                            findings = point.get('value', 'N/A')
                            recorded_at = point.get('recorded_at', 'Unknown date')
                            interpretation = point.get('interpretation', '')
                            conclusions = point.get('conclusions', '')
                            status = point.get('status', 'normal')
                            prompt += f"    * {findings} ({recorded_at}) - {status}"
                            if interpretation:
                                prompt += f"\n      Interpretation: {interpretation}"
                            if conclusions:
                                prompt += f"\n      Conclusion: {conclusions}"
                            prompt += "\n"
        else:  # Body, Vitals, Lifestyle, Summary
            prompt = f"""Please analyze the following health data and provide a comprehensive health assessment.
IMPORTANT: Provide your entire response in {target_language_name} language.

**Health Data Summary:**
- Age: {age_str}
- Sex: {sex_str}
- [Current and Past Conditions and Family History]
  {conditions_str}
  Family History: {family_history_str}
- [Medication being taken]
  {medications_str}
- Analysis Date: {health_data.get('analysis_date', 'Unknown')}
- Total Sections: {len(health_data.get('sections', []))}

**Detailed Health Data:**

"""
            for section in health_data.get("sections", []):
                prompt += f"**Section: {section.get('section_name', 'Unknown')}**\n\n"
                if section.get('section_description'):
                    prompt += f"Description: {section.get('section_description')}\n\n"
                
                for metric in section.get("metrics", []):
                    prompt += f"- **{metric.get('metric_name', 'Unknown')}**\n\n"
                    prompt += f"  - Unit: {metric.get('unit', 'N/A')}\n\n"
                    
                    latest_value = metric.get('latest_value')
                    if latest_value is None:
                        prompt += f"  - Latest Value: None\n\n"
                    else:
                        prompt += f"  - Latest Value: {latest_value}\n\n"
                    
                    prompt += f"  - Status: {metric.get('latest_status', 'unknown')}\n\n"
                    prompt += f"  - Trend: {metric.get('trend', 'unknown')}\n\n"
                    prompt += f"  - Total Records: {metric.get('total_records', 0)}\n\n"
                    
                    # Add recent data points (last 5)
                    data_points = metric.get('data_points', [])[:5]
                    if data_points:
                        prompt += f"  - Recent Values:\n\n"
                        for point in data_points:
                            value = point.get('value', 'N/A')
                            recorded_at = point.get('recorded_at', 'Unknown date')
                            status = point.get('status', 'normal')
                            prompt += f"   * {value} ({recorded_at}) – {status}\n\n"
        
        return prompt
    
    async def _generate_ai_analysis_with_assistant(
        self,
        health_data: Dict[str, Any],
        health_record_type_id: int,
        user_id: int = None,
        target_language: str = 'en'
    ) -> Dict[str, Any]:
        """Generate AI analysis using OpenAI Assistants API"""
        try:
            # Get assistant ID for this health record type (should already be validated in _generate_ai_analysis)
            assistant_id = self.assistant_ids.get(health_record_type_id)
            if not assistant_id:
                logger.error(f"No assistant ID configured for health_record_type_id {health_record_type_id}")
                return {
                    "success": False,
                    "message": f"Assistant not configured for health record type {health_record_type_id}",
                    "analysis": {
                        "areas_of_concern": [],
                        "positive_trends": [],
                        "recommendations": []
                    }
                }
            
            # Format user prompt (without system instructions)
            user_prompt = self._format_user_prompt_for_assistant(health_data, health_record_type_id, target_language)
            
            # Create a new thread
            thread = self.client.beta.threads.create()
            thread_id = thread.id
            
            # Add user message to thread
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_prompt
            )
            
            # Run the assistant
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id
            )
            
            # Poll for completion
            max_wait_time = 60  # seconds
            start_time = datetime.utcnow()
            while True:
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                if run_status.status == "completed":
                    break
                elif run_status.status in ["failed", "cancelled", "expired"]:
                    error_msg = f"Assistant run {run_status.status}: {getattr(run_status, 'last_error', {}).get('message', 'Unknown error')}"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "message": error_msg,
                        "analysis": {
                            "areas_of_concern": [],
                            "positive_trends": [],
                            "recommendations": []
                        }
                    }
                
                # Check timeout
                if (datetime.utcnow() - start_time).total_seconds() > max_wait_time:
                    logger.error("Assistant run timeout")
                    return {
                        "success": False,
                        "message": "Assistant run timeout",
                        "analysis": {
                            "areas_of_concern": [],
                            "positive_trends": [],
                            "recommendations": []
                        }
                    }
                
                # Wait before next poll
                import asyncio
                await asyncio.sleep(1)
            
            # Get the messages from the thread
            messages = self.client.beta.threads.messages.list(thread_id=thread_id)
            
            # Find the assistant's message (first message in the list with role="assistant")
            ai_response = None
            for message in messages.data:
                if message.role == "assistant":
                    # Get text content from message
                    if message.content and len(message.content) > 0:
                        content_block = message.content[0]
                        if hasattr(content_block, 'text'):
                            ai_response = content_block.text.value
                        elif isinstance(content_block, dict) and 'text' in content_block:
                            ai_response = content_block['text'].get('value', '')
                    break
            
            if not ai_response:
                logger.error("No assistant response found")
                return {
                    "success": False,
                    "message": "No response from assistant",
                    "analysis": {
                        "areas_of_concern": [],
                        "positive_trends": [],
                        "recommendations": []
                    }
                }
            
            # Parse response as JSON
            try:
                # Check if response is wrapped in markdown code block
                if '```json' in ai_response:
                    json_match = re.search(r'```json\n(.*?)\n```', ai_response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        analysis = json.loads(json_str)
                    else:
                        analysis = json.loads(ai_response)
                else:
                    analysis = json.loads(ai_response)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                analysis = self._parse_text_response(ai_response)
            
            return {
                "success": True,
                "message": "AI analysis completed successfully",
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Error generating AI analysis with assistant: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"AI analysis failed: {str(e)}",
                "analysis": {
                    "areas_of_concern": [],
                    "positive_trends": [],
                    "recommendations": []
                }
            }
    
    async def _generate_ai_analysis(
        self, 
        health_data: Dict[str, Any], 
        health_record_type_id: int = 1,
        user_id: int = None,
        target_language: str = 'en'
    ) -> Dict[str, Any]:
        """Generate AI analysis using OpenAI Assistants API"""
        if not self.openai_enabled:
            return {
                "success": False,
                "message": "OpenAI service not available",
                "analysis": {
                    "areas_of_concern": [],
                    "positive_trends": [],
                    "recommendations": []
                }
            }
        
        # Always use Assistants API
        assistant_id = self.assistant_ids.get(health_record_type_id)
        if not assistant_id:
            logger.error(f"No assistant ID configured for health_record_type_id {health_record_type_id}")
            return {
                "success": False,
                "message": f"Assistant not configured for health record type {health_record_type_id}",
                "analysis": {
                    "areas_of_concern": [],
                    "positive_trends": [],
                    "recommendations": []
                }
            }
        
        logger.info(f"Using Assistants API for health_record_type_id {health_record_type_id}")
        return await self._generate_ai_analysis_with_assistant(
            health_data, health_record_type_id, user_id, target_language
        )
    
    
    def _parse_text_response(self, text_response: str) -> Dict[str, Any]:
        """Parse text response into structured format if JSON parsing fails"""
        return {
            "areas_of_concern": ["Unable to parse specific concerns from AI response"],
            "positive_trends": ["Unable to parse specific trends from AI response"],
            "recommendations": ["Please review the overall assessment above for recommendations"]
        }
    
    async def _get_medical_images_data(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get medical images data for AI analysis"""
        try:
            # Get all medical images for the user
            medical_images = db.query(HealthRecordDocExam).filter(
                HealthRecordDocExam.created_by == user_id
            ).order_by(HealthRecordDocExam.image_date.desc()).all()
            
            if not medical_images:
                return {}
            
            # Group images by image type
            images_by_type = {}
            for image in medical_images:
                image_type = image.image_type.value if image.image_type else "Others"
                if image_type not in images_by_type:
                    images_by_type[image_type] = []
                images_by_type[image_type].append(image)
            
            # Structure the data for AI analysis
            health_data = {
                "user_id": user_id,
                "analysis_date": datetime.utcnow().isoformat(),
                "sections": []
            }
            
            
            for image_type, images in images_by_type.items():
                section_data = {
                    "section_name": image_type,
                    "section_description": f"Medical imaging studies of type {image_type}",
                    "metrics": []
                }
                
                # Group by body part within each image type
                body_parts = {}
                for image in images:
                    body_part = image.body_part or "Unknown"
                    if body_part not in body_parts:
                        body_parts[body_part] = []
                    body_parts[body_part].append(image)
                
                for body_part, part_images in body_parts.items():
                    # Get the most recent image for this body part
                    latest_image = part_images[0]  # Already sorted by date desc
                    
                    metric_data = {
                        "metric_name": f"{body_part} Imaging",
                        "body_part": body_part,
                        "latest_value": latest_image.findings.value if latest_image.findings else "Unknown",
                        "latest_status": latest_image.findings.value if latest_image.findings else "unknown",
                        "total_records": len(part_images),
                        "data_points": []
                    }
                    
                    # Add recent data points
                    for image in part_images[:5]:  # Last 5 images
                        data_point = {
                            "value": image.findings.value if image.findings else "Unknown",
                            "recorded_at": image.image_date.isoformat() if image.image_date else "Unknown",
                            "status": image.findings.value if image.findings else "unknown",
                            "interpretation": image.interpretation or "",
                            "conclusions": image.conclusions or ""
                        }
                        metric_data["data_points"].append(data_point)
                    
                    section_data["metrics"].append(metric_data)
                
                health_data["sections"].append(section_data)
            
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error fetching medical images data: {e}")
            return {}


# Create a singleton instance
ai_analysis_service = AIAnalysisService()
