"""
Social platform API routes for ANIP.
Posts, Comments, Voting, Communities, and Feed.
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy.orm import defer
from pydantic import BaseModel
from sqlalchemy import func, desc, or_
from sqlalchemy.exc import SQLAlchemyError

from anip.shared.database import get_db_session
from anip.shared.models.social import User, Post, Comment, Vote, Community
from anip.shared.models.news import NewsArticle
from app.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/social", tags=["social"])


# ========== Pydantic Models ==========

class PostCreate(BaseModel):
    title: str
    content: Optional[str] = None
    community_id: Optional[int] = None
    article_id: Optional[int] = None  # If sharing an ANIP article

class PostResponse(BaseModel):
    id: UUID
    title: str
    content: Optional[str]
    author_username: str
    community_name: Optional[str] = None
    article_id: Optional[int] = None
    upvotes: int
    downvotes: int
    comment_count: int = 0
    created_at: datetime
    user_vote: Optional[int] = None  # 1, -1, or None

class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[UUID] = None  # For nested replies

class CommentResponse(BaseModel):
    id: UUID
    content: str
    author_username: str
    parent_id: Optional[UUID]
    upvotes: int
    downvotes: int
    created_at: datetime
    replies: List["CommentResponse"] = []
    user_vote: Optional[int] = None

class VoteRequest(BaseModel):
    vote_type: int  # 1 for upvote, -1 for downvote

class CommunityResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    member_count: int

class UserProfileResponse(BaseModel):
    id: UUID
    username: str
    bio: Optional[str]
    karma: int
    created_at: datetime
    post_count: int = 0
    comment_count: int = 0

class FeedItem(BaseModel):
    type: str  # 'post' or 'article'
    id: str
    title: str
    content: Optional[str] = None
    author: Optional[str] = None
    platform: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    sentiment: Optional[str] = None
    topic: Optional[str] = None
    metadata: Optional[dict] = None
    community: Optional[str] = None
    upvotes: int = 0
    downvotes: int = 0
    importance_score: int = 50
    importance_breakdown: Optional[dict] = None
    comment_count: int = 0
    created_at: datetime


# ========== COMMUNITIES ==========

@router.get("/communities", response_model=List[CommunityResponse])
def list_communities():
    """List all communities."""
    with get_db_session() as db:
        communities = db.query(Community).order_by(desc(Community.member_count)).all()
        return communities


@router.post("/communities", response_model=CommunityResponse)
def create_community(
    name: str = Query(...),
    slug: str = Query(...),
    description: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Create a new community."""
    with get_db_session() as db:
        existing = db.query(Community).filter(Community.slug == slug).first()
        if existing:
            raise HTTPException(status_code=400, detail="Community slug already exists")
        
        community = Community(name=name, slug=slug, description=description)
        db.add(community)
        db.commit()
        db.refresh(community)
        return community


@router.get("/communities/{slug}", response_model=CommunityResponse)
def get_community(slug: str):
    """Get community by slug."""
    with get_db_session() as db:
        community = db.query(Community).filter(Community.slug == slug).first()
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        return community


# ========== POSTS ==========

@router.post("/posts", response_model=PostResponse)
def create_post(post_in: PostCreate, current_user: User = Depends(get_current_user)):
    """Create a new post or share an article."""
    with get_db_session() as db:
        post = Post(
            title=post_in.title,
            content=post_in.content,
            author_id=current_user.id,
            community_id=post_in.community_id,
            article_id=post_in.article_id,
        )
        db.add(post)
        db.commit()
        db.refresh(post)

        # Build response
        author = db.query(User).filter(User.id == post.author_id).first()
        community = None
        if post.community_id:
            comm = db.query(Community).filter(Community.id == post.community_id).first()
            community = comm.name if comm else None

        return PostResponse(
            id=post.id,
            title=post.title,
            content=post.content,
            author_username=author.username,
            community_name=community,
            article_id=post.article_id,
            upvotes=post.upvotes,
            downvotes=post.downvotes,
            comment_count=0,
            created_at=post.created_at,
        )


@router.get("/posts", response_model=List[PostResponse])
def list_posts(
    community_slug: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List posts, optionally filtered by community."""
    with get_db_session() as db:
        query = db.query(Post)
        
        if community_slug:
            community = db.query(Community).filter(Community.slug == community_slug).first()
            if not community:
                raise HTTPException(status_code=404, detail="Community not found")
            query = query.filter(Post.community_id == community.id)
        
        posts = query.order_by(desc(Post.created_at)).offset(offset).limit(limit).all()
        
        results = []
        for post in posts:
            author = db.query(User).filter(User.id == post.author_id).first()
            community_name = None
            if post.community_id:
                comm = db.query(Community).filter(Community.id == post.community_id).first()
                community_name = comm.name if comm else None
            
            comment_count = db.query(func.count(Comment.id)).filter(Comment.post_id == post.id).scalar()
            
            results.append(PostResponse(
                id=post.id,
                title=post.title,
                content=post.content,
                author_username=author.username if author else "deleted",
                community_name=community_name,
                article_id=post.article_id,
                upvotes=post.upvotes,
                downvotes=post.downvotes,
                comment_count=comment_count,
                created_at=post.created_at,
            ))
        
        return results


@router.get("/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: UUID):
    """Get a single post by ID."""
    with get_db_session() as db:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        author = db.query(User).filter(User.id == post.author_id).first()
        community_name = None
        if post.community_id:
            comm = db.query(Community).filter(Community.id == post.community_id).first()
            community_name = comm.name if comm else None
        comment_count = db.query(func.count(Comment.id)).filter(Comment.post_id == post.id).scalar()
        
        return PostResponse(
            id=post.id,
            title=post.title,
            content=post.content,
            author_username=author.username if author else "deleted",
            community_name=community_name,
            article_id=post.article_id,
            upvotes=post.upvotes,
            downvotes=post.downvotes,
            comment_count=comment_count,
            created_at=post.created_at,
        )


# ========== COMMENTS ==========

@router.post("/posts/{post_id}/comments", response_model=CommentResponse)
def create_comment(post_id: UUID, comment_in: CommentCreate, current_user: User = Depends(get_current_user)):
    """Add a comment to a post."""
    with get_db_session() as db:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        comment = Comment(
            post_id=post_id,
            author_id=current_user.id,
            parent_id=comment_in.parent_id,
            content=comment_in.content,
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        
        author = db.query(User).filter(User.id == comment.author_id).first()
        return CommentResponse(
            id=comment.id,
            content=comment.content,
            author_username=author.username,
            parent_id=comment.parent_id,
            upvotes=comment.upvotes,
            downvotes=comment.downvotes,
            created_at=comment.created_at,
            replies=[],
        )


@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
def get_comments(post_id: UUID):
    """Get all comments for a post (threaded)."""
    with get_db_session() as db:
        comments = db.query(Comment).filter(
            Comment.post_id == post_id
        ).order_by(Comment.created_at).all()
        
        # Build threaded structure
        comment_map = {}
        top_level = []
        
        for c in comments:
            author = db.query(User).filter(User.id == c.author_id).first()
            resp = CommentResponse(
                id=c.id,
                content=c.content,
                author_username=author.username if author else "deleted",
                parent_id=c.parent_id,
                upvotes=c.upvotes,
                downvotes=c.downvotes,
                created_at=c.created_at,
                replies=[],
            )
            comment_map[c.id] = resp
            
            if c.parent_id and c.parent_id in comment_map:
                comment_map[c.parent_id].replies.append(resp)
            else:
                top_level.append(resp)
        
        return top_level


# ========== VOTING ==========

@router.post("/posts/{post_id}/vote")
def vote_on_post(post_id: UUID, vote: VoteRequest, current_user: User = Depends(get_current_user)):
    """Upvote or downvote a post."""
    if vote.vote_type not in (1, -1):
        raise HTTPException(status_code=400, detail="vote_type must be 1 or -1")
    
    with get_db_session() as db:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Check existing vote
        existing = db.query(Vote).filter(
            Vote.user_id == current_user.id,
            Vote.votable_id == post_id,
            Vote.votable_type == "post"
        ).first()
        
        if existing:
            if existing.vote_type == vote.vote_type:
                # Same vote → remove it (toggle off)
                if vote.vote_type == 1:
                    post.upvotes = max(0, post.upvotes - 1)
                else:
                    post.downvotes = max(0, post.downvotes - 1)
                db.delete(existing)
            else:
                # Different vote → switch
                if vote.vote_type == 1:
                    post.upvotes += 1
                    post.downvotes = max(0, post.downvotes - 1)
                else:
                    post.downvotes += 1
                    post.upvotes = max(0, post.upvotes - 1)
                existing.vote_type = vote.vote_type
        else:
            # New vote
            new_vote = Vote(
                user_id=current_user.id,
                votable_id=post_id,
                votable_type="post",
                vote_type=vote.vote_type,
            )
            db.add(new_vote)
            if vote.vote_type == 1:
                post.upvotes += 1
            else:
                post.downvotes += 1
        
        # Update author karma
        author = db.query(User).filter(User.id == post.author_id).first()
        if author:
            author.karma = author.karma + vote.vote_type
        
        db.commit()
        return {"upvotes": post.upvotes, "downvotes": post.downvotes}


@router.post("/comments/{comment_id}/vote")
def vote_on_comment(comment_id: UUID, vote: VoteRequest, current_user: User = Depends(get_current_user)):
    """Upvote or downvote a comment."""
    if vote.vote_type not in (1, -1):
        raise HTTPException(status_code=400, detail="vote_type must be 1 or -1")
    
    with get_db_session() as db:
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        existing = db.query(Vote).filter(
            Vote.user_id == current_user.id,
            Vote.votable_id == comment_id,
            Vote.votable_type == "comment"
        ).first()
        
        if existing:
            if existing.vote_type == vote.vote_type:
                if vote.vote_type == 1:
                    comment.upvotes = max(0, comment.upvotes - 1)
                else:
                    comment.downvotes = max(0, comment.downvotes - 1)
                db.delete(existing)
            else:
                if vote.vote_type == 1:
                    comment.upvotes += 1
                    comment.downvotes = max(0, comment.downvotes - 1)
                else:
                    comment.downvotes += 1
                    comment.upvotes = max(0, comment.upvotes - 1)
                existing.vote_type = vote.vote_type
        else:
            new_vote = Vote(
                user_id=current_user.id,
                votable_id=comment_id,
                votable_type="comment",
                vote_type=vote.vote_type,
            )
            db.add(new_vote)
            if vote.vote_type == 1:
                comment.upvotes += 1
            else:
                comment.downvotes += 1
        
        author = db.query(User).filter(User.id == comment.author_id).first()
        if author:
            author.karma = author.karma + vote.vote_type
        
        db.commit()
        return {"upvotes": comment.upvotes, "downvotes": comment.downvotes}


# ========== FEED (Mixed Articles + Posts) ==========

@router.get("/feed", response_model=List[FeedItem])
def get_feed(
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    community_slug: Optional[str] = None,
    sentiment: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
    sort: str = 'importance',
):
    """
    Get the unified social feed.
    Combines ANIP's AI-processed articles with user posts.
    Supports filtering by state/country/sentiment.
    """
    with get_db_session() as db:
        feed_items = []
        half = limit // 2
        
        # --- ANIP Articles --- (Defer embedding column for performance & stability)
        article_query = db.query(NewsArticle).options(defer(NewsArticle.embedding))
        if sentiment:
            article_query = article_query.filter(NewsArticle.sentiment == sentiment)
        if state:
            article_query = article_query.filter(NewsArticle.state == state)
        if country:
            article_query = article_query.filter(NewsArticle.country == country)
        
        # Fetch articles, using created_at as fallback for sorting
        articles = article_query.order_by(
            desc(func.coalesce(NewsArticle.published_at, NewsArticle.created_at))
        ).offset(offset).limit(limit).all()
        
        for a in articles:
            feed_items.append(FeedItem(
                type="article",
                id=str(a.id),
                title=a.title,
                content=(a.summary or a.content or "")[:280] if (a.summary or a.content) else None,
                author=a.author or a.source or "ANIP Intelligence",
                platform=a.api_source,
                source=a.source,
                url=a.url,
                sentiment=a.sentiment,
                topic=a.topic,
                metadata={"country": a.country, "state": a.state, "city": a.city},
                community=a.topic or "news",
                upvotes=0,
                downvotes=0,
                importance_score=50,
                comment_count=0,
                created_at=a.published_at or a.created_at,
            ))
        
        # --- User Posts ---
        post_query = db.query(Post)
        if community_slug:
            community = db.query(Community).filter(Community.slug == community_slug).first()
            if community:
                post_query = post_query.filter(Post.community_id == community.id)
        
        posts = post_query.order_by(desc(Post.created_at)).offset(offset).limit(limit).all()
        
        for p in posts:
            author = db.query(User).filter(User.id == p.author_id).first()
            community_name = None
            if p.community_id:
                comm = db.query(Community).filter(Community.id == p.community_id).first()
                community_name = comm.name if comm else None

            comment_count = db.query(func.count(Comment.id)).filter(Comment.post_id == p.id).scalar()

            # Get platform, source, url from linked article
            platform = 'manual'
            article_url = None
            article_source = None
            meta = {}
            if p.article_id:
                article = db.query(NewsArticle).filter(NewsArticle.id == p.article_id).first()
                if article:
                    platform = article.api_source or 'rss'
                    article_url = article.url
                    article_source = article.source
                    meta = {"country": article.country, "state": article.state, "city": article.city}

            # Strip embedded markdown from content – store only clean text
            raw_content = p.content or ''
            import re
            clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', raw_content)
            clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean)
            clean = re.sub(r'[🔗📌⬆️][^\n]*', '', clean).strip()

            feed_items.append(FeedItem(
                type="post",
                id=str(p.id),
                title=p.title,
                content=clean[:280] if clean else None,
                author=author.username if author else "deleted",
                platform=platform or 'rss',
                source=article_source,
                url=article_url,
                metadata=meta,
                community=community_name,
                upvotes=p.upvotes,
                downvotes=p.downvotes,
                importance_score=p.importance_score or 50,
                importance_breakdown=p.importance_breakdown,
                comment_count=comment_count,
                created_at=p.created_at,
            ))
        
        # Helper to convert mixed datetimes to naive integers for safe sorting
        def safe_ts(dt):
            if not dt:
                return 0
            if dt.tzinfo:
                return dt.astimezone(timezone.utc).replace(tzinfo=None).timestamp()
            return dt.timestamp()

        # Sort items
        if sort == 'importance':
            feed_items.sort(key=lambda x: (x.importance_score, safe_ts(x.created_at)), reverse=True)
        elif sort == 'new':
            feed_items.sort(key=lambda x: safe_ts(x.created_at), reverse=True)
        elif sort == 'hot':
            # Basic Reddit hotness heuristic
            feed_items.sort(
                key=lambda x: (x.upvotes - x.downvotes) / max(1, ((datetime.now(timezone.utc).replace(tzinfo=None) - x.created_at.replace(tzinfo=None)).total_seconds() / 3600 + 2) ** 1.5) if x.created_at else 0, 
                reverse=True
            )
        else:
            feed_items.sort(key=lambda x: safe_ts(x.created_at), reverse=True)

        # Deduplicate by URL to prevent identical articles from showing multiple times
        seen_urls = set()
        deduped_items = []
        for x in feed_items:
            # Normalize URL if possible, or just use identity
            if hasattr(x, 'url') and x.url:
                if x.url in seen_urls:
                    continue
                seen_urls.add(x.url)
            elif isinstance(x, dict) and x.get('url'):
                if x['url'] in seen_urls:
                    continue
                seen_urls.add(x['url'])
            deduped_items.append(x)
        feed_items = deduped_items

        return feed_items[:limit]


# ========== USER PROFILES ==========

@router.get("/users/{username}", response_model=UserProfileResponse)
def get_user_profile(username: str):
    """Get public user profile."""
    with get_db_session() as db:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        post_count = db.query(func.count(Post.id)).filter(Post.author_id == user.id).scalar()
        comment_count = db.query(func.count(Comment.id)).filter(Comment.author_id == user.id).scalar()
        
        return UserProfileResponse(
            id=user.id,
            username=user.username,
            bio=user.bio,
            karma=user.karma,
            created_at=user.created_at,
            post_count=post_count,
            comment_count=comment_count,
        )


@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile."""
    with get_db_session() as db:
        post_count = db.query(func.count(Post.id)).filter(Post.author_id == current_user.id).scalar()
        comment_count = db.query(func.count(Comment.id)).filter(Comment.author_id == current_user.id).scalar()
        
        return UserProfileResponse(
            id=current_user.id,
            username=current_user.username,
            bio=current_user.bio,
            karma=current_user.karma,
            created_at=current_user.created_at,
            post_count=post_count,
            comment_count=comment_count,
        )
