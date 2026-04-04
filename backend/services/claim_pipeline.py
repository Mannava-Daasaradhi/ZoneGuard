"""
End-to-end claim pipeline: signal → disruption → exclusion check → fraud check → payout.

This is the core orchestrator that ties together SignalFusion, ExclusionEngine,
FraudShield, ZoneTwin, Gemini audit, and PayoutSim.
"""

from datetime import datetime, timezone
from ml.signal_fusion import fuse_signals, evaluate_s1, evaluate_s2, evaluate_s3, evaluate_s4
from ml.fraud_shield import calculate_fraud_score
from ml.zone_twin import counterfactual_inactivity
from services.exclusion_engine import evaluate_claim_exclusions
from integrations.gemini import generate_audit_report
from integrations.payout_sim import process_payout
import uuid


async def process_disruption_event(
    zone_id: str,
    zone_data: dict,
    weather_data: dict,
    mobility_data: dict,
    order_data: dict,
    checkin_data: dict,
    riders_with_policies: list[dict],
) -> dict:
    """
    Full pipeline: evaluate signals → create disruption → process claims.
    """

    # Step 1: Evaluate all 4 signals
    s1 = evaluate_s1(
        rainfall_mm=weather_data["rainfall_mm_hr"],
        aqi=weather_data["aqi"],
        temp_c=weather_data["temperature_c"],
        ndma_alert=weather_data.get("ndma_alert", False),
    )
    s2 = evaluate_s2(
        mobility_index=mobility_data["mobility_index"],
        baseline=mobility_data.get("baseline", 100),
    )
    s3 = evaluate_s3(
        order_volume=order_data["order_volume"],
        baseline=order_data.get("baseline", 100),
    )
    s4 = evaluate_s4(
        inactive_riders=checkin_data["inactive_riders"],
        total_riders=checkin_data["total_riders"],
    )

    # Step 2: Fuse signals
    fusion = fuse_signals(s1, s2, s3, s4)

    # No disruption event if NOISE
    if fusion["confidence"] == "NOISE":
        return {"disruption_created": False, "fusion": fusion, "claims": []}

    # Step 3: Create disruption event record
    event_id = f"DE-{uuid.uuid4().hex[:8].upper()}"

    # Step 4: ZoneTwin counterfactual
    zone_twin = counterfactual_inactivity(
        zone_id=zone_id,
        rainfall_mm=weather_data["rainfall_mm_hr"],
        aqi=weather_data["aqi"],
    )

    # Step 5: Process claims for each eligible rider
    claims = []
    for rider in riders_with_policies:
        # Calculate payout (75% of 7-day daily average)
        daily_avg = rider.get("weekly_earnings_baseline", 2000) / 7
        payout_amount = round(daily_avg * 0.75)

        # Fraud check
        fraud = calculate_fraud_score(
            claim_hour=datetime.now(timezone.utc).hour,
            tenure_weeks=rider.get("tenure_weeks", 10),
            zone_inactivity_pct=checkin_data.get("inactivity_pct", 40),
            claim_velocity_7d=rider.get("recent_claims_7d", 0),
            zone_claim_rate_deviation=1.0,
            distance_from_centroid_km=rider.get("distance_km", 1.5),
            s1_value=weather_data["rainfall_mm_hr"],
            days_since_policy_start=rider.get("days_since_policy_start", 5),
        )

        # Exclusion check
        exclusion_check = evaluate_claim_exclusions(
            claim_data={"rider_id": rider["id"], "zone_id": zone_id},
            policy_data=rider.get("policy", {}),
            fraud_score=fraud["score"],
            consecutive_disruption_days=rider.get("consecutive_disruption_days", 0),
        )

        claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"

        # Determine claim status
        if not exclusion_check["passed"]:
            status = "rejected"
        elif fraud["risk_level"] == "hold":
            status = "held"
        elif fusion["confidence"] == "HIGH":
            status = "approved"
        elif fusion["confidence"] == "MEDIUM":
            status = "pending_review"
        else:
            status = "pending_review"

        claim = {
            "id": claim_id,
            "rider_id": rider["id"],
            "policy_id": rider.get("policy_id", ""),
            "zone_id": zone_id,
            "disruption_event_id": event_id,
            "status": status,
            "confidence": fusion["confidence"],
            "recommended_payout": payout_amount,
            "exclusion_check": exclusion_check,
            "fraud_score": fraud["score"],
            "fraud_details": fraud,
            "zone_twin": zone_twin,
        }

        # Generate audit report for MEDIUM confidence claims
        if fusion["confidence"] == "MEDIUM":
            audit = await generate_audit_report({
                "claim_id": claim_id,
                "zone_name": zone_data.get("name", zone_id),
                "zone_id": zone_id,
                "confidence": fusion["confidence"],
                "signals_fired": fusion["signals_fired"],
                "signal_details": fusion["signal_details"],
                "s1": s1, "s2": s2, "s3": s3, "s4": s4,
                "zone_twin": zone_twin,
                "exclusion_check": exclusion_check,
                "fraud_score": fraud["score"],
            })
            claim["audit_report"] = audit

        # Auto-payout for HIGH confidence approved claims
        if status == "approved" and fusion["confidence"] == "HIGH":
            payout = await process_payout(
                rider_id=rider["id"],
                amount=payout_amount,
                upi_id=rider.get("upi_id"),
            )
            claim["payout"] = payout

        claims.append(claim)

    return {
        "disruption_created": True,
        "event_id": event_id,
        "fusion": fusion,
        "zone_twin": zone_twin,
        "claims_count": len(claims),
        "claims": claims,
    }
