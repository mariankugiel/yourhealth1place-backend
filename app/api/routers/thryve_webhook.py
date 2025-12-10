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
        # Read compressed binary body
        compressed_body = await request.body()
        
        if not compressed_body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty request body"
            )
        
        # Initialize webhook service
        webhook_service = ThryveWebhookService(db)
        
        # Decompress payload
        decompressed = webhook_service.decompress_payload(compressed_body)
        
        # Parse JSON
        payload = webhook_service.parse_payload(decompressed)
        
        # Map dataTypeIds to names
        mapped_payload = webhook_service.map_data_type_ids(payload)
        
        # Extract event type and end_user_id
        event_type = payload.get("type", "")
        end_user_id = payload.get("endUserId", "")
        
        # Process based on event type
        processed_count = 0
        if event_type == "event.data.epoch.create":
            for data_item in payload.get("data", []):
                result = webhook_service.process_epoch_create(data_item, end_user_id)
                processed_count += len(data_item.get("epochData", []))
        elif event_type == "event.data.daily.update":
            for data_item in payload.get("data", []):
                result = webhook_service.process_daily_update(data_item, end_user_id)
                processed_count += len(data_item.get("dailyData", []))
        elif event_type == "event.data.daily.create":
            for data_item in payload.get("data", []):
                result = webhook_service.process_daily_create(data_item, end_user_id)
                processed_count += len(data_item.get("dailyData", []))
        else:
            logger.warning(f"Unknown event type: {event_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown event type: {event_type}"
            )
        
        # Store health data
        webhook_service.store_health_data(payload, mapped_payload)
        
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

