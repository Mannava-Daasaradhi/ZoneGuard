"""
Background signal polling service.

Polls all zones for current signal data and evaluates disruption conditions.
In production, this would run as a Celery beat task every 15 minutes.
"""

from integrations.weather import get_current_weather
from integrations.mobility_sim import calculate_mobility_index
from integrations.order_sim import simulate_order_volume
from integrations.whatsapp_sim import simulate_checkins


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
