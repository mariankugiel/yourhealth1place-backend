import os
import json
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.health_record import HealthRecord, HealthRecordMetric, HealthRecordSection, HealthRecordImage
from app.crud.health_record import health_record_section_metric_crud
from app.crud.medical_images import MedicalImageCRUD
from app.crud.ai_analysis import ai_analysis_history_crud

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
            except Exception as e:
                logging.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
                self.model = None
                self.openai_enabled = False
        else:
            self.client = None
            self.model = None
            self.openai_enabled = False
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
                
            if not should_generate:
                # Return the last analysis if available
                last_analysis = ai_analysis_history_crud.get_by_user_and_type(db, user_id, health_record_type_id)
                if last_analysis and last_analysis.analysis_content:
                    try:
                        return {
                            "success": True,
                            "message": f"Using cached analysis ({reason})",
                            "analysis": json.loads(last_analysis.analysis_content),
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
            
            # Generate AI analysis using GPT (either forced or required by 5-day rule)
            ai_analysis_result = await self._generate_ai_analysis(health_data, health_record_type_id)
            ai_analysis = ai_analysis_result["analysis"]
            ai_success = ai_analysis_result["success"]
            
            if ai_success:
                
                # Save analysis to history
                try:
                    ai_analysis_history_crud.create(
                        db=db,
                        user_id=user_id,
                        analysis_type_id=health_record_type_id,
                        health_record_count=current_health_record_count,
                        health_record_updated_at=latest_health_record_updated_at,
                        analysis_content=json.dumps(ai_analysis)
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
            
            # Structure the data for AI analysis
            health_data = {
                "user_id": user_id,
                "analysis_date": datetime.utcnow().isoformat(),
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
    
    async def _generate_ai_analysis(self, health_data: Dict[str, Any], health_record_type_id: int = 1) -> Dict[str, Any]:
        """Generate AI analysis using GPT or fallback to local analysis"""
        if not self.openai_enabled:
            return {
                "success": False,
                "message": "OpenAI service not available, using local analysis",
                "analysis": self._generate_fallback_analysis(health_data)
            }
        
        try:
            # Prepare the prompt for GPT
            prompt = self._create_analysis_prompt(health_data, health_record_type_id)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a medical AI assistant that analyzes health data and provides insights, recommendations, and assessments. 
                        
                        Your role is to:
                        1. Analyze health metrics and identify patterns
                        2. Identify areas of concern based on abnormal values
                        3. Highlight positive trends and improvements
                        4. Provide actionable recommendations
                        5. Assess overall health status
                        6. Identify potential risk factors
                        7. Suggest next steps for health monitoring
                        
                        Always provide evidence-based insights and recommend consulting healthcare providers for medical decisions.
                        Be encouraging but realistic about health status.
                        Focus on actionable, personalized recommendations."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            # Parse the response
            ai_response = response.choices[0].message.content
            
            # Parse response as JSON for all health record types
            try:
                # Check if response is wrapped in markdown code block
                if '```json' in ai_response:
                    # Extract JSON from markdown code block
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
                # If not JSON, create structured response from text
                analysis = self._parse_text_response(ai_response)
            
            return {
                "success": True,
                "message": "AI analysis completed successfully",
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Error generating AI analysis: {e}")
            return {
                "success": False,
                "message": f"AI analysis failed: {str(e)}. Using local analysis instead.",
                "analysis": self._generate_fallback_analysis(health_data)
            }
    
    def _create_analysis_prompt(self, health_data: Dict[str, Any], health_record_type_id: int = 1) -> str:
        """Create a detailed prompt for GPT analysis"""
        
        # Check if this is for medical images (type ID 5)
        if health_record_type_id == 5:
            return self._create_medical_images_prompt(health_data)
        
        prompt = f"""
        Please analyze the following health data and provide a comprehensive health assessment:

        **Health Data Summary:**
        - User ID: {health_data.get('user_id', 'Unknown')}
        - Analysis Date: {health_data.get('analysis_date', 'Unknown')}
        - Total Sections: {len(health_data.get('sections', []))}

        **Detailed Health Data:**

        """
        
        for section in health_data.get("sections", []):
            prompt += f"\n**Section: {section.get('section_name', 'Unknown')}**\n"
            if section.get('section_description'):
                prompt += f"Description: {section.get('section_description')}\n"
            
            for metric in section.get("metrics", []):
                prompt += f"\n- **{metric.get('metric_name', 'Unknown')}**\n"
                prompt += f"  - Unit: {metric.get('unit', 'N/A')}\n"
                prompt += f"  - Latest Value: {metric.get('latest_value', 'N/A')}\n"
                prompt += f"  - Status: {metric.get('latest_status', 'unknown')}\n"
                prompt += f"  - Trend: {metric.get('trend', 'unknown')}\n"
                prompt += f"  - Total Records: {metric.get('total_records', 0)}\n"
                
                if metric.get('reference_range'):
                    prompt += f"  - Reference Range: {metric.get('reference_range')}\n"
                
                # Add recent data points
                data_points = metric.get('data_points', [])[:5]  # Last 5 points
                if data_points:
                    prompt += f"  - Recent Values:\n"
                    for point in data_points:
                        prompt += f"    * {point.get('value', 'N/A')} ({point.get('recorded_at', 'Unknown date')}) - {point.get('status', 'normal')}\n"
        
        prompt += """

        **Please provide your analysis in the following JSON format:**

        {
            "areas_of_concern": [
                "Write 1-2 short, conversational sentences (35-40 words) about specific health concerns. Be direct but encouraging."
            ],
            "positive_trends": [
                "Write 1-2 short, conversational sentences (35-40 words) about positive health trends. Be encouraging and supportive."
            ],
            "recommendations": [
                "Write 1-2 short, conversational sentences (35-40 words) with specific, actionable health recommendations. Be practical and motivating."
            ]
        }

        **Guidelines:**
        - Keep each response conversational and friendly (35-40 words maximum)
        - Be specific and reference actual metric values when possible
        - Use encouraging, supportive language
        - Provide actionable, practical recommendations
        - Be direct but not alarming about concerns
        - Focus on what the user can do to improve their health
        - Avoid medical jargon - use everyday language
        """
        
        return prompt
    
    def _create_medical_images_prompt(self, health_data: Dict[str, Any]) -> str:
        """Create a specialized prompt for medical images analysis"""
        prompt = f"""
        Please analyze the following medical imaging data and provide a comprehensive summary focused on imaging findings and recommendations:

        **Medical Imaging Data Summary:**
        - User ID: {health_data.get('user_id', 'Unknown')}
        - Analysis Date: {health_data.get('analysis_date', 'Unknown')}
        - Total Image Types: {len(health_data.get('sections', []))}

        **Detailed Medical Imaging Data:**

        """
        
        for section in health_data.get("sections", []):
            prompt += f"\n**Image Type: {section.get('section_name', 'Unknown')}**\n"
            if section.get('section_description'):
                prompt += f"Description: {section.get('section_description')}\n"
            
            for metric in section.get("metrics", []):
                prompt += f"\n- **{metric.get('metric_name', 'Unknown')}**\n"
                prompt += f"  - Body Part: {metric.get('body_part', 'N/A')}\n"
                prompt += f"  - Latest Findings: {metric.get('latest_value', 'N/A')}\n"
                prompt += f"  - Status: {metric.get('latest_status', 'unknown')}\n"
                prompt += f"  - Total Records: {metric.get('total_records', 0)}\n"
                
                # Add recent imaging data points
                data_points = metric.get('data_points', [])[:5]  # Last 5 points
                if data_points:
                    prompt += f"  - Recent Imaging Studies:\n"
                    for point in data_points:
                        prompt += f"    * {point.get('value', 'N/A')} ({point.get('recorded_at', 'Unknown date')}) - {point.get('status', 'normal')}\n"
        
        prompt += """

        **Please provide your analysis in the following JSON format:**

        {
            "areas_of_concern": [
                "Write 1-2 short, conversational sentences (35-40 words) about specific imaging concerns. Be direct but encouraging."
            ],
            "positive_trends": [
                "Write 1-2 short, conversational sentences (35-40 words) about positive imaging findings. Be encouraging and supportive."
            ],
            "recommendations": [
                "Write 1-2 short, conversational sentences (35-40 words) with specific, actionable recommendations for imaging follow-up. Be practical and motivating."
            ]
        }

        **Guidelines:**
        - Keep each response conversational and friendly (35-40 words maximum)
        - Be specific and reference actual imaging findings when possible
        - Use encouraging, supportive language
        - Provide actionable, practical recommendations
        - Be direct but not alarming about concerns
        - Focus on what the user can do to monitor their imaging health
        - Avoid medical jargon - use everyday language
        - Mention specific imaging types (X-ray, MRI, CT, Ultrasound, etc.) when relevant
        """
        
        return prompt
    
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
            medical_images = db.query(HealthRecordImage).filter(
                HealthRecordImage.created_by == user_id
            ).order_by(HealthRecordImage.image_date.desc()).all()
            
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

    def _generate_fallback_analysis(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate simple fallback analysis when OpenAI is not available"""
        return {
            "areas_of_concern": ["AI analysis is currently unavailable. Please try again later."],
            "positive_trends": ["Your health data has been recorded successfully."],
            "recommendations": ["Continue monitoring your health metrics regularly."]
        }

# Create a singleton instance
ai_analysis_service = AIAnalysisService()
