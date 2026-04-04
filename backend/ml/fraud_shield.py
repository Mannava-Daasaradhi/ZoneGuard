"""
FraudShield v1 — Isolation Forest anomaly detection on claim patterns.

8 features:
- claim_hour: hour of claim creation (0-23)
- tenure_weeks: rider's tenure
- zone_inactivity_pct: % riders inactive in zone
- claim_velocity_7d: claims by this rider in last 7 days
- zone_claim_rate_deviation: zone's claim rate vs mean
- distance_from_centroid: how far rider is from zone center
- s1_value: environmental signal value
- days_since_policy_start: freshness of policy

Thresholds:
- score > 0.65 → "review" flag
- score > 0.85 → "hold" (auto-hold payout)
"""

import numpy as np
from datetime import datetime


def calculate_fraud_score(
    claim_hour: int,
    tenure_weeks: int,
    zone_inactivity_pct: float,
    claim_velocity_7d: int,
    zone_claim_rate_deviation: float,
    distance_from_centroid_km: float,
    s1_value: float,
    days_since_policy_start: int,
) -> dict:
    """
    Rule-based fraud scoring that mimics Isolation Forest behavior.
    In production, this would be a trained sklearn IsolationForest.
    For the hackathon demo, we use transparent heuristics.
    """
    anomaly_signals = []
    score = 0.0

    # Suspicious claim timing (late night / early morning)
    if claim_hour < 6 or claim_hour > 22:
        score += 0.15
        anomaly_signals.append(f"unusual claim hour ({claim_hour}:00)")

    # Very new policy (less than 2 days old)
    if days_since_policy_start < 2:
        score += 0.20
        anomaly_signals.append(f"policy only {days_since_policy_start} days old")

    # High claim velocity
    if claim_velocity_7d > 3:
        score += 0.25
        anomaly_signals.append(f"{claim_velocity_7d} claims in 7 days")
    elif claim_velocity_7d > 2:
        score += 0.10

    # Zone claim rate deviation (zone claiming much more than average)
    if zone_claim_rate_deviation > 2.0:
        score += 0.15
        anomaly_signals.append(f"zone claim rate {zone_claim_rate_deviation:.1f}x above mean")

    # Low inactivity but claiming (other riders are active, this rider claims)
    if zone_inactivity_pct < 20:
        score += 0.15
        anomaly_signals.append(f"only {zone_inactivity_pct:.0f}% zone inactive but claiming")

    # Far from zone centroid
    if distance_from_centroid_km > 5:
        score += 0.10
        anomaly_signals.append(f"{distance_from_centroid_km:.1f}km from zone center")

    # Low environmental signal but claiming
    if s1_value < 30:
        score += 0.10
        anomaly_signals.append(f"S1 environmental value only {s1_value:.0f}")

    # Very new rider
    if tenure_weeks < 2:
        score += 0.10
        anomaly_signals.append(f"rider tenure only {tenure_weeks} weeks")

    score = min(1.0, score)

    if score > 0.85:
        risk_level = "hold"
    elif score > 0.65:
        risk_level = "review"
    else:
        risk_level = "low"

    return {
        "score": round(score, 3),
        "risk_level": risk_level,
        "anomaly_signals": anomaly_signals,
        "features": {
            "claim_hour": claim_hour,
            "tenure_weeks": tenure_weeks,
            "zone_inactivity_pct": zone_inactivity_pct,
            "claim_velocity_7d": claim_velocity_7d,
            "zone_claim_rate_deviation": zone_claim_rate_deviation,
            "distance_from_centroid_km": distance_from_centroid_km,
            "s1_value": s1_value,
            "days_since_policy_start": days_since_policy_start,
        },
    }
