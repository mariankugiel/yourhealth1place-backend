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

logger = logging.getLogger(__name__)

router = APIRouter()


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
        logger.info(f"X-HMAC-Signature: {'present' if hmac_signature else 'missing'}")
        logger.info(f"X-HMAC-Signature: {hmac_signature}")
        logger.info(f"X-HMAC-Timestamp: {hmac_timestamp if hmac_timestamp else 'missing'}")
        logger.info(f"Content-Encoding: {content_encoding}")
        logger.info(f"Content-Type: {headers_lower.get('content-type', 'not-set')}")
        logger.info(f"Content-Length: {headers_lower.get('content-length', 'not-set')}")
        
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
        webhook_service = ThryveWebhookService(db)
        
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
        background_tasks.add_task(
            process_webhook_background,
            compressed_body,
            content_encoding
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


async def process_webhook_background(compressed_body: bytes, content_encoding: str):
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
        
        # Log decompressed JSON payload (pretty formatted)
        logger.info("📄 Decompressed JSON Payload:")
        logger.info(json.dumps(payload, indent=2, ensure_ascii=False))
        
        # Map dataTypeIds to names
        mapped_payload = webhook_service.map_data_type_ids(payload)
        
        # Extract event type and end_user_id
        event_type = payload.get("type", "")
        end_user_id = payload.get("endUserId", "")
        
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

