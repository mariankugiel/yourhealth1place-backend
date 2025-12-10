import requests
from typing import Optional, Dict
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

