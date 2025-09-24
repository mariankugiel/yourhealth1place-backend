from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timedelta
from app.models.health_record import (
    HealthRecord, HealthRecordSection, HealthRecordMetric, 
    VitalMetric, LifestyleMetric, BodyMetric
)
from app.models.health_record import (
    VitalStatus, LifestyleStatus, BodyStatus, MedicalConditionStatus
)
import logging
import json
from collections import defaultdict

logger = logging.getLogger(__name__)

class HealthRecordAnalyticsService:
    """Service for health record analytics and trend analysis"""
    
    def get_trend_analysis(
        self, 
        db: Session, 
        user_id: int, 
        metric_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get trend analysis for a specific health metric
        
        Args:
            db: Database session
            user_id: ID of the user
            metric_name: Name of the metric to analyze
            days: Number of days to analyze
            
        Returns:
            Dict containing trend analysis data
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get health records for the specified metric
            records = db.query(HealthRecord).filter(
                and_(
                    HealthRecord.created_by == user_id,
                    HealthRecord.recorded_at >= start_date,
                    HealthRecord.recorded_at <= end_date
                )
            ).order_by(HealthRecord.recorded_at).all()
            
            if not records:
                return {
                    "metric": metric_name,
                    "period_days": days,
                    "total_records": 0,
                    "trend": "insufficient_data",
                    "analysis": "No data available for analysis"
                }
            
            # Extract values and dates
            values = []
            dates = []
            statuses = []
            
            for record in records:
                if isinstance(record.value, dict) and metric_name in record.value:
                    values.append(record.value[metric_name])
                    dates.append(record.recorded_at)
                    statuses.append(record.status)
                elif isinstance(record.value, (int, float)):
                    values.append(record.value)
                    dates.append(record.recorded_at)
                    statuses.append(record.status)
            
            if not values:
                return {
                    "metric": metric_name,
                    "period_days": days,
                    "total_records": len(records),
                    "trend": "insufficient_data",
                    "analysis": "No valid values found for the specified metric"
                }
            
            # Calculate basic statistics
            numeric_values = [v for v in values if isinstance(v, (int, float))]
            if numeric_values:
                min_val = min(numeric_values)
                max_val = max(numeric_values)
                avg_val = sum(numeric_values) / len(numeric_values)
                
                # Calculate trend
                if len(numeric_values) >= 2:
                    first_half = numeric_values[:len(numeric_values)//2]
                    second_half = numeric_values[len(numeric_values)//2:]
                    first_avg = sum(first_half) / len(first_half)
                    second_avg = sum(second_half) / len(second_half)
                    
                    if second_avg > first_avg * 1.1:
                        trend = "increasing"
                    elif second_avg < first_avg * 0.9:
                        trend = "decreasing"
                    else:
                        trend = "stable"
                else:
                    trend = "insufficient_data"
            else:
                min_val = max_val = avg_val = None
                trend = "non_numeric"
            
            # Analyze status distribution
            status_counts = defaultdict(int)
            for status in statuses:
                status_counts[status] += 1
            
            # Calculate frequency
            total_days = (end_date - start_date).days
            frequency = len(records) / total_days if total_days > 0 else 0
            
            return {
                "metric": metric_name,
                "period_days": days,
                "total_records": len(records),
                "trend": trend,
                "statistics": {
                    "min_value": min_val,
                    "max_value": max_val,
                    "average_value": avg_val,
                    "frequency_per_day": round(frequency, 2)
                },
                "status_distribution": dict(status_counts),
                "data_points": [
                    {
                        "date": date.isoformat(),
                        "value": value,
                        "status": status
                    } for date, value, status in zip(dates, values, statuses)
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in trend analysis: {e}")
            return {"error": f"Failed to analyze trends: {str(e)}"}
    
    def get_correlation_analysis(
        self, 
        db: Session, 
        user_id: int, 
        metric1: str,
        metric2: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get correlation analysis between two health metrics
        
        Args:
            db: Database session
            user_id: ID of the user
            metric1: First metric name
            metric2: Second metric name
            days: Number of days to analyze
            
        Returns:
            Dict containing correlation analysis data
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get health records for both metrics
            records1 = db.query(HealthRecord).filter(
                and_(
                    HealthRecord.created_by == user_id,
                    HealthRecord.recorded_at >= start_date,
                    HealthRecord.recorded_at <= end_date
                )
            ).order_by(HealthRecord.recorded_at).all()
            
            records2 = db.query(HealthRecord).filter(
                and_(
                    HealthRecord.created_by == user_id,
                    HealthRecord.recorded_at >= start_date,
                    HealthRecord.recorded_at <= end_date
                )
            ).order_by(HealthRecord.recorded_at).all()
            
            if not records1 or not records2:
                return {
                    "metric1": metric1,
                    "metric2": metric2,
                    "period_days": days,
                    "correlation": "insufficient_data",
                    "analysis": "Insufficient data for correlation analysis"
                }
            
            # Create date-value mappings
            metric1_data = {}
            metric2_data = {}
            
            for record in records1:
                if isinstance(record.value, dict) and metric1 in record.value:
                    metric1_data[record.recorded_at.date()] = record.value[metric1]
                elif isinstance(record.value, (int, float)):
                    metric1_data[record.recorded_at.date()] = record.value
            
            for record in records2:
                if isinstance(record.value, dict) and metric2 in record.value:
                    metric2_data[record.recorded_at.date()] = record.value[metric2]
                elif isinstance(record.value, (int, float)):
                    metric2_data[record.recorded_at.date()] = record.value
            
            # Find common dates
            common_dates = set(metric1_data.keys()) & set(metric2_data.keys())
            
            if len(common_dates) < 3:
                return {
                    "metric1": metric1,
                    "metric2": metric2,
                    "period_days": days,
                    "correlation": "insufficient_data",
                    "analysis": "Insufficient overlapping data for correlation analysis"
                }
            
            # Calculate correlation
            values1 = [metric1_data[date] for date in sorted(common_dates)]
            values2 = [metric2_data[date] for date in sorted(common_dates)]
            
            # Simple correlation calculation (Pearson correlation coefficient)
            correlation = self._calculate_correlation(values1, values2)
            
            # Determine correlation strength
            if abs(correlation) >= 0.7:
                strength = "strong"
            elif abs(correlation) >= 0.3:
                strength = "moderate"
            else:
                strength = "weak"
            
            # Determine correlation direction
            if correlation > 0:
                direction = "positive"
            elif correlation < 0:
                direction = "negative"
            else:
                direction = "no"
            
            return {
                "metric1": metric1,
                "metric2": metric2,
                "period_days": days,
                "common_data_points": len(common_dates),
                "correlation_coefficient": round(correlation, 3),
                "correlation_strength": strength,
                "correlation_direction": direction,
                "analysis": f"There is a {strength} {direction} correlation between {metric1} and {metric2}",
                "data_points": [
                    {
                        "date": date.isoformat(),
                        "metric1_value": metric1_data[date],
                        "metric2_value": metric2_data[date]
                    } for date in sorted(common_dates)
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in correlation analysis: {e}")
            return {"error": f"Failed to analyze correlation: {str(e)}"}
    
    def _calculate_correlation(self, values1: List[float], values2: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        try:
            if len(values1) != len(values2) or len(values1) < 2:
                return 0.0
            
            # Convert to numeric values
            numeric_values1 = [float(v) for v in values1 if isinstance(v, (int, float))]
            numeric_values2 = [float(v) for v in values2 if isinstance(v, (int, float))]
            
            if len(numeric_values1) != len(numeric_values2) or len(numeric_values1) < 2:
                return 0.0
            
            n = len(numeric_values1)
            sum1 = sum(numeric_values1)
            sum2 = sum(numeric_values2)
            sum1_sq = sum(x * x for x in numeric_values1)
            sum2_sq = sum(x * x for x in numeric_values2)
            sum_xy = sum(x * y for x, y in zip(numeric_values1, numeric_values2))
            
            numerator = n * sum_xy - sum1 * sum2
            denominator = ((n * sum1_sq - sum1 * sum1) * (n * sum2_sq - sum2 * sum2)) ** 0.5
            
            if denominator == 0:
                return 0.0
            
            return numerator / denominator
            
        except Exception:
            return 0.0
    
    def get_health_score(
        self, 
        db: Session, 
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate overall health score based on various metrics
        
        Args:
            db: Database session
            user_id: ID of the user
            days: Number of days to analyze
            
        Returns:
            Dict containing health score and breakdown
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get recent health records
            records = db.query(HealthRecord).filter(
                and_(
                    HealthRecord.created_by == user_id,
                    HealthRecord.recorded_at >= start_date,
                    HealthRecord.recorded_at <= end_date
                )
            ).all()
            
            if not records:
                return {
                    "health_score": 0,
                    "period_days": days,
                    "analysis": "No health data available for scoring",
                    "breakdown": {}
                }
            
            # Calculate scores for different categories
            vital_score = self._calculate_vital_score(records)
            lifestyle_score = self._calculate_lifestyle_score(records)
            body_score = self._calculate_body_score(records)
            
            # Calculate overall score (weighted average)
            overall_score = (vital_score * 0.4 + lifestyle_score * 0.4 + body_score * 0.2)
            
            # Determine health status
            if overall_score >= 80:
                health_status = "Excellent"
            elif overall_score >= 70:
                health_status = "Good"
            elif overall_score >= 60:
                health_status = "Fair"
            else:
                health_status = "Needs Improvement"
            
            return {
                "health_score": round(overall_score, 1),
                "health_status": health_status,
                "period_days": days,
                "breakdown": {
                    "vital_signs": {
                        "score": round(vital_score, 1),
                        "weight": 0.4
                    },
                    "lifestyle": {
                        "score": round(lifestyle_score, 1),
                        "weight": 0.4
                    },
                    "body_composition": {
                        "score": round(body_score, 1),
                        "weight": 0.2
                    }
                },
                "recommendations": self._generate_health_recommendations(
                    vital_score, lifestyle_score, body_score
                )
            }
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return {"error": f"Failed to calculate health score: {str(e)}"}
    
    def _calculate_vital_score(self, records: List[HealthRecord]) -> float:
        """Calculate score for vital signs"""
        try:
            vital_records = [r for r in records if r.status in [
                VitalStatus.NORMAL, VitalStatus.ELEVATED, VitalStatus.HIGH, 
                VitalStatus.LOW, VitalStatus.CRITICAL
            ]]
            
            if not vital_records:
                return 0.0
            
            score = 0
            total = 0
            
            for record in vital_records:
                if record.status == VitalStatus.NORMAL:
                    score += 100
                elif record.status == VitalStatus.ELEVATED:
                    score += 80
                elif record.status == VitalStatus.HIGH:
                    score += 60
                elif record.status == VitalStatus.LOW:
                    score += 60
                elif record.status == VitalStatus.CRITICAL:
                    score += 20
                total += 1
            
            return score / total if total > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_lifestyle_score(self, records: List[HealthRecord]) -> float:
        """Calculate score for lifestyle metrics"""
        try:
            lifestyle_records = [r for r in records if r.status in [
                LifestyleStatus.EXCELLENT, LifestyleStatus.GOOD, 
                LifestyleStatus.FAIR, LifestyleStatus.POOR, 
                LifestyleStatus.NEEDS_IMPROVEMENT
            ]]
            
            if not lifestyle_records:
                return 0.0
            
            score = 0
            total = 0
            
            for record in lifestyle_records:
                if record.status == LifestyleStatus.EXCELLENT:
                    score += 100
                elif record.status == LifestyleStatus.GOOD:
                    score += 80
                elif record.status == LifestyleStatus.FAIR:
                    score += 60
                elif record.status == LifestyleStatus.POOR:
                    score += 40
                elif record.status == LifestyleStatus.NEEDS_IMPROVEMENT:
                    score += 30
                total += 1
            
            return score / total if total > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_body_score(self, records: List[HealthRecord]) -> float:
        """Calculate score for body composition metrics"""
        try:
            body_records = [r for r in records if r.status in [
                BodyStatus.HEALTHY, BodyStatus.OVERWEIGHT, 
                BodyStatus.UNDERWEIGHT, BodyStatus.OBESE, 
                BodyStatus.ATHLETIC
            ]]
            
            if not body_records:
                return 0.0
            
            score = 0
            total = 0
            
            for record in body_records:
                if record.status == BodyStatus.ATHLETIC:
                    score += 100
                elif record.status == BodyStatus.HEALTHY:
                    score += 90
                elif record.status == BodyStatus.OVERWEIGHT:
                    score += 60
                elif record.status == BodyStatus.UNDERWEIGHT:
                    score += 70
                elif record.status == BodyStatus.OBESE:
                    score += 40
                total += 1
            
            return score / total if total > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def _generate_health_recommendations(
        self, 
        vital_score: float, 
        lifestyle_score: float, 
        body_score: float
    ) -> List[str]:
        """Generate health recommendations based on scores"""
        recommendations = []
        
        if vital_score < 70:
            recommendations.append("Monitor vital signs more frequently and consult healthcare provider if abnormal values persist")
        
        if lifestyle_score < 70:
            recommendations.append("Focus on improving lifestyle habits: exercise regularly, maintain healthy sleep patterns, and manage stress")
        
        if body_score < 70:
            recommendations.append("Consider consulting a nutritionist or fitness professional to improve body composition")
        
        if vital_score >= 80 and lifestyle_score >= 80 and body_score >= 80:
            recommendations.append("Maintain current healthy lifestyle and continue regular health monitoring")
        
        return recommendations

# Create service instance
health_record_analytics_service = HealthRecordAnalyticsService()
