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
        self._appointment_types_cache: Optional[List[Dict]] = None
        self._appointment_types_cache_timestamp: Optional[datetime] = None
        self._calendar_cache: Dict[str, Dict] = {}
        self._calendars_cache: Optional[List[Dict]] = None
        self._calendars_cache_timestamp: Optional[datetime] = None
    
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
        Update appointment details in Acuity (general update endpoint).

        Args:
            appointment_id: Acuity appointment ID
            updates: Dictionary with fields to update

        Returns:
            Updated appointment data or None
        """
        return self._make_request("PUT", f"appointments/{appointment_id}", data=updates)

    def reschedule_appointment(
        self,
        appointment_id: str,
        updates: Dict
    ) -> Optional[Dict]:
        """
        Reschedule an appointment in Acuity.

        Args:
            appointment_id: Acuity appointment ID
            updates: Dictionary with reschedule fields (e.g., datetime, calendarID)

        Returns:
            Updated appointment data or None
        """
        return self._make_request("PUT", f"appointments/{appointment_id}/reschedule", data=updates)
    
    def cancel_appointment(self, appointment_id: str) -> bool:
        """
        Cancel appointment in Acuity
        
        Args:
            appointment_id: Acuity appointment ID
        
        Returns:
            True if successful, False otherwise
        """
        result = self._make_request("PUT", f"appointments/{appointment_id}/cancel")
        return result is not None
    
    def get_available_times(
        self,
        calendar_id: str,
        appointment_type_id: Optional[int] = None,
        date: Optional[str] = None,
        month: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Optional[List[Dict]]:
        """
        Get available time slots from Acuity
        
        Args:
            calendar_id: Calendar ID
            appointment_type_id: Optional appointment type ID (default: 0)
            date: Specific date (YYYY-MM-DD format)
            month: Month to query (YYYY-MM format)
        
        Returns:
            List of available time slots or None
        """
        params = {"calendarID": calendar_id}
        # Determine appointment type (required by Acuity)
        if not appointment_type_id:
            default_type_id = self.get_default_appointment_type_id()
            if default_type_id:
                appointment_type_id = default_type_id
        if appointment_type_id:
            params["appointmentTypeID"] = appointment_type_id
        if date:
            params["date"] = date
        if month:
            params["month"] = month
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        if not self.auth:
            logger.error("Acuity API credentials not configured")
            return None

        url = f"{self.base_url}/availability/times"
        try:
            response = requests.get(url, auth=self.auth, params=params, headers={"Content-Type": "application/json"})
            if response.status_code == 404:
                logger.info(
                    "Acuity returned 404 for availability/times (calendar=%s, date=%s) — returning empty list",
                    calendar_id,
                    date
                )
                return []

            response.raise_for_status()

            if not response.content:
                return []

            data = response.json()
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                times = data.get("times") or data.get("items")
                if isinstance(times, list):
                    return times
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Acuity availability/times request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            return None
    
    def get_availability_dates(
        self,
        calendar_id: str,
        appointment_type_id: int = 0,
        month: Optional[str] = None
    ) -> Optional[List[str]]:
        """
        Get available dates from Acuity
        
        Args:
            calendar_id: Calendar ID
            appointment_type_id: Appointment type ID (default: 0)
            month: Month to query (YYYY-MM format), optional
        
        Returns:
            List of available dates (YYYY-MM-DD format) or None
        """
        params = {
            "calendarID": calendar_id,
        }
        if not appointment_type_id:
            default_type_id = self.get_default_appointment_type_id()
            if default_type_id:
                appointment_type_id = default_type_id
        if appointment_type_id:
            params["appointmentTypeID"] = appointment_type_id
        if month:
            params["month"] = month
        
        if not self.auth:
            logger.error("Acuity API credentials not configured")
            return None

        url = f"{self.base_url}/availability/dates"
        try:
            response = requests.get(url, auth=self.auth, params=params, headers={"Content-Type": "application/json"})
            if response.status_code == 404:
                logger.info(
                    "Acuity returned 404 for availability/dates (calendar=%s, month=%s) — returning empty list",
                    calendar_id,
                    month
                )
                return []

            response.raise_for_status()

            if not response.content:
                return []

            data = response.json()
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                dates = data.get("dates") or data.get("items")
                if isinstance(dates, list):
                    return dates
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Acuity availability/dates request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            return None

    def get_appointment_types(self) -> Optional[List[Dict]]:
        """Fetch appointment types configured in Acuity"""
        if not self.auth:
            logger.error("Acuity API credentials not configured")
            return None

        try:
            response = requests.get(
                f"{self.base_url}/appointment-types",
                auth=self.auth,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                types = data.get("appointmentTypes") or data.get("items")
                if isinstance(types, list):
                    return types
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Acuity appointment types request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            return None

    def get_default_appointment_type_id(self) -> Optional[int]:
        """Return the first appointment type ID configured in Acuity"""
        # Basic caching for 10 minutes to avoid repeated API calls
        if self._appointment_types_cache and self._appointment_types_cache_timestamp:
            if (datetime.utcnow() - self._appointment_types_cache_timestamp).total_seconds() < 600:
                types_cache = self._appointment_types_cache
            else:
                types_cache = None
        else:
            types_cache = None

        if not types_cache:
            types_cache = self.get_appointment_types()
            if types_cache:
                self._appointment_types_cache = types_cache
                self._appointment_types_cache_timestamp = datetime.utcnow()

        if not types_cache:
            return None

        first_type = types_cache[0]
        type_id = first_type.get("id") or first_type.get("appointmentTypeID")
        if type_id is None:
            return None
        try:
            return int(type_id)
        except (TypeError, ValueError):
            return None

    def get_calendar_details(self, calendar_id: str) -> Optional[Dict]:
        """Retrieve Acuity calendar details (e.g., timezone). Uses simple cache to reduce API calls."""
        if not calendar_id:
            return None

        cache_entry = self._calendar_cache.get(calendar_id)
        if cache_entry:
            cached_at = cache_entry.get("cached_at")
            if cached_at and (datetime.utcnow() - cached_at).total_seconds() < 600:
                return cache_entry.get("data")

        try:
            calendar = self._make_request("GET", f"calendars/{calendar_id}")
            if calendar:
                self._calendar_cache[calendar_id] = {
                    "data": calendar,
                    "cached_at": datetime.utcnow()
                }
            return calendar
        except Exception as e:
            logger.error(f"Failed to fetch calendar {calendar_id} details: {e}")
            return None

    def list_calendars(self, force_refresh: bool = False) -> Optional[List[Dict]]:
        """Retrieve all calendars from Acuity (cached for 10 minutes)"""
        if (
            not force_refresh
            and self._calendars_cache
            and self._calendars_cache_timestamp
            and (datetime.utcnow() - self._calendars_cache_timestamp).total_seconds() < 600
        ):
            return self._calendars_cache

        calendars = self._make_request("GET", "calendars")
        if isinstance(calendars, list):
            self._calendars_cache = calendars
            self._calendars_cache_timestamp = datetime.utcnow()
            return calendars

        if calendars is None:
            logger.warning("Failed to retrieve calendars from Acuity")
        else:
            logger.warning(f"Unexpected response when fetching calendars: {calendars}")
        return None
    
    def get_appointments(
        self,
        email: Optional[str] = None,
        calendar_id: Optional[str] = None,
        min_date: Optional[str] = None,
        max_date: Optional[str] = None
    ) -> Optional[List[Dict]]:
        """
        Get appointments from Acuity
        
        Args:
            email: Filter by client email
            calendar_id: Filter by calendar ID
            min_date: Minimum date (YYYY-MM-DD format)
            max_date: Maximum date (YYYY-MM-DD format)
        
        Returns:
            List of appointments or None
        """
        params = {"showDeleted": "true", "showCanceled": "true", "includeCanceled": "true"}
        if email:
            params["email"] = email
        if calendar_id:
            params["calendarID"] = calendar_id
        if min_date:
            params["minDate"] = min_date
        if max_date:
            params["maxDate"] = max_date
        
        return self._make_request("GET", "appointments", params=params)
    
    def create_appointment(
        self,
        calendar_id: str,
        appointment_type_id: Optional[int],
        datetime: str,
        firstName: str,
        lastName: str,
        email: str,
        phone: Optional[str] = None,
        notes: Optional[str] = None,
        fields: Optional[List[Dict]] = None
    ) -> Optional[Dict]:
        """
        Create appointment in Acuity
        
        Args:
            calendar_id: Calendar ID
            appointment_type_id: Appointment type ID (default: 0)
            datetime: Appointment datetime (ISO format with timezone)
            firstName: Client first name
            lastName: Client last name
            email: Client email
            phone: Client phone number (optional)
            notes: Appointment notes (optional)
            fields: Custom fields array [{"id": int, "value": str}] (optional)
        
        Returns:
            Created appointment data or None
        """
        # Determine appointment type ID if not provided
        if not appointment_type_id:
            appointment_type_id = self.get_default_appointment_type_id()

        data = {
            "calendarID": calendar_id,
            "datetime": datetime,
            "firstName": firstName,
            "lastName": lastName,
            "email": email
        }

        if appointment_type_id:
            data["appointmentTypeID"] = appointment_type_id
        
        if phone:
            data["phone"] = phone
        if notes:
            data["notes"] = notes
        if fields:
            data["fields"] = fields
        
        return self._make_request("POST", "appointments", data=data)


acuity_service = AcuityService()

