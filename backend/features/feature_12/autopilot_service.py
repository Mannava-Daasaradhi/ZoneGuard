"""
Feature 12 — SmartClaim Autopilot: Service (5-step pipeline).

Pipeline steps
──────────────
  Step 1  Signal validation          Read QuadSignal rows for the claim
  Step 2  FraudShield score          Import & invoke FraudShield (read-only)
  Step 3  On-chain formula validation Mock interface (ZoneChain not yet live)
  Step 4  LLM structured decision    claude-sonnet-4-6 → {decision, confidence,
                                     reasoning, payout_amount}
  Step 5  IPFS audit log             Write full audit record to local file
                                     (CID stub — real IPFS pinning TBD)

Shadow mode
───────────
  When FEATURE12_SHADOW_MODE=true the service processes only claims whose
  initial confidence falls between FEATURE12_SHADOW_CONFIDENCE_MIN and
  FEATURE12_SHADOW_CONFIDENCE_MAX.  Decisions are logged but NOT applied
  to the underlying Claim row.
"""
from __future__ import annotations

import json
import logging
import math
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from backend.core.config import settings
# Read-only imports from core modules (rule: do not modify these files)
from backend.ml.fraud_shield import FraudShield, FraudShieldResult
from backend.models.zones import Claim, QuadSignal

from backend.features.feature_12.guard_rails import GuardRailOrchestrator, GuardRailResult
from backend.features.feature_12.llm_client import (
    AutopilotLLMClient,
    LLMDecisionInput,
    LLMDecisionOutput,
    LLMParseError,
)
from backend.features.feature_12.models import (
    AutopilotDecision,
    AutopilotDriftSnapshot,
    AutopilotRun,
    AutopilotRunStatus,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ZoneChain mock (Step 3) — replace with real adapter when ZoneChain is live
# ---------------------------------------------------------------------------

@dataclass
class OnChainValidationResult:
    claim_id: str
    formula_payout: float
    is_valid: bool
    validation_hash: str
    formula_version: str = "v1.0-mock"
    validated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    notes: str = "ZoneChain not yet live — mock validation"

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "formula_payout": self.formula_payout,
            "is_valid": self.is_valid,
            "validation_hash": self.validation_hash,
            "formula_version": self.formula_version,
            "validated_at": self.validated_at,
            "notes": self.notes,
        }


def _mock_onchain_validate(claim: Claim) -> OnChainValidationResult:
    """
    Stub for ZoneChain formula validation.

    Logic mirrors the parametric payout formula:
        payout = min(claimed_amount, coverage_amount) - deductible

    When ZoneChain goes live, replace this function body with the real
    ZoneChain adapter call.  The return type must remain OnChainValidationResult.
    """
    coverage = claim.policy.coverage_amount if claim.policy else claim.claimed_amount
    deductible = claim.policy.deductible if claim.policy else 0.0
    formula_payout = max(0.0, min(claim.claimed_amount, coverage) - deductible)

    # Deterministic pseudo-hash for the mock
    import hashlib
    raw = f"{claim.id}:{claim.claimed_amount}:{formula_payout}"
    h = hashlib.sha256(raw.encode()).hexdigest()[:16]

    return OnChainValidationResult(
        claim_id=claim.id,
        formula_payout=round(formula_payout, 2),
        is_valid=True,
        validation_hash=h,
    )


# ---------------------------------------------------------------------------
# Pipeline result container
# ---------------------------------------------------------------------------

@dataclass
class AutopilotPipelineResult:
    run_id: str
    claim_id: str
    is_shadow: bool
    status: str                          # AutopilotRunStatus value
    decision: Optional[str] = None       # AutopilotDecision value
    enforced_payout: Optional[float] = None
    llm_confidence: Optional[float] = None
    llm_reasoning: Optional[str] = None
    escalation_reason: Optional[str] = None
    guard_rail_overrides: list[str] = field(default_factory=list)
    audit_log_path: Optional[str] = None
    error: Optional[str] = None

    # Step snapshots
    step1: Optional[dict] = None
    step2: Optional[dict] = None
    step3: Optional[dict] = None
    step4: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "claim_id": self.claim_id,
            "is_shadow": self.is_shadow,
            "status": self.status,
            "decision": self.decision,
            "enforced_payout": self.enforced_payout,
            "llm_confidence": self.llm_confidence,
            "llm_reasoning": self.llm_reasoning,
            "escalation_reason": self.escalation_reason,
            "guard_rail_overrides": self.guard_rail_overrides,
            "audit_log_path": self.audit_log_path,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# Main service class
# ---------------------------------------------------------------------------

class AutopilotService:
    """
    Orchestrates the 5-step SmartClaim Autopilot pipeline.

    Parameters
    ----------
    db : Session
        SQLAlchemy session (injected by FastAPI dependency).
    llm_client : AutopilotLLMClient, optional
        Defaults to a new instance using settings.
    guard_rail_orchestrator : GuardRailOrchestrator, optional
        Defaults to a new instance (owns its own DriftMonitor).
    """

    def __init__(
        self,
        db: Session,
        llm_client: Optional[AutopilotLLMClient] = None,
        guard_rail_orchestrator: Optional[GuardRailOrchestrator] = None,
    ) -> None:
        self._db = db
        self._llm = llm_client or AutopilotLLMClient()
        self._rails = guard_rail_orchestrator or GuardRailOrchestrator()
        self._fraud_shield = FraudShield()
        self._audit_dir = Path(settings.FEATURE12_AUDIT_DIR)
        self._audit_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def process_claim(self, claim_id: str) -> AutopilotPipelineResult:
        """
        Run the full autopilot pipeline for a single claim.

        Shadow-mode: if FEATURE12_SHADOW_MODE is True, the method checks
        whether this claim falls in the shadow confidence band before
        proceeding.  Non-shadow-band claims are skipped and a SHADOW status
        is returned without touching the Claim row.
        """
        run_id = str(uuid.uuid4())
        logger.info("Autopilot pipeline starting — run=%s claim=%s", run_id, claim_id)

        result = AutopilotPipelineResult(
            run_id=run_id,
            claim_id=claim_id,
            is_shadow=settings.FEATURE12_SHADOW_MODE,
            status=AutopilotRunStatus.RUNNING,
        )

        # Persist the run record immediately so we have a traceable ID
        run_row = self._create_run_row(run_id, claim_id)

        try:
            # Fetch the claim
            claim = self._db.query(Claim).filter(Claim.id == claim_id).first()
            if not claim:
                raise ValueError(f"Claim {claim_id} not found")

            run_row.policy_id = claim.policy_id
            run_row.zone_id = claim.zone_id

            # ── Step 1: Signal validation ──────────────────────────────
            step1 = self._step1_signal_validation(claim)
            result.step1 = step1
            run_row.step1_signal_validation = step1

            # Shadow-mode gate: check claim confidence band
            if settings.FEATURE12_SHADOW_MODE:
                avg_confidence = step1.get("avg_signal_confidence", 0.0)
                lo = settings.FEATURE12_SHADOW_CONFIDENCE_MIN
                hi = settings.FEATURE12_SHADOW_CONFIDENCE_MAX
                if not (lo <= avg_confidence <= hi):
                    logger.info(
                        "Shadow mode: claim %s avg_confidence=%.2f outside band [%.2f, %.2f] — skipping",
                        claim_id, avg_confidence, lo, hi,
                    )
                    result.status = AutopilotRunStatus.SHADOW
                    run_row.status = AutopilotRunStatus.SHADOW
                    self._db.commit()
                    return result

            # ── Step 2: FraudShield score ──────────────────────────────
            step2 = self._step2_fraud_shield(claim)
            result.step2 = step2
            run_row.step2_fraud_shield = step2

            # ── Step 3: On-chain formula validation ───────────────────
            step3 = self._step3_onchain_validation(claim)
            result.step3 = step3
            run_row.step3_onchain_validation = step3
            calculated_payout: float = step3["formula_payout"]

            # ── Step 4: LLM structured decision ───────────────────────
            llm_input = self._build_llm_input(claim, step1, step2, step3)
            llm_output: LLMDecisionOutput = self._llm.decide(llm_input)
            step4 = llm_output.to_dict()
            result.step4 = step4
            run_row.step4_llm_decision = step4
            run_row.llm_proposed_payout = llm_output.payout_amount
            run_row.llm_confidence = llm_output.confidence
            run_row.llm_reasoning = llm_output.reasoning

            # ── Guard rails ───────────────────────────────────────────
            gr_result: GuardRailResult = self._rails.run(
                llm_output=llm_output,
                calculated_payout=calculated_payout,
                claim_id=claim_id,
                is_shadow=settings.FEATURE12_SHADOW_MODE,
            )
            result.decision = gr_result.final_decision
            result.enforced_payout = gr_result.enforced_payout
            result.llm_confidence = llm_output.confidence
            result.llm_reasoning = llm_output.reasoning
            result.escalation_reason = gr_result.escalation_reason
            result.guard_rail_overrides = gr_result.triggered_rails

            run_row.decision = gr_result.final_decision
            run_row.enforced_payout = gr_result.enforced_payout
            run_row.guard_rail_overrides = gr_result.triggered_rails
            run_row.escalation_reason = gr_result.escalation_reason

            if settings.FEATURE12_SHADOW_MODE:
                run_row.shadow_decision = gr_result.final_decision
                run_row.is_shadow = True

            # ── Step 5: IPFS audit log ────────────────────────────────
            audit_path = self._step5_audit_log(
                run_id=run_id,
                claim_id=claim_id,
                pipeline_result=result,
                gr_audit=gr_result.audit_payload,
            )
            result.audit_log_path = audit_path
            run_row.step5_audit_ref = audit_path

            # ── Finalise ──────────────────────────────────────────────
            result.status = AutopilotRunStatus.COMPLETED
            run_row.status = AutopilotRunStatus.COMPLETED
            run_row.completed_at = datetime.utcnow()
            self._db.commit()

            logger.info(
                "Autopilot pipeline completed — run=%s claim=%s decision=%s shadow=%s",
                run_id, claim_id, result.decision, settings.FEATURE12_SHADOW_MODE,
            )

        except Exception as exc:
            logger.exception("Autopilot pipeline failed — run=%s: %s", run_id, exc)
            result.status = AutopilotRunStatus.FAILED
            result.error = str(exc)
            run_row.status = AutopilotRunStatus.FAILED
            run_row.error_message = str(exc)
            run_row.completed_at = datetime.utcnow()
            self._db.commit()

        return result

    # ------------------------------------------------------------------
    # Step 1: Signal validation
    # ------------------------------------------------------------------

    def _step1_signal_validation(self, claim: Claim) -> dict:
        """
        Read QuadSignal rows for the claim and produce a structured summary.

        Returns a dict with:
          signal_count, avg_signal_confidence, signal_types,
          has_weather, has_satellite, has_iot, has_community,
          signals (list of signal dicts), validation_passed
        """
        signals: list[QuadSignal] = (
            self._db.query(QuadSignal)
            .filter(QuadSignal.claim_id == claim.id)
            .all()
        )

        if not signals:
            return {
                "signal_count": 0,
                "avg_signal_confidence": 0.0,
                "signal_types": [],
                "has_weather": False,
                "has_satellite": False,
                "has_iot": False,
                "has_community": False,
                "signals": [],
                "validation_passed": False,
                "validation_notes": "No QuadSignal data found for claim",
            }

        signal_types = list({s.signal_type for s in signals if s.signal_type})
        avg_conf = sum(s.confidence or 0 for s in signals) / len(signals)

        signal_dicts = [
            {
                "id": s.id,
                "type": s.signal_type,
                "source": s.source,
                "value": s.value,
                "confidence": s.confidence,
                "recorded_at": s.recorded_at.isoformat() if s.recorded_at else None,
            }
            for s in signals
        ]

        return {
            "signal_count": len(signals),
            "avg_signal_confidence": round(avg_conf, 4),
            "signal_types": signal_types,
            "has_weather": "WEATHER" in signal_types,
            "has_satellite": "SATELLITE" in signal_types,
            "has_iot": "IOT" in signal_types,
            "has_community": "COMMUNITY" in signal_types,
            "signals": signal_dicts,
            "validation_passed": len(signals) >= 2 and avg_conf >= 0.5,
            "validation_notes": "OK" if len(signals) >= 2 else "Insufficient signals",
        }

    # ------------------------------------------------------------------
    # Step 2: FraudShield score
    # ------------------------------------------------------------------

    def _step2_fraud_shield(self, claim: Claim) -> dict:
        """
        Invoke FraudShield (read-only import) and return its result dict.
        Also updates claim.fraud_score for downstream access.
        """
        claim_data = {
            "zone_id": claim.zone_id,
            "policy_id": claim.policy_id,
            "claimed_amount": claim.claimed_amount,
            "quad_signals": claim.quad_signals,
            "wallet_address": claim.wallet_address,
            "timestamp": claim.submitted_at.isoformat() if claim.submitted_at else None,
            "duplicate_policy_flag": claim.metadata.get("duplicate_policy_flag", False),
            "velocity_breach": claim.metadata.get("velocity_breach", False),
        }
        fs_result: FraudShieldResult = self._fraud_shield.evaluate(claim.id, claim_data)

        # Write fraud_score back to the claim (read-only on fraud_shield, not on Claim)
        claim.fraud_score = fs_result.fraud_score
        self._db.flush()

        return fs_result.to_dict()

    # ------------------------------------------------------------------
    # Step 3: On-chain formula validation
    # ------------------------------------------------------------------

    def _step3_onchain_validation(self, claim: Claim) -> dict:
        """
        Run mock ZoneChain validation.  Returns the on-chain result as a dict.
        """
        oc_result = _mock_onchain_validate(claim)
        return oc_result.to_dict()

    # ------------------------------------------------------------------
    # Step 4: LLM input builder
    # ------------------------------------------------------------------

    def _build_llm_input(
        self,
        claim: Claim,
        step1: dict,
        step2: dict,
        step3: dict,
    ) -> LLMDecisionInput:
        policy = claim.policy
        return LLMDecisionInput(
            claim_id=claim.id,
            zone_id=claim.zone_id,
            policy_id=claim.policy_id,
            claimed_amount=claim.claimed_amount,
            calculated_payout=step3["formula_payout"],
            fraud_score=step2.get("fraud_score", 0.0),
            fraud_risk_level=step2.get("risk_level", "UNKNOWN"),
            fraud_flags=step2.get("anomaly_flags", []),
            signal_summary=step1,
            onchain_validation=step3,
            policy_coverage_amount=policy.coverage_amount if policy else 0.0,
            policy_deductible=policy.deductible if policy else 0.0,
            claim_description=claim.description or "",
        )

    # ------------------------------------------------------------------
    # Step 5: IPFS audit log (local stub)
    # ------------------------------------------------------------------

    def _step5_audit_log(
        self,
        run_id: str,
        claim_id: str,
        pipeline_result: AutopilotPipelineResult,
        gr_audit: dict,
    ) -> str:
        """
        Write a complete audit record to a local JSON file.

        File naming: {audit_dir}/{claim_id}/{run_id}.json
        Returns the file path (used as the audit ref / future IPFS CID).

        When IPFS pinning is available, replace the file write with a
        call to the IPFS HTTP API and return the CID.
        """
        claim_dir = self._audit_dir / claim_id
        claim_dir.mkdir(parents=True, exist_ok=True)
        audit_path = claim_dir / f"{run_id}.json"

        audit_record = {
            "schema_version": "f12-audit-v1",
            "run_id": run_id,
            "claim_id": claim_id,
            "pipeline_version": "feature_12/v1.0",
            "recorded_at": datetime.utcnow().isoformat(),
            "is_shadow": pipeline_result.is_shadow,
            "decision": pipeline_result.decision,
            "enforced_payout": pipeline_result.enforced_payout,
            "llm_confidence": pipeline_result.llm_confidence,
            "guard_rail_overrides": pipeline_result.guard_rail_overrides,
            "escalation_reason": pipeline_result.escalation_reason,
            "steps": {
                "step1_signal_validation": pipeline_result.step1,
                "step2_fraud_shield": pipeline_result.step2,
                "step3_onchain_validation": pipeline_result.step3,
                "step4_llm_decision": pipeline_result.step4,
            },
            "guard_rail_audit": gr_audit,
            "ipfs_stub": {
                "note": "IPFS pinning not yet implemented — local file used as audit log",
                "local_path": str(audit_path),
                "cid": None,
            },
        }

        with open(audit_path, "w", encoding="utf-8") as fh:
            json.dump(audit_record, fh, indent=2, default=str)

        logger.info("Audit log written: %s", audit_path)
        return str(audit_path)

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    def _create_run_row(self, run_id: str, claim_id: str) -> AutopilotRun:
        row = AutopilotRun(
            id=run_id,
            claim_id=claim_id,
            policy_id="",
            zone_id="",
            status=AutopilotRunStatus.RUNNING,
        )
        self._db.add(row)
        self._db.commit()
        return row

    # ------------------------------------------------------------------
    # Override helper (called by the router for GR-4)
    # ------------------------------------------------------------------

    def apply_override(
        self,
        claim_id: str,
        override_decision: str,
        override_reason: str,
        overridden_by: str,
        notes: Optional[str] = None,
    ) -> dict:
        """
        Validate and persist a human override for a claim.
        Returns the override audit record.
        """
        # Find the most recent completed run for this claim
        run_row = (
            self._db.query(AutopilotRun)
            .filter(
                AutopilotRun.claim_id == claim_id,
                AutopilotRun.status == AutopilotRunStatus.COMPLETED,
            )
            .order_by(AutopilotRun.created_at.desc())
            .first()
        )
        original_decision = run_row.decision if run_row else None
        run_id = run_row.id if run_row else "unknown"

        # GR-4 validation
        override_record = self._rails.human_override_rail.validate_override(
            claim_id=claim_id,
            override_decision=override_decision,
            override_reason=override_reason,
            overridden_by=overridden_by,
            original_decision=original_decision,
            notes=notes,
        )
        override_record["autopilot_run_id"] = run_id

        # Write to DB
        from backend.features.feature_12.models import AutopilotOverride, OverrideReason
        override_row = AutopilotOverride(
            id=str(uuid.uuid4()),
            claim_id=claim_id,
            autopilot_run_id=run_id,
            original_decision=original_decision,
            override_decision=override_decision.upper(),
            override_reason=override_reason,
            overridden_by=overridden_by,
            override_notes=notes or "",
        )
        self._db.add(override_row)
        self._db.commit()

        return override_record

    # ------------------------------------------------------------------
    # Drift snapshot persistence
    # ------------------------------------------------------------------

    def persist_drift_snapshot(self) -> Optional[dict]:
        """
        Take a snapshot of the current drift monitor state and write it
        to AutopilotDriftSnapshot.  Returns the snapshot dict or None
        if the window is not yet full.
        """
        snapshot = self._rails.drift_monitor.snapshot()
        if snapshot["window_size"] < settings.FEATURE12_DRIFT_WINDOW_SIZE:
            return None

        now = datetime.utcnow()
        row = AutopilotDriftSnapshot(
            window_start=now,   # In production, derive from deque timestamps
            window_end=now,
            window_size=snapshot["window_size"],
            approval_rate=snapshot["approval_rate"],
            rejection_rate=snapshot["rejection_rate"],
            escalation_rate=snapshot["escalation_rate"],
            shadow_rate=snapshot["shadow_rate"],
            prev_approval_rate=snapshot["prev_approval_rate"],
            prev_rejection_rate=snapshot["prev_rejection_rate"],
            prev_escalation_rate=snapshot["prev_escalation_rate"],
        )
        self._db.add(row)
        self._db.commit()
        return snapshot
