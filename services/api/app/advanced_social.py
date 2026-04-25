"""
Advanced social features: Bookmarks, Search, Trending, User Settings, Profile Edit.
"""
import logging
import math
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy import desc, func, or_, and_, case

from anip.shared.database import get_db_session
from anip.shared.models.social import (
    User, Post, Comment, Community, Vote, Bookmark, UserSettings, Notification
)
from anip.shared.models.news import NewsArticle
from app.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/social", tags=["social-advanced"])


# ========== Pydantic Models ==========

class BookmarkResponse(BaseModel):
    id: UUID
    target_id: str
    target_type: str
    title: str
    preview: Optional[str] = None
    created_at: datetime


class SearchResult(BaseModel):
    type: str   # 'post', 'article', 'community', 'user'
    id: str
    title: str
    preview: Optional[str] = None
    score: float = 0
    sentiment: Optional[str] = None
    community: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None


class TrendingItem(BaseModel):
    id: str
    title: str
    type: str  # 'post' or 'article'
    score: float
    upvotes: int = 0
    comment_count: int = 0
    community: Optional[str] = None
    sentiment: Optional[str] = None
    created_at: datetime


class UserSettingsResponse(BaseModel):
    theme: str
    language: str
    email_notifications: bool
    push_notifications: bool
    whatsapp_notifications: bool
    notify_on_votes: bool
    notify_on_comments: bool
    notify_on_replies: bool
    notify_on_alerts: bool
    feed_sort: str
    show_sentiment: bool
    show_ai_analysis: bool


class UserSettingsUpdate(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    whatsapp_notifications: Optional[bool] = None
    notify_on_votes: Optional[bool] = None
    notify_on_comments: Optional[bool] = None
    notify_on_replies: Optional[bool] = None
    notify_on_alerts: Optional[bool] = None
    feed_sort: Optional[str] = None
    show_sentiment: Optional[bool] = None
    show_ai_analysis: Optional[bool] = None


class ProfileUpdate(BaseModel):
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    preferred_language: Optional[str] = None
    phone_number: Optional[str] = None


class StatsResponse(BaseModel):
    total_users: int
    total_posts: int
    total_comments: int
    total_articles: int
    total_communities: int
    active_users_24h: int


# ========== BOOKMARKS ==========

@router.post("/bookmarks/{target_type}/{target_id}", response_model=BookmarkResponse)
def toggle_bookmark(target_type: str, target_id: str, current_user: User = Depends(get_current_user)):
    """Toggle a bookmark on a post or article. Returns the bookmark if created, 204 if removed."""
    if target_type not in ("post", "article"):
        raise HTTPException(status_code=400, detail="target_type must be 'post' or 'article'")
    
    with get_db_session() as db:
        existing = db.query(Bookmark).filter(
            Bookmark.user_id == current_user.id,
            Bookmark.target_id == target_id,
            Bookmark.target_type == target_type,
        ).first()
        
        if existing:
            db.delete(existing)
            db.commit()
            return BookmarkResponse(
                id=existing.id, target_id=target_id, target_type=target_type,
                title="Removed", created_at=existing.created_at,
            )
        
        # Get title
        title = "Untitled"
        preview = None
        if target_type == "post":
            post = db.query(Post).filter(Post.id == target_id).first()
            if post:
                title = post.title
                preview = (post.content or "")[:200]
        else:
            article = db.query(NewsArticle).filter(NewsArticle.id == int(target_id)).first()
            if article:
                title = article.title
                preview = (article.content or "")[:200]
        
        bookmark = Bookmark(
            user_id=current_user.id,
            target_id=target_id,
            target_type=target_type,
        )
        db.add(bookmark)
        db.commit()
        db.refresh(bookmark)
        
        return BookmarkResponse(
            id=bookmark.id, target_id=target_id, target_type=target_type,
            title=title, preview=preview, created_at=bookmark.created_at,
        )


@router.get("/bookmarks", response_model=List[BookmarkResponse])
def get_bookmarks(
    target_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Get user's bookmarks."""
    with get_db_session() as db:
        query = db.query(Bookmark).filter(Bookmark.user_id == current_user.id)
        if target_type:
            query = query.filter(Bookmark.target_type == target_type)
        
        bookmarks = query.order_by(desc(Bookmark.created_at)).all()
        
        results = []
        for b in bookmarks:
            title = "Untitled"
            preview = None
            if b.target_type == "post":
                post = db.query(Post).filter(Post.id == b.target_id).first()
                if post:
                    title = post.title
                    preview = (post.content or "")[:200]
            else:
                try:
                    article = db.query(NewsArticle).filter(NewsArticle.id == int(b.target_id)).first()
                    if article:
                        title = article.title
                        preview = (article.content or "")[:200]
                except (ValueError, TypeError):
                    pass
            
            results.append(BookmarkResponse(
                id=b.id, target_id=b.target_id, target_type=b.target_type,
                title=title, preview=preview, created_at=b.created_at,
            ))
        
        return results


# ========== SEARCH ==========

@router.get("/search", response_model=List[SearchResult])
def search(
    q: str = Query(..., min_length=2, max_length=200),
    type_filter: Optional[str] = Query(None, description="post, article, community, user"),
    limit: int = Query(default=20, ge=1, le=50),
):
    """Search across posts, articles, communities, and users."""
    results = []
    search_term = f"%{q.lower()}%"
    
    with get_db_session() as db:
        # Search posts
        if not type_filter or type_filter == "post":
            posts = db.query(Post).filter(
                or_(
                    func.lower(Post.title).like(search_term),
                    func.lower(Post.content).like(search_term),
                )
            ).order_by(desc(Post.created_at)).limit(limit).all()
            
            for p in posts:
                author = db.query(User).filter(User.id == p.author_id).first()
                comm_name = None
                if p.community_id:
                    comm = db.query(Community).filter(Community.id == p.community_id).first()
                    comm_name = comm.name if comm else None
                
                results.append(SearchResult(
                    type="post", id=str(p.id), title=p.title,
                    preview=(p.content or "")[:200],
                    community=comm_name,
                    author=author.username if author else None,
                    created_at=p.created_at,
                ))
        
        # Search articles
        if not type_filter or type_filter == "article":
            articles = db.query(NewsArticle).filter(
                or_(
                    func.lower(NewsArticle.title).like(search_term),
                    func.lower(NewsArticle.content).like(search_term),
                )
            ).order_by(desc(NewsArticle.published_at)).limit(limit).all()
            
            for a in articles:
                results.append(SearchResult(
                    type="article", id=str(a.id), title=a.title,
                    preview=(a.content or "")[:200],
                    sentiment=a.sentiment,
                    author=a.author,
                    created_at=a.published_at or a.created_at,
                ))
        
        # Search communities
        if not type_filter or type_filter == "community":
            communities = db.query(Community).filter(
                or_(
                    func.lower(Community.name).like(search_term),
                    func.lower(Community.description).like(search_term),
                )
            ).limit(10).all()
            
            for c in communities:
                results.append(SearchResult(
                    type="community", id=str(c.id), title=c.name,
                    preview=c.description,
                ))
        
        # Search users
        if not type_filter or type_filter == "user":
            users = db.query(User).filter(
                func.lower(User.username).like(search_term)
            ).limit(10).all()
            
            for u in users:
                results.append(SearchResult(
                    type="user", id=str(u.id), title=u.username,
                    preview=u.bio,
                    created_at=u.created_at,
                ))
    
    return results[:limit]


# ========== TRENDING ==========

def hot_score(upvotes: int, downvotes: int, created_at: datetime) -> float:
    """Reddit-like hot score algorithm."""
    score = upvotes - downvotes
    order = math.log10(max(abs(score), 1))
    sign = 1 if score > 0 else -1 if score < 0 else 0
    epoch = datetime(2024, 1, 1)
    seconds = (created_at - epoch).total_seconds()
    return round(sign * order + seconds / 45000, 7)


@router.get("/trending", response_model=List[TrendingItem])
def get_trending(
    period: str = Query(default="day", description="hour, day, week, month"),
    limit: int = Query(default=20, ge=1, le=50),
):
    """Get trending posts and articles using a hot-score algorithm."""
    now = datetime.utcnow()
    periods = {
        "hour": timedelta(hours=1),
        "day": timedelta(days=1),
        "week": timedelta(weeks=1),
        "month": timedelta(days=30),
    }
    cutoff = now - periods.get(period, timedelta(days=1))
    
    with get_db_session() as db:
        items = []
        
        # Trending posts
        posts = db.query(Post).filter(Post.created_at >= cutoff).all()
        for p in posts:
            comment_count = db.query(func.count(Comment.id)).filter(Comment.post_id == p.id).scalar()
            comm_name = None
            if p.community_id:
                comm = db.query(Community).filter(Community.id == p.community_id).first()
                comm_name = comm.name if comm else None
            
            score = hot_score(p.upvotes, p.downvotes, p.created_at)
            items.append(TrendingItem(
                id=str(p.id), title=p.title, type="post",
                score=score, upvotes=p.upvotes, comment_count=comment_count,
                community=comm_name, created_at=p.created_at,
            ))
        
        # Trending articles
        articles = db.query(NewsArticle).filter(
            or_(NewsArticle.published_at >= cutoff, NewsArticle.created_at >= cutoff)
        ).all()
        for a in articles:
            dt = a.published_at or a.created_at
            score = hot_score(0, 0, dt)
            items.append(TrendingItem(
                id=str(a.id), title=a.title, type="article",
                score=score, sentiment=a.sentiment, created_at=dt,
            ))
        
        items.sort(key=lambda x: x.score, reverse=True)
        return items[:limit]


# ========== USER SETTINGS ==========

@router.get("/settings", response_model=UserSettingsResponse)
def get_settings(current_user: User = Depends(get_current_user)):
    """Get user settings."""
    with get_db_session() as db:
        settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
        if not settings:
            settings = UserSettings(user_id=current_user.id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        
        return UserSettingsResponse(
            theme=settings.theme,
            language=settings.language,
            email_notifications=settings.email_notifications,
            push_notifications=settings.push_notifications,
            whatsapp_notifications=settings.whatsapp_notifications,
            notify_on_votes=settings.notify_on_votes,
            notify_on_comments=settings.notify_on_comments,
            notify_on_replies=settings.notify_on_replies,
            notify_on_alerts=settings.notify_on_alerts,
            feed_sort=settings.feed_sort,
            show_sentiment=settings.show_sentiment,
            show_ai_analysis=settings.show_ai_analysis,
        )


@router.put("/settings", response_model=UserSettingsResponse)
def update_settings(update: UserSettingsUpdate, current_user: User = Depends(get_current_user)):
    """Update user settings."""
    with get_db_session() as db:
        settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
        if not settings:
            settings = UserSettings(user_id=current_user.id)
            db.add(settings)
        
        for field, value in update.dict(exclude_unset=True).items():
            if value is not None:
                setattr(settings, field, value)
        
        db.commit()
        db.refresh(settings)
        
        return UserSettingsResponse(
            theme=settings.theme,
            language=settings.language,
            email_notifications=settings.email_notifications,
            push_notifications=settings.push_notifications,
            whatsapp_notifications=settings.whatsapp_notifications,
            notify_on_votes=settings.notify_on_votes,
            notify_on_comments=settings.notify_on_comments,
            notify_on_replies=settings.notify_on_replies,
            notify_on_alerts=settings.notify_on_alerts,
            feed_sort=settings.feed_sort,
            show_sentiment=settings.show_sentiment,
            show_ai_analysis=settings.show_ai_analysis,
        )


# ========== PROFILE EDIT ==========

@router.put("/profile")
def update_profile(update: ProfileUpdate, current_user: User = Depends(get_current_user)):
    """Update user profile."""
    with get_db_session() as db:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if update.bio is not None:
            user.bio = update.bio
        if update.avatar_url is not None:
            user.avatar_url = update.avatar_url
        if update.preferred_language is not None:
            user.preferred_language = update.preferred_language
        if update.phone_number is not None:
            # Basic sanitization for Twilio
            phone = update.phone_number.strip().replace(" ", "").replace("-", "")
            if phone:
                if not phone.startswith('+'):
                    if len(phone) == 10:
                        phone = "+91" + phone
                    else:
                        phone = "+" + phone
                user.phone_number = phone
            else:
                user.phone_number = None

            # Enable WhatsApp notifications automatically when a phone number is added
            if user.phone_number:
                settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
                if not settings:
                    settings = UserSettings(user_id=user.id, whatsapp_notifications=True)
                    db.add(settings)
                else:
                    settings.whatsapp_notifications = True
        
        db.commit()
        return {"status": "ok", "username": user.username}


# ========== PLATFORM STATS ==========

@router.get("/stats", response_model=StatsResponse)
def get_platform_stats():
    """Get platform-wide statistics."""
    with get_db_session() as db:
        cutoff_24h = datetime.utcnow() - timedelta(hours=24)
        
        return StatsResponse(
            total_users=db.query(func.count(User.id)).scalar(),
            total_posts=db.query(func.count(Post.id)).scalar(),
            total_comments=db.query(func.count(Comment.id)).scalar(),
            total_articles=db.query(func.count(NewsArticle.id)).scalar(),
            total_communities=db.query(func.count(Community.id)).scalar(),
            active_users_24h=db.query(func.count(User.id)).filter(
                User.id.in_(
                    db.query(Post.author_id).filter(Post.created_at >= cutoff_24h).union(
                        db.query(Comment.author_id).filter(Comment.created_at >= cutoff_24h)
                    )
                )
            ).scalar(),
        )
