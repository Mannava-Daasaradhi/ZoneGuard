"""
FraudShield v1.5 — Heuristic anomaly detection + Temporal Clustering Ring Detection.

Individual claim scoring (8 features):
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

Ring Detection (temporal clustering):
- Genuine disruptions → Poisson-distributed claim arrival times
- Coordinated fraud rings → tight temporal spike (Telegram "go now" pattern)
- Clustering coefficient on 5-minute-bucket timestamp graph detects coordination
"""

import math
import numpy as np
from datetime import datetime, timezone
from collections import defaultdict
from typing import List, Optional


# ---------------------------------------------------------------------------
# Individual Claim Scoring (v1 — rule-based heuristics)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Temporal Clustering Ring Detection
# ---------------------------------------------------------------------------

BUCKET_SIZE_MINUTES = 5
SPIKE_WINDOW_MINUTES = 15
SPIKE_THRESHOLD_COUNT = 8
COORDINATION_CC_THRESHOLD = 0.45
MIN_ZONE_CLAIMS_FOR_ANALYSIS = 5
POISSON_DEVIATION_THRESHOLD = 3.5


def _bucket_timestamps(timestamps: List[datetime], bucket_minutes: int = BUCKET_SIZE_MINUTES) -> dict:
    if not timestamps:
        return {}
    earliest = min(timestamps)
    buckets = defaultdict(list)
    for ts in timestamps:
        delta_minutes = (ts - earliest).total_seconds() / 60
        bucket_idx = int(delta_minutes // bucket_minutes)
        buckets[bucket_idx].append(ts)
    return dict(buckets)


def _compute_inter_arrival_stats(timestamps: List[datetime]) -> dict:
    if len(timestamps) < 2:
        return {"mean_gap_seconds": None, "cv": None, "min_gap_seconds": None}
    sorted_ts = sorted(timestamps)
    gaps = [
        (sorted_ts[i + 1] - sorted_ts[i]).total_seconds()
        for i in range(len(sorted_ts) - 1)
    ]
    mean_gap = float(np.mean(gaps))
    std_gap = float(np.std(gaps))
    cv = std_gap / mean_gap if mean_gap > 0 else 0.0
    return {
        "mean_gap_seconds": round(mean_gap, 1),
        "std_gap_seconds": round(std_gap, 1),
        "min_gap_seconds": round(min(gaps), 1),
        "cv": round(cv, 3),
    }


def _clustering_coefficient(buckets: dict) -> float:
    if len(buckets) < 2:
        return 0.0
    bucket_ids = sorted(buckets.keys())
    n = len(bucket_ids)
    adjacent_pairs = 0
    for i in range(len(bucket_ids) - 1):
        if bucket_ids[i + 1] - bucket_ids[i] == 1:
            adjacent_pairs += 1
    max_adjacent = n - 1
    if max_adjacent == 0:
        return 0.0
    return round(adjacent_pairs / max_adjacent, 3)


def _spike_detector(buckets: dict, window_buckets: int = 3) -> dict:
    bucket_ids = sorted(buckets.keys())
    max_spike_count = 0
    spike_bucket_start = None
    for i, b in enumerate(bucket_ids):
        window_count = sum(
            len(buckets.get(b + offset, []))
            for offset in range(window_buckets)
        )
        if window_count > max_spike_count:
            max_spike_count = window_count
            spike_bucket_start = b
    return {
        "max_spike_count": max_spike_count,
        "spike_bucket_start": spike_bucket_start,
        "spike_window_minutes": window_buckets * BUCKET_SIZE_MINUTES,
        "spike_threshold": SPIKE_THRESHOLD_COUNT,
        "spike_detected": max_spike_count >= SPIKE_THRESHOLD_COUNT,
    }


def _poisson_z_score(observed_count: int, expected_mean: float) -> float:
    if expected_mean <= 0:
        return 0.0
    return (observed_count - expected_mean) / math.sqrt(expected_mean)


def detect_coordination_ring(
    zone_id: str,
    claim_timestamps: List[datetime],
    expected_claims_mean: Optional[float] = None,
) -> dict:
    """
    Analyze claim timestamps from one zone during an event window to determine
    whether they represent a genuine disruption or a coordinated fraud ring.
    """
    ring_signals = []
    confidence = 0.0

    if len(claim_timestamps) < MIN_ZONE_CLAIMS_FOR_ANALYSIS:
        return {
            "zone_id": zone_id,
            "claim_count": len(claim_timestamps),
            "verdict": "insufficient_data",
            "confidence": 0.0,
            "ring_signals": [],
            "inter_arrival": {},
            "clustering_coefficient": 0.0,
            "spike": {},
            "poisson_z_score": None,
            "recommendation": "Need ≥5 claims in window for ring analysis.",
        }

    buckets = _bucket_timestamps(claim_timestamps)
    inter_arrival = _compute_inter_arrival_stats(claim_timestamps)
    cc = _clustering_coefficient(buckets)
    spike = _spike_detector(buckets)

    cv = inter_arrival.get("cv", 1.0)
    if cv is not None and cv < 0.30:
        ring_signals.append(
            f"inter-arrival CV={cv:.2f} (< 0.30 — highly synchronized; "
            f"genuine disruption CV ≈ 1.0)"
        )
        confidence += 0.35

    if spike.get("spike_detected"):
        ring_signals.append(
            f"temporal spike: {spike['max_spike_count']} claims in "
            f"{spike['spike_window_minutes']} minutes "
            f"(threshold: {SPIKE_THRESHOLD_COUNT})"
        )
        confidence += 0.30

    if cc > COORDINATION_CC_THRESHOLD:
        ring_signals.append(
            f"clustering coefficient={cc:.2f} > {COORDINATION_CC_THRESHOLD} "
            f"(claims bunched in adjacent time windows)"
        )
        confidence += 0.20

    poisson_z = None
    if expected_claims_mean is not None:
        poisson_z = _poisson_z_score(len(claim_timestamps), expected_claims_mean)
        if poisson_z > POISSON_DEVIATION_THRESHOLD:
            ring_signals.append(
                f"ZoneTwin z-score={poisson_z:.1f} "
                f"(observed {len(claim_timestamps)} claims vs expected "
                f"~{expected_claims_mean:.0f} — {poisson_z:.1f}σ deviation)"
            )
            confidence += 0.25

    confidence = min(1.0, confidence)

    if confidence >= 0.70:
        verdict = "ring_detected"
        recommendation = (
            "HOLD all payouts in this batch. Trigger senior FraudShield review. "
            "Do NOT notify riders — ring investigation must not tip off the syndicate. "
            "Clear innocent riders within 4 hours of batch review completion."
        )
    elif confidence >= 0.35:
        verdict = "suspicious"
        recommendation = (
            "Apply TIER 2 soft hold. Send WhatsApp verification to each rider. "
            "Genuine workers in bad weather will confirm; scammers will not reply."
        )
    else:
        verdict = "genuine"
        recommendation = (
            "Claim pattern consistent with genuine zone disruption. "
            "Proceed with auto-payout for HIGH-confidence zone signals."
        )

    return {
        "zone_id": zone_id,
        "claim_count": len(claim_timestamps),
        "verdict": verdict,
        "confidence": round(confidence, 3),
        "ring_signals": ring_signals,
        "inter_arrival": inter_arrival,
        "clustering_coefficient": cc,
        "spike": spike,
        "poisson_z_score": round(poisson_z, 2) if poisson_z is not None else None,
        "recommendation": recommendation,
    }


# ---------------------------------------------------------------------------
# Convenience: combined analysis for a claim batch
# ---------------------------------------------------------------------------

def analyze_zone_event_batch(
    zone_id: str,
    claims: List[dict],
    expected_claims_mean: Optional[float] = None,
) -> dict:
    """
    Run both individual scoring + ring detection on a batch of claims
    from a single zone event.

    FIX (vs original): The summary logic now correctly handles all four
    verdict states — 'ring_detected', 'suspicious', 'insufficient_data',
    and 'genuine'.  Previously, 'suspicious' and 'insufficient_data' fell
    through to the final else-branch which incorrectly said "Approved for
    auto-payout."  That was a logic inversion: the ring detector had flagged
    the batch as uncertain but the summary was telling operators to release it.
    """
    timestamps = [c["created_at"] for c in claims]
    ring_analysis = detect_coordination_ring(zone_id, timestamps, expected_claims_mean)

    individual_scores = []
    high_risk_ids = []

    for claim in claims:
        score_result = calculate_fraud_score(
            claim_hour=claim["claim_hour"],
            tenure_weeks=claim["tenure_weeks"],
            zone_inactivity_pct=claim["zone_inactivity_pct"],
            claim_velocity_7d=claim["claim_velocity_7d"],
            zone_claim_rate_deviation=claim["zone_claim_rate_deviation"],
            distance_from_centroid_km=claim["distance_from_centroid_km"],
            s1_value=claim["s1_value"],
            days_since_policy_start=claim["days_since_policy_start"],
        )
        score_result["claim_id"] = claim["claim_id"]
        individual_scores.append(score_result)

        if score_result["risk_level"] in ("review", "hold"):
            high_risk_ids.append(claim["claim_id"])

    verdict = ring_analysis["verdict"]
    high_risk_count = len(high_risk_ids)

    # -------------------------------------------------------------------
    # FIXED summary logic.
    # Each verdict branch has a distinct, accurate message.
    # The original code let 'suspicious' and 'insufficient_data' fall
    # through to "Approved for auto-payout" which was incorrect.
    # -------------------------------------------------------------------
    if verdict == "ring_detected":
        summary = (
            f"⚠️  RING DETECTED in zone {zone_id}: "
            f"{len(claims)} claims show coordinated fraud pattern "
            f"(confidence {ring_analysis['confidence']:.0%}). "
            f"All payouts held pending investigation."
        )
    elif verdict == "suspicious":
        # Coordination signals present but below ring_detected threshold.
        # Do NOT auto-approve — hold for soft verification.
        summary = (
            f"Zone {zone_id}: {len(claims)} claims processed. "
            f"Batch-level coordination signals detected "
            f"(confidence {ring_analysis['confidence']:.0%}). "
            f"Hold for WhatsApp soft-verification before payout."
        )
    elif verdict == "insufficient_data":
        # Not enough claims to run ring analysis. Cannot conclude either way.
        summary = (
            f"Zone {zone_id}: {len(claims)} claims processed. "
            f"Insufficient claim volume for ring analysis (need ≥{MIN_ZONE_CLAIMS_FOR_ANALYSIS}). "
            f"Individual scores used only — do not batch-approve without zone-level signal."
        )
    elif high_risk_count > 0:
        # Genuine batch verdict but individual flags exist.
        summary = (
            f"Zone {zone_id}: {len(claims)} claims processed. "
            f"{high_risk_count} individual high-risk claim(s) flagged for review. "
            f"Ring pattern: {verdict}."
        )
    else:
        # Genuine batch verdict, no individual flags — safe to auto-payout.
        summary = (
            f"Zone {zone_id}: {len(claims)} claims processed. "
            f"No ring detected. No individual high-risk flags. "
            f"Approved for auto-payout."
        )

    return {
        "ring_analysis": ring_analysis,
        "individual_scores": individual_scores,
        "high_risk_claim_ids": high_risk_ids,
        "summary": summary,
    }
