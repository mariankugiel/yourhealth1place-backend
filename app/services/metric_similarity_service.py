from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
import re
import unicodedata
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_
# from app.models.health_record import MetricCategories, MetricSubCategories  # These classes don't exist
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed. Similarity calculation will use fallback mode.")

class MetricSimilarityService:
    """
    AI-powered service to detect similar metrics and prevent duplication.
    Uses multiple similarity algorithms for comprehensive detection.
    """
    
    def __init__(self):
        self.similarity_threshold = 0.75  # 75% similarity threshold
        self.exact_match_threshold = 0.95  # 95% for near-exact matches
        self.min_word_length = 3  # Minimum word length to consider
        self.section_similarity_threshold = 0.85  # Threshold for sections
        self.metric_similarity_threshold = 0.80  # Threshold for metrics
        self.openai_similarity_threshold = 0.95  # 95% threshold for OpenAI similarity
        self.openai_client = None
        if OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
            try:
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI client initialized for similarity calculation")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.openai_client = None
        
    def check_similar_categories(
        self, 
        new_name: str, 
        health_record_type_id: int, 
        db: Session,
        exclude_user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Check for similar metric categories in a specific health record type.
        
        Args:
            new_name: The new category name to check
            health_record_type_id: The health record type ID
            db: Database session
            exclude_user_id: User ID to exclude from search (for updates)
            
        Returns:
            List of similar categories with similarity scores
        """
        # TODO: Implement when MetricCategories model is available
        logger.warning("check_similar_categories method not implemented - MetricCategories model not available")
        return []
    
    def check_similar_sub_categories(
        self, 
        new_name: str, 
        category_id: int, 
        db: Session,
        exclude_user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Check for similar metric sub-categories in a specific category.
        
        Args:
            new_name: The new sub-category name to check
            category_id: The category ID
            db: Database session
            exclude_user_id: User ID to exclude from search (for updates)
            
        Returns:
            List of similar sub-categories with similarity scores
        """
        # TODO: Implement when MetricSubCategories model is available
        logger.warning("check_similar_sub_categories method not implemented - MetricSubCategories model not available")
        return []
    
    def check_global_similarity(
        self, 
        new_name: str, 
        db: Session,
        exclude_user_id: Optional[int] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Check for similar metrics across all categories and sub-categories.
        
        Args:
            new_name: The new metric name to check
            db: Database session
            exclude_user_id: User ID to exclude from search (for updates)
            
        Returns:
            Dictionary with similar categories and sub-categories
        """
        # TODO: Implement when MetricCategories and MetricSubCategories models are available
        logger.warning("check_global_similarity method not implemented - required models not available")
        return {"similar_categories": [], "similar_sub_categories": []}
    
    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two metric names using multiple algorithms.
        
        Args:
            name1: First metric name
            name2: Second metric name
            
        Returns:
            Similarity score between 0 and 1
        """
        if not name1 or not name2:
            return 0.0
        
        # Normalize names
        name1_normalized = self._normalize_name(name1)
        name2_normalized = self._normalize_name(name2)
        
        # Check for exact match after normalization
        if name1_normalized == name2_normalized:
            return 1.0
        
        # Calculate different similarity scores
        sequence_similarity = SequenceMatcher(None, name1_normalized, name2_normalized).ratio()
        
        # Word-based similarity
        word_similarity = self._calculate_word_similarity(name1_normalized, name2_normalized)
        
        # Abbreviation similarity
        abbreviation_similarity = self._calculate_abbreviation_similarity(name1_normalized, name2_normalized)
        
        # Take the highest similarity score
        max_similarity = max(sequence_similarity, word_similarity, abbreviation_similarity)
        
        return max_similarity
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize metric name for comparison with multilingual support.
        
        Args:
            name: Original metric name
            
        Returns:
            Normalized name
        """
        if not name:
            return ""
        
        # Remove diacritics (á → a, ç → c, etc.)
        normalized = unicodedata.normalize('NFKD', name)
        normalized = ''.join(c for c in normalized if not unicodedata.combining(c))
        
        # Convert to lowercase
        normalized = normalized.lower()
        
        # Remove special characters and extra spaces
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Common abbreviations and synonyms
        abbreviations = {
            'bp': 'blood pressure',
            'hr': 'heart rate',
            'bpm': 'beats per minute',
            'temp': 'temperature',
            'wt': 'weight',
            'ht': 'height',
            'bmi': 'body mass index',
            'o2': 'oxygen',
            'sat': 'saturation',
            'glucose': 'blood glucose',
            'sugar': 'blood glucose',
            'chol': 'cholesterol',
            'hdl': 'high density lipoprotein',
            'ldl': 'low density lipoprotein',
            'trig': 'triglycerides',
            'wbc': 'white blood cells',
            'rbc': 'red blood cells',
            'hgb': 'hemoglobin',
            'hct': 'hematocrit',
            'plt': 'platelets',
            'na': 'sodium',
            'k': 'potassium',
            'cl': 'chloride',
            'co2': 'carbon dioxide',
            'bun': 'blood urea nitrogen',
            'creat': 'creatinine',
            'alt': 'alanine aminotransferase',
            'ast': 'aspartate aminotransferase',
            'alk phos': 'alkaline phosphatase',
            'bil': 'bilirubin',
            'alb': 'albumin',
            'protein': 'total protein',
            'ca': 'calcium',
            'mg': 'magnesium',
            'phos': 'phosphorus',
            'fe': 'iron',
            'ferritin': 'ferritin',
            'tibc': 'total iron binding capacity',
            'vit d': 'vitamin d',
            'vit b12': 'vitamin b12',
            'folate': 'folic acid',
            'tsh': 'thyroid stimulating hormone',
            't4': 'thyroxine',
            't3': 'triiodothyronine',
            'psa': 'prostate specific antigen',
            'hba1c': 'hemoglobin a1c',
            'a1c': 'hemoglobin a1c',
            'urine': 'urinalysis',
            'ua': 'urinalysis',
            # Portuguese abbreviations
            'leuc': 'leucocitos',
            'plaquetas': 'platelets',
            'glicose': 'glucose',
            'colesterol': 'cholesterol',
            'triglicerides': 'triglycerides',
        }
        
        # Replace abbreviations
        for abbrev, full in abbreviations.items():
            normalized = re.sub(r'\b' + re.escape(abbrev) + r'\b', full, normalized)
        
        return normalized
    
    def _calculate_word_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity based on word overlap.
        
        Args:
            name1: First normalized name
            name2: Second normalized name
            
        Returns:
            Word similarity score
        """
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _calculate_abbreviation_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity based on abbreviation patterns.
        
        Args:
            name1: First normalized name
            name2: Second normalized name
            
        Returns:
            Abbreviation similarity score
        """
        # Extract first letters of each word
        def get_initials(name: str) -> str:
            words = name.split()
            return ''.join(word[0] for word in words if len(word) >= self.min_word_length)
        
        initials1 = get_initials(name1)
        initials2 = get_initials(name2)
        
        if not initials1 or not initials2:
            return 0.0
        
        # Compare initials
        if initials1 == initials2:
            return 0.9  # High similarity for matching initials
        
        # Check if one is abbreviation of the other
        if initials1 in name2 or initials2 in name1:
            return 0.8
        
        return 0.0
    
    def _get_match_type(self, similarity_score: float) -> str:
        """
        Get the type of match based on similarity score.
        
        Args:
            similarity_score: Similarity score between 0 and 1
            
        Returns:
            Match type description
        """
        if similarity_score >= self.exact_match_threshold:
            return "exact_match"
        elif similarity_score >= 0.85:
            return "very_similar"
        elif similarity_score >= 0.75:
            return "similar"
        else:
            return "partial_match"
    
    def get_similarity_recommendations(
        self, 
        similar_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate recommendations based on similar items found.
        
        Args:
            similar_items: List of similar items with similarity scores
            
        Returns:
            Recommendations for the user
        """
        if not similar_items:
            return {
                "has_similar": False,
                "recommendations": [],
                "message": "No similar metrics found. You can proceed with creating this metric."
            }
        
        # Group by match type
        exact_matches = [item for item in similar_items if item["match_type"] == "exact_match"]
        very_similar = [item for item in similar_items if item["match_type"] == "very_similar"]
        similar = [item for item in similar_items if item["match_type"] == "similar"]
        
        recommendations = []
        
        if exact_matches:
            recommendations.append({
                "type": "warning",
                "message": f"An exact match already exists: '{exact_matches[0]['display_name']}'",
                "suggestion": "Consider using the existing metric instead of creating a duplicate."
            })
        
        if very_similar:
            recommendations.append({
                "type": "info",
                "message": f"Very similar metrics found: {', '.join([item['display_name'] for item in very_similar[:3]])}",
                "suggestion": "Check if one of these meets your needs before creating a new one."
            })
        
        if similar:
            recommendations.append({
                "type": "info",
                "message": f"Similar metrics found: {', '.join([item['display_name'] for item in similar[:2]])}",
                "suggestion": "Consider using a more descriptive name to avoid confusion."
            })
        
        return {
            "has_similar": True,
            "recommendations": recommendations,
            "similar_items": similar_items[:5],  # Top 5 most similar
            "message": f"Found {len(similar_items)} similar metrics. Please review before proceeding."
        }

    def find_similar_sections(
        self,
        user_id: int,
        section_name: str,
        health_record_type_id: int,
        db: Session,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar sections for a user.
        
        Args:
            user_id: User ID
            section_name: New section name to check
            health_record_type_id: Health record type ID
            db: Database session
            threshold: Similarity threshold (default: 0.85)
            
        Returns:
            List of similar sections with similarity scores, sorted by score descending
        """
        from app.models.health_record import HealthRecordSection
        
        threshold = threshold or self.section_similarity_threshold
        
        # Get all user sections of the same type
        existing_sections = db.query(HealthRecordSection).filter(
            and_(
                HealthRecordSection.created_by == user_id,
                HealthRecordSection.health_record_type_id == health_record_type_id
            )
        ).all()
        
        similar_sections = []
        normalized_new_name = self._normalize_name(section_name)
        
        for section in existing_sections:
            similarity = self._calculate_similarity(
                normalized_new_name,
                self._normalize_name(section.display_name or section.name)
            )
            
            if similarity >= threshold:
                similar_sections.append({
                    "id": section.id,
                    "name": section.name,
                    "display_name": section.display_name,
                    "similarity_score": similarity,
                    "match_type": self._get_match_type(similarity)
                })
        
        # Sort by similarity score descending
        similar_sections.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return similar_sections
    
    def find_similar_metrics(
        self,
        section_id: int,
        metric_name: str,
        db: Session,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar metrics within a section.
        
        Args:
            section_id: Section ID
            metric_name: New metric name to check
            db: Database session
            threshold: Similarity threshold (default: 0.80)
            
        Returns:
            List of similar metrics with similarity scores, sorted by score descending
        """
        from app.models.health_record import HealthRecordMetric
        
        threshold = threshold or self.metric_similarity_threshold
        
        # Get all metrics in this section
        existing_metrics = db.query(HealthRecordMetric).filter(
            HealthRecordMetric.section_id == section_id
        ).all()
        
        similar_metrics = []
        normalized_new_name = self._normalize_name(metric_name)
        
        for metric in existing_metrics:
            similarity = self._calculate_similarity(
                normalized_new_name,
                self._normalize_name(metric.display_name or metric.name)
            )
            
            if similarity >= threshold:
                similar_metrics.append({
                    "id": metric.id,
                    "name": metric.name,
                    "display_name": metric.display_name,
                    "similarity_score": similarity,
                    "match_type": self._get_match_type(similarity)
                })
        
        # Sort by similarity score descending
        similar_metrics.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return similar_metrics
    
    def batch_check_similarity(
        self,
        user_id: int,
        sections: List[Dict[str, Any]],
        metrics: List[Dict[str, Any]],
        health_record_type_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Batch check similarity for multiple sections and metrics.
        
        Args:
            user_id: User ID
            sections: List of dicts with 'name' key
            metrics: List of dicts with 'metric_name' and 'section_name' keys
            health_record_type_id: Health record type ID
            db: Database session
            
        Returns:
            Dictionary with similarity status for each section and metric
        """
        from app.models.health_record import HealthRecordSection
        
        result = {
            "sections": [],
            "metrics": []
        }
        
        # Check sections
        for section_data in sections:
            section_name = section_data.get("name") or section_data.get("type_of_analysis", "")
            if not section_name:
                continue
                
            # First check exact match
            normalized_name = section_name.lower().replace(" ", "_")
            exact_match = db.query(HealthRecordSection).filter(
                and_(
                    HealthRecordSection.name == normalized_name,
                    HealthRecordSection.health_record_type_id == health_record_type_id,
                    HealthRecordSection.created_by == user_id
                )
            ).first()
            
            if exact_match:
                result["sections"].append({
                    "name": section_name,
                    "status": "exist",
                    "similarity_score": 1.0,
                    "existing_section_id": exact_match.id,
                    "existing_display_name": exact_match.display_name
                })
            else:
                # Check for similar sections
                similar = self.find_similar_sections(
                    user_id, section_name, health_record_type_id, db
                )
                
                if similar and similar[0]["similarity_score"] >= 0.90:
                    # Very similar - treat as existing
                    result["sections"].append({
                        "name": section_name,
                        "status": "exist",
                        "similarity_score": similar[0]["similarity_score"],
                        "existing_section_id": similar[0]["id"],
                        "existing_display_name": similar[0]["display_name"]
                    })
                elif similar and similar[0]["similarity_score"] >= self.section_similarity_threshold:
                    # Similar - suggest existing
                    result["sections"].append({
                        "name": section_name,
                        "status": "similar",
                        "similarity_score": similar[0]["similarity_score"],
                        "existing_section_id": similar[0]["id"],
                        "existing_display_name": similar[0]["display_name"]
                    })
                else:
                    # New section
                    result["sections"].append({
                        "name": section_name,
                        "status": "new",
                        "similarity_score": None,
                        "existing_section_id": None,
                        "existing_display_name": None
                    })
        
        # Check metrics - need to find section first
        section_cache = {}  # Cache section lookups
        
        for metric_data in metrics:
            metric_name = metric_data.get("metric_name", "")
            section_name = metric_data.get("section_name") or metric_data.get("type_of_analysis", "")
            
            if not metric_name or not section_name:
                continue
            
            # Get or find section
            if section_name not in section_cache:
                normalized_section_name = section_name.lower().replace(" ", "_")
                section = db.query(HealthRecordSection).filter(
                    and_(
                        HealthRecordSection.name == normalized_section_name,
                        HealthRecordSection.health_record_type_id == health_record_type_id,
                        HealthRecordSection.created_by == user_id
                    )
                ).first()
                
                # If not found, check similar sections
                if not section:
                    similar_sections = self.find_similar_sections(
                        user_id, section_name, health_record_type_id, db, threshold=0.90
                    )
                    if similar_sections:
                        section = db.query(HealthRecordSection).filter(
                            HealthRecordSection.id == similar_sections[0]["id"]
                        ).first()
                
                section_cache[section_name] = section
            
            section = section_cache[section_name]
            
            if not section:
                # Section doesn't exist yet, metric will be new
                result["metrics"].append({
                    "metric_name": metric_name,
                    "section_name": section_name,
                    "status": "new",
                    "similarity_score": None,
                    "existing_metric_id": None,
                    "existing_display_name": None
                })
                continue
            
            # Check exact match
            normalized_metric_name = metric_name.lower().replace(" ", "_")
            from app.models.health_record import HealthRecordMetric
            exact_match = db.query(HealthRecordMetric).filter(
                and_(
                    HealthRecordMetric.section_id == section.id,
                    HealthRecordMetric.name == normalized_metric_name
                )
            ).first()
            
            if exact_match:
                result["metrics"].append({
                    "metric_name": metric_name,
                    "section_name": section_name,
                    "status": "exist",
                    "similarity_score": 1.0,
                    "existing_metric_id": exact_match.id,
                    "existing_display_name": exact_match.display_name
                })
            else:
                # Check for similar metrics
                similar = self.find_similar_metrics(section.id, metric_name, db)
                
                if similar and similar[0]["similarity_score"] >= 0.90:
                    # Very similar - treat as existing
                    result["metrics"].append({
                        "metric_name": metric_name,
                        "section_name": section_name,
                        "status": "exist",
                        "similarity_score": similar[0]["similarity_score"],
                        "existing_metric_id": similar[0]["id"],
                        "existing_display_name": similar[0]["display_name"]
                    })
                elif similar and similar[0]["similarity_score"] >= self.metric_similarity_threshold:
                    # Similar - suggest existing
                    result["metrics"].append({
                        "metric_name": metric_name,
                        "section_name": section_name,
                        "status": "similar",
                        "similarity_score": similar[0]["similarity_score"],
                        "existing_metric_id": similar[0]["id"],
                        "existing_display_name": similar[0]["display_name"]
                    })
                else:
                    # New metric
                    result["metrics"].append({
                        "metric_name": metric_name,
                        "section_name": section_name,
                        "status": "new",
                        "similarity_score": None,
                        "existing_metric_id": None,
                        "existing_display_name": None
                    })
        
        return result
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1_array = np.array(vec1)
            vec2_array = np.array(vec2)
            
            dot_product = np.dot(vec1_array, vec2_array)
            norm1 = np.linalg.norm(vec1_array)
            norm2 = np.linalg.norm(vec2_array)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    async def calculate_similarity_openai_batch(
        self,
        parsed_names: List[str],
        existing_metrics_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Calculate similarity between parsed and existing metric names using OpenAI embeddings.
        
        Args:
            parsed_names: List of metric names from document analysis
            existing_metrics_data: List of dicts with keys: 'name', 'display_name', 'id', etc.
        
        Returns:
            List of dicts with similarity results for each parsed name
        """
        if not parsed_names or not existing_metrics_data:
            return []
        
        # Fallback to difflib if OpenAI not available
        if not self.openai_client:
            logger.warning("OpenAI not available, using difflib fallback for similarity")
            return self._calculate_similarity_fallback(parsed_names, existing_metrics_data)
        
        try:
            # Extract existing names
            existing_names = [metric.get('display_name') or metric.get('name', '') for metric in existing_metrics_data]
            existing_names = [name for name in existing_names if name]  # Filter empty names
            
            if not existing_names:
                # No existing metrics, return all as new
                return [
                    {
                        "parsed_name": name,
                        "best_match": None,
                        "suggested_name": name,
                        "can_toggle": False
                    }
                    for name in parsed_names
                ]
            
            # Combine all names for batch embedding
            all_names = parsed_names + existing_names
            
            logger.info(f"Calculating OpenAI embeddings for {len(all_names)} metric names")
            
            # Get embeddings in batch
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=all_names
            )
            
            # Extract embeddings
            embeddings = [item.embedding for item in response.data]
            parsed_embeddings = embeddings[:len(parsed_names)]
            existing_embeddings = embeddings[len(parsed_names):]
            
            # Calculate similarities
            results = []
            for i, parsed_name in enumerate(parsed_names):
                best_match = None
                best_similarity = 0.0
                
                for j, existing_metric in enumerate(existing_metrics_data):
                    similarity = self._cosine_similarity(
                        parsed_embeddings[i],
                        existing_embeddings[j]
                    )
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = {
                            "existing_name": existing_metric.get('name', ''),
                            "display_name": existing_metric.get('display_name') or existing_metric.get('name', ''),
                            "metric_id": existing_metric.get('id'),
                            "similarity_score": similarity
                        }
                
                # Determine suggested name and toggle availability
                if best_match and best_match["similarity_score"] >= self.openai_similarity_threshold:
                    # Similarity >= 95%: suggest existing name
                    suggested_name = best_match["display_name"]
                    can_toggle = True
                else:
                    # Similarity < 95%: suggest parsed name
                    suggested_name = parsed_name
                    can_toggle = best_match is not None  # Can toggle if there's a match
                
                results.append({
                    "parsed_name": parsed_name,
                    "best_match": best_match if best_match and best_match["similarity_score"] >= 0.80 else None,
                    "suggested_name": suggested_name,
                    "can_toggle": can_toggle
                })
            
            logger.info(f"OpenAI similarity calculation completed for {len(results)} metrics")
            return results
            
        except Exception as e:
            logger.error(f"Error in OpenAI similarity calculation: {e}", exc_info=True)
            # Fallback to difflib
            logger.info("Falling back to difflib similarity calculation")
            return self._calculate_similarity_fallback(parsed_names, existing_metrics_data)
    
    def _calculate_similarity_fallback(
        self,
        parsed_names: List[str],
        existing_metrics_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Fallback similarity calculation using difflib"""
        results = []
        
        for parsed_name in parsed_names:
            best_match = None
            best_similarity = 0.0
            
            for existing_metric in existing_metrics_data:
                existing_name = existing_metric.get('display_name') or existing_metric.get('name', '')
                if not existing_name:
                    continue
                
                similarity = self._calculate_similarity(parsed_name, existing_name)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = {
                        "existing_name": existing_metric.get('name', ''),
                        "display_name": existing_name,
                        "metric_id": existing_metric.get('id'),
                        "similarity_score": similarity
                    }
            
            # Determine suggested name
            if best_match and best_match["similarity_score"] >= self.openai_similarity_threshold:
                suggested_name = best_match["display_name"]
                can_toggle = True
            else:
                suggested_name = parsed_name
                can_toggle = best_match is not None and best_match["similarity_score"] >= 0.80
            
            results.append({
                "parsed_name": parsed_name,
                "best_match": best_match if best_match and best_match["similarity_score"] >= 0.80 else None,
                "suggested_name": suggested_name,
                "can_toggle": can_toggle
            })
        
        return results

# Global instance
metric_similarity_service = MetricSimilarityService() 