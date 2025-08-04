import psycopg2
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.core.akeyless_service import akeyless_service
import logging

logger = logging.getLogger(__name__)

class RDSService:
    def __init__(self):
        self.database_url = settings.DATABASE_URL
        
    async def get_encryption_key(self, key_name: str) -> str:
        """Get encryption key from Akeyless"""
        try:
            key = await akeyless_service.get_secret(key_name)
            return key
        except Exception as e:
            logger.error(f"Failed to get encryption key from Akeyless: {e}")
            raise
    
    def _get_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(self.database_url)
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def store_health_data(self, internal_user_id: str, data_type: str, data: Dict[str, Any]) -> str:
        """Store sensitive health data in encrypted RDS"""
        try:
            # Generate unique record ID
            record_id = str(uuid.uuid4())
            
            # Get encryption key for this data type
            encryption_key = await self.get_encryption_key(f"health-data-{data_type}")
            
            # Encrypt sensitive data
            encrypted_data = self._encrypt_data(data, encryption_key)
            
            # Store in RDS
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS health_data (
                    record_id VARCHAR(255) PRIMARY KEY,
                    internal_user_id VARCHAR(255) NOT NULL,
                    data_type VARCHAR(100) NOT NULL,
                    encrypted_data JSONB NOT NULL,
                    encryption_key_id VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_health_data_user_id 
                ON health_data(internal_user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_health_data_type 
                ON health_data(data_type)
            """)
            
            # Insert data
            cursor.execute("""
                INSERT INTO health_data 
                (record_id, internal_user_id, data_type, encrypted_data, encryption_key_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (record_id, internal_user_id, data_type, json.dumps(encrypted_data), f"health-data-{data_type}"))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Log access for analytics
            await self._log_data_access(internal_user_id, data_type, "store", record_id)
            
            return record_id
            
        except Exception as e:
            logger.error(f"Failed to store health data: {e}")
            raise
    
    async def retrieve_health_data(self, internal_user_id: str, data_type: str, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve sensitive health data from encrypted RDS"""
        try:
            # Get encryption key
            encryption_key = await self.get_encryption_key(f"health-data-{data_type}")
            
            # Retrieve from RDS
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT encrypted_data FROM health_data 
                WHERE record_id = %s AND internal_user_id = %s AND is_active = TRUE
            """, (record_id, internal_user_id))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not result:
                return None
            
            encrypted_data = json.loads(result[0])
            
            # Decrypt data
            decrypted_data = self._decrypt_data(encrypted_data, encryption_key)
            
            # Log access for analytics
            await self._log_data_access(internal_user_id, data_type, "retrieve", record_id)
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve health data: {e}")
            return None
    
    async def list_health_data(self, internal_user_id: str, data_type: str = None) -> List[Dict[str, Any]]:
        """List health data records for a user"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if data_type:
                cursor.execute("""
                    SELECT record_id, data_type, created_at, updated_at 
                    FROM health_data 
                    WHERE internal_user_id = %s AND data_type = %s AND is_active = TRUE
                    ORDER BY created_at DESC
                """, (internal_user_id, data_type))
            else:
                cursor.execute("""
                    SELECT record_id, data_type, created_at, updated_at 
                    FROM health_data 
                    WHERE internal_user_id = %s AND is_active = TRUE
                    ORDER BY created_at DESC
                """, (internal_user_id,))
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Return metadata only (not the encrypted data)
            records = []
            for row in results:
                records.append({
                    'record_id': row[0],
                    'data_type': row[1],
                    'created_at': row[2].isoformat() if row[2] else None,
                    'updated_at': row[3].isoformat() if row[3] else None
                })
            
            return records
            
        except Exception as e:
            logger.error(f"Failed to list health data: {e}")
            return []
    
    async def update_health_data(self, internal_user_id: str, record_id: str, data: Dict[str, Any]) -> bool:
        """Update sensitive health data in RDS"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get the existing record to determine data type
            cursor.execute("""
                SELECT data_type FROM health_data 
                WHERE record_id = %s AND internal_user_id = %s AND is_active = TRUE
            """, (record_id, internal_user_id))
            
            result = cursor.fetchone()
            if not result:
                return False
            
            data_type = result[0]
            
            # Get encryption key
            encryption_key = await self.get_encryption_key(f"health-data-{data_type}")
            
            # Encrypt new data
            encrypted_data = self._encrypt_data(data, encryption_key)
            
            # Update in RDS
            cursor.execute("""
                UPDATE health_data 
                SET encrypted_data = %s, updated_at = CURRENT_TIMESTAMP
                WHERE record_id = %s AND internal_user_id = %s
            """, (json.dumps(encrypted_data), record_id, internal_user_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Log access for analytics
            await self._log_data_access(internal_user_id, data_type, "update", record_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update health data: {e}")
            return False
    
    async def delete_health_data(self, internal_user_id: str, record_id: str) -> bool:
        """Soft delete health data (mark as inactive)"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get the record to determine data type
            cursor.execute("""
                SELECT data_type FROM health_data 
                WHERE record_id = %s AND internal_user_id = %s AND is_active = TRUE
            """, (record_id, internal_user_id))
            
            result = cursor.fetchone()
            if not result:
                return False
            
            data_type = result[0]
            
            # Soft delete (mark as inactive)
            cursor.execute("""
                UPDATE health_data 
                SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE record_id = %s AND internal_user_id = %s
            """, (record_id, internal_user_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
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
                'source': 'rds_service'
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
rds_service = RDSService() 