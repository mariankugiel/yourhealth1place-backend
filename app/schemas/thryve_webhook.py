from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union


class ThryveEpochDataEntry(BaseModel):
    startTimestamp: Optional[int] = None
    endTimestamp: Optional[int] = None
    timezoneOffset: int
    dataTypeId: int
    dataTypeName: Optional[str] = None  # Mapped name
    value: Union[str, float, int, bool]


class ThryveDailyDataEntry(BaseModel):
    day: int
    timezoneOffset: int
    dataTypeId: int
    dataTypeName: Optional[str] = None  # Mapped name
    value: Union[str, float, int, bool]


class ThryveDataSourceData(BaseModel):
    dataSourceId: int
    dataSourceName: str
    epochData: Optional[List[ThryveEpochDataEntry]] = None
    dailyData: Optional[List[ThryveDailyDataEntry]] = None


class ThryveWebhookPayload(BaseModel):
    endUserId: str
    timestampType: str
    type: str  # event.data.epoch.create, event.data.daily.update, event.data.daily.create
    data: List[ThryveDataSourceData]


class ThryveWebhookResponse(BaseModel):
    status: str
    message: str
    processed_count: Optional[int] = None

