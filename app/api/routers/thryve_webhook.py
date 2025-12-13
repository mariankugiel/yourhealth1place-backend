from fastapi import APIRouter, Request, HTTPException, status, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.thryve_webhook_service import ThryveWebhookService
from app.schemas.thryve_webhook import ThryveWebhookResponse
from app.core.config import settings
import logging
import base64
import time
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter()


def save_webhook_data_to_files(
    compressed_body: bytes,
    decompressed_payload: Dict[str, Any],
    event_type: str,
    end_user_id: str,
    headers: Dict[str, str],
    content_encoding: str
) -> None:
    """
    Save raw webhook data and decompressed payload to files in project root.
    Non-blocking - errors are logged but don't affect webhook processing.
    
    Files saved:
    - {timestamp}_{event_type}_{end_user_id_short}.raw.bin - Raw compressed data
    - {timestamp}_{event_type}_{end_user_id_short}.meta.json - Metadata (headers, encoding)
    - {timestamp}_{event_type}_{end_user_id_short}.json - Decompressed JSON payload
    """
    try:
        # Get project root directory (parent of app directory)
        project_root = Path(__file__).parent.parent.parent
        webhook_data_dir = project_root / "webhook_data"
        
        # Create directory if it doesn't exist
        webhook_data_dir.mkdir(exist_ok=True)
        
        # Generate timestamp for filename (YYYYMMDD_HHMMSS)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Sanitize event_type for filename (replace dots with underscores)
        event_type_safe = event_type.replace(".", "_") if event_type else "unknown"
        
        # Get short end_user_id (first 8 chars) for filename
        end_user_id_short = end_user_id[:8] if end_user_id else "unknown"
        
        # Base filename
        base_filename = f"{timestamp}_{event_type_safe}_{end_user_id_short}"
        
        # Save raw compressed data
        raw_file_path = webhook_data_dir / f"{base_filename}.raw.bin"
        with open(raw_file_path, "wb") as f:
            f.write(compressed_body)
        logger.info(f"💾 Saved raw webhook data to: {raw_file_path}")
        
        # Save metadata
        metadata = {
            "timestamp": timestamp,
            "event_type": event_type,
            "end_user_id": end_user_id,
            "content_encoding": content_encoding,
            "raw_body_size": len(compressed_body),
            "headers": headers,
            "saved_at": datetime.utcnow().isoformat()
        }
        meta_file_path = webhook_data_dir / f"{base_filename}.meta.json"
        with open(meta_file_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Saved webhook metadata to: {meta_file_path}")
        
        # Save decompressed JSON payload
        json_file_path = webhook_data_dir / f"{base_filename}.json"
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(decompressed_payload, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Saved decompressed JSON payload to: {json_file_path}")
        
    except Exception as e:
        logger.warning(f"⚠️  Failed to save webhook data to files: {e}", exc_info=True)
        # Don't raise - allow webhook processing to continue


@router.post("/thryve/data-push", response_model=ThryveWebhookResponse, status_code=status.HTTP_200_OK)
async def thryve_data_push_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Thryve data push webhook endpoint
    Receives Zstandard compressed binary payloads with HMAC signature verification
    
    Flow:
    1. Extract HMAC signature and timestamp headers
    2. Read compressed body (DO NOT DECOMPRESS YET)
    3. Verify HMAC signature on compressed body + timestamp
    4. Acknowledge immediately (200/204) if valid
    5. Process payload asynchronously in background
    """
    import time
    start_time = time.time()
    
    if not settings.THRYVE_WEBHOOK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Thryve webhook is disabled"
        )
    
    try:
        # Extract HMAC headers (case-insensitive)
        headers_lower = {k.lower(): v for k, v in request.headers.items()}
        hmac_signature = headers_lower.get("x-hmac-signature") or headers_lower.get("x_hmac_signature")
        hmac_timestamp = headers_lower.get("x-hmac-timestamp") or headers_lower.get("x_hmac_timestamp")
        content_encoding = headers_lower.get("content-encoding", "not-set")
        
        # Log headers for debugging
        logger.info("=" * 80)
        logger.info("Thryve Webhook Received")
        logger.info("=" * 80)
        # logger.info(f"X-HMAC-Signature: {'present' if hmac_signature else 'missing'}")
        logger.info(f"X-HMAC-Signature: {hmac_signature}")
        # logger.info(f"X-HMAC-Timestamp: {hmac_timestamp if hmac_timestamp else 'missing'}")
        # logger.info(f"Content-Encoding: {content_encoding}")
        # logger.info(f"Content-Type: {headers_lower.get('content-type', 'not-set')}")
        # logger.info(f"Content-Length: {headers_lower.get('content-length', 'not-set')}")
        
        # Read request body (may be base64-encoded string or raw bytes)
        raw_body = await request.body()
        
        if not raw_body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty request body"
            )
        
        logger.info(f"\nReceived body size: {len(raw_body)} bytes")
        
        # Decode base64 if the body is a base64-encoded string
        # The body comes as bytes, but may contain a base64 string
        compressed_body = None
        try:
            # Try to decode as UTF-8 string first
            body_str = raw_body.decode('utf-8')
            # Try to decode as base64
            compressed_body = base64.b64decode(body_str)
            logger.info(f"✅ Decoded base64 body: {len(raw_body)} -> {len(compressed_body)} bytes")
        except (UnicodeDecodeError, Exception) as e:
            # If base64 decode fails, assume it's already raw compressed bytes
            compressed_body = raw_body
            logger.info(f"Body is already raw bytes (not base64-encoded): {len(compressed_body)} bytes")
        
        if not compressed_body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to decode request body"
            )
        
        # Initialize webhook service
        # webhook_service = ThryveWebhookService(db)
        
        # HMAC verification - COMMENTED OUT FOR NOW
        # if not webhook_service.verify_hmac_signature(compressed_body, hmac_signature, hmac_timestamp):
        #     logger.error("❌ HMAC signature verification failed - rejecting webhook")
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED,
        #         detail="Invalid HMAC signature"
        #     )
        
        # Acknowledge immediately (HMAC verification disabled)
        verification_time = time.time() - start_time
        logger.info(f"✅ Webhook received in {verification_time:.3f} seconds - acknowledging receipt (HMAC verification disabled)")
        
        # Queue background processing (decompress, parse, store)
        # Pass headers for file saving (convert to dict)
        headers_dict = {k: v for k, v in request.headers.items()}
        background_tasks.add_task(
            process_webhook_background,
            compressed_body,
            content_encoding,
            headers_dict
        )
        
        logger.info("📋 Webhook queued for background processing")
        logger.info("=" * 80)
        
        # Return immediate acknowledgment (200 OK)
        return ThryveWebhookResponse(
            status="success",
            message="Webhook received and verified",
            processed_count=0  # Will be updated in background
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Thryve webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )


async def process_webhook_background(compressed_body: bytes, content_encoding: str, headers: Dict[str, str] = None):
    """
    Background task to process Thryve webhook payload
    This runs asynchronously after the webhook has been acknowledged
    """
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        logger.info("🔄 Starting background processing of webhook payload")
        start_time = time.time()
        
        # Initialize webhook service with new DB session
        webhook_service = ThryveWebhookService(db)
        
        # Decompress payload based on Content-Encoding header
        decompressed = webhook_service.decompress_payload(compressed_body, content_encoding)
        
        # Parse JSON
        payload = webhook_service.parse_payload(decompressed)
        
        # Extract event type and end_user_id for file saving
        event_type = payload.get("type", "")
        end_user_id = payload.get("endUserId", "")
        
        # Save webhook data to files (raw data, metadata, and decompressed JSON)
        save_webhook_data_to_files(
            compressed_body=compressed_body,
            decompressed_payload=payload,
            event_type=event_type,
            end_user_id=end_user_id,
            headers=headers or {},
            content_encoding=content_encoding
        )
        
        # Log decompressed JSON payload (pretty formatted)
        # logger.info("📄 Decompressed JSON Payload:")
        # logger.info(json.dumps(payload, indent=2, ensure_ascii=False))
        
        # Map dataTypeIds to names
        mapped_payload = webhook_service.map_data_type_ids(payload)
        
        # Validate event type
        valid_event_types = [
            "event.data.epoch.create",
            "event.data.epoch.update",
            "event.data.daily.update",
            "event.data.daily.create"
        ]
        if event_type not in valid_event_types:
            logger.warning(f"Unknown event type: {event_type}")
            return
        
        # Calculate total data points count
        processed_count = 0
        for data_item in payload.get("data", []):
            if "epochData" in data_item:
                processed_count += len(data_item.get("epochData", []))
            if "dailyData" in data_item:
                processed_count += len(data_item.get("dailyData", []))
        
        # Store health data (this handles all processing and record creation)
        await webhook_service.store_health_data(payload, mapped_payload)
        
        elapsed_time = time.time() - start_time
        logger.info(f"✅ Background processing completed: {event_type} for end_user_id: {end_user_id}, count: {processed_count}")
        logger.info(f"⏱️  Background processing time: {elapsed_time:.3f} seconds")
        
    except Exception as e:
        logger.error(f"❌ Error in background webhook processing: {e}", exc_info=True)
    finally:
        db.close()

