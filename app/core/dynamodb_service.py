import boto3
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.core.akeyless_service import akeyless_service
import logging

logger = logging.getLogger(__name__)

class DynamoDBService:
    def __init__(self):
        self.session = boto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.dynamodb = self.session.resource('dynamodb')
        self.table_name = settings.AWS_DYNAMODB_TABLE
        
    async def get_encryption_key(self, key_name: str) -> str:
        """Get encryption key from Akeyless"""
        try:
            key = await akeyless_service.get_secret(key_name)
            return key
        except Exception as e:
            logger.error(f"Failed to get encryption key from Akeyless: {e}")
            raise
    
    async def store_health_data(self, internal_user_id: str, data_type: str, data: Dict[str, Any]) -> str:
        """Store sensitive health data in encrypted DynamoDB"""
        try:
            # Generate unique record ID
            record_id = str(uuid.uuid4())
            
            # Get encryption key for this data type
            encryption_key = await self.get_encryption_key(f"health-data-{data_type}")
            
            # Encrypt sensitive data
            encrypted_data = self._encrypt_data(data, encryption_key)
            
            # Prepare DynamoDB item
            item = {
                'record_id': record_id,
                'internal_user_id': internal_user_id,
                'data_type': data_type,
                'encrypted_data': encrypted_data,
                'encryption_key_id': f"health-data-{data_type}",
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'is_active': True
            }
            
            # Store in DynamoDB
            table = self.dynamodb.Table(self.table_name)
            table.put_item(Item=item)
            
            # Log access for analytics
            await self._log_data_access(internal_user_id, data_type, "store", record_id)
            
            return record_id
            
        except Exception as e:
            logger.error(f"Failed to store health data: {e}")
            raise
    
    async def retrieve_health_data(self, internal_user_id: str, data_type: str, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve sensitive health data from encrypted DynamoDB"""
        try:
            # Get encryption key
            encryption_key = await self.get_encryption_key(f"health-data-{data_type}")
            
            # Retrieve from DynamoDB
            table = self.dynamodb.Table(self.table_name)
            response = table.get_item(
                Key={
                    'record_id': record_id,
                    'internal_user_id': internal_user_id
                }
            )
            
            if 'Item' not in response:
                return None
            
            item = response['Item']
            
            # Decrypt data
            decrypted_data = self._decrypt_data(item['encrypted_data'], encryption_key)
            
            # Log access for analytics
            await self._log_data_access(internal_user_id, data_type, "retrieve", record_id)
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve health data: {e}")
            return None
    
    async def list_health_data(self, internal_user_id: str, data_type: str = None) -> List[Dict[str, Any]]:
        """List health data records for a user"""
        try:
            table = self.dynamodb.Table(self.table_name)
            
            # Build query parameters
            query_params = {
                'IndexName': 'InternalUserIndex',
                'KeyConditionExpression': 'internal_user_id = :user_id',
                'ExpressionAttributeValues': {
                    ':user_id': internal_user_id,
                    ':active': True
                },
                'FilterExpression': 'is_active = :active'
            }
            
            if data_type:
                query_params['FilterExpression'] += ' AND data_type = :data_type'
                query_params['ExpressionAttributeValues'][':data_type'] = data_type
            
            response = table.query(**query_params)
            
            # Return metadata only (not the encrypted data)
            records = []
            for item in response.get('Items', []):
                records.append({
                    'record_id': item['record_id'],
                    'data_type': item['data_type'],
                    'created_at': item['created_at'],
                    'updated_at': item['updated_at']
                })
            
            return records
            
        except Exception as e:
            logger.error(f"Failed to list health data: {e}")
            return []
    
    async def update_health_data(self, internal_user_id: str, record_id: str, data: Dict[str, Any]) -> bool:
        """Update sensitive health data in DynamoDB"""
        try:
            # Get the existing record to determine data type
            table = self.dynamodb.Table(self.table_name)
            response = table.get_item(
                Key={
                    'record_id': record_id,
                    'internal_user_id': internal_user_id
                }
            )
            
            if 'Item' not in response:
                return False
            
            existing_item = response['Item']
            data_type = existing_item['data_type']
            
            # Get encryption key
            encryption_key = await self.get_encryption_key(f"health-data-{data_type}")
            
            # Encrypt new data
            encrypted_data = self._encrypt_data(data, encryption_key)
            
            # Update in DynamoDB
            table.update_item(
                Key={
                    'record_id': record_id,
                    'internal_user_id': internal_user_id
                },
                UpdateExpression='SET encrypted_data = :data, updated_at = :updated_at',
                ExpressionAttributeValues={
                    ':data': encrypted_data,
                    ':updated_at': datetime.utcnow().isoformat()
                }
            )
            
            # Log access for analytics
            await self._log_data_access(internal_user_id, data_type, "update", record_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update health data: {e}")
            return False
    
    async def delete_health_data(self, internal_user_id: str, record_id: str) -> bool:
        """Soft delete health data (mark as inactive)"""
        try:
            table = self.dynamodb.Table(self.table_name)
            
            # Get the record to determine data type
            response = table.get_item(
                Key={
                    'record_id': record_id,
                    'internal_user_id': internal_user_id
                }
            )
            
            if 'Item' not in response:
                return False
            
            data_type = response['Item']['data_type']
            
            # Soft delete (mark as inactive)
            table.update_item(
                Key={
                    'record_id': record_id,
                    'internal_user_id': internal_user_id
                },
                UpdateExpression='SET is_active = :active, updated_at = :updated_at',
                ExpressionAttributeValues={
                    ':active': False,
                    ':updated_at': datetime.utcnow().isoformat()
                }
            )
            
            # Log access for analytics
            await self._log_data_access(internal_user_id, data_type, "delete", record_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete health data: {e}")
            return False
    
    async def _log_data_access(self, internal_user_id: str, data_type: str, action: str, record_id: str):
        """Log data access for analytics and compliance"""
        try:
            # This would typically log to CloudWatch or a separate logging service
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'internal_user_id': internal_user_id,
                'data_type': data_type,
                'action': action,
                'record_id': record_id,
                'source': 'dynamodb_service'
            }
            
            # Log to CloudWatch or your preferred logging service
            logger.info(f"Health data access: {json.dumps(log_entry)}")
            
        except Exception as e:
            logger.error(f"Failed to log data access: {e}")
    
    def _encrypt_data(self, data: Dict[str, Any], key: str) -> Dict[str, Any]:
        """Encrypt sensitive data (simplified for demo)"""
        # In production, use proper encryption libraries
        # This is a placeholder for demonstration
        return {
            'encrypted': True,
            'data': data,  # In production, this would be properly encrypted
            'key_id': key
        }
    
    def _decrypt_data(self, encrypted_data: Dict[str, Any], key: str) -> Dict[str, Any]:
        """Decrypt sensitive data (simplified for demo)"""
        # In production, use proper decryption libraries
        # This is a placeholder for demonstration
        return encrypted_data.get('data', {})

# Create service instance
dynamodb_service = DynamoDBService() 