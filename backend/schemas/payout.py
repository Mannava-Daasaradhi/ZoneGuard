from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PayoutResponse(BaseModel):
    id: str
    claim_id: str
    rider_id: str
    amount: float
    upi_ref: str
    status: str
    retry_count: int = 0
    gateway_response: Optional[str]
    created_at: datetime
    settled_at: Optional[datetime]

    class Config:
        from_attributes = True
