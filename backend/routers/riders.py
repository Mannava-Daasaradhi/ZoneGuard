from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.database import get_db
from models.rider import Rider
from models.zone import Zone
from schemas.rider import (
    RiderRegister,
    RiderResponse,
    RiderKYC,
    RiderEShramKYC,
    EShramVerificationResponse,
)
from ml.zone_risk_scorer import calculate_zone_premium
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/riders", tags=["riders"])


@router.post("/register")
async def register_rider(payload: RiderRegister, db: AsyncSession = Depends(get_db)):
    """Register a new rider and return premium quote."""

    zone = await db.get(Zone, payload.zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    existing = await db.get(Rider, payload.rider_id)
    if existing:
        raise HTTPException(status_code=409, detail="Rider already registered")

    rider = Rider(
        id=payload.rider_id,
        name=payload.name,
        phone=payload.phone,
        zone_id=payload.zone_id,
        weekly_earnings_baseline=payload.weekly_earnings,
        upi_id=payload.upi_id,
    )
    db.add(rider)

    zone.active_riders = (zone.active_riders or 0) + 1
    await db.commit()
    await db.refresh(rider)

    premium_quote = calculate_zone_premium(
        {
            "historical_disruptions": zone.historical_disruptions,
            "risk_tier": zone.risk_tier,
            "active_riders": zone.active_riders,
        },
        rider_tenure_weeks=0,
    )

    return {
        "rider": RiderResponse.model_validate(rider),
        "premium_quote": premium_quote,
    }


@router.get("/{rider_id}")
async def get_rider(rider_id: str, db: AsyncSession = Depends(get_db)):
    rider = await db.get(Rider, rider_id)
    if not rider:
        raise HTTPException(status_code=404, detail="Rider not found")
    return RiderResponse.model_validate(rider)


@router.post("/{rider_id}/kyc")
async def update_kyc(rider_id: str, payload: RiderKYC, db: AsyncSession = Depends(get_db)):
    """Basic UPI + phone KYC (Phase 2)."""
    rider = await db.get(Rider, rider_id)
    if not rider:
        raise HTTPException(status_code=404, detail="Rider not found")

    rider.upi_id = payload.upi_id
    rider.phone = payload.phone
    rider.kyc_verified = True
    await db.commit()

    return {"status": "kyc_verified", "rider_id": rider_id}


@router.post("/{rider_id}/eshram-kyc", response_model=EShramVerificationResponse)
async def eshram_kyc(
    rider_id: str,
    payload: RiderEShramKYC,
    db: AsyncSession = Depends(get_db),
):
    """
    e-Shram portal KYC integration (Phase 3).

    Verifies the rider's e-Shram UAN against the portal and optionally
    cross-checks their declared weekly earnings against work history.

    In production this calls the e-Shram portal REST API
    (https://eshram.gov.in/api/v1/worker/verify).
    For the hackathon sandbox, we simulate the verification response.

    Verification outcomes:
    - eshram_verified = True  → identity confirmed, deduplication passed
    - eshram_income_verified  → declared earnings within 20% of portal records
    - income_match            → "match" | "deviation_minor" | "deviation_major"
    """
    rider = await db.get(Rider, rider_id)
    if not rider:
        raise HTTPException(status_code=404, detail="Rider not found")

    # --- Deduplication check: another rider already using this e-Shram ID ---
    existing = await db.execute(
        select(Rider).where(
            Rider.eshram_id == payload.eshram_id,
            Rider.id != rider_id,
        )
    )
    if existing.scalars().first():
        raise HTTPException(
            status_code=409,
            detail=f"e-Shram ID {payload.eshram_id} is already linked to another rider account.",
        )

    # --- Simulate e-Shram portal API call ---
    verification_result = await _call_eshram_portal(
        eshram_id=payload.eshram_id,
        rider_id=rider_id,
        declared_earnings=payload.declared_weekly_earnings,
        stored_earnings_baseline=rider.weekly_earnings_baseline,
    )

    # --- Update rider record ---
    now = datetime.now(timezone.utc)
    rider.eshram_id = payload.eshram_id
    rider.eshram_verified = verification_result["verified"]
    rider.eshram_income_verified = verification_result["income_verified"]
    rider.eshram_verified_at = now if verification_result["verified"] else None

    # Elevate kyc_verified to True once e-Shram is confirmed
    if verification_result["verified"]:
        rider.kyc_verified = True

    await db.commit()

    logger.info(
        f"[e-Shram KYC] rider={rider_id} eshram_id={payload.eshram_id} "
        f"verified={verification_result['verified']} "
        f"income_verified={verification_result['income_verified']}"
    )

    return EShramVerificationResponse(
        rider_id=rider_id,
        eshram_id=payload.eshram_id,
        eshram_verified=verification_result["verified"],
        eshram_income_verified=verification_result["income_verified"],
        income_match=verification_result.get("income_match"),
        income_deviation_pct=verification_result.get("income_deviation_pct"),
        message=verification_result["message"],
        verified_at=now if verification_result["verified"] else None,
    )


# ---------------------------------------------------------------------------
# e-Shram portal simulation
# ---------------------------------------------------------------------------

async def _call_eshram_portal(
    eshram_id: str,
    rider_id: str,
    declared_earnings: float | None,
    stored_earnings_baseline: float,
) -> dict:
    """
    Simulate the e-Shram portal verification API.

    Production endpoint: POST https://eshram.gov.in/api/v1/worker/verify
    Required headers: X-API-Key, X-Requester-ID (IRDAI partner ID)

    The portal returns:
    {
        "uan": str,
        "name": str,
        "mobile_verified": bool,
        "occupation_code": str,
        "weekly_income_band": str,   # e.g. "₹10,000–₹15,000"
        "state": str,
        "registered_at": ISO datetime
    }

    For the sandbox, we derive a simulated response deterministically
    from the rider_id so demos are reproducible.
    """
    # Deterministic "portal" response based on rider_id hash
    seed = sum(ord(c) for c in rider_id)

    # Simulate portal income band (₹/week) from rider's stored baseline
    # Portal returns a ±30% range around the stored baseline
    portal_weekly_income = stored_earnings_baseline * (0.85 + (seed % 30) / 100)

    income_match = "match"
    income_deviation_pct = None
    income_verified = False

    if declared_earnings is not None:
        deviation = abs(declared_earnings - portal_weekly_income) / max(portal_weekly_income, 1)
        income_deviation_pct = round(deviation * 100, 1)

        if deviation <= 0.20:
            income_match = "match"
            income_verified = True
        elif deviation <= 0.40:
            income_match = "deviation_minor"
            income_verified = False  # requires manual review
        else:
            income_match = "deviation_major"
            income_verified = False
    else:
        # No earnings declared — skip income check
        income_verified = False
        income_match = None

    message_parts = [f"e-Shram ID {eshram_id} verified successfully."]
    if income_match == "match":
        message_parts.append("Declared earnings match portal records. Income baseline confirmed.")
    elif income_match == "deviation_minor":
        message_parts.append(
            f"Earnings deviation {income_deviation_pct}% (< 40%) — flagged for manual review. "
            f"Coverage proceeds with declared baseline."
        )
    elif income_match == "deviation_major":
        message_parts.append(
            f"Earnings deviation {income_deviation_pct}% exceeds 40% — income not verified. "
            f"Coverage proceeds with conservative declared baseline; manual review required."
        )
    else:
        message_parts.append("Income check skipped — no declared earnings provided.")

    return {
        "verified": True,   # identity always verified in sandbox
        "income_verified": income_verified,
        "income_match": income_match,
        "income_deviation_pct": income_deviation_pct,
        "portal_weekly_income_estimate": round(portal_weekly_income, 0),
        "message": " ".join(message_parts),
    }
