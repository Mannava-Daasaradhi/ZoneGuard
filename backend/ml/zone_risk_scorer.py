"""
ZoneRisk Scorer — Weighted rule-based risk model.

5 factors with transparent weights:
- disruption_freq (35%): historical disruption frequency for the zone
- imd_forecast (25%): IMD seasonal forecast severity
- rider_tenure (15%): rider's tenure in weeks (lower = higher risk)
- zone_class (15%): zone classification risk level
- claim_history (10%): recent claim volume for the zone

Output: risk score 0-100 → premium tier (₹29/₹49/₹69/₹99)
"""

PREMIUM_TIERS = {
    (0, 30): {"premium": 29, "tier": "low", "max_payout": 1800},
    (30, 55): {"premium": 49, "tier": "medium", "max_payout": 2200},
    (55, 75): {"premium": 69, "tier": "high", "max_payout": 2800},
    (75, 101): {"premium": 99, "tier": "flood-prone", "max_payout": 3500},
}

# Zone classification base scores
ZONE_CLASS_SCORES = {
    "low": 20,
    "medium": 50,
    "high": 70,
    "flood-prone": 90,
}


def calculate_risk_score(
    disruption_freq: int,        # historical disruptions per year
    imd_forecast_severity: float, # 0-100 severity from IMD
    rider_tenure_weeks: int,
    zone_classification: str,
    recent_claims_7d: int,
    total_zone_riders: int,
) -> dict:
    """Calculate zone risk score with full factor breakdown."""

    # Factor 1: Disruption frequency (35%)
    # Scale: 0 disruptions = 0, 10+ = 100
    disrupt_score = min(100, (disruption_freq / 10) * 100)

    # Factor 2: IMD forecast (25%)
    imd_score = min(100, imd_forecast_severity)

    # Factor 3: Rider tenure (15%)
    # New riders = higher risk, capped at 52 weeks
    tenure_score = max(0, 100 - (min(rider_tenure_weeks, 52) / 52 * 100))

    # Factor 4: Zone classification (15%)
    zone_score = ZONE_CLASS_SCORES.get(zone_classification, 50)

    # Factor 5: Claim history (10%)
    # Claims as % of riders, scaled
    claim_rate = (recent_claims_7d / max(total_zone_riders, 1)) * 100
    claim_score = min(100, claim_rate * 10)  # 10% claim rate = 100

    # Weighted total
    weights = {
        "disruption_freq": 0.35,
        "imd_forecast": 0.25,
        "rider_tenure": 0.15,
        "zone_class": 0.15,
        "claim_history": 0.10,
    }

    scores = {
        "disruption_freq": disrupt_score,
        "imd_forecast": imd_score,
        "rider_tenure": tenure_score,
        "zone_class": zone_score,
        "claim_history": claim_score,
    }

    total_score = sum(scores[k] * weights[k] for k in weights)
    total_score = round(min(100, max(0, total_score)))

    # Determine premium tier
    tier_info = {"premium": 49, "tier": "medium", "max_payout": 2200}
    for (low, high), info in PREMIUM_TIERS.items():
        if low <= total_score < high:
            tier_info = info
            break

    factor_breakdown = {}
    for k in weights:
        contribution = round(scores[k] * weights[k], 1)
        factor_breakdown[k] = {
            "weight": weights[k],
            "raw_score": round(scores[k], 1),
            "contribution": contribution,
            "contribution_inr": round(contribution * tier_info["premium"] / 100, 1),
        }

    return {
        "risk_score": total_score,
        "premium": tier_info["premium"],
        "tier": tier_info["tier"],
        "max_payout": tier_info["max_payout"],
        "factor_breakdown": factor_breakdown,
    }


def calculate_zone_premium(zone_data: dict, rider_tenure_weeks: int = 0) -> dict:
    """Convenience function for zone-based premium calculation."""
    return calculate_risk_score(
        disruption_freq=zone_data.get("historical_disruptions", 3),
        imd_forecast_severity=zone_data.get("imd_severity", 40),
        rider_tenure_weeks=rider_tenure_weeks,
        zone_classification=zone_data.get("risk_tier", "medium"),
        recent_claims_7d=zone_data.get("recent_claims", 2),
        total_zone_riders=zone_data.get("active_riders", 100),
    )
