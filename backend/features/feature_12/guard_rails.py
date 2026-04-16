"""
Feature 12 — SmartClaim Autopilot: Guard Rails.

Five guard rails enforced in order after the LLM returns its decision:

  GR-1  Formula enforcement         — LLM cannot change calculated payout
  GR-2  Confidence gate             — ESCALATE if confidence < 80 %
  GR-3  Immutable reasoning audit   — full LLM output stored unconditionally
  GR-4  Human override endpoint     — supported via AutopilotRouter; recorded here
  GR-5  Statistical drift monitor   — tracks approval/rejection/escalation rates

Guard rails are pure functions / stateless helpers; they receive the current
pipeline state and mutate only the fields they own.
"""
from __future__ import annotations

import logging
import math
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from config import settings
from features.feature_12.llm_client import LLMDecisionOutput
from features.feature_12.models import AutopilotDecision

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared result container
# ---------------------------------------------------------------------------

@dataclass
class GuardRailResult:
    """Accumulates the outcome of all guard-rail checks for one pipeline run."""
    final_decision: str                        # AutopilotDecision value
    enforced_payout: float
    escalation_reason: Optional[str] = None
    triggered_rails: list[str] = field(default_factory=list)
    audit_payload: dict = field(default_factory=dict)

    @property
    def was_escalated_by_guard_rail(self) -> bool:
        return "GR-2" in self.triggered_rails


# ---------------------------------------------------------------------------
# GR-1: Formula enforcement
# ---------------------------------------------------------------------------

class FormulaEnforcementRail:
    """
    Guard Rail 1 — LLM cannot override the formula-calculated payout.

    If the LLM's payout_amount differs from calculated_payout (even by a
    floating-point rounding artefact), the calculated value wins and the
    discrepancy is recorded in the audit log.
    """

    RAIL_ID = "GR-1"
    TOLERANCE = 0.01   # cents tolerance for floating-point equality

    def apply(
        self,
        llm_output: LLMDecisionOutput,
        calculated_payout: float,
        result: GuardRailResult,
    ) -> None:
        llm_payout = llm_output.payout_amount
        delta = abs(llm_payout - calculated_payout)

        if delta > self.TOLERANCE:
            logger.warning(
                "%s: LLM proposed payout %.2f differs from calculated %.2f — enforcing calculated",
                self.RAIL_ID, llm_payout, calculated_payout,
            )
            result.triggered_rails.append(self.RAIL_ID)
            result.audit_payload[self.RAIL_ID] = {
                "llm_proposed_payout": llm_payout,
                "calculated_payout": calculated_payout,
                "delta": delta,
                "action": "payout_overridden",
            }
        else:
            result.audit_payload[self.RAIL_ID] = {"action": "payout_accepted"}

        # Always set enforced payout to the formula value
        result.enforced_payout = calculated_payout


# ---------------------------------------------------------------------------
# GR-2: Confidence gate
# ---------------------------------------------------------------------------

class ConfidenceGateRail:
    """
    Guard Rail 2 — Escalate automatically if LLM confidence < threshold.

    Default threshold: 0.80 (80 %).
    Configurable via FEATURE12_CONFIDENCE_ESCALATION_THRESHOLD.
    """

    RAIL_ID = "GR-2"

    def __init__(self, threshold: Optional[float] = None) -> None:
        self.threshold = threshold or settings.FEATURE12_CONFIDENCE_ESCALATION_THRESHOLD

    def apply(
        self,
        llm_output: LLMDecisionOutput,
        result: GuardRailResult,
    ) -> None:
        if llm_output.confidence < self.threshold:
            original = result.final_decision
            result.final_decision = AutopilotDecision.ESCALATE
            result.triggered_rails.append(self.RAIL_ID)
            reason = (
                f"LLM confidence {llm_output.confidence:.2%} below threshold "
                f"{self.threshold:.0%}; original={original}"
            )
            result.escalation_reason = reason
            result.audit_payload[self.RAIL_ID] = {
                "confidence": llm_output.confidence,
                "threshold": self.threshold,
                "original_decision": original,
                "action": "escalated",
                "reason": reason,
            }
            logger.info("%s triggered: %s", self.RAIL_ID, reason)
        else:
            result.audit_payload[self.RAIL_ID] = {
                "confidence": llm_output.confidence,
                "threshold": self.threshold,
                "action": "passed",
            }


# ---------------------------------------------------------------------------
# GR-3: Immutable reasoning audit
# ---------------------------------------------------------------------------

class ImmutableReasoningAuditRail:
    """
    Guard Rail 3 — Capture the full LLM output unconditionally.

    The audit payload is written to the IPFS audit log in Step 5.
    This rail can never suppress or redact the LLM reasoning.
    """

    RAIL_ID = "GR-3"

    def apply(
        self,
        llm_output: LLMDecisionOutput,
        claim_id: str,
        result: GuardRailResult,
    ) -> None:
        snapshot = {
            "claim_id": claim_id,
            "llm_model": llm_output.model,
            "decision": llm_output.decision,
            "confidence": llm_output.confidence,
            "reasoning": llm_output.reasoning,
            "payout_amount": llm_output.payout_amount,
            "raw_response": llm_output.raw_response,
            "input_tokens": llm_output.input_tokens,
            "output_tokens": llm_output.output_tokens,
            "latency_ms": llm_output.latency_ms,
            "captured_at": datetime.utcnow().isoformat(),
        }
        result.audit_payload[self.RAIL_ID] = snapshot
        logger.debug("%s: reasoning captured for claim %s", self.RAIL_ID, claim_id)


# ---------------------------------------------------------------------------
# GR-4: Human override support
# ---------------------------------------------------------------------------

class HumanOverrideRail:
    """
    Guard Rail 4 — Validate and record human override requests.

    The actual HTTP endpoint lives in autopilot_router.py.
    This class handles the business-logic side: validating the override
    payload and building the audit record.
    """

    RAIL_ID = "GR-4"

    VALID_DECISIONS = {d.value for d in AutopilotDecision}

    def validate_override(
        self,
        claim_id: str,
        override_decision: str,
        override_reason: str,
        overridden_by: str,
        original_decision: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """
        Validate an override request.  Returns a clean dict ready to be
        persisted as an AutopilotOverride row.

        Raises
        ------
        ValueError
            If override_decision is not a recognised AutopilotDecision.
        """
        od = override_decision.upper()
        if od not in self.VALID_DECISIONS:
            raise ValueError(
                f"Invalid override_decision '{od}'. "
                f"Must be one of {self.VALID_DECISIONS}."
            )
        if not overridden_by:
            raise ValueError("overridden_by must not be empty.")

        record = {
            "claim_id": claim_id,
            "override_decision": od,
            "override_reason": override_reason,
            "overridden_by": overridden_by,
            "original_decision": original_decision,
            "override_notes": notes or "",
            "overridden_at": datetime.utcnow().isoformat(),
            "rail_id": self.RAIL_ID,
        }
        logger.info(
            "%s: human override recorded — claim=%s decision=%s by=%s",
            self.RAIL_ID, claim_id, od, overridden_by,
        )
        return record


# ---------------------------------------------------------------------------
# GR-5: Statistical drift monitor
# ---------------------------------------------------------------------------

class StatisticalDriftMonitor:
    """
    Guard Rail 5 — Track approval / rejection / escalation rates over a
    sliding window and alert when a rate shifts by more than the configured
    threshold.

    This is an in-process monitor that stores its window in a deque.
    On production deployments this should be backed by Redis or the DB
    (AutopilotDriftSnapshot rows); the interface is identical.

    Parameters
    ----------
    window_size : int
        Number of decisions to retain in the sliding window.
    alert_threshold : float
        Maximum allowed rate delta vs previous window before an alert fires.
    """

    RAIL_ID = "GR-5"

    def __init__(
        self,
        window_size: Optional[int] = None,
        alert_threshold: Optional[float] = None,
    ) -> None:
        self.window_size = window_size or settings.FEATURE12_DRIFT_WINDOW_SIZE
        self.alert_threshold = alert_threshold or settings.FEATURE12_DRIFT_ALERT_THRESHOLD

        # Each entry: {"decision": str, "is_shadow": bool, "ts": datetime}
        self._window: deque[dict] = deque(maxlen=self.window_size)
        self._prev_rates: dict[str, float] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record(self, decision: str, is_shadow: bool = False) -> Optional[dict]:
        """
        Record a new autopilot decision and check for drift.

        Returns a drift alert dict if a rate has shifted beyond the
        configured threshold, else None.
        """
        self._window.append(
            {"decision": decision, "is_shadow": is_shadow, "ts": datetime.utcnow()}
        )

        if len(self._window) < self.window_size:
            return None   # Not enough data yet

        rates = self._compute_rates()
        alert = self._check_drift(rates)

        if alert:
            logger.warning(
                "%s DRIFT ALERT: metric=%s delta=%.4f",
                self.RAIL_ID, alert["metric"], alert["delta"],
            )

        # Rotate baseline every full window
        self._prev_rates = rates
        return alert

    def current_rates(self) -> dict[str, float]:
        """Return current approval / rejection / escalation rates."""
        return self._compute_rates()

    def snapshot(self) -> dict:
        """Full snapshot suitable for persisting as AutopilotDriftSnapshot."""
        rates = self._compute_rates()
        return {
            "window_size": len(self._window),
            "approval_rate": rates.get("APPROVE", 0.0),
            "rejection_rate": rates.get("REJECT", 0.0),
            "escalation_rate": rates.get("ESCALATE", 0.0),
            "shadow_rate": self._shadow_rate(),
            "prev_approval_rate": self._prev_rates.get("APPROVE"),
            "prev_rejection_rate": self._prev_rates.get("REJECT"),
            "prev_escalation_rate": self._prev_rates.get("ESCALATE"),
            "captured_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compute_rates(self) -> dict[str, float]:
        total = len(self._window)
        if total == 0:
            return {}
        counts: dict[str, int] = {}
        for entry in self._window:
            d = entry["decision"]
            counts[d] = counts.get(d, 0) + 1
        return {d: round(c / total, 4) for d, c in counts.items()}

    def _shadow_rate(self) -> float:
        total = len(self._window)
        if total == 0:
            return 0.0
        shadows = sum(1 for e in self._window if e["is_shadow"])
        return round(shadows / total, 4)

    def _check_drift(self, rates: dict[str, float]) -> Optional[dict]:
        if not self._prev_rates:
            return None
        worst_metric: Optional[str] = None
        worst_delta = 0.0
        for metric, rate in rates.items():
            prev = self._prev_rates.get(metric, 0.0)
            delta = abs(rate - prev)
            if delta > worst_delta:
                worst_delta = delta
                worst_metric = metric
        if worst_delta >= self.alert_threshold:
            return {
                "rail_id": self.RAIL_ID,
                "metric": worst_metric,
                "current_rate": rates.get(worst_metric, 0.0),
                "prev_rate": self._prev_rates.get(worst_metric, 0.0),
                "delta": round(worst_delta, 4),
                "threshold": self.alert_threshold,
                "window_size": len(self._window),
                "alerted_at": datetime.utcnow().isoformat(),
            }
        return None


# ---------------------------------------------------------------------------
# Orchestrator — apply all rails in sequence
# ---------------------------------------------------------------------------

class GuardRailOrchestrator:
    """
    Run all five guard rails in the correct order and return a consolidated
    GuardRailResult.

    Usage::

        orchestrator = GuardRailOrchestrator(drift_monitor=app_drift_monitor)
        result = orchestrator.run(
            llm_output=llm_output,
            calculated_payout=formula_payout,
            claim_id=claim.id,
        )
    """

    def __init__(self, drift_monitor: Optional[StatisticalDriftMonitor] = None) -> None:
        self._gr1 = FormulaEnforcementRail()
        self._gr2 = ConfidenceGateRail()
        self._gr3 = ImmutableReasoningAuditRail()
        self._gr4 = HumanOverrideRail()
        self._drift = drift_monitor or StatisticalDriftMonitor()

    def run(
        self,
        llm_output: LLMDecisionOutput,
        calculated_payout: float,
        claim_id: str,
        is_shadow: bool = False,
    ) -> GuardRailResult:
        """Apply GR-1 through GR-5 and return the consolidated result."""
        result = GuardRailResult(
            final_decision=llm_output.decision,
            enforced_payout=calculated_payout,
        )

        # GR-1: Enforce formula payout
        self._gr1.apply(llm_output, calculated_payout, result)

        # GR-2: Confidence gate (may change decision to ESCALATE)
        self._gr2.apply(llm_output, result)

        # GR-3: Immutable reasoning snapshot
        self._gr3.apply(llm_output, claim_id, result)

        # GR-5: Record decision in drift monitor (GR-4 is event-driven via endpoint)
        drift_alert = self._drift.record(result.final_decision, is_shadow=is_shadow)
        if drift_alert:
            result.audit_payload["GR-5_drift_alert"] = drift_alert

        return result

    @property
    def drift_monitor(self) -> StatisticalDriftMonitor:
        return self._drift

    @property
    def human_override_rail(self) -> HumanOverrideRail:
        return self._gr4
