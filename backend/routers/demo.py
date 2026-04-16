"""Demo mode endpoint — resets data for clean judge runs."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from db.database import get_db
from models.claim import Claim
from models.payout import Payout
from models.signal import SignalReading, DisruptionEvent
from models.audit import AuditLog
from models.notification import Notification
from routers.zones import clear_signal_cache

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])


@router.post("/reset")
async def demo_reset(db: AsyncSession = Depends(get_db)):
    """Reset transient data for a fresh demo. Preserves zones, riders, policies, exclusions."""

    # Delete in FK order
    await db.execute(delete(Notification))
    await db.execute(delete(AuditLog))
    await db.execute(delete(Payout))
    await db.execute(delete(Claim))
    await db.execute(delete(SignalReading))
    await db.execute(delete(DisruptionEvent))

    await db.commit()

    # Clear signal cache for all zones
    from routers.zones import _signal_cache
    _signal_cache.clear()

    return {
        "status": "reset_complete",
        "cleared": ["notifications", "audit_logs", "payouts", "claims", "signal_readings", "disruption_events", "signal_cache"],
    }
