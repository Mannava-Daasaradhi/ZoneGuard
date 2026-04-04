"""
Simulated OSRM mobility index.

Mobility inversely correlates with weather severity.
Formula: mobility_index = max(5, 100 - (rainfall_factor * 0.6 + aqi_factor * 0.3 + temp_factor * 0.1))
"""

import random


def calculate_mobility_index(
    rainfall_mm: float,
    aqi: float,
    temp_c: float,
    baseline: float = 100,
) -> dict:
    """Calculate simulated mobility index based on weather conditions."""

    # Rainfall impact: exponential increase above threshold
    rainfall_factor = min(100, (rainfall_mm / 65) * 80) if rainfall_mm > 10 else rainfall_mm * 0.5

    # AQI impact: significant above 200
    aqi_factor = min(100, max(0, (aqi - 100) / 3))

    # Temperature impact: significant above 40°C
    temp_factor = min(100, max(0, (temp_c - 35) * 12))

    # Weighted disruption
    disruption = rainfall_factor * 0.6 + aqi_factor * 0.3 + temp_factor * 0.1

    # Add gaussian noise for realism
    noise = random.gauss(0, 3)
    mobility_index = max(5, min(100, 100 - disruption + noise))

    return {
        "mobility_index": round(mobility_index, 1),
        "baseline": baseline,
        "pct_of_baseline": round((mobility_index / baseline) * 100, 1),
        "factors": {
            "rainfall_impact": round(rainfall_factor, 1),
            "aqi_impact": round(aqi_factor, 1),
            "temp_impact": round(temp_factor, 1),
        },
        "source": "simulated_osrm",
    }
