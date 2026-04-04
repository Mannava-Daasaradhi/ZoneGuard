"""
Disruption Simulator — The demo killer feature.

Pre-configured scenarios with signal overrides that trigger
the full QuadSignal → Claim → Payout pipeline in real-time.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.database import get_db
from models.zone import Zone
from models.simulation import SimulationEvent
from models.signal import DisruptionEvent
from models.rider import Rider
from models.policy import Policy
from models.claim import Claim
from models.payout import Payout
from models.audit import AuditLog
from ml.signal_fusion import evaluate_s1, evaluate_s2, evaluate_s3, evaluate_s4, fuse_signals
from ml.fraud_shield import calculate_fraud_score
from ml.zone_twin import counterfactual_inactivity
from services.exclusion_engine import evaluate_claim_exclusions
from integrations.gemini import generate_audit_report
from integrations.payout_sim import process_payout
from routers.zones import update_signal_cache
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/api/v1/simulator", tags=["simulator"])

# Pre-configured disruption scenarios
SCENARIOS = {
    "flash_flood": {
        "name": "Flash Flood",
        "weather": {"rainfall_mm_hr": 82, "temperature_c": 28, "aqi": 120, "humidity": 95, "description": "heavy intensity rain", "source": "simulator"},
        "mobility_index": 12,
        "order_volume": 8,
        "inactivity_pct": 0.55,
    },
    "severe_aqi": {
        "name": "Severe AQI Event",
        "weather": {"rainfall_mm_hr": 2, "temperature_c": 32, "aqi": 420, "humidity": 45, "description": "haze", "source": "simulator"},
        "mobility_index": 28,
        "order_volume": 22,
        "inactivity_pct": 0.48,
    },
    "transport_strike": {
        "name": "Transport Strike",
        "weather": {"rainfall_mm_hr": 5, "temperature_c": 30, "aqi": 110, "humidity": 55, "description": "clear sky", "source": "simulator"},
        "mobility_index": 15,
        "order_volume": 18,
        "inactivity_pct": 0.62,
    },
    "heat_wave": {
        "name": "Heat Wave",
        "weather": {"rainfall_mm_hr": 0, "temperature_c": 46, "aqi": 180, "humidity": 25, "description": "clear sky", "source": "simulator"},
        "mobility_index": 30,
        "order_volume": 25,
        "inactivity_pct": 0.45,
    },
}


class SimulatorTrigger(BaseModel):
    zone_id: str
    scenario: str


@router.post("/trigger")
async def trigger_disruption(payload: SimulatorTrigger, db: AsyncSession = Depends(get_db)):
    """Trigger a simulated disruption — the 2-minute demo moment."""

    if payload.scenario not in SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Unknown scenario. Options: {list(SCENARIOS.keys())}")

    zone = await db.get(Zone, payload.zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    scenario = SCENARIOS[payload.scenario]
    weather = scenario["weather"]
    active_riders = zone.active_riders or 100

    # Evaluate all 4 signals with scenario overrides
    s1 = evaluate_s1(weather["rainfall_mm_hr"], weather["aqi"], weather["temperature_c"])
    s2 = evaluate_s2(scenario["mobility_index"])
    s3 = evaluate_s3(scenario["order_volume"])

    inactive_count = int(active_riders * scenario["inactivity_pct"])
    s4 = evaluate_s4(inactive_count, active_riders)

    fusion = fuse_signals(s1, s2, s3, s4)

    # Store simulation event
    sim_event = SimulationEvent(
        zone_id=payload.zone_id,
        scenario=payload.scenario,
        signal_overrides=scenario,
        triggered_by="admin",
    )
    db.add(sim_event)

    # Create disruption event
    disruption = DisruptionEvent(
        zone_id=payload.zone_id,
        confidence=fusion["confidence"],
        signals_fired=fusion["signals_fired"],
        signal_details=fusion["signal_details"],
        source="simulator",
    )
    db.add(disruption)
    await db.flush()

    # Update signal cache for real-time frontend polling
    cache_data = {
        "zone_id": payload.zone_id,
        "zone_name": zone.name,
        "s1_environmental": {"status": "firing" if s1["breached"] else "inactive", "value": f"Rainfall: {weather['rainfall_mm_hr']:.0f}mm/hr", "threshold": ">65mm/hr", "raw": s1},
        "s2_mobility": {"status": "firing" if s2["breached"] else "inactive", "value": f"Mobility: {scenario['mobility_index']:.0f}% of baseline", "threshold": "<25% of baseline", "raw": s2},
        "s3_economic": {"status": "firing" if s3["breached"] else "inactive", "value": f"Orders: {scenario['order_volume']:.0f}% of baseline", "threshold": "<30% of baseline", "raw": s3},
        "s4_crowd": {"status": "firing" if s4["breached"] else "inactive", "value": f"Check-ins: {s4['value']:.0f}% inactivity", "threshold": "≥40% inactivity", "raw": s4},
        "confidence": fusion["confidence"],
        "signals_fired": fusion["signals_fired"],
        "is_disrupted": fusion["signals_fired"] >= 2,
        "fusion": fusion,
        "weather": weather,
    }
    update_signal_cache(payload.zone_id, cache_data)

    # ZoneTwin counterfactual
    zone_twin = counterfactual_inactivity(payload.zone_id, weather["rainfall_mm_hr"], weather["aqi"])

    # Process claims for riders with active policies
    result = await db.execute(
        select(Rider, Policy)
        .join(Policy, Policy.rider_id == Rider.id)
        .where(Rider.zone_id == payload.zone_id)
        .where(Policy.status == "active")
    )
    riders_policies = result.all()

    claims_created = []
    payouts_created = []

    for rider, policy in riders_policies:
        daily_avg = (rider.weekly_earnings_baseline or 2000) / 7
        payout_amount = round(daily_avg * 0.75)

        # Fraud check
        fraud = calculate_fraud_score(
            claim_hour=datetime.now(timezone.utc).hour,
            tenure_weeks=rider.tenure_weeks or 10,
            zone_inactivity_pct=scenario["inactivity_pct"] * 100,
            claim_velocity_7d=0,
            zone_claim_rate_deviation=1.0,
            distance_from_centroid_km=1.5,
            s1_value=weather["rainfall_mm_hr"],
            days_since_policy_start=max(0, (datetime.now(timezone.utc) - policy.coverage_start).days) if policy.coverage_start else 5,
        )

        # Exclusion check
        excl_check = evaluate_claim_exclusions(
            claim_data={"rider_id": rider.id, "zone_id": payload.zone_id},
            policy_data={"coverage_start": policy.coverage_start},
            fraud_score=fraud["score"],
        )

        # Determine status
        if not excl_check["passed"]:
            status = "rejected"
        elif fraud["risk_level"] == "hold":
            status = "held"
        elif fusion["confidence"] == "HIGH":
            status = "approved"
        else:
            status = "pending_review"

        claim = Claim(
            rider_id=rider.id,
            policy_id=policy.id,
            zone_id=payload.zone_id,
            disruption_event_id=disruption.id,
            status=status,
            confidence=fusion["confidence"],
            recommended_payout=payout_amount,
            exclusion_check=excl_check,
            fraud_score=fraud["score"],
        )
        if status == "approved":
            claim.actual_payout = payout_amount
        db.add(claim)
        await db.flush()
        claims_created.append({
            "id": claim.id, "rider_id": rider.id, "status": status,
            "recommended_payout": payout_amount, "fraud_score": fraud["score"],
            "exclusion_check": excl_check,
        })

        # Generate audit report for MEDIUM claims
        if fusion["confidence"] == "MEDIUM":
            audit = await generate_audit_report({
                "claim_id": claim.id, "zone_name": zone.name, "zone_id": payload.zone_id,
                "confidence": fusion["confidence"], "signals_fired": fusion["signals_fired"],
                "signal_details": fusion["signal_details"],
                "s1": s1, "s2": s2, "s3": s3, "s4": s4,
                "zone_twin": zone_twin, "exclusion_check": excl_check, "fraud_score": fraud["score"],
            })
            audit_log = AuditLog(
                claim_id=claim.id, event_type="gemini_audit",
                content=audit["report"], model_used=audit["model_used"], generated_by="system",
            )
            db.add(audit_log)

        # Auto-payout for approved HIGH confidence claims
        if status == "approved":
            payout_result = await process_payout(rider.id, payout_amount, rider.upi_id)
            payout = Payout(
                claim_id=claim.id, rider_id=rider.id, amount=payout_amount,
                upi_ref=payout_result["upi_ref"], status=payout_result["status"],
                gateway_response=str(payout_result["gateway_response"]),
            )
            if payout_result["status"] == "settled":
                payout.settled_at = datetime.now(timezone.utc)
            db.add(payout)
            payouts_created.append({
                "id": payout.id, "rider_id": rider.id, "amount": payout_amount,
                "upi_ref": payout_result["upi_ref"], "status": payout_result["status"],
            })

    await db.commit()

    return {
        "simulation_id": sim_event.id,
        "scenario": scenario["name"],
        "zone": {"id": zone.id, "name": zone.name},
        "disruption_event_id": disruption.id,
        "fusion": fusion,
        "zone_twin": zone_twin,
        "claims_created": len(claims_created),
        "claims": claims_created,
        "payouts_created": len(payouts_created),
        "payouts": payouts_created,
        "signals": cache_data,
    }


@router.get("/active")
async def get_active_simulations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SimulationEvent).where(SimulationEvent.is_active == 1).order_by(SimulationEvent.started_at.desc())
    )
    events = result.scalars().all()
    return [
        {"id": e.id, "zone_id": e.zone_id, "scenario": e.scenario, "started_at": e.started_at.isoformat()}
        for e in events
    ]


@router.delete("/stop/{sim_id}")
async def stop_simulation(sim_id: str, db: AsyncSession = Depends(get_db)):
    sim = await db.get(SimulationEvent, sim_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")

    sim.is_active = 0
    sim.ended_at = datetime.now(timezone.utc)

    # Also end the disruption event
    result = await db.execute(
        select(DisruptionEvent)
        .where(DisruptionEvent.zone_id == sim.zone_id)
        .where(DisruptionEvent.is_active == 1)
        .where(DisruptionEvent.source == "simulator")
    )
    for event in result.scalars().all():
        event.is_active = 0
        event.ended_at = datetime.now(timezone.utc)

    from routers.zones import clear_signal_cache
    clear_signal_cache(sim.zone_id)

    await db.commit()
    return {"status": "stopped", "simulation_id": sim_id}


@router.get("/scenarios")
async def list_scenarios():
    """List available disruption scenarios."""
    return {k: {"name": v["name"], "description": f"Simulates {v['name'].lower()} conditions"} for k, v in SCENARIOS.items()}
