from fastapi import APIRouter, Depends, Query
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
from ml.zone_twin import ZONE_BASELINES
from routers.zones import update_signal_cache, _signal_cache
from datetime import datetime, timezone, timedelta
import uuid

router = APIRouter(prefix="/api/v1/signals", tags=["signals"])


@router.get("/at-risk")
async def get_at_risk_zones(db: AsyncSession = Depends(get_db)):
    """Zones with 2+ breached signals in most recent reading."""
    at_risk = []
    for zone_id, cache in _signal_cache.items():
        if cache.get("signals_fired", 0) >= 2:
            at_risk.append({
                "zone_id": zone_id,
                "zone_name": cache.get("zone_name", zone_id),
                "signals_fired": cache["signals_fired"],
                "confidence": cache.get("confidence", "UNKNOWN"),
                "is_disrupted": cache.get("is_disrupted", False),
            })

    # If cache empty, check DB for recent disruption events
    if not at_risk:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=6)
        result = await db.execute(
            select(DisruptionEvent)
            .where(DisruptionEvent.is_active == 1)
            .where(DisruptionEvent.started_at >= cutoff)
        )
        events = result.scalars().all()
        for e in events:
            zone = await db.get(Zone, e.zone_id)
            at_risk.append({
                "zone_id": e.zone_id,
                "zone_name": zone.name if zone else e.zone_id,
                "signals_fired": e.signals_fired,
                "confidence": e.confidence,
                "is_disrupted": True,
            })

    return at_risk


@router.get("/history/{zone_id}")
async def get_signal_history(
    zone_id: str,
    limit: int = Query(50, ge=1, le=500),
    signal_type: str = Query(None, description="Filter by S1/S2/S3/S4"),
    db: AsyncSession = Depends(get_db),
):
    """Last N signal readings for a zone, optionally filtered by type."""
    query = select(SignalReading).where(SignalReading.zone_id == zone_id)
    if signal_type:
        query = query.where(SignalReading.signal_type == signal_type.upper())
    query = query.order_by(SignalReading.recorded_at.desc()).limit(limit)

    result = await db.execute(query)
    readings = result.scalars().all()

    return [
        {
            "id": r.id,
            "signal_type": r.signal_type,
            "value": r.value,
            "threshold": r.threshold,
            "is_breached": bool(r.is_breached),
            "raw_data": r.raw_data,
            "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
        }
        for r in readings
    ]


@router.get("/baselines/{zone_id}")
async def get_signal_baselines(zone_id: str, db: AsyncSession = Depends(get_db)):
    """Current signal values vs historical baselines for a zone."""
    baseline = ZONE_BASELINES.get(zone_id, ZONE_BASELINES.get("hsr", {}))

    # Get latest signal readings from cache or DB
    cached = _signal_cache.get(zone_id)
    current = {}
    if cached:
        current = {
            "rainfall_mm_hr": cached.get("weather", {}).get("rainfall_mm_hr", 0),
            "mobility_index": cached.get("s2_mobility", {}).get("raw", {}).get("value", 100),
            "order_volume": cached.get("s3_economic", {}).get("raw", {}).get("value", 100),
            "inactivity_pct": cached.get("s4_crowd", {}).get("raw", {}).get("value", 0),
        }

    return {
        "zone_id": zone_id,
        "baselines": {
            "avg_rainfall_mm": baseline.get("avg_rainfall_mm", 0),
            "avg_mobility": baseline.get("avg_mobility", 0),
            "avg_inactivity_pct": baseline.get("avg_inactivity_pct", 0),
            "disruption_rainfall_threshold": baseline.get("disruption_rainfall_threshold", 0),
            "flood_correlation": baseline.get("flood_correlation", 0),
        },
        "current": current,
    }


@router.post("/ndma-override/{zone_id}")
async def ndma_override(zone_id: str, db: AsyncSession = Depends(get_db)):
    """NDMA flood alert override — immediately triggers S1 breach and disruption event."""
    zone = await db.get(Zone, zone_id)
    if not zone:
        return {"error": "Zone not found"}

    # Create S1 override reading
    reading = SignalReading(
        id=uuid.uuid4().hex[:12],
        zone_id=zone_id,
        signal_type="S1",
        value=999.0,
        threshold=65.0,
        is_breached=1,
        raw_data={"source": "ndma_override", "alert_type": "flood", "override": True},
    )
    db.add(reading)

    # Evaluate with forced S1 breach
    s1 = {"breached": True, "value": 999, "threshold": 65, "reason": "NDMA flood alert override"}
    s2 = {"breached": True, "value": 10, "threshold": 25, "reason": "Assumed during NDMA override"}
    s3 = {"breached": True, "value": 15, "threshold": 30, "reason": "Assumed during NDMA override"}
    s4 = {"breached": True, "value": 60, "threshold": 40, "reason": "Assumed during NDMA override"}
    fusion = fuse_signals(s1, s2, s3, s4)

    # Create disruption event
    event = DisruptionEvent(
        zone_id=zone_id,
        confidence="HIGH",
        signals_fired=4,
        signal_details=fusion["signal_details"],
        source="ndma_override",
    )
    db.add(event)
    await db.flush()

    # Update signal cache
    update_signal_cache(zone_id, {
        "zone_id": zone_id,
        "zone_name": zone.name,
        "s1_environmental": {"status": "firing", "value": "NDMA Flood Alert", "threshold": ">65mm/hr", "raw": s1},
        "s2_mobility": {"status": "firing", "value": "Mobility: 10% of baseline", "threshold": "<25% of baseline", "raw": s2},
        "s3_economic": {"status": "firing", "value": "Orders: 15% of baseline", "threshold": "<30% of baseline", "raw": s3},
        "s4_crowd": {"status": "firing", "value": "Check-ins: 60% inactivity", "threshold": ">=40% inactivity", "raw": s4},
        "confidence": "HIGH",
        "signals_fired": 4,
        "is_disrupted": True,
        "fusion": fusion,
    })

    # Process claims for riders with active policies
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

    claims_result = None
    if riders_with_policies:
        claims_result = await process_disruption_event(
            zone_id=zone_id,
            zone_data={"id": zone.id, "name": zone.name, "lat": zone.lat, "lng": zone.lng, "active_riders": zone.active_riders},
            weather_data={"rainfall_mm_hr": 999, "aqi": 0, "temperature_c": 30, "source": "ndma_override"},
            mobility_data={"mobility_index": 10},
            order_data={"order_volume": 15},
            checkin_data={"inactive_riders": 60, "total_riders": 100},
            riders_with_policies=riders_with_policies,
        )

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
        "event_id": event.id,
        "confidence": "HIGH",
        "signals_fired": 4,
        "source": "ndma_override",
        "claims": claims_result,
    }


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
        "s4_crowd": {"status": "firing" if s4["breached"] else "inactive", "value": f"Check-ins: {s4['value']:.0f}% inactivity", "threshold": ">=40% inactivity", "raw": s4},
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
