from fastapi import APIRouter, HTTPException, status, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.services.thryve_data_source_service import ThryveDataSourceService
from app.services.thryve_integration_service import ThryveIntegrationService
from app.services.thryve_webhook_service import ThryveWebhookService
from app.schemas.thryve_integration import (
    ThryveDataSourceResponse,
    ThryveConnectionRequest,
    ThryveConnectionResponse,
    ThryveIntegrationStatus,
    ThryveSyncRequest,
    ThryveSyncResponse
)
from app.api.v1.endpoints.auth import get_user_id_from_token
from app.crud.user import get_user_by_supabase_id
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/thryve/data-sources", response_model=List[ThryveDataSourceResponse])
async def get_thryve_data_sources(db: Session = Depends(get_db)):
    """Get all available Thryve data sources"""
    try:
        service = ThryveDataSourceService()
        data_sources = service.get_all(db)
        return [
            ThryveDataSourceResponse(
                id=ds.id,
                name=ds.name,
                data_source_type=ds.data_source_type,
                retrieval_method=ds.retrieval_method,
                historic_data=ds.historic_data,
                shared_oauth_client=ds.shared_oauth_client
            )
            for ds in data_sources
        ]
    except Exception as e:
        logger.error(f"Error getting Thryve data sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get data sources"
        )


@router.get("/thryve/connection-url", response_model=ThryveConnectionResponse)
async def get_connection_url(
    data_source_id: int = Query(..., description="Thryve data source ID"),
    redirect_uri: Optional[str] = Query(None, description="Redirect URI after connection"),
    current_user_id: str = Depends(get_user_id_from_token),
    db: Session = Depends(get_db)
):
    """Get connection URL for a Thryve data source"""
    try:
        integration_service = ThryveIntegrationService()
        
        # Get or create access token
        access_token = await integration_service.get_user_access_token(current_user_id)
        if not access_token:
            # Need to get access token first - use partner_user_id (can be user_id or email)
            # For now, using user_id as partner_user_id
            access_token = integration_service.get_access_token(current_user_id)
            await integration_service.save_access_token(current_user_id, access_token)
        
        # Get connection session token
        connection_session_token = integration_service.get_connection_session_token(
            access_token, locale="en"
        )
        
        # Build connection URL
        if not redirect_uri:
            redirect_uri = f"{integration_service.service_base_url}/dataSourceDirectConnectionResult.html"
        
        connection_url = integration_service.build_connection_url(
            connection_session_token, data_source_id, redirect_uri
        )
        
        return ThryveConnectionResponse(
            url=connection_url,
            connection_session_token=connection_session_token
        )
    except Exception as e:
        logger.error(f"Error getting connection URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get connection URL: {str(e)}"
        )


@router.get("/thryve/disconnection-url", response_model=ThryveConnectionResponse)
async def get_disconnection_url(
    data_source_id: int = Query(..., description="Thryve data source ID"),
    redirect_uri: Optional[str] = Query(None, description="Redirect URI after disconnection"),
    current_user_id: str = Depends(get_user_id_from_token),
    db: Session = Depends(get_db)
):
    """Get disconnection URL for a Thryve data source"""
    try:
        integration_service = ThryveIntegrationService()
        
        # Get access token
        access_token = await integration_service.get_user_access_token(current_user_id)
        if not access_token:
            # No access token means integration is not actually connected
            # Remove the integration from user_integrations instead of raising an error
            logger.info(f"No Thryve access token found for user {current_user_id}. Removing integration for data source {data_source_id}.")
            
            # Map data source ID to field name
            data_source_to_field = {
                1: "fitbit",
                2: "garmin",
                3: "polar",
                8: "withings",
                11: "strava",
                16: "omron_connect",
                17: "suunto",
                18: "oura",
                27: "beurer",
                38: "huawei_health",
            }
            
            field_name = data_source_to_field.get(data_source_id)
            if field_name:
                # Remove the integration by setting it to False
                from app.core.supabase_client import SupabaseService
                supabase_service = SupabaseService()
                await supabase_service.update_user_integrations(
                    user_id=current_user_id,
                    integrations={field_name: False}
                )
                logger.info(f"Removed {field_name} integration for user {current_user_id}")
            
            # Return a dummy response that indicates the integration was removed
            # The frontend will handle this by updating the UI
            if not redirect_uri:
                redirect_uri = f"{integration_service.service_base_url}/dataSourceDirectConnectionResult.html"
            
            # Return a response that indicates success (integration removed)
            return ThryveConnectionResponse(
                url=redirect_uri + "?dataSource=" + str(data_source_id) + "&connected=false",
                connection_session_token=""
            )
        
        # Get connection session token
        connection_session_token = integration_service.get_connection_session_token(
            access_token, locale="en"
        )
        
        # Build disconnection URL
        if not redirect_uri:
            redirect_uri = f"{integration_service.service_base_url}/dataSourceDirectConnectionResult.html"
        
        disconnection_url = integration_service.build_disconnection_url(
            connection_session_token, data_source_id, redirect_uri
        )
        
        return ThryveConnectionResponse(
            url=disconnection_url,
            connection_session_token=connection_session_token
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting disconnection URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get disconnection URL: {str(e)}"
        )


@router.post("/thryve/connect", response_model=ThryveConnectionResponse)
async def connect_data_source(
    request: ThryveConnectionRequest,
    background_tasks: BackgroundTasks,
    current_user_id: str = Depends(get_user_id_from_token),
    db: Session = Depends(get_db)
):
    """Initiate connection to a Thryve data source and trigger background sync"""
    # Get connection URL
    connection_response = await get_connection_url(
        data_source_id=request.data_source_id,
        redirect_uri=request.redirect_uri,
        current_user_id=current_user_id,
        db=db
    )
    
    # Trigger background sync after successful connection
    # Note: This will run after the response is returned
    try:
        integration_service = ThryveIntegrationService()
        access_token = await integration_service.get_user_access_token(current_user_id)
        
        if access_token:
            # Get internal user ID from Supabase user ID
            user = get_user_by_supabase_id(db, current_user_id)
            if user:
                # Add background task to sync data
                background_tasks.add_task(
                    sync_health_data_background,
                    user_id=user.id,
                    access_token=access_token,
                    data_source_id=request.data_source_id,
                    days_back=30
                )
                logger.info(f"Added background sync task for user {user.id}, data source {request.data_source_id}")
    except Exception as e:
        # Don't fail the connection if sync setup fails
        logger.warning(f"Failed to setup background sync: {e}")
    
    return connection_response


async def sync_health_data_background(
    user_id: int,
    access_token: str,
    data_source_id: int,
    days_back: int = 30
):
    """Background task to sync health data from Thryve"""
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        webhook_service = ThryveWebhookService(db)
        result = webhook_service.sync_health_data_from_thryve(
            db=db,
            user_id=user_id,
            access_token=access_token,
            data_source_id=data_source_id,
            days_back=days_back
        )
        logger.info(f"Background sync completed for user {user_id}: {result}")
    except Exception as e:
        logger.error(f"Error in background sync task: {e}", exc_info=True)
    finally:
        db.close()


@router.post("/thryve/disconnect", response_model=ThryveConnectionResponse)
async def disconnect_data_source(
    request: ThryveConnectionRequest,
    current_user_id: str = Depends(get_user_id_from_token),
    db: Session = Depends(get_db)
):
    """Initiate disconnection from a Thryve data source"""
    return await get_disconnection_url(
        data_source_id=request.data_source_id,
        redirect_uri=request.redirect_uri,
        current_user_id=current_user_id,
        db=db
    )


@router.post("/thryve/sync-data", response_model=ThryveSyncResponse)
async def sync_health_data(
    request: ThryveSyncRequest,
    current_user_id: str = Depends(get_user_id_from_token),
    db: Session = Depends(get_db)
):
    """Sync health data from Thryve API for a specific data source"""
    try:
        integration_service = ThryveIntegrationService()
        
        # Get access token
        access_token = await integration_service.get_user_access_token(current_user_id)
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User does not have Thryve access token. Please connect a data source first."
            )
        
        # Get internal user ID from Supabase user ID
        user = get_user_by_supabase_id(db, current_user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Sync health data
        webhook_service = ThryveWebhookService(db)
        result = webhook_service.sync_health_data_from_thryve(
            db=db,
            user_id=user.id,
            access_token=access_token,
            data_source_id=request.data_source_id,
            days_back=request.days_back or 30
        )
        
        return ThryveSyncResponse(
            success=result.get("success", False),
            records_created=result.get("records_created", 0),
            records_updated=result.get("records_updated", 0),
            records_skipped=result.get("records_skipped", 0),
            errors=result.get("errors", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing health data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync health data: {str(e)}"
        )


@router.get("/thryve/status", response_model=List[ThryveIntegrationStatus])
async def get_integration_status(
    current_user_id: str = Depends(get_user_id_from_token)
):
    """Get user's Thryve integration status"""
    # TODO: Implement status retrieval from Supabase or Thryve API
    # For now, return empty list
    return []

