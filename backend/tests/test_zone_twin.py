"""Tests for ZoneTwin counterfactual simulation — p10 < p50 < p90, known zones."""

from ml.zone_twin import counterfactual_inactivity, ZONE_BASELINES


class TestZoneTwin:
    def test_all_zones_have_baselines(self):
        """All 10 seeded zones should have baselines."""
        expected = {"hsr", "koramangala", "whitefield", "indiranagar", "electronic-city",
                    "bellandur", "btm-layout", "jp-nagar", "yelahanka", "hebbal"}
        assert expected == set(ZONE_BASELINES.keys())

    def test_percentile_ordering(self):
        """p10 < p50 < p90 for any zone."""
        result = counterfactual_inactivity("bellandur", rainfall_mm=80)
        p = result["expected_inactivity"]
        assert p["p10"] <= p["p50"] <= p["p90"]

    def test_high_rainfall_high_inactivity(self):
        """Bellandur (flood-prone, correlation=0.94) at heavy rain should show high inactivity."""
        result = counterfactual_inactivity("bellandur", rainfall_mm=100)
        assert result["expected_inactivity"]["p50"] > 30

    def test_low_rainfall_low_inactivity(self):
        """Whitefield (low risk, correlation=0.45) at normal rain should show low inactivity."""
        result = counterfactual_inactivity("whitefield", rainfall_mm=5)
        assert result["expected_inactivity"]["p50"] < 20

    def test_unknown_zone_fallback(self):
        """Unknown zone should fall back to HSR baselines."""
        result = counterfactual_inactivity("nonexistent_zone", rainfall_mm=50)
        assert result["zone_id"] == "nonexistent_zone"
        assert "expected_inactivity" in result

    def test_aqi_contribution(self):
        """High AQI should increase expected inactivity."""
        normal = counterfactual_inactivity("hsr", rainfall_mm=30, aqi=100)
        high_aqi = counterfactual_inactivity("hsr", rainfall_mm=30, aqi=350)
        assert high_aqi["expected_inactivity"]["p50"] > normal["expected_inactivity"]["p50"]

    def test_percentile_bounds(self):
        """Percentiles should be within [0, 100]."""
        for zone_id in ZONE_BASELINES:
            result = counterfactual_inactivity(zone_id, rainfall_mm=200, aqi=500)
            p = result["expected_inactivity"]
            assert 0 <= p["p10"] <= 100
            assert 0 <= p["p50"] <= 100
            assert 0 <= p["p90"] <= 100

    def test_interpretation_present(self):
        result = counterfactual_inactivity("bellandur", rainfall_mm=80)
        assert "interpretation" in result
        assert len(result["interpretation"]) > 0

    def test_historical_baseline_returned(self):
        result = counterfactual_inactivity("hsr", rainfall_mm=30)
        b = result["historical_baseline"]
        assert "avg_inactivity_pct" in b
        assert "disruption_threshold_mm" in b
        assert "flood_correlation" in b

    def test_flood_prone_vs_low_risk(self):
        """Bellandur (flood-prone) at same conditions should show more inactivity than Whitefield (low)."""
        bellandur = counterfactual_inactivity("bellandur", rainfall_mm=60)
        whitefield = counterfactual_inactivity("whitefield", rainfall_mm=60)
        assert bellandur["expected_inactivity"]["p50"] > whitefield["expected_inactivity"]["p50"]
