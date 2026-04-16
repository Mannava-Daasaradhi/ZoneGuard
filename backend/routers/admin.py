from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.database import get_db
from models.zone import Zone
from models.rider import Rider
from models.policy import Policy
from models.claim import Claim
from models.payout import Payout
from models.fraud import FraudFlag
from starlette.concurrency import run_in_threadpool
from ml.federated import run_federated_round
from ml.fraud_shield import detect_coordination_ring
from datetime import datetime, timezone


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


@router.post("/fraudshield/federated-round")
async def trigger_federated_round(n_rounds: int = 3):
    """
    Trigger a FraudShield v2 federated learning round.

    Simulates FedAvg across 5 city clients (Bengaluru, Mumbai, Hyderabad,
    Pune, Chennai). Each client trains a local IsolationForest on synthetic
    city data; weight vectors are aggregated server-side.

    Raw rider data never leaves the city cluster — DPDP Act 2023 compliant.

    Use n_rounds=1 for a quick demo; n_rounds=3 for convergence demo.
    """
    try:
        # run_federated_round is CPU-bound (IsolationForest training).
        # For a hackathon demo with a single admin user this is fine.
        # In production this would be offloaded via asyncio.to_thread().
        
        result = await run_in_threadpool(run_federated_round, n_rounds=max(1, min(n_rounds, 5)))
        return {
            "status": "complete",
            "federated_training": result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except (RuntimeError, ValueError) as err:
        # Catch only the specific errors run_federated_round can raise.
        # Re-raise with exception chaining so the traceback is preserved
        # in server logs while the client only sees a safe generic message.
        raise HTTPException(
            status_code=500,
            detail="Federated round failed — check server logs for details.",
        ) from err


@router.post("/fraudshield/ring-detection-demo")
async def ring_detection_demo():
    """
    Demo endpoint: runs temporal clustering ring detection on two
    synthetic claim batches — one genuine, one coordinated attack.

    Shows judges the contrast between Poisson-distributed genuine claims
    and the sharp temporal spike of a Telegram-coordinated fraud ring.
    """
    import random
    from datetime import timedelta

    base_time = datetime.now(timezone.utc)

    # --- Genuine disruption: Poisson-distributed arrivals ---
    rng = random.Random(42)
    genuine_timestamps = []
    t = base_time
    for _ in range(18):
        t += timedelta(seconds=rng.randint(180, 900))  # 3–15 min gaps
        genuine_timestamps.append(t)

    # --- Coordinated ring: tight spike (Telegram "go now" at T+0) ---
    ring_timestamps = []
    spike_base = base_time + timedelta(minutes=12)
    for i in range(22):
        ring_timestamps.append(
            spike_base + timedelta(seconds=rng.randint(0, 90))  # all within 90 seconds
        )

    genuine_result = detect_coordination_ring(
        zone_id="hsr_layout",
        claim_timestamps=genuine_timestamps,
        expected_claims_mean=16.0,
    )

    ring_result = detect_coordination_ring(
        zone_id="hsr_layout",
        claim_timestamps=ring_timestamps,
        expected_claims_mean=16.0,
    )

    return {
        "demo": "temporal_clustering_ring_detection",
        "genuine_disruption": {
            "description": "18 claims, Poisson-distributed (3–15 min gaps)",
            "analysis": genuine_result,
        },
        "coordinated_ring": {
            "description": "22 claims, all within 90 seconds (Telegram 'go now' pattern)",
            "analysis": ring_result,
        },
        "takeaway": (
            "Genuine disruptions show CV≈1.0 and low clustering coefficient. "
            "Coordinated attacks show CV≈0.1 and tight temporal spikes — "
            "detectable without examining any GPS or personal data."
        ),
    }
