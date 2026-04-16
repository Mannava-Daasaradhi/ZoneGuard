from pydantic import BaseModel
from typing import Optional


class ZoneResponse(BaseModel):
    id: str
    name: str
    pin_code: str
    lat: float
    lng: float
    risk_tier: str
    risk_score: int
    weekly_premium: int
    max_weekly_payout: int
    active_riders: int
    historical_disruptions: int
    zone_baselines: Optional[dict] = None

    class Config:
        from_attributes = True


class ZoneSignalStatus(BaseModel):
    zone_id: str
    zone_name: str
    s1_environmental: dict
    s2_mobility: dict
    s3_economic: dict
    s4_crowd: dict
    confidence: str
    signals_fired: int
    is_disrupted: bool
