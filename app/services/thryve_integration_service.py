import requests
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.supabase_client import SupabaseService
import logging
import base64

logger = logging.getLogger(__name__)


class ThryveIntegrationService:
    """Service for Thryve integration operations"""
    
    def __init__(self):
        self.supabase_service = SupabaseService()
        self.api_base_url = settings.THRYVE_API_BASE_URL
        self.api_widget_url = settings.THRYVE_API_WIDGET_URL
        self.service_base_url = settings.THRYVE_SERVICE_BASE_URL
    
    def _get_auth_headers(self, content_type: str = "application/x-www-form-urlencoded") -> Dict[str, str]:
        """Get authentication headers for Thryve API"""
        credentials = f"{settings.THRYVE_WEB_AUTH_USERNAME}:{settings.THRYVE_WEB_AUTH_PASSWORD}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        return {
            "Authorization": f"Basic {encoded_credentials}",
            "AppAuthorization": settings.THRYVE_APP_AUTHORIZATION,
            "Content-Type": content_type
        }
    
    def get_access_token(self, partner_user_id: str) -> str:
        """
        Get Thryve access token for a partner user ID
        API: POST https://api.und-gesund.de/v5/accessToken
        Body: partnerUserID=xxxx
        Returns: access token string (which is also the end_user_id)
        """
        try:
            url = f"{self.api_base_url}/v5/accessToken"
            headers = self._get_auth_headers()
            data = {"partnerUserID": partner_user_id}
            
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            
            # Response is a plain string, not JSON
            access_token = response.text.strip()
            logger.info(f"Successfully retrieved Thryve access token for partner_user_id: {partner_user_id}")
            return access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Thryve access token: {e}")
            raise
    
    def get_connection_session_token(self, end_user_id: str, locale: str = "en") -> str:
        """
        Get connection session token from Thryve widget API
        API: POST https://api.thryve.de/widget/v6/connection
        Body: {"endUserId": "xxx", "locale": "en"} (JSON)
        Returns: connectionSessionToken from the URL in response
        """
        try:
            url = f"{self.api_widget_url}/widget/v6/connection"
            # Use application/json content type for this endpoint
            headers = self._get_auth_headers(content_type="application/json")
            data = {
                "endUserId": end_user_id,
                "locale": locale
            }
            
            # Use json parameter to send as JSON body (automatically sets Content-Type to application/json)
            # But we're already setting it in headers, so this should work
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            # Extract connectionSessionToken from URL
            # URL format: https://connect.thryve.de/?connectionSessionToken=2089135578X1504707759582499029&platform=web&lang=en
            url_str = result.get("data", {}).get("url", "")
            if "connectionSessionToken=" in url_str:
                token = url_str.split("connectionSessionToken=")[1].split("&")[0]
                logger.info(f"Successfully retrieved connection session token")
                return token
            else:
                raise ValueError("Connection session token not found in response URL")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get connection session token: {e}")
            raise
    
    def build_connection_url(self, connection_session_token: str, data_source_id: int, redirect_uri: str) -> str:
        """
        Build connection URL for a data source
        Format: https://service2.und-gesund.de/dataSourceDirectConnection.html?token={token}&dataSource={dataSourceId}&redirect_uri={redirectURL}
        """
        from urllib.parse import quote
        encoded_redirect_uri = quote(redirect_uri, safe='')
        return f"{self.service_base_url}/dataSourceDirectConnection.html?token={connection_session_token}&dataSource={data_source_id}&redirect_uri={encoded_redirect_uri}"
    
    def build_disconnection_url(self, connection_session_token: str, data_source_id: int, redirect_uri: str) -> str:
        """
        Build disconnection URL for a data source
        Format: https://service2.und-gesund.de/dataSourceDirectRevoke.html?token={token}&dataSource={dataSourceId}&direct=true&redirect_uri={redirectURL}
        """
        from urllib.parse import quote
        encoded_redirect_uri = quote(redirect_uri, safe='')
        return f"{self.service_base_url}/dataSourceDirectRevoke.html?token={connection_session_token}&dataSource={data_source_id}&direct=true&redirect_uri={encoded_redirect_uri}"
    
    async def save_access_token(self, user_id: str, access_token: str) -> None:
        """Save Thryve access token to Supabase user_integrations table"""
        try:
            await self.supabase_service.update_user_integrations(
                user_id=user_id,
                integrations={"thryve_access_token": access_token}
            )
            logger.info(f"Successfully saved Thryve access token for user: {user_id}")
        except Exception as e:
            logger.error(f"Failed to save Thryve access token: {e}")
            raise
    
    async def get_user_access_token(self, user_id: str) -> Optional[str]:
        """Get Thryve access token from Supabase user_integrations table"""
        try:
            integrations = await self.supabase_service.get_user_integrations(user_id)
            return integrations.get("thryve_access_token") if integrations else None
        except Exception as e:
            logger.error(f"Failed to get Thryve access token: {e}")
            return None
    
    def fetch_dynamic_epoch_values(
        self, 
        access_token: str, 
        start_date: str, 
        end_date: str, 
        data_source_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch dynamic epoch values from Thryve API
        API: POST https://api.und-gesund.de/v5/dynamicEpochValues
        
        Args:
            access_token: Thryve access token (authenticationToken)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            data_source_id: Optional data source ID to filter by
        
        Returns:
            List of response objects from the API
        """
        try:
            url = f"{self.api_base_url}/v5/dynamicEpochValues"
            headers = self._get_auth_headers(content_type="application/x-www-form-urlencoded")
            
            data = {
                "authenticationToken": access_token,
                "startTimestamp": start_date,
                "endTimestamp": end_date,
                "displayTypeName": "true",
                "detailed": "true"
            }
            
            # Add data source filter if provided
            if data_source_id:
                data["dataSources"] = str(data_source_id)
            
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully fetched epoch values for date range {start_date} to {end_date}")
            return result if isinstance(result, list) else [result]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch dynamic epoch values: {e}")
            raise
    
    def fetch_daily_dynamic_values(
        self, 
        access_token: str, 
        start_day: str, 
        end_day: str, 
        data_source_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch daily dynamic values from Thryve API
        API: POST https://api.und-gesund.de/v5/dailyDynamicValues
        
        Args:
            access_token: Thryve access token (authenticationToken)
            start_day: Start day in YYYY-MM-DD format
            end_day: End day in YYYY-MM-DD format
            data_source_id: Optional data source ID to filter by
        
        Returns:
            List of response objects from the API
        """
        try:
            url = f"{self.api_base_url}/v5/dailyDynamicValues"
            headers = self._get_auth_headers(content_type="application/x-www-form-urlencoded")
            
            data = {
                "authenticationToken": access_token,
                "startDay": start_day,
                "endDay": end_day,
                "displayTypeName": "true",
                "detailed": "true"
            }
            
            # Add data source filter if provided
            if data_source_id:
                data["dataSources"] = str(data_source_id)
            
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully fetched daily values for date range {start_day} to {end_day}")
            return result if isinstance(result, list) else [result]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch daily dynamic values: {e}")
            raise
    
    def _transform_epoch_response_to_webhook_format(
        self, 
        response_data: List[Dict[str, Any]], 
        data_source_id: int,
        db: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Transform epoch API response to webhook-compatible format
        
        Args:
            response_data: List of API response objects
            data_source_id: Data source ID
            db: Optional database session to get data source name
        
        Returns:
            Webhook-compatible format: {"data": [{"epochData": [...], "dataSourceId": X, "dataSourceName": "..."}]}
        """
        from datetime import datetime
        
        # Get data source name if db is provided
        data_source_name = "Unknown"
        if db:
            from app.services.thryve_data_source_service import ThryveDataSourceService
            data_source = ThryveDataSourceService.get_by_id(db, data_source_id)
            if data_source:
                data_source_name = data_source.name
        
        epoch_data = []
        
        for response_item in response_data:
            data_sources = response_item.get("dataSources", [])
            for ds in data_sources:
                if ds.get("dataSource") == data_source_id:
                    for entry in ds.get("data", []):
                        # Convert dynamicValueType to dataTypeId
                        data_type_id = entry.get("dynamicValueType")
                        if not data_type_id:
                            continue
                        
                        # Convert ISO timestamp to Unix milliseconds
                        start_timestamp_str = entry.get("startTimestamp")
                        end_timestamp_str = entry.get("endTimestamp")
                        
                        start_timestamp_ms = None
                        end_timestamp_ms = None
                        
                        if start_timestamp_str and start_timestamp_str != "null":
                            try:
                                dt = datetime.fromisoformat(start_timestamp_str.replace('Z', '+00:00'))
                                start_timestamp_ms = int(dt.timestamp() * 1000)
                            except Exception as e:
                                logger.warning(f"Failed to parse startTimestamp {start_timestamp_str}: {e}")
                                continue
                        
                        if end_timestamp_str and end_timestamp_str != "null":
                            try:
                                dt = datetime.fromisoformat(end_timestamp_str.replace('Z', '+00:00'))
                                end_timestamp_ms = int(dt.timestamp() * 1000)
                            except Exception as e:
                                logger.warning(f"Failed to parse endTimestamp {end_timestamp_str}: {e}")
                                end_timestamp_ms = None
                        
                        # Convert value based on valueType
                        value = entry.get("value")
                        value_type = entry.get("valueType", "").upper()
                        
                        if value_type == "DOUBLE" or value_type == "FLOAT":
                            try:
                                value = float(value)
                            except (ValueError, TypeError):
                                logger.warning(f"Failed to convert value to float: {value}")
                                continue
                        elif value_type == "LONG" or value_type == "INTEGER":
                            try:
                                value = int(float(value))  # Convert via float first to handle "70.0"
                            except (ValueError, TypeError):
                                logger.warning(f"Failed to convert value to int: {value}")
                                continue
                        elif value_type == "BOOLEAN":
                            value = str(value).lower() == "true"
                        # STRING and other types keep as-is
                        
                        # Build epoch entry in webhook format
                        epoch_entry = {
                            "dataTypeId": data_type_id,
                            "value": value,
                            "startTimestamp": start_timestamp_ms,
                            "createdAt": entry.get("createdAt", ""),
                        }
                        
                        if end_timestamp_ms is not None:
                            epoch_entry["endTimestamp"] = end_timestamp_ms
                        
                        # Add details if available
                        if entry.get("details"):
                            epoch_entry["details"] = entry.get("details")
                        
                        epoch_data.append(epoch_entry)
        
        return {
            "data": [{
                "dataSourceId": data_source_id,
                "dataSourceName": data_source_name,
                "epochData": epoch_data
            }]
        }
    
    def _transform_daily_response_to_webhook_format(
        self, 
        response_data: List[Dict[str, Any]], 
        data_source_id: int,
        db: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Transform daily API response to webhook-compatible format
        
        Args:
            response_data: List of API response objects
            data_source_id: Data source ID
            db: Optional database session to get data source name
        
        Returns:
            Webhook-compatible format: {"data": [{"dailyData": [...], "dataSourceId": X, "dataSourceName": "..."}]}
        """
        from datetime import datetime
        
        # Get data source name if db is provided
        data_source_name = "Unknown"
        if db:
            from app.services.thryve_data_source_service import ThryveDataSourceService
            data_source = ThryveDataSourceService.get_by_id(db, data_source_id)
            if data_source:
                data_source_name = data_source.name
        
        daily_data = []
        
        for response_item in response_data:
            data_sources = response_item.get("dataSources", [])
            for ds in data_sources:
                if ds.get("dataSource") == data_source_id:
                    for entry in ds.get("data", []):
                        # Convert dailyDynamicValueType to dataTypeId
                        data_type_id = entry.get("dailyDynamicValueType")
                        if not data_type_id:
                            continue
                        
                        # Convert day (YYYY-MM-DD) to Unix milliseconds (start of day)
                        day_str = entry.get("day")
                        day_timestamp_ms = None
                        
                        if day_str:
                            try:
                                dt = datetime.strptime(day_str, "%Y-%m-%d")
                                day_timestamp_ms = int(dt.timestamp() * 1000)
                            except Exception as e:
                                logger.warning(f"Failed to parse day {day_str}: {e}")
                                continue
                        
                        # Convert value based on valueType
                        value = entry.get("value")
                        value_type = entry.get("valueType", "").upper()
                        
                        if value_type == "DOUBLE" or value_type == "FLOAT":
                            try:
                                value = float(value)
                            except (ValueError, TypeError):
                                logger.warning(f"Failed to convert value to float: {value}")
                                continue
                        elif value_type == "LONG" or value_type == "INTEGER":
                            try:
                                value = int(float(value))
                            except (ValueError, TypeError):
                                logger.warning(f"Failed to convert value to int: {value}")
                                continue
                        elif value_type == "BOOLEAN":
                            value = str(value).lower() == "true"
                        # STRING and other types keep as-is
                        
                        # Build daily entry in webhook format
                        daily_entry = {
                            "dataTypeId": data_type_id,
                            "value": value,
                            "day": day_timestamp_ms,
                            "createdAt": entry.get("createdAt", ""),
                        }
                        
                        # Add details if available
                        if entry.get("details"):
                            daily_entry["details"] = entry.get("details")
                        
                        daily_data.append(daily_entry)
        
        return {
            "data": [{
                "dataSourceId": data_source_id,
                "dataSourceName": data_source_name,
                "dailyData": daily_data
            }]
        }

