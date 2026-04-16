"""
Feature 12 — SmartClaim Autopilot: ORM models.

All autopilot-specific tables live here.
This module NEVER imports from or modifies backend/models/zones.py.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float,
    Integer, JSON, String, Text,
)
from sqlalchemy.orm import DeclarativeBase


# Feature-12 uses its own Base so migrations stay isolated.
class Feature12Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class AutopilotDecision(str, enum.Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ESCALATE = "ESCALATE"


class AutopilotRunStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SHADOW = "SHADOW"          # Processed but not applied (shadow mode)


class OverrideReason(str, enum.Enum):
    HUMAN_REVIEW = "HUMAN_REVIEW"
    COMPLIANCE = "COMPLIANCE"
    TECHNICAL_ERROR = "TECHNICAL_ERROR"
    POLICY_EXCEPTION = "POLICY_EXCEPTION"
    OTHER = "OTHER"


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

class AutopilotRun(Feature12Base):
    """
    One execution of the 5-step autopilot pipeline for a single claim.
    """
    __tablename__ = "f12_autopilot_runs"

    id = Column(String(36), primary_key=True)                # UUID
    claim_id = Column(String(36), nullable=False, index=True)
    policy_id = Column(String(36), nullable=False)
    zone_id = Column(String(36), nullable=False)

    # Pipeline step artefacts (stored as JSON blobs)
    step1_signal_validation = Column(JSON)   # QuadSignal summary
    step2_fraud_shield = Column(JSON)        # FraudShieldResult dict
    step3_onchain_validation = Column(JSON)  # ZoneChain mock result
    step4_llm_decision = Column(JSON)        # Raw LLM structured output
    step5_audit_ref = Column(String(512))    # Path / CID of IPFS audit log

    # Derived from Step 4
    decision = Column(Enum(AutopilotDecision))
    llm_confidence = Column(Float)           # 0.0 – 1.0
    llm_reasoning = Column(Text)
    llm_proposed_payout = Column(Float)      # What LLM suggested (may differ)
    enforced_payout = Column(Float)          # Guard-rail-enforced value

    # Guard-rail metadata
    guard_rail_overrides = Column(JSON, default=list)   # list of guard rail IDs triggered
    escalation_reason = Column(String(512))

    # Shadow mode flag
    is_shadow = Column(Boolean, default=False)
    shadow_decision = Column(Enum(AutopilotDecision))   # What we *would* have done

    # Lifecycle
    status = Column(Enum(AutopilotRunStatus), default=AutopilotRunStatus.PENDING)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AutopilotOverride(Feature12Base):
    """
    Human override record — Guard Rail 4.
    Written when POST /api/v1/autopilot/override/{claim_id} is called.
    """
    __tablename__ = "f12_autopilot_overrides"

    id = Column(String(36), primary_key=True)
    claim_id = Column(String(36), nullable=False, index=True)
    autopilot_run_id = Column(String(36), nullable=False)

    original_decision = Column(Enum(AutopilotDecision))
    override_decision = Column(Enum(AutopilotDecision), nullable=False)
    override_reason = Column(Enum(OverrideReason), nullable=False)
    override_notes = Column(Text)
    overridden_by = Column(String(255), nullable=False)   # user/service identity
    overridden_at = Column(DateTime, default=datetime.utcnow)

    created_at = Column(DateTime, default=datetime.utcnow)


class AutopilotDriftSnapshot(Feature12Base):
    """
    Statistical drift monitor snapshots — Guard Rail 5.
    Written periodically (or on each N-th run) to track rate changes.
    """
    __tablename__ = "f12_drift_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    window_start = Column(DateTime, nullable=False)
    window_end = Column(DateTime, nullable=False)
    window_size = Column(Integer, nullable=False)   # number of runs in window

    approval_rate = Column(Float)
    rejection_rate = Column(Float)
    escalation_rate = Column(Float)
    shadow_rate = Column(Float)

    # Baseline comparison (previous window)
    prev_approval_rate = Column(Float)
    prev_rejection_rate = Column(Float)
    prev_escalation_rate = Column(Float)

    drift_detected = Column(Boolean, default=False)
    drift_metric = Column(String(100))   # which metric triggered alert
    drift_delta = Column(Float)          # magnitude of drift

    alert_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
