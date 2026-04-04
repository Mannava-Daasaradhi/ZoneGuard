from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class RiderRegister(BaseModel):
    rider_id: str
    name: str
    phone: Optional[str] = None
    zone_id: str
    weekly_earnings: float
    upi_id: Optional[str] = None


class RiderResponse(BaseModel):
    id: str
    name: str
    phone: Optional[str]
    zone_id: str
    weekly_earnings_baseline: float
    tenure_weeks: int
    kyc_verified: bool
    upi_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class RiderKYC(BaseModel):
    upi_id: str
    phone: str
