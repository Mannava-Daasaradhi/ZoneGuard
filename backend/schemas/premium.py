from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional


class PremiumPaymentCreate(BaseModel):
    """Schema for creating a new premium payment record."""
    rider_id: str
    policy_id: str
    amount: float = Field(..., gt=0, description="Premium amount in INR")
    week_start: date
    week_end: date
    status: str = Field(default="paid", pattern="^(pending|paid|failed)$")
    payment_method: str = Field(default="UPI")
    transaction_ref: Optional[str] = None


class PremiumPaymentResponse(BaseModel):
    """Schema for premium payment response."""
    id: str
    rider_id: str
    policy_id: str
    amount: float
    week_start: date
    week_end: date
    status: str
    payment_method: str
    transaction_ref: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PremiumStatsResponse(BaseModel):
    """Schema for rider premium statistics."""
    rider_id: str
    total_paid: float = Field(..., description="Total premium amount paid by rider")
    total_payouts: float = Field(..., description="Total payout amount received by rider")
    net_benefit: float = Field(..., description="Net benefit (payouts - premiums)")
    coverage_weeks: int = Field(..., description="Number of weeks with coverage")
    payment_count: int = Field(..., description="Number of premium payments made")
