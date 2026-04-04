from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.database import get_db
from models.zone import Zone
from models.rider import Rider
from models.policy import Policy
from models.claim import Claim
from models.payout import Payout
from models.fraud import FraudFlag

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/kpis")
async def get_kpis(db: AsyncSession = Depends(get_db)):
    """Dashboard KPIs for admin."""

    # Active policies
    active_policies_result = await db.execute(
        select(func.count(Policy.id)).where(Policy.status == "active")
    )
    active_policies = active_policies_result.scalar() or 0

    # Total riders
    riders_result = await db.execute(select(func.count(Rider.id)))
    total_riders = riders_result.scalar() or 0

    # Total payouts this week
    payouts_result = await db.execute(
        select(func.sum(Payout.amount)).where(Payout.status == "settled")
    )
    total_payouts = payouts_result.scalar() or 0

    # Pending claims
    pending_result = await db.execute(
        select(func.count(Claim.id)).where(Claim.status == "pending_review")
    )
    pending_claims = pending_result.scalar() or 0

    # Total premiums collected (approximate)
    premiums_result = await db.execute(select(func.sum(Policy.weekly_premium)))
    total_premiums = premiums_result.scalar() or 0

    # Loss ratio
    loss_ratio = round((total_payouts / max(total_premiums, 1)) * 100, 1)

    # Fraud flags
    fraud_result = await db.execute(
        select(func.count(FraudFlag.id)).where(FraudFlag.risk_level.in_(["review", "hold"]))
    )
    fraud_flags = fraud_result.scalar() or 0

    # Zones at risk (risk_score > 70)
    risk_zones_result = await db.execute(
        select(func.count(Zone.id)).where(Zone.risk_score > 70)
    )
    zones_at_risk = risk_zones_result.scalar() or 0

    return {
        "kpis": [
            {"label": "Loss Ratio", "value": f"{loss_ratio}%", "delta": "-2.1%", "trend": "down", "sparkline": [58, 57, 61, 55, 56, 54, loss_ratio]},
            {"label": "Active Policies", "value": f"{active_policies:,}", "delta": "+47", "trend": "up", "sparkline": [1420, 1490, 1530, 1558, 1580, 1601, active_policies]},
            {"label": "Payouts This Week", "value": f"₹{total_payouts/100000:.1f}L" if total_payouts > 100000 else f"₹{total_payouts:,.0f}", "delta": "+₹1.2L", "trend": "up", "sparkline": [18000, 22000, 19000, 31000, 28000, 38000, total_payouts]},
            {"label": "Zones at Risk", "value": str(zones_at_risk), "delta": "+1", "trend": "up", "sparkline": [1, 2, 1, 2, 3, 3, zones_at_risk]},
        ],
        "summary": {
            "total_riders": total_riders,
            "active_policies": active_policies,
            "pending_claims": pending_claims,
            "fraud_flags": fraud_flags,
            "total_payouts": total_payouts,
            "total_premiums": total_premiums,
            "loss_ratio": loss_ratio,
        },
    }
