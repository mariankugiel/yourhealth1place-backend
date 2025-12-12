import zstandard as zstd
import json
import logging
import hmac
import hashlib
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.services.thryve_data_type_service import ThryveDataTypeService
from app.models.health_record import HealthRecordSection, HealthRecordMetric
from app.core.config import settings

logger = logging.getLogger(__name__)


class ThryveWebhookService:
    """Service for processing Thryve webhook payloads"""
    
    def __init__(self, db: Session):
        self.db = db
        self.data_type_service = ThryveDataTypeService()
    
    def verify_hmac_signature(
        self, 
        compressed_body: bytes, 
        signature: str, 
        timestamp: str
    ) -> bool:
        """
        Verify HMAC-SHA256 signature for Thryve webhook payload
        
        Args:
            compressed_body: The compressed payload as received (before decompression)
            signature: The HMAC signature from X-HMAC-Signature header
            timestamp: The timestamp from X-HMAC-Timestamp header
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not settings.THRYVE_WEBHOOK_HMAC_SECRET:
            logger.warning("THRYVE_WEBHOOK_HMAC_SECRET not configured, skipping HMAC verification")
            return True  # Allow processing if secret not configured (for testing)
        
        if not signature or not timestamp:
            logger.error("Missing HMAC signature or timestamp headers")
            return False
        
        try:
            # Create message: compressed_body + timestamp
            # According to Thryve docs, signature is calculated on compressed payload + timestamp
            message = compressed_body + timestamp.encode('utf-8')
            
            # Calculate HMAC-SHA256
            secret_bytes = settings.THRYVE_WEBHOOK_HMAC_SECRET.encode('utf-8')
            computed_signature = hmac.new(
                secret_bytes,
                message,
                hashlib.sha256
            ).hexdigest()
            
            # Constant-time comparison to prevent timing attacks
            is_valid = hmac.compare_digest(computed_signature, signature)
            
            if is_valid:
                logger.info("✅ HMAC signature verification successful")
            else:
                logger.error(f"❌ HMAC signature verification failed")
                logger.error(f"   Expected: {computed_signature[:16]}...")
                logger.error(f"   Received: {signature[:16]}...")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error during HMAC verification: {e}")
            return False
    
    def decompress_payload(self, compressed_body: bytes, content_encoding: str = None) -> bytes:
        """
        Decompress payload based on Content-Encoding header
        According to Thryve docs: Content-Type: application/json, Content-Encoding: zstd
        """
        if not compressed_body:
            raise ValueError("Empty payload body")
        
        # Check Content-Encoding header first (Thryve standard)
        if content_encoding and content_encoding.lower() == "zstd":
            logger.info("Content-Encoding: zstd detected - attempting zstandard decompression")
            try:
                dctx = zstd.ZstdDecompressor()
                decompressed = dctx.decompress(compressed_body)
                logger.info(f"✅ Successfully decompressed zstandard payload: {len(compressed_body)} -> {len(decompressed)} bytes")
                return decompressed
            except Exception as e:
                logger.error(f"❌ Failed to decompress zstandard payload: {e}")
                raise ValueError(f"Failed to decompress zstd payload: {e}")
        
        # If Content-Encoding is not zstd, check if it's plain JSON
        if content_encoding and content_encoding.lower() not in ["zstd", "not-set", ""]:
            logger.warning(f"Unknown Content-Encoding: {content_encoding}. Attempting to parse as JSON...")
        
        # Try to detect if it's already JSON (starts with { or [)
        try:
            first_char = compressed_body[:1].decode('utf-8', errors='ignore')
            if first_char in ['{', '[']:
                logger.info("Payload appears to be plain JSON (not compressed)")
                return compressed_body  # Return as-is, will be parsed as JSON
        except:
            pass
        
        # Check zstandard magic bytes as fallback detection
        zstd_magic = compressed_body[:4] if len(compressed_body) >= 4 else b''
        is_zstd_magic = (
            zstd_magic == b'\x28\xb5\x2f\xfd' or  # Zstandard magic (big-endian)
            zstd_magic == b'\xfd\x2f\xb5\x28'     # Zstandard magic (little-endian)
        )
        
        if is_zstd_magic:
            logger.warning("Zstandard magic bytes detected but Content-Encoding header missing. Attempting decompression...")
            try:
                dctx = zstd.ZstdDecompressor()
                decompressed = dctx.decompress(compressed_body)
                logger.info(f"✅ Successfully decompressed (magic bytes detected): {len(compressed_body)} -> {len(decompressed)} bytes")
                return decompressed
            except Exception as e:
                logger.warning(f"Failed to decompress despite magic bytes: {e}")
        
        # Fallback: try as plain JSON
        try:
            decoded = compressed_body.decode('utf-8')
            if decoded.strip().startswith(('{', '[')):
                logger.info("Payload parsed as plain JSON (fallback)")
                return compressed_body
        except UnicodeDecodeError:
            pass
        
        # If we get here, it's neither zstandard nor plain JSON
        logger.error(f"❌ Unable to determine payload format. Size: {len(compressed_body)}, Magic: {zstd_magic.hex()}, Content-Encoding: {content_encoding}")
        raise ValueError(f"Unable to decompress or parse payload. Content-Encoding: {content_encoding}, Magic bytes: {zstd_magic.hex()}")
    
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
        Temporarily: Only compare by data_type_id, ignore event_type
        """
        mapped_payload = payload.copy()
        
        # Process epoch data
        if "epochData" in str(payload):
            for data_item in payload.get("data", []):
                if "epochData" in data_item:
                    for epoch_entry in data_item["epochData"]:
                        data_type_id = epoch_entry.get("dataTypeId")
                        if data_type_id:
                            data_type_name = self.data_type_service.map_data_type_id_simple(
                                self.db, data_type_id
                            )
                            if data_type_name:
                                epoch_entry["dataTypeName"] = data_type_name
                            else:
                                logger.warning(f"Data type ID {data_type_id} not found")
        
        # Process daily data
        if "dailyData" in str(payload):
            for data_item in payload.get("data", []):
                if "dailyData" in data_item:
                    for daily_entry in data_item["dailyData"]:
                        data_type_id = daily_entry.get("dataTypeId")
                        if data_type_id:
                            data_type_name = self.data_type_service.map_data_type_id_simple(
                                self.db, data_type_id
                            )
                            if data_type_name:
                                daily_entry["dataTypeName"] = data_type_name
                            else:
                                logger.warning(f"Data type ID {data_type_id} not found")
        
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
    
    async def store_health_data(self, payload: Dict[str, Any], mapped_payload: Dict[str, Any]) -> None:
        """
        Store health data from Thryve webhook into health_records
        Maps end_user_id (Thryve access token) to internal user_id via Supabase
        """
        from app.crud.user import get_user_by_supabase_id
        from app.core.supabase_client import SupabaseService
        from app.models.user import User
        from app.models.health_record import HealthRecord, HealthRecordSection, HealthRecordMetric
        from app.models.health_metrics import HealthRecordMetricTemplate, HealthRecordSectionTemplate
        from app.schemas.health_record import HealthRecordCreate
        from app.crud.health_record import health_record_crud
        from datetime import datetime
        
        logger.info("Storing health data from Thryve webhook")
        end_user_id = payload.get("endUserId", "")
        
        if not end_user_id:
            logger.warning("No endUserId in payload, skipping storage")
            return
        
        # Get Supabase user_id from user_integrations table using thryve_access_token
        supabase_service = SupabaseService()
        
        try:
            # Query Supabase user_integrations to find user_id with matching thryve_access_token
            try:
                response = supabase_service.client.table("user_integrations").select("user_id").eq("thryve_access_token", end_user_id).execute()
                if response.data and len(response.data) > 0:
                    supabase_user_id = response.data[0].get("user_id")
                    if supabase_user_id:
                        user = get_user_by_supabase_id(self.db, supabase_user_id)
                    else:
                        user = None
                else:
                    user = None
            except Exception as e:
                logger.error(f"Error finding user by thryve_access_token: {e}")
                user = None
            
            if not user:
                logger.warning(f"User not found for Thryve end_user_id: {end_user_id}")
                return
            
            logger.info(f"Found user {user.id} for Thryve end_user_id: {end_user_id}")
            
            # Process data based on event type
            event_type = payload.get("type", "")
            data_items = payload.get("data", [])
            
            created_count = 0
            skipped_count = 0
            
            for data_item in data_items:
                # Process epoch data
                if "epochData" in data_item:
                    for epoch_entry in data_item.get("epochData", []):
                        result = self._create_health_record_from_epoch(
                            self.db, user.id, epoch_entry
                        )
                        if result:
                            created_count += 1
                        else:
                            skipped_count += 1
                
                # Process daily data
                if "dailyData" in data_item:
                    for daily_entry in data_item.get("dailyData", []):
                        result = self._create_health_record_from_daily(
                            self.db, user.id, daily_entry
                        )
                        if result:
                            created_count += 1
                        else:
                            skipped_count += 1
            
            logger.info(f"Created {created_count} health records, skipped {skipped_count} for user {user.id}")
            
        except Exception as e:
            logger.error(f"Error storing health data: {e}", exc_info=True)
    
    def _get_or_create_user_section(
        self, db: Session, user_id: int, section_template_id: int
    ) -> HealthRecordSection:
        """Get or create user's health record section from template"""
        from app.models.health_metrics import HealthRecordSectionTemplate
        
        # Check if user already has this section
        existing_section = db.query(HealthRecordSection).filter(
            and_(
                HealthRecordSection.section_template_id == section_template_id,
                HealthRecordSection.created_by == user_id
            )
        ).first()
        
        if existing_section:
            return existing_section
        
        # Get template
        template = db.query(HealthRecordSectionTemplate).filter(
            HealthRecordSectionTemplate.id == section_template_id
        ).first()
        
        if not template:
            raise ValueError(f"Section template {section_template_id} not found")
        
        # Create user section from template
        new_section = HealthRecordSection(
            name=template.name,
            display_name=template.display_name,
            description=template.description,
            source_language=template.source_language,
            health_record_type_id=template.health_record_type_id,
            section_template_id=template.id,
            is_default=False,  # User's active section
            created_by=user_id
        )
        
        db.add(new_section)
        db.commit()
        db.refresh(new_section)
        
        logger.info(f"Created user section {new_section.id} from template {section_template_id} for user {user_id}")
        return new_section
    
    def _get_or_create_user_metric(
        self, db: Session, user_id: int, section_id: int, metric_template_id: int
    ) -> HealthRecordMetric:
        """Get or create user's health record metric from template"""
        from app.models.health_metrics import HealthRecordMetricTemplate
        
        # Check if user already has this metric in this section
        existing_metric = db.query(HealthRecordMetric).filter(
            and_(
                HealthRecordMetric.metric_tmp_id == metric_template_id,
                HealthRecordMetric.section_id == section_id,
                HealthRecordMetric.created_by == user_id
            )
        ).first()
        
        if existing_metric:
            return existing_metric
        
        # Get template
        template = db.query(HealthRecordMetricTemplate).filter(
            HealthRecordMetricTemplate.id == metric_template_id
        ).first()
        
        if not template:
            raise ValueError(f"Metric template {metric_template_id} not found")
        
        # Create user metric from template
        new_metric = HealthRecordMetric(
            section_id=section_id,
            metric_tmp_id=template.id,
            name=template.name,
            display_name=template.display_name,
            description=template.description,
            default_unit=template.default_unit,
            source_language=template.source_language,
            reference_data=template.reference_data,
            data_type=template.data_type,
            is_default=False,  # User's active metric
            created_by=user_id
        )
        
        db.add(new_metric)
        db.commit()
        db.refresh(new_metric)
        
        logger.info(f"Created user metric {new_metric.id} from template {metric_template_id} for user {user_id}")
        return new_metric
    
    def _create_health_record_from_epoch(
        self, db: Session, user_id: int, epoch_entry: Dict[str, Any]
    ) -> bool:
        """Create health record from epoch data entry"""
        from app.schemas.health_record import HealthRecordCreate
        from app.crud.health_record import health_record_crud
        from app.models.thryve_data_type import ThryveDataType
        from datetime import datetime
        
        try:
            data_type_id = epoch_entry.get("dataTypeId")
            if not data_type_id:
                logger.warning("No dataTypeId in epoch entry")
                return False
            
            # Get ThryveDataType - temporarily only compare by data_type_id
            thryve_data_type = db.query(ThryveDataType).filter(
                ThryveDataType.data_type_id == data_type_id,
                ThryveDataType.is_active == True
            ).first()
            
            if not thryve_data_type:
                logger.warning(f"Thryve data type {data_type_id} not found")
                return False
            
            # Find metric template linked to this Thryve data type
            from app.models.health_metrics import HealthRecordMetricTemplate
            metric_template = db.query(HealthRecordMetricTemplate).filter(
                HealthRecordMetricTemplate.thryve_data_type_id == thryve_data_type.id,
                HealthRecordMetricTemplate.is_active == True
            ).first()
            
            if not metric_template:
                logger.warning(f"No metric template found for Thryve data type {data_type_id}")
                return False
            
            # Get or create user section
            section = self._get_or_create_user_section(
                db, user_id, metric_template.section_template_id
            )
            
            # Get or create user metric
            metric = self._get_or_create_user_metric(
                db, user_id, section.id, metric_template.id
            )
            
            # Parse timestamp
            start_timestamp = epoch_entry.get("startTimestamp")
            if not start_timestamp:
                logger.warning("No startTimestamp in epoch entry")
                return False
            
            # Convert milliseconds to datetime
            recorded_at = datetime.fromtimestamp(start_timestamp / 1000.0)
            
            # Parse value
            value = epoch_entry.get("value")
            if value is None:
                logger.warning("No value in epoch entry")
                return False
            
            # Convert to float if needed
            try:
                value_float = float(value)
            except (ValueError, TypeError):
                logger.warning(f"Invalid value format: {value}")
                return False
            
            # Create health record
            health_record_data = HealthRecordCreate(
                section_id=section.id,
                metric_id=metric.id,
                value=value_float,
                status="normal",  # Default status
                source="thryve",
                recorded_at=recorded_at
            )
            
            health_record, was_created = health_record_crud.create(
                db, health_record_data, user_id
            )
            
            if was_created:
                logger.info(f"Created health record {health_record.id} for metric {metric.id}")
            else:
                logger.info(f"Updated existing health record {health_record.id} for metric {metric.id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating health record from epoch entry: {e}", exc_info=True)
            return False
    
    def _create_health_record_from_daily(
        self, db: Session, user_id: int, daily_entry: Dict[str, Any]
    ) -> bool:
        """Create health record from daily data entry"""
        from app.schemas.health_record import HealthRecordCreate
        from app.crud.health_record import health_record_crud
        from app.models.thryve_data_type import ThryveDataType
        from datetime import datetime
        
        try:
            data_type_id = daily_entry.get("dataTypeId")
            if not data_type_id:
                logger.warning("No dataTypeId in daily entry")
                return False
            
            # Get ThryveDataType - temporarily only compare by data_type_id
            thryve_data_type = db.query(ThryveDataType).filter(
                ThryveDataType.data_type_id == data_type_id,
                ThryveDataType.is_active == True
            ).first()
            
            if not thryve_data_type:
                logger.warning(f"Thryve data type {data_type_id} not found")
                return False
            
            # Find metric template linked to this Thryve data type
            from app.models.health_metrics import HealthRecordMetricTemplate
            metric_template = db.query(HealthRecordMetricTemplate).filter(
                HealthRecordMetricTemplate.thryve_data_type_id == thryve_data_type.id,
                HealthRecordMetricTemplate.is_active == True
            ).first()
            
            if not metric_template:
                logger.warning(f"No metric template found for Thryve data type {data_type_id}")
                return False
            
            # Get or create user section
            section = self._get_or_create_user_section(
                db, user_id, metric_template.section_template_id
            )
            
            # Get or create user metric
            metric = self._get_or_create_user_metric(
                db, user_id, section.id, metric_template.id
            )
            
            # Parse day timestamp
            day_timestamp = daily_entry.get("day")
            if not day_timestamp:
                logger.warning("No day timestamp in daily entry")
                return False
            
            # Convert Unix timestamp to datetime (start of day)
            recorded_at = datetime.fromtimestamp(day_timestamp)
            
            # Parse value
            value = daily_entry.get("value")
            if value is None:
                logger.warning("No value in daily entry")
                return False
            
            # Convert to float if needed
            try:
                value_float = float(value)
            except (ValueError, TypeError):
                logger.warning(f"Invalid value format: {value}")
                return False
            
            # Create health record
            health_record_data = HealthRecordCreate(
                section_id=section.id,
                metric_id=metric.id,
                value=value_float,
                status="normal",  # Default status
                source="thryve",
                recorded_at=recorded_at
            )
            
            health_record, was_created = health_record_crud.create(
                db, health_record_data, user_id
            )
            
            if was_created:
                logger.info(f"Created health record {health_record.id} for metric {metric.id}")
            else:
                logger.info(f"Updated existing health record {health_record.id} for metric {metric.id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating health record from daily entry: {e}", exc_info=True)
            return False

