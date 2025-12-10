import zstandard as zstd
import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.services.thryve_data_type_service import ThryveDataTypeService

logger = logging.getLogger(__name__)


class ThryveWebhookService:
    """Service for processing Thryve webhook payloads"""
    
    def __init__(self, db: Session):
        self.db = db
        self.data_type_service = ThryveDataTypeService()
    
    def decompress_payload(self, compressed_body: bytes) -> bytes:
        """
        Decompress Zstandard compressed binary payload
        """
        try:
            dctx = zstd.ZstdDecompressor()
            decompressed = dctx.decompress(compressed_body)
            return decompressed
        except Exception as e:
            logger.error(f"Failed to decompress payload: {e}")
            raise
    
    def parse_payload(self, payload: bytes) -> Dict[str, Any]:
        """
        Parse JSON payload from decompressed bytes
        """
        try:
            payload_str = payload.decode('utf-8')
            return json.loads(payload_str)
        except Exception as e:
            logger.error(f"Failed to parse payload: {e}")
            raise
    
    def map_data_type_ids(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map all dataTypeId values to names in the payload
        """
        event_type = payload.get("type", "")
        mapped_payload = payload.copy()
        
        # Process epoch data
        if "epochData" in str(payload):
            for data_item in payload.get("data", []):
                if "epochData" in data_item:
                    for epoch_entry in data_item["epochData"]:
                        data_type_id = epoch_entry.get("dataTypeId")
                        if data_type_id:
                            data_type_name = self.data_type_service.map_data_type_id(
                                self.db, data_type_id, event_type
                            )
                            if data_type_name:
                                epoch_entry["dataTypeName"] = data_type_name
                            else:
                                logger.warning(f"Data type ID {data_type_id} not found for event type {event_type}")
        
        # Process daily data
        if "dailyData" in str(payload):
            for data_item in payload.get("data", []):
                if "dailyData" in data_item:
                    for daily_entry in data_item["dailyData"]:
                        data_type_id = daily_entry.get("dataTypeId")
                        if data_type_id:
                            data_type_name = self.data_type_service.map_data_type_id(
                                self.db, data_type_id, event_type
                            )
                            if data_type_name:
                                daily_entry["dataTypeName"] = data_type_name
                            else:
                                logger.warning(f"Data type ID {data_type_id} not found for event type {event_type}")
        
        return mapped_payload
    
    def process_epoch_create(self, data: Dict[str, Any], end_user_id: str) -> Dict[str, Any]:
        """
        Process event.data.epoch.create events
        """
        logger.info(f"Processing epoch.create event for end_user_id: {end_user_id}")
        # TODO: Implement health record storage logic
        return {"status": "processed", "event_type": "epoch.create"}
    
    def process_daily_update(self, data: Dict[str, Any], end_user_id: str) -> Dict[str, Any]:
        """
        Process event.data.daily.update events
        """
        logger.info(f"Processing daily.update event for end_user_id: {end_user_id}")
        # TODO: Implement health record storage logic
        return {"status": "processed", "event_type": "daily.update"}
    
    def process_daily_create(self, data: Dict[str, Any], end_user_id: str) -> Dict[str, Any]:
        """
        Process event.data.daily.create events
        """
        logger.info(f"Processing daily.create event for end_user_id: {end_user_id}")
        # TODO: Implement health record storage logic
        return {"status": "processed", "event_type": "daily.create"}
    
    def store_health_data(self, payload: Dict[str, Any], mapped_payload: Dict[str, Any]) -> None:
        """
        Store health data from Thryve webhook into health_records
        Maps end_user_id (Thryve access token) to internal user_id via Supabase
        """
        from app.crud.user import get_user_by_supabase_id
        from app.core.supabase_client import SupabaseService
        from app.models.user import User
        import asyncio
        
        logger.info("Storing health data from Thryve webhook")
        end_user_id = payload.get("endUserId", "")
        
        if not end_user_id:
            logger.warning("No endUserId in payload, skipping storage")
            return
        
        # Get Supabase user_id from user_integrations table using thryve_access_token
        # Since access_token = end_user_id, we need to find user with matching thryve_access_token
        supabase_service = SupabaseService()
        
        # Find user by thryve_access_token in user_integrations
        # We'll need to query Supabase to find the user
        try:
            # Query Supabase user_integrations to find user_id with matching thryve_access_token
            # This is async, so we need to handle it properly
            async def find_user():
                # Get all user integrations and find matching thryve_access_token
                # Note: This is a simplified approach - in production, you might want a more efficient query
                try:
                    # Query Supabase for user with matching thryve_access_token
                    response = supabase_service.client.table("user_integrations").select("user_id").eq("thryve_access_token", end_user_id).execute()
                    if response.data and len(response.data) > 0:
                        supabase_user_id = response.data[0].get("user_id")
                        if supabase_user_id:
                            # Find internal user by supabase_user_id
                            user = get_user_by_supabase_id(self.db, supabase_user_id)
                            return user
                except Exception as e:
                    logger.error(f"Error finding user by thryve_access_token: {e}")
                return None
            
            # Run async function
            user = asyncio.run(find_user())
            
            if not user:
                logger.warning(f"User not found for Thryve end_user_id: {end_user_id}")
                return
            
            logger.info(f"Found user {user.id} for Thryve end_user_id: {end_user_id}")
            
            # TODO: Implement actual health record creation based on event type
            # This will require mapping Thryve data types to HealthRecordMetric
            # and creating HealthRecord entries
            
        except Exception as e:
            logger.error(f"Error storing health data: {e}", exc_info=True)

