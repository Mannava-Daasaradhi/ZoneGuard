"""
Feature 12 — SmartClaim Autopilot: FastAPI Router.

Endpoints
─────────
  POST   /api/v1/autopilot/process/{claim_id}     Run autopilot pipeline
  GET    /api/v1/autopilot/run/{run_id}            Fetch a single pipeline run
  GET    /api/v1/autopilot/claim/{claim_id}/runs   All runs for a claim
  POST   /api/v1/autopilot/override/{claim_id}     Human override (Guard Rail 4)
  GET    /api/v1/autopilot/drift                   Current drift monitor stats
  POST   /api/v1/autopilot/drift/snapshot          Persist a drift snapshot

Integration note (per spec — do NOT modify backend/api/router.py)
─────────────────────────────────────────────────────────────────
  Add the following line to backend/api/router.py when wiring this feature:

      from features.feature_12.autopilot_router import router as f12_router
      app.include_router(f12_router, prefix="/api/v1", tags=["SmartClaim Autopilot"])

  See CHANGES.md for the full integration diff.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from features.feature_12.autopilot_service import AutopilotService
from features.feature_12.models import AutopilotRun, AutopilotOverride

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/autopilot", tags=["SmartClaim Autopilot (Feature 12)"])


# ---------------------------------------------------------------------------
# Shared dependency
# ---------------------------------------------------------------------------

def get_autopilot_service(db: Session = Depends(get_db)) -> AutopilotService:
    return AutopilotService(db=db)


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class ProcessClaimResponse(BaseModel):
    run_id: str
    claim_id: str
    status: str
    is_shadow: bool
    decision: Optional[str] = None
    enforced_payout: Optional[float] = None
    llm_confidence: Optional[float] = None
    llm_reasoning: Optional[str] = None
    escalation_reason: Optional[str] = None
    guard_rail_overrides: list[str] = Field(default_factory=list)
    audit_log_path: Optional[str] = None
    error: Optional[str] = None


class OverrideRequest(BaseModel):
    override_decision: str = Field(
        ...,
        description="APPROVE | REJECT | ESCALATE",
        examples=["APPROVE"],
    )
    override_reason: str = Field(
        ...,
        description="Reason code from OverrideReason enum",
        examples=["HUMAN_REVIEW"],
    )
    overridden_by: str = Field(
        ...,
        description="Identity of the user or service initiating the override",
        examples=["underwriter@zoneguard.io"],
    )
    notes: Optional[str] = Field(None, description="Free-text notes")


class OverrideResponse(BaseModel):
    claim_id: str
    override_decision: str
    override_reason: str
    overridden_by: str
    original_decision: Optional[str] = None
    autopilot_run_id: str
    overridden_at: str


class RunSummary(BaseModel):
    run_id: str
    claim_id: str
    status: str
    decision: Optional[str]
    llm_confidence: Optional[float]
    enforced_payout: Optional[float]
    is_shadow: bool
    started_at: str
    completed_at: Optional[str]


class DriftStats(BaseModel):
    window_size: int
    approval_rate: Optional[float]
    rejection_rate: Optional[float]
    escalation_rate: Optional[float]
    shadow_rate: Optional[float]
    captured_at: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/process/{claim_id}",
    response_model=ProcessClaimResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Run the SmartClaim Autopilot pipeline for a claim",
)
def process_claim(
    claim_id: str,
    svc: AutopilotService = Depends(get_autopilot_service),
) -> ProcessClaimResponse:
    """
    Trigger the 5-step autopilot pipeline for the given claim.

    In shadow mode (default) the decision is logged but NOT applied to the
    claim status.  Only MEDIUM-confidence claims (between
    FEATURE12_SHADOW_CONFIDENCE_MIN and FEATURE12_SHADOW_CONFIDENCE_MAX) are
    processed.
    """
    logger.info("POST /autopilot/process/%s", claim_id)
    result = svc.process_claim(claim_id)
    return ProcessClaimResponse(**result.to_dict())


@router.get(
    "/run/{run_id}",
    response_model=RunSummary,
    summary="Fetch details of a single autopilot run",
)
def get_run(
    run_id: str,
    db: Session = Depends(get_db),
) -> RunSummary:
    row: Optional[AutopilotRun] = db.query(AutopilotRun).filter(AutopilotRun.id == run_id).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Autopilot run {run_id} not found")
    return _run_to_summary(row)


@router.get(
    "/claim/{claim_id}/runs",
    response_model=list[RunSummary],
    summary="List all autopilot runs for a claim",
)
def list_runs_for_claim(
    claim_id: str,
    db: Session = Depends(get_db),
) -> list[RunSummary]:
    rows: list[AutopilotRun] = (
        db.query(AutopilotRun)
        .filter(AutopilotRun.claim_id == claim_id)
        .order_by(AutopilotRun.created_at.desc())
        .all()
    )
    return [_run_to_summary(r) for r in rows]


@router.post(
    "/override/{claim_id}",
    response_model=OverrideResponse,
    status_code=status.HTTP_200_OK,
    summary="Apply a human override to a claim decision (Guard Rail 4)",
)
def human_override(
    claim_id: str,
    body: OverrideRequest,
    svc: AutopilotService = Depends(get_autopilot_service),
) -> OverrideResponse:
    """
    Guard Rail 4 — Human override endpoint.

    Writes an AutopilotOverride row and returns the override audit record.
    The underlying Claim status is NOT automatically updated here; the
    claims service must be called separately.
    """
    logger.info(
        "POST /autopilot/override/%s — decision=%s by=%s",
        claim_id, body.override_decision, body.overridden_by,
    )
    try:
        record = svc.apply_override(
            claim_id=claim_id,
            override_decision=body.override_decision,
            override_reason=body.override_reason,
            overridden_by=body.overridden_by,
            notes=body.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return OverrideResponse(
        claim_id=record["claim_id"],
        override_decision=record["override_decision"],
        override_reason=record["override_reason"],
        overridden_by=record["overridden_by"],
        original_decision=record.get("original_decision"),
        autopilot_run_id=record["autopilot_run_id"],
        overridden_at=record["overridden_at"],
    )


@router.get(
    "/drift",
    response_model=DriftStats,
    summary="Current drift monitor statistics (Guard Rail 5)",
)
def get_drift_stats(
    svc: AutopilotService = Depends(get_autopilot_service),
) -> DriftStats:
    """Return current approval/rejection/escalation rates from the in-process monitor."""
    snapshot = svc._rails.drift_monitor.snapshot()
    return DriftStats(
        window_size=snapshot["window_size"],
        approval_rate=snapshot.get("approval_rate"),
        rejection_rate=snapshot.get("rejection_rate"),
        escalation_rate=snapshot.get("escalation_rate"),
        shadow_rate=snapshot.get("shadow_rate"),
        captured_at=snapshot["captured_at"],
    )


@router.post(
    "/drift/snapshot",
    status_code=status.HTTP_201_CREATED,
    summary="Persist a drift snapshot to the database",
)
def persist_drift_snapshot(
    svc: AutopilotService = Depends(get_autopilot_service),
) -> dict:
    """Trigger a drift snapshot write.  Useful for scheduled jobs."""
    snap = svc.persist_drift_snapshot()
    if snap is None:
        return {"message": "Window not yet full — snapshot not written", "written": False}
    return {"message": "Drift snapshot persisted", "written": True, "snapshot": snap}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _run_to_summary(row: AutopilotRun) -> RunSummary:
    return RunSummary(
        run_id=row.id,
        claim_id=row.claim_id,
        status=row.status.value if row.status else "UNKNOWN",
        decision=row.decision.value if row.decision else None,
        llm_confidence=row.llm_confidence,
        enforced_payout=row.enforced_payout,
        is_shadow=row.is_shadow or False,
        started_at=row.started_at.isoformat() if row.started_at else "",
        completed_at=row.completed_at.isoformat() if row.completed_at else None,
    )
