from pydantic import BaseModel
from typing import Optional, List


class ThryveDataSourceResponse(BaseModel):
    id: int
    name: str
    data_source_type: str
    retrieval_method: str
    historic_data: bool
    shared_oauth_client: str


class ThryveConnectionRequest(BaseModel):
    data_source_id: int
    redirect_uri: Optional[str] = None


class ThryveConnectionResponse(BaseModel):
    url: str
    connection_session_token: str


class ThryveIntegrationStatus(BaseModel):
    data_source_id: int
    data_source_name: str
    connected: bool
    connected_at: Optional[str] = None

