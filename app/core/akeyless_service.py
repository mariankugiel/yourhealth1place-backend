import akeyless
from akeyless import ApiClient, Configuration
from akeyless.api import V2Api
from akeyless.models import GetSecretValue
from typing import Optional, Dict, Any
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class AkeylessService:
    def __init__(self):
        self.config = Configuration(
            host=settings.AKEYLESS_URL
        )
        self.api_client = ApiClient(self.config)
        self.v2_api = V2Api(self.api_client)
        
        # Set authentication
        self.api_client.set_auth_token(
            settings.AKEYLESS_ACCESS_ID,
            settings.AKEYLESS_ACCESS_KEY
        )
    
    async def get_secret(self, secret_name: str) -> str:
        """Get a secret from Akeyless"""
        try:
            body = GetSecretValue(
                names=[secret_name],
                token=settings.AKEYLESS_ACCESS_KEY
            )
            
            response = self.v2_api.get_secret_value(body)
            
            if response and response.secrets:
                return response.secrets[0]
            else:
                raise ValueError(f"Secret {secret_name} not found")
                
        except Exception as e:
            logger.error(f"Failed to get secret {secret_name} from Akeyless: {e}")
            raise
    
    async def create_secret(self, secret_name: str, secret_value: str, description: str = "") -> bool:
        """Create a new secret in Akeyless"""
        try:
            from akeyless.models import CreateSecret
            
            body = CreateSecret(
                name=secret_name,
                value=secret_value,
                description=description,
                token=settings.AKEYLESS_ACCESS_KEY
            )
            
            response = self.v2_api.create_secret(body)
            return True
            
        except Exception as e:
            logger.error(f"Failed to create secret {secret_name} in Akeyless: {e}")
            return False
    
    async def update_secret(self, secret_name: str, secret_value: str) -> bool:
        """Update an existing secret in Akeyless"""
        try:
            from akeyless.models import UpdateSecretValue
            
            body = UpdateSecretValue(
                name=secret_name,
                value=secret_value,
                token=settings.AKEYLESS_ACCESS_KEY
            )
            
            response = self.v2_api.update_secret_value(body)
            return True
            
        except Exception as e:
            logger.error(f"Failed to update secret {secret_name} in Akeyless: {e}")
            return False
    
    async def delete_secret(self, secret_name: str) -> bool:
        """Delete a secret from Akeyless"""
        try:
            from akeyless.models import DeleteItem
            
            body = DeleteItem(
                name=secret_name,
                token=settings.AKEYLESS_ACCESS_KEY
            )
            
            response = self.v2_api.delete_item(body)
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete secret {secret_name} from Akeyless: {e}")
            return False
    
    async def list_secrets(self, path: str = "/") -> list:
        """List secrets in Akeyless"""
        try:
            from akeyless.models import ListItems
            
            body = ListItems(
                path=path,
                token=settings.AKEYLESS_ACCESS_KEY
            )
            
            response = self.v2_api.list_items(body)
            
            if response and response.items:
                return [item.name for item in response.items]
            return []
            
        except Exception as e:
            logger.error(f"Failed to list secrets from Akeyless: {e}")
            return []
    
    async def get_encryption_key(self, key_name: str) -> str:
        """Get encryption key for specific data type"""
        try:
            return await self.get_secret(f"encryption-key-{key_name}")
        except Exception as e:
            logger.error(f"Failed to get encryption key {key_name}: {e}")
            raise
    
    async def get_supabase_key(self, key_type: str) -> str:
        """Get Supabase-specific key"""
        try:
            return await self.get_secret(f"supabase-{key_type}")
        except Exception as e:
            logger.error(f"Failed to get Supabase key {key_type}: {e}")
            raise
    
    async def get_aws_key(self, key_type: str) -> str:
        """Get AWS-specific key"""
        try:
            return await self.get_secret(f"aws-{key_type}")
        except Exception as e:
            logger.error(f"Failed to get AWS key {key_type}: {e}")
            raise
    
    async def log_key_access(self, key_name: str, service: str, action: str, user_id: str = None):
        """Log key access for audit purposes"""
        try:
            from akeyless.models import CreateSecret
            
            log_entry = {
                "key_name": key_name,
                "service": service,
                "action": action,
                "user_id": user_id,
                "timestamp": akeyless.datetime.now().isoformat()
            }
            
            log_name = f"key-access-logs/{key_name}/{akeyless.datetime.now().strftime('%Y%m%d')}"
            
            body = CreateSecret(
                name=log_name,
                value=str(log_entry),
                description=f"Key access log for {key_name}",
                token=settings.AKEYLESS_ACCESS_KEY
            )
            
            self.v2_api.create_secret(body)
            
        except Exception as e:
            logger.error(f"Failed to log key access: {e}")
    
    async def rotate_encryption_key(self, key_name: str) -> bool:
        """Rotate encryption key"""
        try:
            import secrets
            
            # Generate new key
            new_key = secrets.token_hex(32)
            
            # Create new key version
            new_key_name = f"{key_name}-v{int(akeyless.datetime.now().timestamp())}"
            
            success = await self.create_secret(new_key_name, new_key, f"Rotated key for {key_name}")
            
            if success:
                # Log the rotation
                await self.log_key_access(key_name, "system", "rotate")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to rotate encryption key {key_name}: {e}")
            return False

# Global instance
akeyless_service = AkeylessService() 