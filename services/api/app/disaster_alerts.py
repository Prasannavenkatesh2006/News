"""
Disaster Alert System for ANIP.
Detects disaster-related articles using keyword analysis and creates alerts.
Broadcasts real-time disaster notifications via WebSocket.
"""
import logging
import re
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy import desc, func

from anip.shared.database import get_db_session
from anip.shared.models.social import DisasterAlert, Post, Community, User, Notification
from anip.shared.models.news import NewsArticle
from app.auth import get_current_user
from app.websocket_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/alerts", tags=["disaster-alerts"])

# Disaster detection keywords and their severities
DISASTER_PATTERNS = {
    "earthquake": {
        "keywords": ["earthquake", "seismic", "tremor", "quake", "richter", "magnitude"],
        "type": "earthquake",
        "base_severity": "high",
    },
    "flood": {
        "keywords": ["flood", "flooding", "flash flood", "overflow", "deluge", "inundation"],
        "type": "flood",
        "base_severity": "high",
    },
    "hurricane": {
        "keywords": ["hurricane", "typhoon", "cyclone", "tropical storm", "storm surge"],
        "type": "hurricane",
        "base_severity": "critical",
    },
    "wildfire": {
        "keywords": ["wildfire", "bushfire", "forest fire", "blaze", "fire outbreak"],
        "type": "wildfire",
        "base_severity": "high",
    },
    "tsunami": {
        "keywords": ["tsunami", "tidal wave"],
        "type": "tsunami",
        "base_severity": "critical",
    },
    "tornado": {
        "keywords": ["tornado", "twister", "funnel cloud"],
        "type": "tornado",
        "base_severity": "high",
    },
    "volcanic": {
        "keywords": ["volcano", "volcanic", "eruption", "lava", "pyroclastic"],
        "type": "volcanic_eruption",
        "base_severity": "critical",
    },
    "drought": {
        "keywords": ["drought", "water shortage", "water crisis", "desertification"],
        "type": "drought",
        "base_severity": "medium",
    },
    "landslide": {
        "keywords": ["landslide", "mudslide", "rockslide", "avalanche"],
        "type": "landslide",
        "base_severity": "high",
    },
    "pandemic": {
        "keywords": ["pandemic", "epidemic", "outbreak", "contagion"],
        "type": "pandemic",
        "base_severity": "critical",
    },
}

SEVERITY_ESCALATORS = [
    "death", "dead", "killed", "casualties", "fatalities",
    "destruction", "destroyed", "devastating", "catastrophic", "emergency",
    "evacuate", "evacuation", "rescue", "missing", "trapped",
]


class AlertResponse(BaseModel):
    id: UUID
    alert_type: str
    severity: str
    title: str
    description: Optional[str]
    location: Optional[str]
    source_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AlertStats(BaseModel):
    active_critical: int
    active_high: int
    active_medium: int
    active_low: int
    total_active: int
    total_resolved: int


def detect_disaster(title: str, content: str) -> Optional[dict]:
    """
    Analyze text for disaster indicators.
    Returns disaster info dict or None if no disaster detected.
    """
    text = f"{title} {content}".lower()
    
    detected = None
    max_keyword_hits = 0
    
    for category, config in DISASTER_PATTERNS.items():
        hits = sum(1 for kw in config["keywords"] if kw in text)
        if hits > max_keyword_hits:
            max_keyword_hits = hits
            detected = config
    
    if not detected or max_keyword_hits == 0:
        return None
    
    # Determine severity
    severity = detected["base_severity"]
    escalation_hits = sum(1 for word in SEVERITY_ESCALATORS if word in text)
    if escalation_hits >= 3 and severity != "critical":
        severity = "critical"
    elif escalation_hits >= 1 and severity == "medium":
        severity = "high"
    
    # Try to extract location (simple heuristic: look for "in <Location>")
    location = None
    location_match = re.search(r'(?:in|near|across|hits?|strikes?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})', f"{title} {content}")
    if location_match:
        location = location_match.group(1)
    
    return {
        "alert_type": detected["type"],
        "severity": severity,
        "location": location,
        "keyword_hits": max_keyword_hits,
        "escalation_hits": escalation_hits,
    }


async def process_article_for_alerts(article_id: int):
    """
    Check if an article contains disaster-related content and create an alert.
    Called after article ingestion or classification.
    """
    with get_db_session() as db:
        article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
        if not article:
            return None
        
        result = detect_disaster(article.title or "", article.content or "")
        if not result:
            return None
        
        # Check if similar alert exists in last 24 hours
        cutoff = datetime.utcnow() - timedelta(hours=24)
        existing = db.query(DisasterAlert).filter(
            DisasterAlert.alert_type == result["alert_type"],
            DisasterAlert.is_active == True,
            DisasterAlert.created_at >= cutoff,
        ).first()
        
        if existing:
            # Update existing alert
            existing.source_count += 1
            if result["severity"] == "critical" and existing.severity != "critical":
                existing.severity = "critical"
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            alert = existing
        else:
            alert = DisasterAlert(
                article_id=article_id,
                alert_type=result["alert_type"],
                severity=result["severity"],
                title=f"🚨 {result['alert_type'].replace('_', ' ').title()} Alert: {article.title[:100]}",
                description=f"Source: {article.source or 'Unknown'}. {(article.content or '')[:300]}",
                location=result["location"],
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)
        
        # Broadcast alert via WebSocket
        alert_data = {
            "type": "disaster_alert",
            "data": {
                "id": str(alert.id),
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "title": alert.title,
                "location": alert.location,
                "source_count": alert.source_count,
                "created_at": alert.created_at.isoformat(),
            }
        }
        await manager.broadcast_alert(alert_data)
        await manager.broadcast_to_feed(alert_data)
        
        # Broadcast via WhatsApp for high/critical alerts
        if alert.severity in ("high", "critical"):
            from anip.shared.notifications import notifier
            whatsapp_msg = f"🚨 PULSE {alert.severity.upper()} ALERT: {alert.title}\n\n{alert.description[:200]}...\n\nLocation: {alert.location or 'Unknown'}"
            try:
                count = notifier.broadcast_alert(db, whatsapp_msg)
                logger.info(f"WhatsApp broadcast sent to {count} users.")
            except Exception as e:
                logger.error(f"Failed to broadcast WhatsApp alert: {e}")
        
        # Create post in natural-disasters community
        disaster_community = db.query(Community).filter(Community.slug == "natural-disasters").first()
        if disaster_community:
            existing_post = db.query(Post).filter(Post.article_id == article_id).first()
            if not existing_post:
                post = Post(
                    title=f"🚨 {alert.title}",
                    content=alert.description,
                    article_id=article_id,
                    community_id=disaster_community.id,
                    post_type="alert",
                    is_pinned=(result["severity"] == "critical"),
                )
                db.add(post)
                db.commit()
        
        logger.info(f"🚨 Disaster alert created: {alert.alert_type} ({alert.severity}) - {alert.title[:60]}")
        return alert


# ========== API Routes ==========

@router.get("", response_model=List[AlertResponse])
def list_alerts(
    active_only: bool = Query(default=True),
    severity: Optional[str] = Query(default=None),
    alert_type: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
):
    """List disaster alerts."""
    with get_db_session() as db:
        query = db.query(DisasterAlert)
        if active_only:
            query = query.filter(DisasterAlert.is_active == True)
        if severity:
            query = query.filter(DisasterAlert.severity == severity)
        if alert_type:
            query = query.filter(DisasterAlert.alert_type == alert_type)
        
        alerts = query.order_by(desc(DisasterAlert.created_at)).limit(limit).all()
        return [AlertResponse(
            id=a.id, alert_type=a.alert_type, severity=a.severity,
            title=a.title, description=a.description, location=a.location,
            source_count=a.source_count, is_active=a.is_active,
            created_at=a.created_at, updated_at=a.updated_at,
        ) for a in alerts]


@router.get("/stats", response_model=AlertStats)
def alert_stats():
    """Get alert statistics."""
    with get_db_session() as db:
        active = db.query(DisasterAlert).filter(DisasterAlert.is_active == True)
        return AlertStats(
            active_critical=active.filter(DisasterAlert.severity == "critical").count(),
            active_high=active.filter(DisasterAlert.severity == "high").count(),
            active_medium=active.filter(DisasterAlert.severity == "medium").count(),
            active_low=active.filter(DisasterAlert.severity == "low").count(),
            total_active=active.count(),
            total_resolved=db.query(DisasterAlert).filter(DisasterAlert.is_active == False).count(),
        )


@router.post("/scan")
async def scan_articles_for_disasters(
    hours: int = Query(default=24, ge=1, le=168),
    current_user: User = Depends(get_current_user),
):
    """Manually trigger disaster scan on recent articles."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    alerts_created = 0
    
    with get_db_session() as db:
        articles = db.query(NewsArticle).filter(
            NewsArticle.created_at >= cutoff
        ).all()
        
        for article in articles:
            try:
                result = await process_article_for_alerts(article.id)
                if result:
                    alerts_created += 1
            except Exception as e:
                logger.warning(f"Error scanning article {article.id}: {e}")
    
    return {"scanned": len(articles), "alerts_created": alerts_created}


@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: UUID, current_user: User = Depends(get_current_user)):
    """Mark an alert as resolved."""
    with get_db_session() as db:
        alert = db.query(DisasterAlert).filter(DisasterAlert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        alert.is_active = False
        alert.updated_at = datetime.utcnow()
        db.commit()
        return {"status": "resolved"}
