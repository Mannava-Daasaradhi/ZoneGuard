from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from models.zone import Zone
from models.rider import Rider
from ml.zone_risk_scorer import calculate_zone_premium, calculate_risk_score

router = APIRouter(prefix="/api/v1/premium", tags=["premium"])


@router.get("/calculate")
async def calculate_premium(
    zone_id: str = Query(...),
    rider_id: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Dynamic premium calculation with full factor breakdown."""

    zone = await db.get(Zone, zone_id)
    if not zone:
        return {"error": "Zone not found"}

    tenure_weeks = 0
    if rider_id:
        rider = await db.get(Rider, rider_id)
        if rider:
            tenure_weeks = rider.tenure_weeks

    result = calculate_risk_score(
        disruption_freq=zone.historical_disruptions,
        imd_forecast_severity=40,  # default moderate
        rider_tenure_weeks=tenure_weeks,
        zone_classification=zone.risk_tier,
        recent_claims_7d=2,  # default
        total_zone_riders=zone.active_riders or 100,
    )

    return {
        "zone_id": zone_id,
        "zone_name": zone.name,
        "rider_id": rider_id,
        **result,
    }
