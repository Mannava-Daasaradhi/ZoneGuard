"""Tests for FraudShield anomaly detection — known inputs, threshold verification."""

from ml.fraud_shield import calculate_fraud_score


class TestFraudScore:
    def _normal_claim(self, **overrides):
        defaults = {
            "claim_hour": 14,
            "tenure_weeks": 30,
            "zone_inactivity_pct": 45.0,
            "claim_velocity_7d": 1,
            "zone_claim_rate_deviation": 1.0,
            "distance_from_centroid_km": 2.0,
            "s1_value": 70.0,
            "days_since_policy_start": 30,
        }
        defaults.update(overrides)
        return calculate_fraud_score(**defaults)

    def test_normal_claim_low_risk(self):
        result = self._normal_claim()
        assert result["risk_level"] == "low"
        assert result["score"] < 0.65

    def test_suspicious_timing(self):
        result = self._normal_claim(claim_hour=3)
        assert result["score"] > 0
        assert any("hour" in s for s in result["anomaly_signals"])

    def test_new_policy_flag(self):
        result = self._normal_claim(days_since_policy_start=1)
        assert result["score"] >= 0.20
        assert any("policy" in s for s in result["anomaly_signals"])

    def test_high_velocity_flag(self):
        result = self._normal_claim(claim_velocity_7d=4)
        assert result["score"] >= 0.25
        assert any("claims" in s for s in result["anomaly_signals"])

    def test_low_inactivity_flag(self):
        result = self._normal_claim(zone_inactivity_pct=10)
        assert any("inactive" in s for s in result["anomaly_signals"])

    def test_hold_threshold(self):
        """Score > 0.85 should trigger 'hold' risk level."""
        result = self._normal_claim(
            claim_hour=3,
            days_since_policy_start=1,
            claim_velocity_7d=4,
            zone_inactivity_pct=10,
            s1_value=20,
            tenure_weeks=1,
        )
        assert result["risk_level"] == "hold"
        assert result["score"] > 0.85

    def test_review_threshold(self):
        """Score > 0.65 but <= 0.85 should trigger 'review'."""
        result = self._normal_claim(
            claim_hour=3,
            days_since_policy_start=1,
            claim_velocity_7d=3,
            zone_claim_rate_deviation=2.5,
            s1_value=20,
        )
        assert result["risk_level"] == "review"
        assert 0.65 < result["score"] <= 0.85

    def test_score_capped_at_1(self):
        """Score should never exceed 1.0 no matter how many flags."""
        result = self._normal_claim(
            claim_hour=3,
            days_since_policy_start=0,
            claim_velocity_7d=5,
            zone_claim_rate_deviation=3.0,
            zone_inactivity_pct=5,
            distance_from_centroid_km=10,
            s1_value=10,
            tenure_weeks=1,
        )
        assert result["score"] <= 1.0

    def test_features_returned(self):
        result = self._normal_claim()
        assert "features" in result
        assert result["features"]["claim_hour"] == 14
        assert result["features"]["tenure_weeks"] == 30
