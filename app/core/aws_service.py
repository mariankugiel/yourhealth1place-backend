import boto3
import aioboto3
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.core.akeyless_service import akeyless_service
import logging

logger = logging.getLogger(__name__)

class AWSService:
    def __init__(self):
        self.session = boto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.s3_client = self.session.client('s3')
        self.athena_client = self.session.client('athena')
        self.glue_client = self.session.client('glue')
    
    async def get_encryption_key(self, key_name: str) -> str:
        """Get encryption key from Akeyless"""
        try:
            key = await akeyless_service.get_secret(key_name)
            return key
        except Exception as e:
            logger.error(f"Failed to get encryption key from Akeyless: {e}")
            raise
    
    async def store_health_data(self, user_id: str, data_type: str, data: Dict[str, Any]) -> str:
        """Store sensitive health data in encrypted S3"""
        try:
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            
            # Get encryption key for this data type
            encryption_key = await self.get_encryption_key(f"health-data-{data_type}")
            
            # Prepare metadata (no sensitive info)
            metadata = {
                "user_id": user_id,
                "data_type": data_type,
                "timestamp": datetime.utcnow().isoformat(),
                "file_id": file_id,
                "encryption_key_id": f"health-data-{data_type}"
            }
            
            # Encrypt data (in production, use proper encryption)
            encrypted_data = self._encrypt_data(data, encryption_key)
            
            # Store in S3
            s3_key = f"health-data/{user_id}/{data_type}/{file_id}.json"
            
            self.s3_client.put_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=s3_key,
                Body=json.dumps(encrypted_data),
                Metadata=metadata,
                ServerSideEncryption='aws:kms'
            )
            
            # Log access for analytics
            await self._log_data_access(user_id, data_type, "store", file_id)
            
            return file_id
            
        except Exception as e:
            logger.error(f"Failed to store health data: {e}")
            raise
    
    async def retrieve_health_data(self, user_id: str, data_type: str, file_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve sensitive health data from encrypted S3"""
        try:
            # Get encryption key
            encryption_key = await self.get_encryption_key(f"health-data-{data_type}")
            
            # Retrieve from S3
            s3_key = f"health-data/{user_id}/{data_type}/{file_id}.json"
            
            response = self.s3_client.get_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=s3_key
            )
            
            encrypted_data = json.loads(response['Body'].read())
            
            # Decrypt data
            decrypted_data = self._decrypt_data(encrypted_data, encryption_key)
            
            # Log access for analytics
            await self._log_data_access(user_id, data_type, "retrieve", file_id)
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve health data: {e}")
            return None
    
    async def list_health_data(self, user_id: str, data_type: str = None) -> List[Dict[str, Any]]:
        """List health data files for a user"""
        try:
            prefix = f"health-data/{user_id}/"
            if data_type:
                prefix += f"{data_type}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=settings.AWS_S3_BUCKET,
                Prefix=prefix
            )
            
            files = []
            for obj in response.get('Contents', []):
                # Extract metadata from S3 object
                metadata_response = self.s3_client.head_object(
                    Bucket=settings.AWS_S3_BUCKET,
                    Key=obj['Key']
                )
                
                files.append({
                    "file_id": metadata_response['Metadata'].get('file_id'),
                    "data_type": metadata_response['Metadata'].get('data_type'),
                    "timestamp": metadata_response['Metadata'].get('timestamp'),
                    "size": obj['Size']
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list health data: {e}")
            return []
    
    async def delete_health_data(self, user_id: str, data_type: str, file_id: str) -> bool:
        """Delete sensitive health data from S3"""
        try:
            s3_key = f"health-data/{user_id}/{data_type}/{file_id}.json"
            
            self.s3_client.delete_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=s3_key
            )
            
            # Log access for analytics
            await self._log_data_access(user_id, data_type, "delete", file_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete health data: {e}")
            return False
    
    async def _log_data_access(self, user_id: str, data_type: str, action: str, file_id: str):
        """Log data access for analytics via Athena"""
        try:
            log_data = {
                "user_id": user_id,
                "data_type": data_type,
                "action": action,
                "file_id": file_id,
                "timestamp": datetime.utcnow().isoformat(),
                "access_id": str(uuid.uuid4())
            }
            
            # Store log in S3 for Athena querying
            log_key = f"access-logs/{datetime.utcnow().strftime('%Y/%m/%d')}/{log_data['access_id']}.json"
            
            self.s3_client.put_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=log_key,
                Body=json.dumps(log_data),
                ServerSideEncryption='aws:kms'
            )
            
        except Exception as e:
            logger.error(f"Failed to log data access: {e}")
    
    async def query_health_analytics(self, query: str) -> List[Dict[str, Any]]:
        """Query health data analytics using Athena"""
        try:
            # Start query execution
            response = self.athena_client.start_query_execution(
                QueryString=query,
                QueryExecutionContext={
                    'Database': settings.AWS_ATHENA_DATABASE
                },
                ResultConfiguration={
                    'OutputLocation': f's3://{settings.AWS_S3_BUCKET}/athena-results/'
                },
                WorkGroup=settings.AWS_ATHENA_WORKGROUP
            )
            
            query_execution_id = response['QueryExecutionId']
            
            # Wait for query to complete
            while True:
                status_response = self.athena_client.get_query_execution(
                    QueryExecutionId=query_execution_id
                )
                status = status_response['QueryExecution']['Status']['State']
                
                if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                    break
            
            if status == 'SUCCEEDED':
                # Get results
                results_response = self.athena_client.get_query_results(
                    QueryExecutionId=query_execution_id
                )
                
                # Parse results
                results = []
                for row in results_response['ResultSet']['Rows'][1:]:  # Skip header
                    row_data = {}
                    for i, col in enumerate(row['Data']):
                        col_name = results_response['ResultSet']['ResultSetMetadata']['ColumnInfo'][i]['Name']
                        row_data[col_name] = col.get('VarCharValue', '')
                    results.append(row_data)
                
                return results
            else:
                logger.error(f"Athena query failed with status: {status}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to query health analytics: {e}")
            return []
    
    def _encrypt_data(self, data: Dict[str, Any], key: str) -> Dict[str, Any]:
        """Encrypt data (simplified - in production use proper encryption)"""
        # This is a placeholder - in production, use proper encryption libraries
        return {
            "encrypted": True,
            "data": data,  # In production, this would be properly encrypted
            "encryption_method": "placeholder"
        }
    
    def _decrypt_data(self, encrypted_data: Dict[str, Any], key: str) -> Dict[str, Any]:
        """Decrypt data (simplified - in production use proper decryption)"""
        # This is a placeholder - in production, use proper decryption libraries
        return encrypted_data.get("data", {})

# Global instance
aws_service = AWSService() 