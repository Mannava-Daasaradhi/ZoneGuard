"""Tests for ZoneRisk Scorer — premium tier boundaries, weight sum = 1.0."""

from ml.zone_risk_scorer import calculate_risk_score, calculate_zone_premium, PREMIUM_TIERS


class TestRiskScorer:
    def test_weights_sum_to_one(self):
        """All 5 factor weights must sum to exactly 1.0."""
        # Weights are internal to calculate_risk_score, verify via factor_breakdown
        result = calculate_risk_score(
            disruption_freq=5, imd_forecast_severity=50,
            rider_tenure_weeks=20, zone_classification="medium",
            recent_claims_7d=2, total_zone_riders=100,
        )
        total_weight = sum(f["weight"] for f in result["factor_breakdown"].values())
        assert abs(total_weight - 1.0) < 0.001

    def test_low_risk_zone(self):
        result = calculate_risk_score(
            disruption_freq=1, imd_forecast_severity=10,
            rider_tenure_weeks=52, zone_classification="low",
            recent_claims_7d=0, total_zone_riders=200,
        )
        assert result["tier"] == "low"
        assert result["premium"] == 39
        assert result["risk_score"] < 30

    def test_medium_risk_zone(self):
        result = calculate_risk_score(
            disruption_freq=3, imd_forecast_severity=40,
            rider_tenure_weeks=20, zone_classification="medium",
            recent_claims_7d=2, total_zone_riders=100,
        )
        assert result["tier"] == "medium"
        assert result["premium"] == 89
        assert 30 <= result["risk_score"] < 55

    def test_high_risk_zone(self):
        result = calculate_risk_score(
            disruption_freq=6, imd_forecast_severity=60,
            rider_tenure_weeks=10, zone_classification="high",
            recent_claims_7d=5, total_zone_riders=100,
        )
        assert result["tier"] == "high"
        assert result["premium"] == 139
        assert 55 <= result["risk_score"] < 75

    def test_flood_prone_zone(self):
        result = calculate_risk_score(
            disruption_freq=10, imd_forecast_severity=90,
            rider_tenure_weeks=2, zone_classification="flood-prone",
            recent_claims_7d=10, total_zone_riders=50,
        )
        assert result["tier"] == "flood-prone"
        assert result["premium"] == 225
        assert result["risk_score"] >= 75

    def test_risk_score_bounds(self):
        """Risk score should always be 0-100."""
        # Minimum possible
        result = calculate_risk_score(
            disruption_freq=0, imd_forecast_severity=0,
            rider_tenure_weeks=100, zone_classification="low",
            recent_claims_7d=0, total_zone_riders=1000,
        )
        assert 0 <= result["risk_score"] <= 100

        # Maximum possible
        result = calculate_risk_score(
            disruption_freq=20, imd_forecast_severity=100,
            rider_tenure_weeks=0, zone_classification="flood-prone",
            recent_claims_7d=100, total_zone_riders=10,
        )
        assert 0 <= result["risk_score"] <= 100

    def test_premium_tiers_cover_full_range(self):
        """Premium tiers should cover 0-100 without gaps."""
        ranges = sorted(PREMIUM_TIERS.keys())
        assert ranges[0][0] == 0
        assert ranges[-1][1] == 101  # 101 because range is [low, high)
        for i in range(len(ranges) - 1):
            assert ranges[i][1] == ranges[i + 1][0]

    def test_factor_breakdown_structure(self):
        result = calculate_risk_score(
            disruption_freq=5, imd_forecast_severity=50,
            rider_tenure_weeks=20, zone_classification="medium",
            recent_claims_7d=2, total_zone_riders=100,
        )
        assert "factor_breakdown" in result
        expected_factors = {"disruption_freq", "imd_forecast", "rider_tenure", "zone_class", "claim_history"}
        assert set(result["factor_breakdown"].keys()) == expected_factors
        for factor in result["factor_breakdown"].values():
            assert "weight" in factor
            assert "raw_score" in factor
            assert "contribution" in factor

    def test_zone_premium_convenience(self):
        result = calculate_zone_premium(
            {"historical_disruptions": 3, "risk_tier": "medium", "active_riders": 100}
        )
        assert "premium" in result
        assert "tier" in result
        assert "max_payout" in result

    def test_tenure_discount(self):
        """Longer tenure should lower risk score."""
        new_rider = calculate_risk_score(
            disruption_freq=3, imd_forecast_severity=40,
            rider_tenure_weeks=0, zone_classification="medium",
            recent_claims_7d=2, total_zone_riders=100,
        )
        veteran = calculate_risk_score(
            disruption_freq=3, imd_forecast_severity=40,
            rider_tenure_weeks=52, zone_classification="medium",
            recent_claims_7d=2, total_zone_riders=100,
        )
        assert new_rider["risk_score"] > veteran["risk_score"]
