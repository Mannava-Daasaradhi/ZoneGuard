from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional
import re


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
    eshram_id: Optional[str] = None
    eshram_verified: bool = False
    eshram_income_verified: bool = False
    eshram_verified_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RiderKYC(BaseModel):
    upi_id: str
    phone: str


class RiderEShramKYC(BaseModel):
    """
    e-Shram portal KYC payload.

    eshram_id follows the UAN (Universal Account Number) format:
    UW-XXXXXXXXXX-X  (UW prefix + 10 digits + 1 check digit)
    Example: UW-1234567890-1

    Also accepts plain 12-digit UAN for backward compatibility with
    older e-Shram portal exports.
    """
    eshram_id: str
    declared_weekly_earnings: Optional[float] = None  # cross-checked against e-Shram work history

    @field_validator("eshram_id")
    @classmethod
    def validate_eshram_format(cls, v: str) -> str:
        # FIX: normalize FIRST, then validate.
        # The original code ran re.match on the raw value, so lowercase
        # inputs like "uw-1234567890-1" were rejected even though the
        # function returned v.strip().upper() at the end — by that point
        # the ValueError had already been raised.
        normalized = v.strip().upper()
        pattern = r"^(UW-\d{10}-\d|\d{12})$"
        if not re.fullmatch(pattern, normalized):
            raise ValueError(
                "Invalid e-Shram ID format. Expected UW-XXXXXXXXXX-X (e.g. UW-1234567890-1) "
                "or a plain 12-digit UAN."
            )
        return normalized


class EShramVerificationResponse(BaseModel):
    rider_id: str
    eshram_id: str
    eshram_verified: bool
    eshram_income_verified: bool
    income_match: Optional[str] = None   # "match" | "deviation_minor" | "deviation_major"
    income_deviation_pct: Optional[float] = None
    message: str
    verified_at: Optional[datetime] = None
