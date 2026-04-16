"""
ZoneGuard Pulse — Feature 14
pulse_router.py

FastAPI router mounted at /api/v1/pulse

Endpoints:
  GET  /api/v1/pulse/{zone_id}                 — full pulse snapshot
  GET  /api/v1/pulse/{zone_id}/quad-signals    — QuadSignal meter only
  GET  /api/v1/pulse/{zone_id}/chart-72h       — 72-hour disruption chart
  GET  /api/v1/pulse/{zone_id}/coverage        — coverage status
  GET  /api/v1/pulse/{zone_id}/activity        — anonymised zone activity
  POST /api/v1/pulse/whatsapp-brief            — WhatsApp brief text generator
  POST /api/v1/pulse/{zone_id}/notify-check    — trigger threshold notifications

INTEGRATION NOTE (do not modify router.py — see CHANGES.md):
  Add to backend/main.py (or wherever routers are included):
    from backend.features.feature_14.pulse_router import router as pulse_router
    app.include_router(pulse_router)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from features.feature_14.pulse_service import (
    get_pulse_snapshot,
    get_quad_signal_meter,
    get_72h_disruption_chart,
    get_coverage_status,
    get_zone_activity,
    generate_whatsapp_brief,
    trigger_threshold_notifications,
)

router = APIRouter(prefix="/api/v1/pulse", tags=["pulse-feature-14"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class WhatsAppBriefRequest(BaseModel):
    zone_id: str = Field(..., description="Zone ID (e.g. 'hsr', 'bellandur')")


class WhatsAppBriefResponse(BaseModel):
    zone_id: str
    brief: str
    char_count: int


class NotifyCheckResponse(BaseModel):
    zone_id: str
    notifications_created: int
    details: list[dict]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/{zone_id}", summary="Full Pulse snapshot for a zone")
async def pulse_snapshot(zone_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns the complete ZoneGuard Pulse feed for a zone:
    - QuadSignal meter (value vs threshold for S1–S4)
    - 72-hour disruption probability bar chart data
    - Coverage status (active policies, expiry proximity)
    - Zone activity signal (anonymised rider count)
    """
    snapshot = await get_pulse_snapshot(zone_id, db)
    return snapshot


@router.get("/{zone_id}/quad-signals", summary="QuadSignal meter for a zone")
async def quad_signals(zone_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns how close each of the four signals (S1 Environmental, S2 Mobility,
    S3 Economic, S4 Crowd) is to its trigger threshold, expressed as a
    percentage. Values ≥75% will carry alert_triggered=true.
    """
    meter = await get_quad_signal_meter(zone_id, db)
    return {"zone_id": zone_id, "quad_signal_meter": meter}


@router.get("/{zone_id}/chart-72h", summary="72-hour disruption probability chart")
async def chart_72h(zone_id: str):
    """
    Returns 12 six-hour buckets (72 hours) of predicted disruption probability
    derived from ZoneTwin v1 counterfactual simulation. No DB read required.
    """
    chart = get_72h_disruption_chart(zone_id)
    return {"zone_id": zone_id, "buckets": chart}


@router.get("/{zone_id}/coverage", summary="Policy coverage status")
async def coverage_status(zone_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns active policy count, coverage percentage of zone riders, and
    policies expiring within 7 days — read from the existing Policy table.
    """
    coverage = await get_coverage_status(zone_id, db)
    return coverage


@router.get("/{zone_id}/activity", summary="Anonymised zone activity signal")
async def zone_activity(zone_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns anonymised rider count for the zone. Count is rounded to the
    nearest FEATURE14_ZONE_ACTIVITY_NOISE_FLOOR (default 3) to prevent
    individual identification.
    """
    activity = await get_zone_activity(zone_id, db)
    return activity


@router.post(
    "/whatsapp-brief",
    response_model=WhatsAppBriefResponse,
    summary="Generate WhatsApp brief text for a zone",
)
async def whatsapp_brief(
    payload: WhatsAppBriefRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generates a plain-text WhatsApp message brief for the given zone,
    summarising current signal status, coverage, activity, and 72-hour outlook.

    Character limit controlled by FEATURE14_WHATSAPP_MAX_CHARS (default 800).
    """
    zone_id = payload.zone_id
    snapshot = await get_pulse_snapshot(zone_id, db)

    brief = generate_whatsapp_brief(
        zone_name=snapshot["zone_name"],
        quad_signals=snapshot["quad_signal_meter"],
        coverage=snapshot["coverage_status"],
        activity=snapshot["zone_activity"],
        disruption_chart=snapshot["disruption_72h_chart"],
    )
    return WhatsAppBriefResponse(
        zone_id=zone_id,
        brief=brief,
        char_count=len(brief),
    )


@router.post(
    "/{zone_id}/notify-check",
    response_model=NotifyCheckResponse,
    summary="Trigger push notifications for signals at ≥75% of threshold",
)
async def notify_check(zone_id: str, db: AsyncSession = Depends(get_db)):
    """
    Checks the current QuadSignal meter for the zone and creates
    SIGNAL_ALERT notifications for all riders with active policies in the
    zone when any signal has reached ≥FEATURE14_ALERT_THRESHOLD_PCT (75%)
    of its trigger threshold.

    Safe to call repeatedly — creates notifications for newly-alerting
    signals only based on current readings.
    """
    quad = await get_quad_signal_meter(zone_id, db)
    notifications = await trigger_threshold_notifications(zone_id, quad, db)
    return NotifyCheckResponse(
        zone_id=zone_id,
        notifications_created=len(notifications),
        details=notifications,
    )
