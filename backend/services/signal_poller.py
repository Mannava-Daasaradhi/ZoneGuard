"""
Background signal polling service.

Polls all zones for current signal data and evaluates disruption conditions.
In production, this would run as a Celery beat task every 15 minutes.
"""

import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import async_session
from models.zone import Zone
from models.signal import SignalReading, DisruptionEvent
from models.rider import Rider
from models.policy import Policy
from integrations.weather import get_current_weather
from integrations.mobility_sim import calculate_mobility_index
from integrations.order_sim import simulate_order_volume
from integrations.whatsapp_sim import simulate_checkins
from ml.signal_fusion import evaluate_s1, evaluate_s2, evaluate_s3, evaluate_s4, fuse_signals

logger = logging.getLogger(__name__)

# Minimum confidence level to log and potentially trigger claims
TRIGGER_CONFIDENCE_LEVELS = {"HIGH", "MEDIUM"}


async def poll_zone_signals(zone_data: dict) -> dict:
    """Poll all 4 signal sources for a single zone."""

    # S1: Weather
    weather = await get_current_weather(zone_data["lat"], zone_data["lng"])

    # S2: Mobility (derived from weather)
    mobility = calculate_mobility_index(
        rainfall_mm=weather["rainfall_mm_hr"],
        aqi=weather["aqi"],
        temp_c=weather["temperature_c"],
    )

    # S3: Orders (derived from mobility)
    orders = simulate_order_volume(mobility["mobility_index"])

    # S4: WhatsApp check-ins
    # Disruption severity estimated from weather
    severity = min(1.0, max(0, (weather["rainfall_mm_hr"] - 20) / 80))
    checkins = simulate_checkins(
        total_riders=zone_data.get("active_riders", 100),
        disruption_severity=severity,
    )

    return {
        "zone_id": zone_data["id"],
        "weather": weather,
        "mobility": mobility,
        "orders": orders,
        "checkins": checkins,
    }


async def _store_signal_readings(
    session: AsyncSession,
    zone_id: str,
    s1: dict,
    s2: dict,
    s3: dict,
    s4: dict,
) -> list[str]:
    """
    Store individual signal readings in the database for analytics.
    
    Returns list of created signal reading IDs.
    """
    readings = []
    signal_data = [
        ("S1", s1["value"], s1["threshold"], s1["breached"], s1.get("details", {})),
        ("S2", s2["value"], s2["threshold"], s2["breached"], s2.get("details", {})),
        ("S3", s3["value"], s3["threshold"], s3["breached"], s3.get("details", {})),
        ("S4", s4["value"], s4["threshold"], s4["breached"], s4.get("details", {})),
    ]
    
    for signal_type, value, threshold, breached, raw_data in signal_data:
        reading_id = uuid.uuid4().hex[:12]
        reading = SignalReading(
            id=reading_id,
            zone_id=zone_id,
            signal_type=signal_type,
            value=float(value) if not isinstance(value, str) else 0,
            threshold=float(threshold),
            is_breached=1 if breached else 0,
            raw_data=raw_data,
        )
        session.add(reading)
        readings.append(reading_id)
    
    return readings


async def _create_disruption_event(
    session: AsyncSession,
    zone_id: str,
    fusion: dict,
) -> str:
    """
    Create a disruption event record in the database.
    
    Returns the created event ID.
    """
    event_id = f"DE-{uuid.uuid4().hex[:8].upper()}"
    event = DisruptionEvent(
        id=event_id,
        zone_id=zone_id,
        confidence=fusion["confidence"],
        signals_fired=fusion["signals_fired"],
        signal_details=fusion["signal_details"],
        source="auto",
    )
    session.add(event)
    return event_id


async def _get_riders_with_active_policies(
    session: AsyncSession,
    zone_id: str,
) -> list[dict]:
    """
    Fetch all riders in a zone who have active policies.
    
    Returns list of rider data with policy info.
    """
    now = datetime.now(timezone.utc)
    
    # Query riders with active policies in this zone
    stmt = (
        select(Rider, Policy)
        .join(Policy, Rider.id == Policy.rider_id)
        .where(
            Rider.zone_id == zone_id,
            Policy.status == "active",
            Policy.coverage_start <= now,
            Policy.coverage_end >= now,
        )
    )
    
    result = await session.execute(stmt)
    rows = result.all()
    
    riders = []
    for rider, policy in rows:
        riders.append({
            "id": rider.id,
            "name": rider.name,
            "phone": rider.phone,
            "zone_id": rider.zone_id,
            "weekly_earnings_baseline": rider.weekly_earnings_baseline,
            "tenure_weeks": rider.tenure_weeks,
            "upi_id": rider.upi_id,
            "policy_id": policy.id,
            "policy": {
                "id": policy.id,
                "weekly_premium": policy.weekly_premium,
                "max_payout": policy.max_payout,
                "coverage_start": policy.coverage_start.isoformat(),
                "coverage_end": policy.coverage_end.isoformat(),
            },
            "days_since_policy_start": (now - policy.coverage_start).days,
        })
    
    return riders


async def poll_single_zone(zone: Zone) -> dict:
    """
    Poll signals for a single zone and evaluate disruption conditions.
    
    Returns poll result including fusion evaluation.
    """
    zone_data = {
        "id": zone.id,
        "name": zone.name,
        "lat": zone.lat,
        "lng": zone.lng,
        "active_riders": zone.active_riders or 100,
    }
    
    # Fetch all signals
    signals = await poll_zone_signals(zone_data)
    weather = signals["weather"]
    mobility = signals["mobility"]
    orders = signals["orders"]
    checkins = signals["checkins"]
    
    # Evaluate each signal
    s1 = evaluate_s1(
        rainfall_mm=weather["rainfall_mm_hr"],
        aqi=weather["aqi"],
        temp_c=weather["temperature_c"],
    )
    s2 = evaluate_s2(
        mobility_index=mobility["mobility_index"],
        baseline=mobility.get("baseline", 100),
    )
    s3 = evaluate_s3(
        order_volume=orders["order_volume"],
        baseline=orders.get("baseline", 100),
    )
    s4 = evaluate_s4(
        inactive_riders=checkins["inactive_riders"],
        total_riders=checkins["total_riders"],
    )
    
    # Fuse signals
    fusion = fuse_signals(s1, s2, s3, s4)
    
    return {
        "zone_id": zone.id,
        "zone_name": zone.name,
        "signals": signals,
        "s1": s1,
        "s2": s2,
        "s3": s3,
        "s4": s4,
        "fusion": fusion,
    }


async def poll_all_zones() -> dict:
    """
    Main polling function — polls all zones and processes disruption events.
    
    This is called by the scheduler every 15 minutes.
    
    Returns summary of polling results.
    """
    poll_id = uuid.uuid4().hex[:8]
    start_time = datetime.now(timezone.utc)
    
    logger.info(f"[poll:{poll_id}] Starting signal poll for all zones")
    
    results = {
        "poll_id": poll_id,
        "started_at": start_time.isoformat(),
        "zones_polled": 0,
        "disruptions_detected": 0,
        "high_confidence": 0,
        "medium_confidence": 0,
        "errors": [],
        "zone_results": [],
    }
    
    try:
        async with async_session() as session:
            # Fetch all zones
            stmt = select(Zone)
            result = await session.execute(stmt)
            zones = result.scalars().all()
            
            if not zones:
                logger.warning(f"[poll:{poll_id}] No zones found in database")
                results["completed_at"] = datetime.now(timezone.utc).isoformat()
                return results
            
            logger.info(f"[poll:{poll_id}] Found {len(zones)} zones to poll")
            
            # Poll each zone
            for zone in zones:
                try:
                    poll_result = await poll_single_zone(zone)
                    results["zones_polled"] += 1
                    
                    fusion = poll_result["fusion"]
                    confidence = fusion["confidence"]
                    
                    # Store signal readings for analytics
                    reading_ids = await _store_signal_readings(
                        session,
                        zone.id,
                        poll_result["s1"],
                        poll_result["s2"],
                        poll_result["s3"],
                        poll_result["s4"],
                    )
                    
                    # Log and process if confidence is HIGH or MEDIUM
                    if confidence in TRIGGER_CONFIDENCE_LEVELS:
                        results["disruptions_detected"] += 1
                        
                        if confidence == "HIGH":
                            results["high_confidence"] += 1
                            logger.warning(
                                f"[poll:{poll_id}] HIGH confidence disruption in zone {zone.id} "
                                f"({zone.name}) — {fusion['signals_fired']}/4 signals fired"
                            )
                        else:
                            results["medium_confidence"] += 1
                            logger.info(
                                f"[poll:{poll_id}] MEDIUM confidence disruption in zone {zone.id} "
                                f"({zone.name}) — {fusion['signals_fired']}/4 signals fired"
                            )
                        
                        # Create disruption event
                        event_id = await _create_disruption_event(
                            session, zone.id, fusion
                        )
                        poll_result["disruption_event_id"] = event_id
                        
                        # Optionally trigger claims for HIGH confidence
                        # (In production, this would be more sophisticated)
                        if confidence == "HIGH":
                            riders = await _get_riders_with_active_policies(
                                session, zone.id
                            )
                            poll_result["affected_riders"] = len(riders)
                            logger.info(
                                f"[poll:{poll_id}] {len(riders)} riders with active policies "
                                f"in disrupted zone {zone.id}"
                            )
                            
                            # Note: Full claim processing is handled separately
                            # via process_disruption_event in claim_pipeline.py
                            # This scheduler focuses on detection and logging
                    else:
                        logger.debug(
                            f"[poll:{poll_id}] Zone {zone.id} ({zone.name}): "
                            f"{confidence} confidence ({fusion['signals_fired']}/4 signals)"
                        )
                    
                    results["zone_results"].append({
                        "zone_id": zone.id,
                        "zone_name": zone.name,
                        "confidence": confidence,
                        "signals_fired": fusion["signals_fired"],
                        "signal_readings": reading_ids,
                        "disruption_event_id": poll_result.get("disruption_event_id"),
                    })
                    
                except Exception as zone_error:
                    error_msg = f"Error polling zone {zone.id}: {str(zone_error)}"
                    logger.error(f"[poll:{poll_id}] {error_msg}", exc_info=True)
                    results["errors"].append({
                        "zone_id": zone.id,
                        "error": error_msg,
                    })
            
            # Commit all changes
            await session.commit()
            
    except Exception as e:
        error_msg = f"Critical error during poll: {str(e)}"
        logger.error(f"[poll:{poll_id}] {error_msg}", exc_info=True)
        results["errors"].append({"critical": error_msg})
    
    # Finalize results
    end_time = datetime.now(timezone.utc)
    duration_ms = (end_time - start_time).total_seconds() * 1000
    results["completed_at"] = end_time.isoformat()
    results["duration_ms"] = round(duration_ms, 2)
    
    logger.info(
        f"[poll:{poll_id}] Poll completed — {results['zones_polled']} zones, "
        f"{results['disruptions_detected']} disruptions detected "
        f"({results['high_confidence']} HIGH, {results['medium_confidence']} MEDIUM), "
        f"{len(results['errors'])} errors, {duration_ms:.0f}ms"
    )
    
    return results

