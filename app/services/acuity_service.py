"""
Acuity Scheduling Service
Handles integration with Acuity Scheduling API for appointment management
"""
import requests
from typing import Dict, Optional, List
from datetime import datetime
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class AcuityService:
    """Service for interacting with Acuity Scheduling API"""
    
    def __init__(self):
        self.base_url = "https://acuityscheduling.com/api/v1"
        self.user_id = settings.ACUITY_USER_ID
        self.api_key = settings.ACUITY_API_KEY
        self.auth = (self.user_id, self.api_key) if self.user_id and self.api_key else None
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make HTTP request to Acuity API"""
        if not self.auth:
            logger.error("Acuity API credentials not configured")
            return None
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                auth=self.auth,
                json=data,
                params=params,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Acuity API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            return None
    
    def generate_embed_url(
        self, 
        owner_id: str, 
        calendar_id: Optional[str] = None,
        ref: str = "embedded_csp"
    ) -> str:
        """
        Generate Acuity embed URL for iframe
        
        Args:
            owner_id: Acuity user ID (owner)
            calendar_id: Optional calendar ID to filter to specific calendar
            ref: Reference parameter (default: embedded_csp)
        
        Returns:
            Embed URL string
        """
        base_url = "https://app.acuityscheduling.com/schedule.php"
        params = [f"owner={owner_id}", f"ref={ref}"]
        
        if calendar_id:
            params.append(f"calendarID={calendar_id}")
        
        return f"{base_url}?{'&'.join(params)}"
    
    def get_appointment(self, appointment_id: str) -> Optional[Dict]:
        """
        Get appointment details from Acuity
        
        Args:
            appointment_id: Acuity appointment ID
        
        Returns:
            Appointment data dictionary or None
        """
        return self._make_request("GET", f"appointments/{appointment_id}")
    
    def update_appointment(
        self, 
        appointment_id: str, 
        updates: Dict
    ) -> Optional[Dict]:
        """
        Update/reschedule appointment in Acuity
        
        Args:
            appointment_id: Acuity appointment ID
            updates: Dictionary with fields to update
        
        Returns:
            Updated appointment data or None
        """
        return self._make_request("PUT", f"appointments/{appointment_id}", data=updates)
    
    def cancel_appointment(self, appointment_id: str) -> bool:
        """
        Cancel appointment in Acuity
        
        Args:
            appointment_id: Acuity appointment ID
        
        Returns:
            True if successful, False otherwise
        """
        result = self._make_request("DELETE", f"appointments/{appointment_id}")
        return result is not None
    
    def get_available_times(
        self,
        calendar_id: str,
        appointment_type_id: Optional[int] = None,
        date: Optional[str] = None,
        month: Optional[str] = None
    ) -> Optional[List[Dict]]:
        """
        Get available time slots from Acuity
        
        Args:
            calendar_id: Calendar ID
            appointment_type_id: Optional appointment type ID
            date: Specific date (YYYY-MM-DD format)
            month: Month to query (YYYY-MM format)
        
        Returns:
            List of available time slots or None
        """
        params = {"calendarID": calendar_id}
        if appointment_type_id:
            params["appointmentTypeID"] = appointment_type_id
        if date:
            params["date"] = date
        if month:
            params["month"] = month
        
        return self._make_request("GET", "available-times", params=params)


acuity_service = AcuityService()

