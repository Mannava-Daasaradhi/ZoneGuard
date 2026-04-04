from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any
from models.notification import NotificationType


class NotificationCreate(BaseModel):
    rider_id: str
    type: NotificationType
    title: str
    message: str
    data: Optional[dict[str, Any]] = None


class NotificationResponse(BaseModel):
    id: str
    rider_id: str
    type: NotificationType
    title: str
    message: str
    data: dict[str, Any]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationUnreadCount(BaseModel):
    rider_id: str
    unread_count: int
