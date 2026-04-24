"""
AI Summarizer using GPT-4o-mini.
Rewrites raw scraped content into professional news posts.
Falls back to rule-based summarization if OpenAI key is unavailable.
"""
import os
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Post format template
POST_FORMAT = "[{platform}] {event}: {summary} — {stat}"

PLATFORM_LABELS = {
    "reddit": "Reddit",
    "reddit_post": "Reddit",
    "hackernews": "Hacker News",
    "github": "GitHub",
    "github_trending": "GitHub Trending",
    "google_trends": "Google Trends",
    "wikipedia": "Wikipedia",
    "product_hunt": "Product Hunt",
    "newsapi": "News",
    "gdelt": "Global News",
    "x": "X (Twitter)",
    "x_trending": "X (Twitter)",
    "youtube": "YouTube",
    "linkedin": "LinkedIn",
}


def ai_rewrite(scraped_item: dict) -> str:
    """
    Rewrite scraped content using GPT-4o-mini.
    Returns the rewritten content string.
    Falls back to rule-based rewrite if API unavailable.
    """
    if OPENAI_API_KEY and OPENAI_API_KEY not in ("", "your_openai_api_key_here"):
        result = _openai_rewrite(scraped_item)
        if result:
            return result

    return _rule_based_rewrite(scraped_item)


def _openai_rewrite(scraped_item: dict) -> Optional[str]:
    """Use OpenAI GPT-4o-mini for summarization."""
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)

        platform = PLATFORM_LABELS.get(scraped_item.get("platform", ""), scraped_item.get("source", "News"))
        title = scraped_item.get("title", "")
        content = scraped_item.get("content", "")[:500]
        upvotes = scraped_item.get("upvotes", 0)
        url = scraped_item.get("url", "")

        stat_str = ""
        if upvotes > 0:
            stat_str = f"{upvotes:,} upvotes"
        elif scraped_item.get("metadata", {}).get("views"):
            stat_str = f"{scraped_item['metadata']['views']:,} views"

        prompt = f"""You are an AI news curator for ANIP Social, an autonomous news platform.
Rewrite this scraped content into a compelling, professional social media post (2-4 sentences max).

Platform: {platform}
Title: {title}
Content: {content}
Engagement: {stat_str}
Source URL: {url}

Rules:
- Start with the platform emoji and name: e.g. "🔥 Hacker News:"
- Be factual and neutral
- Include the key insight or finding
- End with the engagement metric if impressive
- Max 400 characters
- DO NOT include URLs (they'll be added separately)

Write ONLY the post content, no extra commentary."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.5,
        )

        text = response.choices[0].message.content.strip()
        logger.debug(f"GPT rewrote: {text[:80]}")
        return text

    except ImportError:
        logger.debug("openai package not installed")
        return None
    except Exception as e:
        logger.warning(f"OpenAI rewrite failed: {e}")
        return None


def _rule_based_rewrite(scraped_item: dict) -> str:
    """
    Rule-based fallback summarizer.
    Produces readable posts without GPT.
    """
    platform = PLATFORM_LABELS.get(
        scraped_item.get("platform", scraped_item.get("type", "")),
        scraped_item.get("source", "News"),
    )
    title = scraped_item.get("title", "").strip()
    content = scraped_item.get("content", "").strip()
    upvotes = scraped_item.get("upvotes", 0)

    # Remove existing platform prefix from title if present
    for prefix in PLATFORM_LABELS.values():
        if title.startswith(f"🔥 {prefix}:") or title.startswith(f"📰 {prefix}:"):
            title = title.split(":", 1)[-1].strip()
            break

    # Build stat string
    stat_parts = []
    if upvotes and upvotes > 0:
        stat_parts.append(f"{upvotes:,} upvotes")
    meta = scraped_item.get("metadata", {})
    if meta.get("stars"):
        stat_parts.append(f"⭐ {meta['stars']:,} stars")
    if meta.get("views"):
        stat_parts.append(f"👁️ {meta['views']:,} views")

    stat_str = " · ".join(stat_parts) if stat_parts else None

    # Build post
    # Use first 2 sentences of content as summary
    sentences = re.split(r'(?<=[.!?])\s+', content)
    summary = " ".join(sentences[:2])[:250] if sentences else content[:250]

    if stat_str:
        result = f"{title}\n\n{summary}\n\n📊 {stat_str}"
    else:
        result = f"{title}\n\n{summary}"

    return result[:600]


def build_post_title(scraped_item: dict, rewritten_content: str) -> str:
    """
    Build a clean post title from rewritten content.
    Uses first line of rewritten content or original title.
    """
    first_line = rewritten_content.split("\n")[0].strip()
    original_title = scraped_item.get("title", "")

    # If first line is too short, use original title
    if len(first_line) < 20:
        return original_title[:200]

    return first_line[:200]
