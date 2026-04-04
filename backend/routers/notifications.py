from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.database import get_db
from models.notification import Notification, create_notification
from schemas.notification import NotificationCreate, NotificationResponse, NotificationUnreadCount

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    rider_id: str = Query(..., description="Rider ID to fetch notifications for"),
    db: AsyncSession = Depends(get_db),
):
    """List all notifications for a rider, newest first."""
    query = (
        select(Notification)
        .where(Notification.rider_id == rider_id)
        .order_by(Notification.created_at.desc())
    )
    result = await db.execute(query)
    notifications = result.scalars().all()
    return [NotificationResponse.model_validate(n) for n in notifications]


@router.post("", response_model=NotificationResponse, status_code=201)
async def create_notification_endpoint(
    payload: NotificationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new notification."""
    notification = await create_notification(
        db=db,
        rider_id=payload.rider_id,
        type=payload.type,
        title=payload.title,
        message=payload.message,
        metadata=payload.data,
    )
    await db.commit()
    await db.refresh(notification)
    return NotificationResponse.model_validate(notification)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Mark a notification as read."""
    notification = await db.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return NotificationResponse.model_validate(notification)


@router.get("/unread-count", response_model=NotificationUnreadCount)
async def get_unread_count(
    rider_id: str = Query(..., description="Rider ID to get unread count for"),
    db: AsyncSession = Depends(get_db),
):
    """Get the count of unread notifications for a rider."""
    query = (
        select(func.count(Notification.id))
        .where(Notification.rider_id == rider_id)
        .where(Notification.is_read == False)  # noqa: E712
    )
    result = await db.execute(query)
    count = result.scalar() or 0
    return NotificationUnreadCount(rider_id=rider_id, unread_count=count)
