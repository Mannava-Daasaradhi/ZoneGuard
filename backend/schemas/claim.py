from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ClaimResponse(BaseModel):
    id: str
    rider_id: str
    policy_id: str
    zone_id: str
    disruption_event_id: str
    status: str
    confidence: str
    recommended_payout: float
    actual_payout: Optional[float]
    exclusion_check: dict
    fraud_score: Optional[float]
    created_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]

    class Config:
        from_attributes = True


class ClaimReview(BaseModel):
    action: str  # "approve" or "reject"
    reviewed_by: str = "admin"
