"""
Scraper API routes: ingest endpoint, stats, health monitoring.
This is the central hub that scrapers POST content to.
"""
import logging
import os
import time
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from collections import deque, defaultdict
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import func, desc

from anip.shared.database import get_db_session
from anip.shared.models.social import User, Post, Community
from anip.shared.models.news import NewsArticle

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/scraper", tags=["scraper"])

AI_BOT_TOKEN = os.getenv("AI_BOT_TOKEN", "anip-ai-bot-secret-2024")
AI_BOT_USERNAME = "ai-curator"
AI_BOT_EMAIL = "ai@anip.social"

# In-memory stats ring buffer (last 60 minutes, one entry per minute)
posts_timeline: deque = deque(maxlen=60)
platform_counts: Dict[str, int] = defaultdict(int)
total_auto_posts: int = 0
scraper_health: Dict[str, dict] = {}
last_post_time: Optional[float] = None

# Posts per minute tracking
minute_buckets: deque = deque(maxlen=60)
current_minute_count: int = 0
current_minute_start: float = time.time()


class ScraperIngestRequest(BaseModel):
    type: Optional[str] = None
    title: str
    content: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    platform: Optional[str] = None
    topic_hint: Optional[str] = None
    community_id: Optional[int] = None
    upvotes: Optional[int] = 0
    comments: Optional[int] = 0
    author: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    chart_image: Optional[str] = None
    # Alternative field names from regional scrapers
    source_name: Optional[str] = None
    source_type: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    published_at: Optional[str] = None


class ScraperStatsResponse(BaseModel):
    total_auto_posts: int
    posts_per_minute: float
    platform_breakdown: Dict[str, int]
    scraper_health: Dict[str, dict]
    timeline: List[Dict]
    active_scrapers: int


def get_or_create_ai_bot(db) -> User:
    """Get or create the AI bot user."""
    bot = db.query(User).filter(User.username == AI_BOT_USERNAME).first()
    if not bot:
        import bcrypt
        import uuid
        hashed = bcrypt.hashpw(b"ai-bot-secure-password-xyz", bcrypt.gensalt()).decode()
        bot = User(
            username=AI_BOT_USERNAME,
            email=AI_BOT_EMAIL,
            password_hash=hashed,
            bio="🤖 AI Curator — Automatically aggregating trending content from 12+ platforms every minute.",
        )
        db.add(bot)
        db.commit()
        db.refresh(bot)
        logger.info(f"✅ Created AI bot user: {AI_BOT_USERNAME}")
    return bot


def update_stats(platform: str):
    """Update in-memory statistics."""
    global total_auto_posts, current_minute_count, current_minute_start, last_post_time
    
    total_auto_posts += 1
    platform_counts[platform] += 1
    last_post_time = time.time()
    
    # Per-minute tracking
    now = time.time()
    if now - current_minute_start >= 60:
        minute_buckets.append({
            "timestamp": datetime.fromtimestamp(current_minute_start, timezone.utc).isoformat(),
            "count": current_minute_count,
        })
        current_minute_count = 0
        current_minute_start = now
    current_minute_count += 1
    
    # Update scraper health
    scraper_health[platform] = {
        "last_seen": datetime.now(timezone.utc).isoformat(),
        "status": "active",
        "posts_today": scraper_health.get(platform, {}).get("posts_today", 0) + 1,
    }


async def broadcast_new_post(post_data: dict):
    """Broadcast new auto-post via WebSocket."""
    try:
        from app.websocket_manager import manager
        await manager.broadcast_to_feed({
            "type": "new_auto_post",
            "post": post_data,
            "source": post_data.get("platform", "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.debug(f"WebSocket broadcast failed: {e}")


@router.post("/ingest")
async def ingest_scraped_content(
    request: Request,
    item: ScraperIngestRequest,
    background_tasks: BackgroundTasks,
):
    """
    Main ingest endpoint for scrapers.
    Receives scraped content and auto-posts to the social feed.
    """
    # Verify scraper token
    token = request.headers.get("X-Scraper-Token", "")
    if token != AI_BOT_TOKEN and AI_BOT_TOKEN != "":
        raise HTTPException(status_code=403, detail="Invalid scraper token")
    
    platform = item.platform or item.type or "unknown"
    
    # Normalize field names from different scraper formats:
    # Indian news scraper sends 'source_name' / 'source_type' instead of 'source' / 'platform'
    if item.source is None and item.source_name:
        item.source = item.source_name
    elif item.source is None and item.metadata and item.metadata.get('source_name'):
        item.source = item.metadata.get('source_name')
    if item.platform is None and item.source_type:
        platform = item.source_type
    elif item.platform is None and item.metadata and item.metadata.get('source_type'):
        platform = item.metadata.get('source_type')
    
    # Normalize top-level country/state fields into metadata
    if item.metadata is None:
        item.metadata = {}
    if item.country and not item.metadata.get('country'):
        item.metadata['country'] = item.country
    if item.state and not item.metadata.get('state'):
        item.metadata['state'] = item.state
    if item.city and not item.metadata.get('city'):
        item.metadata['city'] = item.city
    
    try:
        with get_db_session() as db:
            # Get or create AI bot user
            bot_user = get_or_create_ai_bot(db)
            
            # Determine community
            community_id = item.community_id
            if not community_id:
                community_id = _infer_community(db, item.topic_hint or item.type)
            
            # Build rich content
            content_parts = []
            if item.content:
                content_parts.append(item.content)
            if item.url:
                content_parts.append(f"\n🔗 [Original Source]({item.url})")
            if item.source:
                content_parts.append(f"📌 Via: **{item.source}**")
            if item.upvotes and item.upvotes > 0:
                content_parts.append(f"⬆️ {item.upvotes:,} engagement points")
            
            content = "\n".join(content_parts)
            
            # Create the news article first (for raw news feed and AI analysis)
            # Parse published_at if provided (ISO format string)
            published_at = None
            if item.published_at:
                try:
                    published_at = datetime.fromisoformat(item.published_at.replace('Z', '+00:00'))
                except:
                    published_at = None
            
            article = NewsArticle(
                title=item.title,
                content=item.content,
                source=item.source,
                url=item.url,
                author=item.author,
                api_source=platform,
                topic=item.topic_hint,
                published_at=published_at,  # Use original publication date if available
                # Additional metadata from our scrapers
                country=item.metadata.get('country') if item.metadata else None,
                state=item.metadata.get('state') if item.metadata else None,
                city=item.metadata.get('city') if item.metadata else None,
            )
            db.add(article)
            db.flush() # Get the article ID
            
            # Extract importance data from metadata if present, or calculate it if missing
            imp_score = item.metadata.get('importance_score') if item.metadata else None
            imp_breakdown = item.metadata.get('importance_breakdown') if item.metadata else None

            # Senior Dev: If importance is missing (direct post path), calculate it now as a fail-safe
            if imp_score is None:
                try:
                    from anip.shared.importance_scorer import ImportanceScorer
                    scorer = ImportanceScorer()
                    # We need to convert pydantic model to dict for calculation
                    imp_score, imp_breakdown = scorer.calculate_importance(item.model_dump())
                    logger.info(f"✨ AI Ranked (Direct Post): {item.title[:40]} → {imp_score}")
                except Exception as e:
                    logger.warning(f"Importance calculation failed (is importance_scorer.py available?): {e}")

            # Default to 50 if still none
            if imp_score is None:
                imp_score = 50

            # enforce threshold: only skip if it's really low (e.g. 20)
            if imp_score < 20:
                 logger.info(f"⏭️  Skipping garbage/spam ({imp_score}): {item.title[:50]}")
                 return {"success": False, "reason": "low_importance", "score": imp_score}



            # Create the social post linked to this article
            post = Post(
                title=item.title,
                content=content,
                author_id=bot_user.id,
                community_id=community_id,
                article_id=article.id,
                post_type="article_share",
                importance_score=imp_score,
                importance_breakdown=imp_breakdown
            )
            db.add(post)
            db.commit()
            db.refresh(post)
            db.refresh(article)
            
            # Build response data
            comm_name = None
            if community_id:
                comm = db.query(Community).filter(Community.id == community_id).first()
                comm_name = comm.name if comm else None
            
            post_data = {
                "id": str(post.id),
                "title": post.title,
                "content": post.content,
                "author": AI_BOT_USERNAME,
                "community": comm_name,
                "platform": platform,
                "source": item.source,
                "url": item.url,
                "upvotes": 0,
                "created_at": post.created_at.isoformat(),
                "is_auto_post": True,
                "chart_image": item.chart_image,
            }
            
            # Update stats
            update_stats(platform)
            
            # Broadcast via WebSocket (background)
            background_tasks.add_task(broadcast_new_post, post_data)
            
            logger.info(f"✅ Auto-posted [{platform}]: {item.title[:60]}")
            return {"success": True, "post_id": str(post.id), "community": comm_name}
    
    except Exception as e:
        logger.error(f"❌ Ingest failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _infer_community(db, topic_hint: Optional[str]) -> int:
    """Infer community ID from topic hint."""
    topic_map = {
        "technology": "technology",
        "tech": "technology",
        "economy": "economy",
        "business": "economy",
        "politics": "politics",
        "climate": "climate",
        "health": "health",
        "science": "science",
        "natural-disasters": "natural-disasters",
    }
    
    slug = topic_map.get((topic_hint or "").lower(), "technology")
    comm = db.query(Community).filter(Community.slug == slug).first()
    if comm:
        return comm.id
    
    # Fallback to first community
    first = db.query(Community).first()
    return first.id if first else None


@router.get("/stats", response_model=ScraperStatsResponse)
def get_scraper_stats():
    """Get real-time scraper statistics."""
    # Calculate posts per minute (last 5 minutes)
    recent_buckets = list(minute_buckets)[-5:]
    if recent_buckets:
        avg_ppm = sum(b["count"] for b in recent_buckets) / len(recent_buckets)
    else:
        avg_ppm = current_minute_count / max(1, (time.time() - current_minute_start) / 60)
    
    # Build timeline (last 30 minutes)
    timeline = list(minute_buckets)[-30:]
    
    # Add current minute
    timeline.append({
        "timestamp": datetime.fromtimestamp(current_minute_start, timezone.utc).isoformat(),
        "count": current_minute_count,
    })
    
    # Check scraper health (any scraper not seen in 5 min = degraded)
    now = datetime.now(timezone.utc)
    health = {}
    for platform, info in scraper_health.items():
        last = datetime.fromisoformat(info["last_seen"])
        age_minutes = (now - last).total_seconds() / 60
        health[platform] = {
            **info,
            "status": "active" if age_minutes < 5 else "degraded" if age_minutes < 15 else "offline",
        }
    
    return ScraperStatsResponse(
        total_auto_posts=total_auto_posts,
        posts_per_minute=round(avg_ppm, 1),
        platform_breakdown=dict(platform_counts),
        scraper_health=health,
        timeline=timeline,
        active_scrapers=sum(1 for h in health.values() if h["status"] == "active"),
    )


@router.post("/scraper/heartbeat")
def scraper_heartbeat(platform: str, status: str = "active"):
    """Scrapers ping this to report they're alive."""
    scraper_health[platform] = {
        "last_seen": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "posts_today": scraper_health.get(platform, {}).get("posts_today", 0),
    }
    return {"ok": True}


@router.get("/health")
def scraper_health_check():
    """Check if the scraper system is operational."""
    return {
        "status": "operational",
        "total_auto_posts": total_auto_posts,
        "last_post": last_post_time,
        "active_scrapers": len(scraper_health),
    }
