"""
Simulated WhatsApp check-in responses.

At HIGH disruption: 40-60% inactivity responses
At normal: 2-8% inactivity
"""

import random


def simulate_checkins(total_riders: int, disruption_severity: float) -> dict:
    """
    Simulate WhatsApp rider check-in responses.

    disruption_severity: 0.0 (normal) to 1.0 (extreme disruption)
    """

    # Response rate: 60-90% of riders respond
    response_rate = random.uniform(0.60, 0.90)
    respondents = int(total_riders * response_rate)

    # Inactivity rate based on disruption severity
    # Normal: 2-8%, Mild: 15-25%, Moderate: 30-45%, Severe: 45-65%
    if disruption_severity > 0.8:
        base_inactive_pct = random.uniform(0.45, 0.65)
    elif disruption_severity > 0.5:
        base_inactive_pct = random.uniform(0.30, 0.45)
    elif disruption_severity > 0.2:
        base_inactive_pct = random.uniform(0.15, 0.25)
    else:
        base_inactive_pct = random.uniform(0.02, 0.08)

    inactive_riders = int(respondents * base_inactive_pct)
    active_riders = respondents - inactive_riders

    return {
        "total_riders": total_riders,
        "respondents": respondents,
        "response_rate_pct": round(response_rate * 100, 1),
        "inactive_riders": inactive_riders,
        "active_riders": active_riders,
        "inactivity_pct": round((inactive_riders / max(total_riders, 1)) * 100, 1),
        "source": "simulated_whatsapp",
    }
