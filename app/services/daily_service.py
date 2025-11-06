"""
Daily.co Video Service
Handles integration with Daily.co API for video room management
"""
import requests
from typing import Dict, Optional
from datetime import datetime, timedelta
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class DailyService:
    """Service for interacting with Daily.co API"""
    
    def __init__(self):
        self.api_key = settings.DAILY_API_KEY
        self.base_url = settings.DAILY_API_URL.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make HTTP request to Daily.co API"""
        if not self.api_key:
            logger.error("Daily.co API key not configured")
            return None
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Daily.co API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            return None
    
    def create_room(
        self,
        appointment_id: int,
        patient_name: str,
        professional_name: str,
        scheduled_time: datetime,
        duration_minutes: int = 30
    ) -> Optional[Dict]:
        """
        Create Daily.co video room for appointment
        
        Args:
            appointment_id: Local appointment ID
            patient_name: Patient's name
            professional_name: Professional's name
            scheduled_time: Appointment scheduled time
            duration_minutes: Appointment duration in minutes
        
        Returns:
            Room data dictionary with room URL and name, or None
        """
        # Calculate room expiry (1 hour after appointment ends)
        expiry_time = scheduled_time + timedelta(minutes=duration_minutes + 60)
        expiry_timestamp = int(expiry_time.timestamp())
        
        room_name = f"appointment-{appointment_id}"
        
        room_config = {
            "name": room_name,
            "privacy": "private",
            "properties": {
                "exp": expiry_timestamp,
                "enable_knocking": True,
                "enable_screenshare": True,
                "enable_chat": True,
                "start_video_off": False,
                "start_audio_off": False,
            },
            "config": {
                "max_participants": 10,
                "nbf": int(scheduled_time.timestamp()),
                "exp": expiry_timestamp
            }
        }
        
        result = self._make_request("POST", "rooms", data=room_config)
        
        if result:
            return {
                "room_url": result.get("url"),
                "room_name": result.get("name"),
                "id": result.get("id")
            }
        return None
    
    def get_room_info(self, room_name: str) -> Optional[Dict]:
        """
        Get Daily.co room information
        
        Args:
            room_name: Room name or ID
        
        Returns:
            Room data dictionary or None
        """
        return self._make_request("GET", f"rooms/{room_name}")
    
    def delete_room(self, room_name: str) -> bool:
        """
        Delete Daily.co room
        
        Args:
            room_name: Room name or ID
        
        Returns:
            True if successful, False otherwise
        """
        result = self._make_request("DELETE", f"rooms/{room_name}")
        return result is not None
    
    def create_meeting_token(
        self,
        room_name: str,
        user_id: str,
        is_owner: bool = False,
        user_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate meeting token for joining room
        
        Args:
            room_name: Room name or ID
            user_id: User ID (can be appointment ID or user ID)
            is_owner: Whether user is room owner
            user_name: Optional user name
        
        Returns:
            Token string or None
        """
        token_config = {
            "properties": {
                "room_name": room_name,
                "user_id": user_id,
                "is_owner": is_owner,
            }
        }
        
        if user_name:
            token_config["properties"]["user_name"] = user_name
        
        result = self._make_request("POST", "meeting-tokens", data=token_config)
        
        if result:
            return result.get("token")
        return None
    
    def get_room_token(
        self,
        room_name: str,
        user_id: str,
        is_owner: bool = False,
        user_name: Optional[str] = None
    ) -> Optional[str]:
        """Alias for create_meeting_token for consistency"""
        return self.create_meeting_token(room_name, user_id, is_owner, user_name)


daily_service = DailyService()

