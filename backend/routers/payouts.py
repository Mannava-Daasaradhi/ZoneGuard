from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.database import get_db
from models.payout import Payout
from schemas.payout import PayoutResponse

router = APIRouter(prefix="/api/v1/payouts", tags=["payouts"])


@router.get("")
async def list_payouts(rider_id: str = Query(None), db: AsyncSession = Depends(get_db)):
    query = select(Payout)
    if rider_id:
        query = query.where(Payout.rider_id == rider_id)
    query = query.order_by(Payout.created_at.desc())

    result = await db.execute(query)
    payouts = result.scalars().all()
    return [PayoutResponse.model_validate(p) for p in payouts]
