"""
Daily.co Video Service
Handles integration with Daily.co API for video room management
"""
import requests
from typing import Dict, Optional
import time
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
        appointment_id: Optional[int] = None,
        acuity_appointment_id: Optional[str] = None,
        patient_name: str = "",
        professional_name: str = "",
        scheduled_time: Optional[datetime] = None,
        duration_minutes: int = 30
    ) -> Optional[Dict]:
        """
        Create Daily.co video room for appointment
        
        Args:
            appointment_id: Local appointment ID (optional)
            acuity_appointment_id: Acuity appointment ID (preferred for uniqueness)
            patient_name: Patient's name
            professional_name: Professional's name
            scheduled_time: Appointment scheduled time
            duration_minutes: Appointment duration in minutes
        
        Returns:
            Room data dictionary with room URL and name, or None
        """
        # Use Acuity appointment ID if available, otherwise use local ID, otherwise generate unique name
        if acuity_appointment_id:
            room_name = f"appointment-{acuity_appointment_id}"
        elif appointment_id and appointment_id > 0:
            room_name = f"appointment-{appointment_id}"
        else:
            # Generate unique room name using timestamp
            import time
            room_name = f"appointment-{int(time.time() * 1000)}"
        
        # Check if room already exists
        existing_room = self.get_room_info(room_name)
        if existing_room:
            logger.info(f"Room {room_name} already exists, reusing it")
            return {
                "room_url": existing_room.get("url"),
                "room_name": existing_room.get("name"),
                "id": existing_room.get("id")
            }
        
        # Calculate room expiry (1 hour after appointment ends)
        if scheduled_time:
            expiry_time = scheduled_time + timedelta(minutes=duration_minutes + 60)
            expiry_timestamp = int(expiry_time.timestamp())
            nbf_timestamp = int(scheduled_time.timestamp())
        else:
            expiry_timestamp = int((datetime.utcnow() + timedelta(days=1)).timestamp())
            nbf_timestamp = int(datetime.utcnow().timestamp())
        
        room_config = {
            "name": room_name,
            "privacy": "private",
            "properties": {
                "exp": expiry_timestamp,
                "nbf": nbf_timestamp,
                "enable_knocking": True,
                "enable_screenshare": True,
                "enable_chat": True,
                "start_video_off": False,
                "start_audio_off": False,
                "max_participants": 10,
            },
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
            Room data dictionary or None if room doesn't exist
        """
        if not self.api_key:
            logger.error("Daily.co API key not configured")
            return None
        
        url = f"{self.base_url}/rooms/{room_name}"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 404:
                # Room doesn't exist - this is expected, not an error
                logger.debug(f"Room {room_name} does not exist in Daily.co")
                return None
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            # Only log as error if it's not a 404
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
                logger.debug(f"Room {room_name} does not exist in Daily.co")
                return None
            logger.error(f"Daily.co API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            return None
    
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

