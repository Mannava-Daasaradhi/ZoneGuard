from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.database import get_db
from models.zone import Zone
from models.signal import SignalReading, DisruptionEvent
from models.claim import Claim
from models.rider import Rider
from models.policy import Policy
from services.signal_poller import poll_zone_signals
from services.claim_pipeline import process_disruption_event
from ml.signal_fusion import evaluate_s1, evaluate_s2, evaluate_s3, evaluate_s4, fuse_signals
from routers.zones import update_signal_cache
from datetime import datetime, timezone, timedelta
import uuid

router = APIRouter(prefix="/api/v1/signals", tags=["signals"])


@router.post("/poll/{zone_id}")
async def poll_signals(zone_id: str, db: AsyncSession = Depends(get_db)):
    """Poll signals for a zone, evaluate fusion, and trigger claims if needed."""

    zone = await db.get(Zone, zone_id)
    if not zone:
        return {"error": "Zone not found"}

    zone_data = {"id": zone.id, "name": zone.name, "lat": zone.lat, "lng": zone.lng, "active_riders": zone.active_riders}
    signals = await poll_zone_signals(zone_data)

    weather = signals["weather"]
    mobility = signals["mobility"]
    orders = signals["orders"]
    checkins = signals["checkins"]

    # Evaluate fusion
    s1 = evaluate_s1(weather["rainfall_mm_hr"], weather["aqi"], weather["temperature_c"])
    s2 = evaluate_s2(mobility["mobility_index"])
    s3 = evaluate_s3(orders["order_volume"])
    s4 = evaluate_s4(checkins["inactive_riders"], checkins["total_riders"])
    fusion = fuse_signals(s1, s2, s3, s4)

    # Store signal readings
    for sig_type, sig_data in [("S1", s1), ("S2", s2), ("S3", s3), ("S4", s4)]:
        reading = SignalReading(
            id=uuid.uuid4().hex[:12],
            zone_id=zone_id,
            signal_type=sig_type,
            value=float(sig_data.get("value", 0)),
            threshold=float(sig_data.get("threshold", 0)),
            is_breached=1 if sig_data["breached"] else 0,
            raw_data=sig_data,
        )
        db.add(reading)

    # Update signal cache for frontend polling
    cache_data = {
        "zone_id": zone_id,
        "zone_name": zone.name,
        "s1_environmental": {"status": "firing" if s1["breached"] else "inactive", "value": f"Rainfall: {weather['rainfall_mm_hr']:.0f}mm/hr", "threshold": ">65mm/hr", "raw": s1},
        "s2_mobility": {"status": "firing" if s2["breached"] else "inactive", "value": f"Mobility: {s2['value']:.0f}% of baseline", "threshold": "<25% of baseline", "raw": s2},
        "s3_economic": {"status": "firing" if s3["breached"] else "inactive", "value": f"Orders: {s3['value']:.0f}% of baseline", "threshold": "<30% of baseline", "raw": s3},
        "s4_crowd": {"status": "firing" if s4["breached"] else "inactive", "value": f"Check-ins: {s4['value']:.0f}% inactivity", "threshold": "≥40% inactivity", "raw": s4},
        "confidence": fusion["confidence"],
        "signals_fired": fusion["signals_fired"],
        "is_disrupted": fusion["signals_fired"] >= 2,
        "fusion": fusion,
        "weather": weather,
    }
    update_signal_cache(zone_id, cache_data)

    # If disruption detected, create event and process claims
    claims_result = None
    if fusion["signals_fired"] >= 2:
        event = DisruptionEvent(
            zone_id=zone_id,
            confidence=fusion["confidence"],
            signals_fired=fusion["signals_fired"],
            signal_details=fusion["signal_details"],
            source="auto",
        )
        db.add(event)
        await db.flush()

        # Get riders with active policies in this zone
        result = await db.execute(
            select(Rider, Policy)
            .join(Policy, Policy.rider_id == Rider.id)
            .where(Rider.zone_id == zone_id)
            .where(Policy.status == "active")
        )
        riders_policies = result.all()

        riders_with_policies = []
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        for rider, policy in riders_policies:
            # Compute consecutive disruption days from recent claims
            recent_claims_result = await db.execute(
                select(func.count(Claim.id))
                .where(Claim.rider_id == rider.id)
                .where(Claim.status.in_(["approved", "pending_review"]))
                .where(Claim.created_at >= week_ago)
            )
            consecutive_days = recent_claims_result.scalar() or 0

            riders_with_policies.append({
                "id": rider.id,
                "weekly_earnings_baseline": rider.weekly_earnings_baseline,
                "tenure_weeks": rider.tenure_weeks,
                "upi_id": rider.upi_id,
                "policy_id": policy.id,
                "policy": {"coverage_start": policy.coverage_start},
                "days_since_policy_start": max(0, (datetime.now(timezone.utc) - policy.coverage_start).days),
                "consecutive_disruption_days": consecutive_days,
            })

        if riders_with_policies:
            claims_result = await process_disruption_event(
                zone_id=zone_id,
                zone_data=zone_data,
                weather_data=weather,
                mobility_data=mobility,
                order_data=orders,
                checkin_data=checkins,
                riders_with_policies=riders_with_policies,
            )

            # Store claims in DB
            for claim_data in claims_result.get("claims", []):
                claim = Claim(
                    id=claim_data["id"],
                    rider_id=claim_data["rider_id"],
                    policy_id=claim_data["policy_id"],
                    zone_id=zone_id,
                    disruption_event_id=event.id,
                    status=claim_data["status"],
                    confidence=claim_data["confidence"],
                    recommended_payout=claim_data["recommended_payout"],
                    exclusion_check=claim_data["exclusion_check"],
                    fraud_score=claim_data.get("fraud_score"),
                )
                if claim_data["status"] == "approved":
                    claim.actual_payout = claim_data["recommended_payout"]
                db.add(claim)

    await db.commit()

    return {
        "zone_id": zone_id,
        "signals": cache_data,
        "disruption": fusion["confidence"] if fusion["signals_fired"] >= 2 else None,
        "claims": claims_result,
    }


@router.get("/active-events")
async def get_active_events(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DisruptionEvent).where(DisruptionEvent.is_active == 1).order_by(DisruptionEvent.started_at.desc())
    )
    events = result.scalars().all()
    return [
        {
            "id": e.id, "zone_id": e.zone_id, "confidence": e.confidence,
            "signals_fired": e.signals_fired, "started_at": e.started_at.isoformat(),
            "source": e.source,
        }
        for e in events
    ]
