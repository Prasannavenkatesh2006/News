"""
Reddit scraper using official public API (no authentication required).
Uses the JSON endpoint that Reddit makes publicly available.
Polls every 1 minute for hot posts across major subreddits.
"""
import os
import sys
import time
import logging
import schedule
import requests
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.kafka_publisher import publish_to_kafka
from common.rate_limiter import rate_limit, BackoffRetry

logging.basicConfig(level=logging.INFO, format='%(asctime)s [Reddit] %(message)s')
logger = logging.getLogger(__name__)

REDDIT_BASE = "https://www.reddit.com"
SUBREDDITS = ["worldnews", "technology", "india", "programming", "science", "todayilearned", "explainlikeimfive"]
seen_ids = set()

HEADERS = {
    "User-Agent": "ANIPBot/1.0 (AI News Intelligence Platform; contact@anip.social)",
    "Accept": "application/json",
}

TOPIC_HINTS = {
    "worldnews": "politics",
    "technology": "technology",
    "india": "politics",
    "programming": "technology",
    "science": "science",
    "todayilearned": "science",
    "explainlikeimfive": "science",
}


@BackoffRetry(max_retries=3, base_delay=5.0)
@rate_limit(calls_per_minute=10)
def scrape_reddit():
    """Scrape hot posts from multiple subreddits."""
    logger.info("📰 Scraping Reddit...")
    
    posted = 0
    for subreddit in SUBREDDITS:
        try:
            resp = requests.get(
                f"{REDDIT_BASE}/r/{subreddit}/hot.json",
                params={"limit": 10},
                headers=HEADERS,
                timeout=10,
            )
            if resp.status_code == 429:
                logger.warning(f"Rate limited on r/{subreddit}, backing off...")
                time.sleep(30)
                continue
            resp.raise_for_status()
            
            data = resp.json()
            posts = data.get("data", {}).get("children", [])
            
            for post_data in posts:
                p = post_data.get("data", {})
                post_id = p.get("id", "")
                
                if post_id in seen_ids:
                    continue
                
                upvotes = p.get("ups", 0) or 0
                if upvotes < 50:  # Quality filter
                    continue
                
                # Only recent posts (last 2 hours)
                created = p.get("created_utc", 0)
                age_hours = (datetime.now(timezone.utc).timestamp() - created) / 3600
                if age_hours > 2:
                    continue
                
                seen_ids.add(post_id)
                
                title = p.get("title", "")
                selftext = p.get("selftext", "")
                url = p.get("url", "")
                permalink = p.get("permalink", "")
                comments = p.get("num_comments", 0)
                author = p.get("author", "unknown")
                flair = p.get("link_flair_text", "")
                
                content_parts = []
                if selftext and selftext != "[removed]":
                    content_parts.append(selftext[:400])
                if url and not url.startswith("https://www.reddit.com"):
                    content_parts.append(f"🔗 {url}")
                content_parts.append(f"\n📊 {upvotes:,} upvotes · {comments:,} comments · u/{author}")
                if flair:
                    content_parts.append(f"🏷️ {flair}")
                
                publish_to_kafka({
                    "type": "reddit_post",
                    "title": f"📰 Reddit r/{subreddit}: {title}",
                    "content": "\n".join(content_parts),
                    "source": f"Reddit r/{subreddit}",
                    "url": f"{REDDIT_BASE}{permalink}",
                    "platform": "reddit",
                    "upvotes": upvotes,
                    "comments": comments,
                    "author": author,
                    "subreddit": subreddit,
                    "topic_hint": TOPIC_HINTS.get(subreddit, "technology"),
                })
                posted += 1
            
            time.sleep(2)  # Be polite between subreddits
            
        except Exception as e:
            logger.error(f"❌ Reddit r/{subreddit} failed: {e}")
    
    logger.info(f"✅ Published {posted} Reddit posts")


def main():
    logger.info("🚀 Reddit scraper starting...")
    scrape_reddit()
    schedule.every(1).minutes.do(scrape_reddit)
    
    while True:
        schedule.run_pending()
        time.sleep(10)


if __name__ == "__main__":
    main()
