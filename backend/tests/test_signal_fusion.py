"""Tests for QuadSignal Fusion Engine — all threshold combinations and NDMA override."""

from ml.signal_fusion import evaluate_s1, evaluate_s2, evaluate_s3, evaluate_s4, fuse_signals, THRESHOLDS


class TestEvaluateS1:
    def test_rainfall_breach(self):
        result = evaluate_s1(rainfall_mm=80, aqi=100, temp_c=30)
        assert result["breached"] is True
        assert "rainfall" in result["reason"]

    def test_aqi_breach(self):
        result = evaluate_s1(rainfall_mm=10, aqi=350, temp_c=30)
        assert result["breached"] is True
        assert "AQI" in result["reason"]

    def test_temp_breach(self):
        result = evaluate_s1(rainfall_mm=10, aqi=100, temp_c=45)
        assert result["breached"] is True
        assert "temp" in result["reason"]

    def test_no_breach(self):
        result = evaluate_s1(rainfall_mm=10, aqi=100, temp_c=30)
        assert result["breached"] is False

    def test_ndma_override(self):
        result = evaluate_s1(rainfall_mm=0, aqi=50, temp_c=25, ndma_alert=True)
        assert result["breached"] is True
        assert result["reason"] == "ndma_override"

    def test_boundary_rainfall(self):
        # Exactly at threshold should NOT breach (>65, not >=65)
        result = evaluate_s1(rainfall_mm=65, aqi=100, temp_c=30)
        assert result["breached"] is False
        result = evaluate_s1(rainfall_mm=65.1, aqi=100, temp_c=30)
        assert result["breached"] is True

    def test_multiple_breaches(self):
        result = evaluate_s1(rainfall_mm=80, aqi=350, temp_c=45)
        assert result["breached"] is True
        assert "rainfall" in result["reason"]
        assert "AQI" in result["reason"]
        assert "temp" in result["reason"]


class TestEvaluateS2:
    def test_mobility_breach(self):
        # mobility_index=20 on baseline=100 → 20% of baseline (< 25% threshold)
        result = evaluate_s2(mobility_index=20, baseline=100)
        assert result["breached"] is True

    def test_no_breach(self):
        result = evaluate_s2(mobility_index=50, baseline=100)
        assert result["breached"] is False

    def test_boundary(self):
        # 25% of baseline = exactly at threshold (< 25, not <=)
        result = evaluate_s2(mobility_index=25, baseline=100)
        assert result["breached"] is False
        result = evaluate_s2(mobility_index=24.9, baseline=100)
        assert result["breached"] is True


class TestEvaluateS3:
    def test_order_breach(self):
        # 20% of baseline (< 30% threshold)
        result = evaluate_s3(order_volume=20, baseline=100)
        assert result["breached"] is True

    def test_no_breach(self):
        result = evaluate_s3(order_volume=50, baseline=100)
        assert result["breached"] is False

    def test_boundary(self):
        result = evaluate_s3(order_volume=30, baseline=100)
        assert result["breached"] is False
        result = evaluate_s3(order_volume=29.9, baseline=100)
        assert result["breached"] is True


class TestEvaluateS4:
    def test_crowd_breach(self):
        result = evaluate_s4(inactive_riders=50, total_riders=100)
        assert result["breached"] is True

    def test_no_breach(self):
        result = evaluate_s4(inactive_riders=30, total_riders=100)
        assert result["breached"] is False

    def test_boundary(self):
        # >= 40% threshold
        result = evaluate_s4(inactive_riders=40, total_riders=100)
        assert result["breached"] is True
        result = evaluate_s4(inactive_riders=39, total_riders=100)
        assert result["breached"] is False


class TestFuseSignals:
    def _make_signal(self, breached: bool):
        return {"breached": breached, "value": 0, "threshold": 0, "details": {}, "reason": "test"}

    def test_4_signals_high(self):
        s = self._make_signal(True)
        result = fuse_signals(s, s, s, s)
        assert result["confidence"] == "HIGH"
        assert result["signals_fired"] == 4
        assert result["should_auto_payout"] is True

    def test_3_signals_medium(self):
        y, n = self._make_signal(True), self._make_signal(False)
        result = fuse_signals(y, y, y, n)
        assert result["confidence"] == "MEDIUM"
        assert result["signals_fired"] == 3
        assert result["should_recheck"] is True

    def test_2_signals_low(self):
        y, n = self._make_signal(True), self._make_signal(False)
        result = fuse_signals(y, y, n, n)
        assert result["confidence"] == "LOW"
        assert result["signals_fired"] == 2
        assert result["needs_review"] is True

    def test_1_signal_noise(self):
        y, n = self._make_signal(True), self._make_signal(False)
        result = fuse_signals(y, n, n, n)
        assert result["confidence"] == "NOISE"
        assert result["signals_fired"] == 1

    def test_0_signals_noise(self):
        n = self._make_signal(False)
        result = fuse_signals(n, n, n, n)
        assert result["confidence"] == "NOISE"
        assert result["signals_fired"] == 0

    def test_timestamp_present(self):
        s = self._make_signal(True)
        result = fuse_signals(s, s, s, s)
        assert "timestamp" in result
