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
    
    async def store_document(self, internal_user_id: str, file_data: bytes, file_name: str, content_type: str) -> str:
        """Store user uploaded documents in encrypted S3"""
        try:
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            
            # Get encryption key for documents
            encryption_key = await self.get_encryption_key("document-encryption")
            
            # Prepare metadata (no sensitive info)
            metadata = {
                "internal_user_id": internal_user_id,
                "original_filename": file_name,
                "content_type": content_type,
                "timestamp": datetime.utcnow().isoformat(),
                "file_id": file_id,
                "encryption_key_id": "document-encryption"
            }
            
            # Encrypt file data (in production, use proper encryption)
            encrypted_data = self._encrypt_file_data(file_data, encryption_key)
            
            # Store in S3
            s3_key = f"documents/{internal_user_id}/{file_id}/{file_name}"
            
            self.s3_client.put_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=s3_key,
                Body=encrypted_data,
                Metadata=metadata,
                ContentType=content_type,
                ServerSideEncryption='AES256'
            )
            
            # Log access for analytics
            await self._log_data_access(internal_user_id, "document", "store", file_id)
            
            return file_id
            
        except Exception as e:
            logger.error(f"Failed to store document: {e}")
            raise
    
    def generate_presigned_url(self, s3_url: str, expiration: int = 3600) -> str:
        """Generate a presigned URL for downloading a document from S3"""
        try:
            # Parse S3 URL to extract bucket and key
            # Format: s3://bucket-name/key/path
            if not s3_url.startswith('s3://'):
                raise ValueError(f"Invalid S3 URL format: {s3_url}")
            
            # Remove s3:// prefix and split bucket and key
            s3_path = s3_url[5:]  # Remove 's3://'
            bucket_key = s3_path.split('/', 1)
            
            if len(bucket_key) != 2:
                raise ValueError(f"Invalid S3 URL format: {s3_url}")
            
            bucket_name, key = bucket_key
            
            # Generate presigned URL with download headers
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket_name, 
                    'Key': key,
                    'ResponseContentDisposition': 'attachment'  # Force download instead of opening in browser
                },
                ExpiresIn=expiration
            )
            
            logger.info(f"Generated presigned URL for {s3_url}")
            return presigned_url
            
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {s3_url}: {e}")
            raise
    
    def delete_document(self, s3_url: str) -> bool:
        """Delete a document from S3"""
        try:
            # Parse S3 URL to extract bucket and key
            if not s3_url.startswith('s3://'):
                logger.error(f"Invalid S3 URL format: {s3_url}")
                return False
            
            # Remove s3:// prefix and split bucket and key
            s3_path = s3_url[5:]  # Remove 's3://'
            bucket_key = s3_path.split('/', 1)
            
            if len(bucket_key) != 2:
                logger.error(f"Invalid S3 URL format: {s3_url}")
                return False
            
            bucket_name, key = bucket_key
            
            # Delete the object from S3
            self.s3_client.delete_object(Bucket=bucket_name, Key=key)
            logger.info(f"Successfully deleted document from S3: {s3_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document from S3 {s3_url}: {e}")
            return False
    
    async def retrieve_document(self, internal_user_id: str, file_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user uploaded document from encrypted S3"""
        try:
            # Get encryption key
            encryption_key = await self.get_encryption_key("document-encryption")
            
            # List objects to find the file
            prefix = f"documents/{internal_user_id}/{file_id}/"
            response = self.s3_client.list_objects_v2(
                Bucket=settings.AWS_S3_BUCKET,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return None
            
            # Get the first file (should be only one)
            s3_key = response['Contents'][0]['Key']
            
            # Retrieve from S3
            response = self.s3_client.get_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=s3_key
            )
            
            encrypted_data = response['Body'].read()
            
            # Decrypt data
            decrypted_data = self._decrypt_file_data(encrypted_data, encryption_key)
            
            # Log access for analytics
            await self._log_data_access(internal_user_id, "document", "retrieve", file_id)
            
            return {
                'file_data': decrypted_data,
                'content_type': response.get('ContentType', 'application/octet-stream'),
                'original_filename': response.get('Metadata', {}).get('original_filename', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve document: {e}")
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
                ServerSideEncryption='AES256'
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
    
    def _encrypt_file_data(self, file_data: bytes, key: str) -> bytes:
        """Encrypt file data (simplified - in production use proper encryption)"""
        # This is a placeholder - in production, use proper encryption libraries
        return file_data  # In production, this would be properly encrypted
    
    def _decrypt_file_data(self, encrypted_data: bytes, key: str) -> bytes:
        """Decrypt file data (simplified - in production use proper decryption)"""
        # This is a placeholder - in production, use proper decryption libraries
        return encrypted_data  # In production, this would be properly decrypted
    
    def upload_message_attachment(self, file_data: bytes, file_name: str, content_type: str, user_id: int) -> Dict[str, Any]:
        """Upload message attachment to S3 (unencrypted for quick access)"""
        try:
            # Generate unique file key
            file_extension = file_name.split('.')[-1] if '.' in file_name else ''
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            s3_key = f"message-attachments/{user_id}/{unique_filename}"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=s3_key,
                Body=file_data,
                ContentType=content_type or 'application/octet-stream',
                Metadata={
                    'original-filename': file_name,
                    'uploaded-by': str(user_id)
                }
            )
            
            # Generate presigned URL for download
            s3_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.AWS_S3_BUCKET, 'Key': s3_key},
                ExpiresIn=3600  # 1 hour
            )
            
            return {
                'file_name': unique_filename,
                'original_file_name': file_name,
                'file_type': content_type or 'application/octet-stream',
                'file_size': len(file_data),
                'file_extension': file_extension,
                's3_bucket': settings.AWS_S3_BUCKET,
                's3_key': s3_key,
                's3_url': s3_url,
                'uploaded_by': user_id
            }
            
        except Exception as e:
            logger.error(f"Failed to upload message attachment: {e}")
            raise

# Global instance
aws_service = AWSService() 