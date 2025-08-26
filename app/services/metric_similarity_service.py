from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
import re
from sqlalchemy.orm import Session
from app.models.health_record import MetricCategories, MetricSubCategories
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class MetricSimilarityService:
    """
    AI-powered service to detect similar metrics and prevent duplication.
    Uses multiple similarity algorithms for comprehensive detection.
    """
    
    def __init__(self):
        self.similarity_threshold = 0.75  # 75% similarity threshold
        self.exact_match_threshold = 0.95  # 95% for near-exact matches
        self.min_word_length = 3  # Minimum word length to consider
        
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
        try:
            # Get existing categories for this health record type
            query = db.query(MetricCategories).filter(
                MetricCategories.health_record_type_id == health_record_type_id,
                MetricCategories.is_active == True
            )
            
            if exclude_user_id:
                query = query.filter(MetricCategories.created_by != exclude_user_id)
            
            existing_categories = query.all()
            
            similar_categories = []
            
            for category in existing_categories:
                similarity_score = self._calculate_similarity(new_name, category.name)
                
                if similarity_score >= self.similarity_threshold:
                    similar_categories.append({
                        "id": category.id,
                        "name": category.name,
                        "display_name": category.display_name,
                        "similarity_score": round(similarity_score, 3),
                        "is_default": category.is_default,
                        "created_by": category.created_by,
                        "match_type": self._get_match_type(similarity_score)
                    })
            
            # Sort by similarity score (highest first)
            similar_categories.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            return similar_categories
            
        except Exception as e:
            logger.error(f"Error checking similar categories: {str(e)}")
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
        try:
            # Get existing sub-categories for this category
            query = db.query(MetricSubCategories).filter(
                MetricSubCategories.category_id == category_id,
                MetricSubCategories.is_active == True
            )
            
            if exclude_user_id:
                query = query.filter(MetricSubCategories.created_by != exclude_user_id)
            
            existing_sub_categories = query.all()
            
            similar_sub_categories = []
            
            for sub_category in existing_sub_categories:
                similarity_score = self._calculate_similarity(new_name, sub_category.name)
                
                if similarity_score >= self.similarity_threshold:
                    similar_sub_categories.append({
                        "id": sub_category.id,
                        "name": sub_category.name,
                        "display_name": sub_category.display_name,
                        "similarity_score": round(similarity_score, 3),
                        "is_default": sub_category.is_default,
                        "created_by": sub_category.created_by,
                        "match_type": self._get_match_type(similarity_score)
                    })
            
            # Sort by similarity score (highest first)
            similar_sub_categories.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            return similar_sub_categories
            
        except Exception as e:
            logger.error(f"Error checking similar sub-categories: {str(e)}")
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
        try:
            # Check categories
            similar_categories = []
            categories_query = db.query(MetricCategories).filter(
                MetricCategories.is_active == True
            )
            
            if exclude_user_id:
                categories_query = categories_query.filter(
                    MetricCategories.created_by != exclude_user_id
                )
            
            for category in categories_query.all():
                similarity_score = self._calculate_similarity(new_name, category.name)
                
                if similarity_score >= self.similarity_threshold:
                    similar_categories.append({
                        "id": category.id,
                        "name": category.name,
                        "display_name": category.display_name,
                        "health_record_type_id": category.health_record_type_id,
                        "similarity_score": round(similarity_score, 3),
                        "is_default": category.is_default,
                        "created_by": category.created_by,
                        "match_type": self._get_match_type(similarity_score)
                    })
            
            # Check sub-categories
            similar_sub_categories = []
            sub_categories_query = db.query(MetricSubCategories).filter(
                MetricSubCategories.is_active == True
            )
            
            if exclude_user_id:
                sub_categories_query = sub_categories_query.filter(
                    MetricSubCategories.created_by != exclude_user_id
                )
            
            for sub_category in sub_categories_query.all():
                similarity_score = self._calculate_similarity(new_name, sub_category.name)
                
                if similarity_score >= self.similarity_threshold:
                    similar_sub_categories.append({
                        "id": sub_category.id,
                        "name": sub_category.name,
                        "display_name": sub_category.display_name,
                        "category_id": sub_category.category_id,
                        "similarity_score": round(similarity_score, 3),
                        "is_default": sub_category.is_default,
                        "created_by": sub_category.created_by,
                        "match_type": self._get_match_type(similarity_score)
                    })
            
            # Sort by similarity score
            similar_categories.sort(key=lambda x: x["similarity_score"], reverse=True)
            similar_sub_categories.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            return {
                "similar_categories": similar_categories,
                "similar_sub_categories": similar_sub_categories
            }
            
        except Exception as e:
            logger.error(f"Error checking global similarity: {str(e)}")
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
        Normalize metric name for comparison.
        
        Args:
            name: Original metric name
            
        Returns:
            Normalized name
        """
        # Convert to lowercase
        normalized = name.lower()
        
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
            'ua': 'urinalysis'
        }
        
        # Replace abbreviations
        for abbrev, full in abbreviations.items():
            normalized = re.sub(r'\b' + abbrev + r'\b', full, normalized)
        
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

# Global instance
metric_similarity_service = MetricSimilarityService() 