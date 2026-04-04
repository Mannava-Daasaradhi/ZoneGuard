from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.database import get_db
from models.rider import Rider
from models.zone import Zone
from schemas.rider import RiderRegister, RiderResponse, RiderKYC
from ml.zone_risk_scorer import calculate_zone_premium

router = APIRouter(prefix="/api/v1/riders", tags=["riders"])


@router.post("/register")
async def register_rider(payload: RiderRegister, db: AsyncSession = Depends(get_db)):
    """Register a new rider and return premium quote."""

    # Check zone exists
    zone = await db.get(Zone, payload.zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    # Check rider doesn't already exist
    existing = await db.get(Rider, payload.rider_id)
    if existing:
        raise HTTPException(status_code=409, detail="Rider already registered")

    # Create rider
    rider = Rider(
        id=payload.rider_id,
        name=payload.name,
        phone=payload.phone,
        zone_id=payload.zone_id,
        weekly_earnings_baseline=payload.weekly_earnings,
        upi_id=payload.upi_id,
    )
    db.add(rider)

    # Update zone active rider count
    zone.active_riders = (zone.active_riders or 0) + 1

    await db.commit()
    await db.refresh(rider)

    # Calculate premium quote
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
    rider = await db.get(Rider, rider_id)
    if not rider:
        raise HTTPException(status_code=404, detail="Rider not found")

    rider.upi_id = payload.upi_id
    rider.phone = payload.phone
    rider.kyc_verified = True
    await db.commit()

    return {"status": "kyc_verified", "rider_id": rider_id}
