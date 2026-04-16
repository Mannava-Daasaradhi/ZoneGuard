from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.database import get_db
from models.zone import Zone
from schemas.zone import ZoneResponse
from services.signal_poller import poll_zone_signals
from ml.signal_fusion import evaluate_s1, evaluate_s2, evaluate_s3, evaluate_s4, fuse_signals
from ml.zone_twin import counterfactual_inactivity

router = APIRouter(prefix="/api/v1/zones", tags=["zones"])

# In-memory cache of latest signal readings per zone (for real-time polling)
_signal_cache: dict[str, dict] = {}


@router.get("")
async def list_zones(db: AsyncSession = Depends(get_db)) -> list[ZoneResponse]:
    result = await db.execute(select(Zone))
    zones = result.scalars().all()
    return [ZoneResponse.model_validate(z) for z in zones]


@router.get("/{zone_id}")
async def get_zone(zone_id: str, db: AsyncSession = Depends(get_db)):
    zone = await db.get(Zone, zone_id)
    if not zone:
        return {"error": "Zone not found"}, 404
    return ZoneResponse.model_validate(zone)


@router.get("/{zone_id}/signals/current")
async def get_current_signals(zone_id: str, db: AsyncSession = Depends(get_db)):
    """Get current signal readings for a zone (cached or live)."""
    if zone_id in _signal_cache:
        return _signal_cache[zone_id]

    zone = await db.get(Zone, zone_id)
    if not zone:
        return {"error": "Zone not found"}

    signals = await poll_zone_signals({
        "id": zone.id, "lat": zone.lat, "lng": zone.lng,
        "active_riders": zone.active_riders,
    })

    # Evaluate fusion
    weather = signals["weather"]
    mobility = signals["mobility"]
    orders = signals["orders"]
    checkins = signals["checkins"]

    s1 = evaluate_s1(weather["rainfall_mm_hr"], weather["aqi"], weather["temperature_c"])
    s2 = evaluate_s2(mobility["mobility_index"])
    s3 = evaluate_s3(orders["order_volume"])
    s4 = evaluate_s4(checkins["inactive_riders"], checkins["total_riders"])
    fusion = fuse_signals(s1, s2, s3, s4)

    result = {
        "zone_id": zone_id,
        "zone_name": zone.name,
        "s1_environmental": {
            "status": "firing" if s1["breached"] else "inactive",
            "value": f"Rainfall: {weather['rainfall_mm_hr']:.0f}mm/hr",
            "threshold": ">65mm/hr",
            "raw": s1,
        },
        "s2_mobility": {
            "status": "firing" if s2["breached"] else "inactive",
            "value": f"Mobility: {s2['value']:.0f}% of baseline",
            "threshold": "<25% of baseline",
            "raw": s2,
        },
        "s3_economic": {
            "status": "firing" if s3["breached"] else "inactive",
            "value": f"Orders: {s3['value']:.0f}% of baseline",
            "threshold": "<30% of baseline",
            "raw": s3,
        },
        "s4_crowd": {
            "status": "firing" if s4["breached"] else "inactive",
            "value": f"Check-ins: {s4['value']:.0f}% inactivity",
            "threshold": "≥40% inactivity",
            "raw": s4,
        },
        "confidence": fusion["confidence"],
        "signals_fired": fusion["signals_fired"],
        "is_disrupted": fusion["signals_fired"] >= 2,
        "fusion": fusion,
        "weather": weather,
    }

    _signal_cache[zone_id] = result
    return result


@router.get("/{zone_id}/risk-score")
async def get_risk_score(zone_id: str, db: AsyncSession = Depends(get_db)):
    """Zone risk score with ZoneTwin counterfactual."""
    zone = await db.get(Zone, zone_id)
    if not zone:
        return {"error": "Zone not found"}

    # Get current weather for counterfactual
    signals = _signal_cache.get(zone_id)
    rainfall = 20  # default
    aqi = 100
    if signals:
        rainfall = signals.get("weather", {}).get("rainfall_mm_hr", 20)
        aqi = signals.get("weather", {}).get("aqi", 100)

    twin = counterfactual_inactivity(zone_id, rainfall, aqi)

    return {
        "zone_id": zone_id,
        "risk_score": zone.risk_score,
        "risk_tier": zone.risk_tier,
        "zone_twin": twin,
    }


def update_signal_cache(zone_id: str, data: dict):
    """Update the signal cache (used by simulator and poller)."""
    _signal_cache[zone_id] = data


def clear_signal_cache(zone_id: str):
    """Clear cached signals for a zone."""
    _signal_cache.pop(zone_id, None)
