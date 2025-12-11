from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.thryve_webhook_service import ThryveWebhookService
from app.schemas.thryve_webhook import ThryveWebhookResponse
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/thryve/data-push", response_model=ThryveWebhookResponse, status_code=status.HTTP_200_OK)
async def thryve_data_push_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Thryve data push webhook endpoint
    Receives Zstandard compressed binary payloads
    """
    if not settings.THRYVE_WEBHOOK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Thryve webhook is disabled"
        )
    
    try:
        # Log request headers for debugging
        content_type = request.headers.get("content-type", "not-set")
        content_length = request.headers.get("content-length", "not-set")
        logger.info(f"Thryve webhook received - Content-Type: {content_type}, Content-Length: {content_length}")
        
        # Read compressed binary body
        compressed_body = await request.body()
        
        if not compressed_body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty request body"
            )
        
        logger.info(f"Received body size: {len(compressed_body)} bytes")
        
        # Initialize webhook service
        webhook_service = ThryveWebhookService(db)
        
        # Decompress payload (with fallback to plain JSON)
        decompressed = webhook_service.decompress_payload(compressed_body)
        
        # Parse JSON
        payload = webhook_service.parse_payload(decompressed)
        
        # Map dataTypeIds to names
        mapped_payload = webhook_service.map_data_type_ids(payload)
        
        # Extract event type and end_user_id
        event_type = payload.get("type", "")
        end_user_id = payload.get("endUserId", "")
        
        # Validate event type
        valid_event_types = [
            "event.data.epoch.create",
            "event.data.daily.update",
            "event.data.daily.create"
        ]
        if event_type not in valid_event_types:
            logger.warning(f"Unknown event type: {event_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown event type: {event_type}"
            )
        
        # Calculate total data points count
        processed_count = 0
        for data_item in payload.get("data", []):
            if "epochData" in data_item:
                processed_count += len(data_item.get("epochData", []))
            if "dailyData" in data_item:
                processed_count += len(data_item.get("dailyData", []))
        
        # Store health data (this handles all processing and record creation)
        await webhook_service.store_health_data(payload, mapped_payload)
        
        logger.info(f"Successfully processed {event_type} for end_user_id: {end_user_id}, count: {processed_count}")
        
        return ThryveWebhookResponse(
            status="success",
            message=f"Processed {event_type}",
            processed_count=processed_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Thryve webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )

