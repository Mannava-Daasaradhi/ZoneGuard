from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.database import get_db
from models.claim import Claim
from models.payout import Payout
from models.audit import AuditLog
from models.rider import Rider
from schemas.claim import ClaimResponse, ClaimReview
from integrations.payout_sim import process_payout
from datetime import datetime, timezone

router = APIRouter(prefix="/api/v1/claims", tags=["claims"])


@router.get("")
async def list_claims(
    status: str = Query(None),
    zone_id: str = Query(None),
    rider_id: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Claim)
    if status:
        query = query.where(Claim.status == status)
    if zone_id:
        query = query.where(Claim.zone_id == zone_id)
    if rider_id:
        query = query.where(Claim.rider_id == rider_id)
    query = query.order_by(Claim.created_at.desc())

    result = await db.execute(query)
    claims = result.scalars().all()
    return [ClaimResponse.model_validate(c) for c in claims]


@router.get("/{claim_id}")
async def get_claim(claim_id: str, db: AsyncSession = Depends(get_db)):
    claim = await db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    # Get audit report if exists
    audit_result = await db.execute(
        select(AuditLog).where(AuditLog.claim_id == claim_id).order_by(AuditLog.created_at.desc())
    )
    audit = audit_result.scalars().first()

    return {
        "claim": ClaimResponse.model_validate(claim),
        "audit_report": {
            "content": audit.content if audit else None,
            "model_used": audit.model_used if audit else None,
            "generated_at": audit.created_at.isoformat() if audit else None,
        } if audit else None,
    }


@router.post("/{claim_id}/review")
async def review_claim(claim_id: str, payload: ClaimReview, db: AsyncSession = Depends(get_db)):
    claim = await db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    if claim.status not in ("pending_review", "held"):
        raise HTTPException(status_code=400, detail=f"Claim cannot be reviewed in '{claim.status}' status")

    claim.status = "approved" if payload.action == "approve" else "rejected"
    claim.reviewed_at = datetime.now(timezone.utc)
    claim.reviewed_by = payload.reviewed_by

    payout_result = None
    if payload.action == "approve":
        claim.actual_payout = claim.recommended_payout

        # Ensure no duplicate payout exists for this claim
        existing_payout = await db.execute(select(Payout).where(Payout.claim_id == claim_id))
        if not existing_payout.scalars().first():
            rider = await db.get(Rider, claim.rider_id)
            upi_id = rider.upi_id if rider else None
            payout_result = await process_payout(claim.rider_id, claim.recommended_payout, upi_id)
            payout = Payout(
                claim_id=claim_id,
                rider_id=claim.rider_id,
                amount=claim.recommended_payout,
                upi_ref=payout_result["upi_ref"],
                status=payout_result["status"],
                gateway_response=str(payout_result["gateway_response"]),
            )
            if payout_result["status"] == "settled":
                payout.settled_at = datetime.now(timezone.utc)
            db.add(payout)

    # Log the review
    audit = AuditLog(
        claim_id=claim_id,
        event_type="claim_review",
        content=f"Claim {payload.action}d by {payload.reviewed_by}",
        generated_by=payload.reviewed_by,
    )
    db.add(audit)
    await db.commit()

    return {
        "status": claim.status,
        "claim_id": claim_id,
        "payout": payout_result,
    }
