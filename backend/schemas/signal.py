from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SignalReadingResponse(BaseModel):
    id: str
    zone_id: str
    signal_type: str
    value: float
    threshold: float
    is_breached: int
    raw_data: dict
    recorded_at: datetime

    class Config:
        from_attributes = True


class DisruptionEventResponse(BaseModel):
    id: str
    zone_id: str
    confidence: str
    signals_fired: int
    signal_details: dict
    started_at: datetime
    ended_at: Optional[datetime]
    is_active: int
    source: str

    class Config:
        from_attributes = True
