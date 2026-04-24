"""
Notification system API routes.
Handles creating, reading, and managing user notifications.
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy import desc

from anip.shared.database import get_db_session
from anip.shared.models.social import Notification, User
from app.auth import get_current_user
from app.websocket_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    id: UUID
    type: str
    title: str
    message: Optional[str]
    link: Optional[str]
    actor_username: Optional[str] = None
    is_read: bool
    created_at: datetime


class NotificationCount(BaseModel):
    unread: int
    total: int


@router.get("", response_model=List[NotificationResponse])
def get_notifications(
    limit: int = Query(default=30, ge=1, le=100),
    unread_only: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
):
    """Get the current user's notifications."""
    with get_db_session() as db:
        query = db.query(Notification).filter(Notification.user_id == current_user.id)
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        notifs = query.order_by(desc(Notification.created_at)).limit(limit).all()
        
        results = []
        for n in notifs:
            actor_name = None
            if n.actor_id:
                actor = db.query(User).filter(User.id == n.actor_id).first()
                actor_name = actor.username if actor else None
            
            results.append(NotificationResponse(
                id=n.id,
                type=n.type,
                title=n.title,
                message=n.message,
                link=n.link,
                actor_username=actor_name,
                is_read=n.is_read,
                created_at=n.created_at,
            ))
        
        return results


@router.get("/count", response_model=NotificationCount)
def get_notification_count(current_user: User = Depends(get_current_user)):
    """Get notification counts."""
    with get_db_session() as db:
        total = db.query(Notification).filter(Notification.user_id == current_user.id).count()
        unread = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).count()
        return NotificationCount(unread=unread, total=total)


@router.post("/{notification_id}/read")
def mark_as_read(notification_id: UUID, current_user: User = Depends(get_current_user)):
    """Mark a notification as read."""
    with get_db_session() as db:
        notif = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        ).first()
        if not notif:
            raise HTTPException(status_code=404, detail="Notification not found")
        notif.is_read = True
        db.commit()
        return {"status": "ok"}


@router.post("/read-all")
def mark_all_read(current_user: User = Depends(get_current_user)):
    """Mark all notifications as read."""
    with get_db_session() as db:
        db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).update({Notification.is_read: True})
        db.commit()
        return {"status": "ok"}


async def create_notification(
    user_id: UUID,
    type: str,
    title: str,
    message: str = None,
    link: str = None,
    actor_id: UUID = None,
):
    """Create a notification and push it via WebSocket."""
    with get_db_session() as db:
        notif = Notification(
            user_id=user_id,
            actor_id=actor_id,
            type=type,
            title=title,
            message=message,
            link=link,
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        
        # Push via WebSocket
        actor_name = None
        if actor_id:
            actor = db.query(User).filter(User.id == actor_id).first()
            actor_name = actor.username if actor else None
        
        await manager.send_to_user(str(user_id), {
            "type": "notification",
            "data": {
                "id": str(notif.id),
                "type": type,
                "title": title,
                "message": message,
                "link": link,
                "actor": actor_name,
                "created_at": notif.created_at.isoformat(),
            }
        })
        
        return notif
