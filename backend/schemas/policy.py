from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PolicyCreate(BaseModel):
    rider_id: str
    zone_id: str
    is_forward_locked: bool = False
    forward_lock_weeks: int = 0


class PolicyResponse(BaseModel):
    id: str
    rider_id: str
    zone_id: str
    status: str
    weekly_premium: float
    max_payout: float
    coverage_start: datetime
    coverage_end: datetime
    is_forward_locked: bool
    forward_lock_weeks: int
    created_at: datetime
    exclusions: list[dict] = []

    class Config:
        from_attributes = True


class ExclusionResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    check_phase: str

    class Config:
        from_attributes = True
