from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.services.thryve_data_source_service import ThryveDataSourceService
from app.services.thryve_integration_service import ThryveIntegrationService
from app.schemas.thryve_integration import (
    ThryveDataSourceResponse,
    ThryveConnectionRequest,
    ThryveConnectionResponse,
    ThryveIntegrationStatus
)
from app.api.v1.endpoints.auth import get_user_id_from_token
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User does not have Thryve access token. Please connect a data source first."
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
    current_user_id: str = Depends(get_user_id_from_token),
    db: Session = Depends(get_db)
):
    """Initiate connection to a Thryve data source"""
    return await get_connection_url(
        data_source_id=request.data_source_id,
        redirect_uri=request.redirect_uri,
        current_user_id=current_user_id,
        db=db
    )


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


@router.get("/thryve/status", response_model=List[ThryveIntegrationStatus])
async def get_integration_status(
    current_user_id: str = Depends(get_user_id_from_token)
):
    """Get user's Thryve integration status"""
    # TODO: Implement status retrieval from Supabase or Thryve API
    # For now, return empty list
    return []

