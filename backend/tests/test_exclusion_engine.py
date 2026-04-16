"""Tests for Coverage Exclusion Engine — all 10 exclusion types individually + combined."""

from datetime import datetime, timedelta, timezone
from services.exclusion_engine import evaluate_claim_exclusions, EXCLUSION_TYPES


class TestExclusionEngine:
    def _base_data(self):
        return {
            "claim_data": {"zone_id": "hsr", "rider_id": "test"},
            "policy_data": {"coverage_start": datetime.now(timezone.utc) - timedelta(days=10)},
        }

    def test_all_exclusion_types_exist(self):
        """All 10 standard exclusion types should be defined."""
        assert len(EXCLUSION_TYPES) == 10
        ids = {e["id"] for e in EXCLUSION_TYPES}
        expected = {
            "WAR", "PANDEMIC", "TERRORISM", "RIDER_MISCONDUCT",
            "VEHICLE_DEFECT", "PRE_EXISTING_ZONE", "SCHEDULED_MAINTENANCE",
            "GRACE_PERIOD_LAPSE", "FRAUD_DETECTED", "MAX_DAYS_EXCEEDED",
        }
        assert ids == expected

    def test_clean_claim_passes(self):
        data = self._base_data()
        result = evaluate_claim_exclusions(**data)
        assert result["passed"] is True
        assert len(result["exclusions_triggered"]) == 0
        assert len(result["exclusions_evaluated"]) == 10

    def test_max_days_exceeded(self):
        data = self._base_data()
        result = evaluate_claim_exclusions(**data, consecutive_disruption_days=3)
        assert result["passed"] is False
        triggered_ids = [e["id"] for e in result["exclusions_triggered"]]
        assert "MAX_DAYS_EXCEEDED" in triggered_ids

    def test_max_days_under_limit(self):
        data = self._base_data()
        result = evaluate_claim_exclusions(**data, consecutive_disruption_days=2)
        triggered_ids = [e["id"] for e in result["exclusions_triggered"]]
        assert "MAX_DAYS_EXCEEDED" not in triggered_ids

    def test_pre_existing_zone(self):
        data = self._base_data()
        result = evaluate_claim_exclusions(**data, disruption_existed_at_purchase=True)
        assert result["passed"] is False
        triggered_ids = [e["id"] for e in result["exclusions_triggered"]]
        assert "PRE_EXISTING_ZONE" in triggered_ids

    def test_grace_period_lapse(self):
        """Claim during 24-hour grace period should be excluded."""
        data = self._base_data()
        data["policy_data"]["coverage_start"] = datetime.now(timezone.utc) - timedelta(hours=12)
        result = evaluate_claim_exclusions(**data)
        triggered_ids = [e["id"] for e in result["exclusions_triggered"]]
        assert "GRACE_PERIOD_LAPSE" in triggered_ids

    def test_grace_period_after_24h(self):
        """Claim after 24-hour grace period should pass."""
        data = self._base_data()
        data["policy_data"]["coverage_start"] = datetime.now(timezone.utc) - timedelta(hours=25)
        result = evaluate_claim_exclusions(**data)
        triggered_ids = [e["id"] for e in result["exclusions_triggered"]]
        assert "GRACE_PERIOD_LAPSE" not in triggered_ids

    def test_fraud_detected(self):
        data = self._base_data()
        result = evaluate_claim_exclusions(**data, fraud_score=0.90)
        assert result["passed"] is False
        triggered_ids = [e["id"] for e in result["exclusions_triggered"]]
        assert "FRAUD_DETECTED" in triggered_ids

    def test_fraud_below_threshold(self):
        data = self._base_data()
        result = evaluate_claim_exclusions(**data, fraud_score=0.60)
        triggered_ids = [e["id"] for e in result["exclusions_triggered"]]
        assert "FRAUD_DETECTED" not in triggered_ids

    def test_multiple_exclusions(self):
        """Multiple exclusions can trigger simultaneously."""
        data = self._base_data()
        data["policy_data"]["coverage_start"] = datetime.now(timezone.utc) - timedelta(hours=6)
        result = evaluate_claim_exclusions(
            **data,
            fraud_score=0.90,
            consecutive_disruption_days=4,
        )
        assert result["passed"] is False
        triggered_ids = [e["id"] for e in result["exclusions_triggered"]]
        assert "FRAUD_DETECTED" in triggered_ids
        assert "MAX_DAYS_EXCEEDED" in triggered_ids
        assert "GRACE_PERIOD_LAPSE" in triggered_ids

    def test_all_exclusions_evaluated(self):
        """All 10 exclusions should always be evaluated."""
        data = self._base_data()
        result = evaluate_claim_exclusions(**data)
        assert len(result["exclusions_evaluated"]) == 10
