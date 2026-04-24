"""
Auto-post ANIP articles to communities based on AI topic classification.
This bridges the ANIP intelligence pipeline with the social platform.
"""
import logging
from anip.shared.database import get_db_session
from anip.shared.models.news import NewsArticle
from anip.shared.models.social import Post, Community

logger = logging.getLogger(__name__)

# Map ANIP's classification labels to community slugs
TOPIC_TO_COMMUNITY = {
    "technology": "technology",
    "tech": "technology",
    "ai": "technology",
    "artificial intelligence": "technology",
    "software": "technology",
    "business": "economy",
    "economy": "economy",
    "finance": "economy",
    "markets": "economy",
    "politics": "politics",
    "government": "politics",
    "election": "politics",
    "policy": "politics",
    "climate": "climate",
    "environment": "climate",
    "weather": "climate",
    "health": "health",
    "medicine": "health",
    "healthcare": "health",
    "disaster": "natural-disasters",
    "earthquake": "natural-disasters",
    "flood": "natural-disasters",
    "hurricane": "natural-disasters",
    "science": "science",
    "space": "science",
    "research": "science",
}


def auto_post_article_to_community(article_id: int):
    """
    Given an article ID, create a system post in the matching community.
    Returns the created Post or None if no match.
    """
    with get_db_session() as db:
        article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
        if not article or not article.topic:
            return None
        
        # Find matching community
        topic_lower = article.topic.lower().strip()
        community_slug = TOPIC_TO_COMMUNITY.get(topic_lower)
        
        if not community_slug:
            # Try partial match
            for keyword, slug in TOPIC_TO_COMMUNITY.items():
                if keyword in topic_lower or topic_lower in keyword:
                    community_slug = slug
                    break
        
        if not community_slug:
            return None
        
        community = db.query(Community).filter(Community.slug == community_slug).first()
        if not community:
            return None
        
        # Check if already posted
        existing = db.query(Post).filter(Post.article_id == article_id).first()
        if existing:
            return existing
        
        # Create system post (no author = system generated)
        post = Post(
            title=article.title,
            content=f"📰 Source: {article.source or 'Unknown'}\n\n{(article.content or '')[:500]}",
            article_id=article_id,
            community_id=community.id,
            author_id=None,  # System post
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        
        logger.info(f"✅ Auto-posted article '{article.title[:50]}...' to c/{community_slug}")
        return post


def auto_post_all_unposted_articles():
    """Post all classified articles that haven't been posted to communities yet."""
    with get_db_session() as db:
        # Get articles with topics that don't have corresponding posts
        articles = db.query(NewsArticle).filter(
            NewsArticle.topic.isnot(None),
            ~NewsArticle.id.in_(
                db.query(Post.article_id).filter(Post.article_id.isnot(None))
            )
        ).limit(100).all()
        
        posted = 0
        for article in articles:
            try:
                result = auto_post_article_to_community(article.id)
                if result:
                    posted += 1
            except Exception as e:
                logger.warning(f"Failed to auto-post article {article.id}: {e}")
        
        logger.info(f"🏘️ Auto-posted {posted} articles to communities")
        return posted
