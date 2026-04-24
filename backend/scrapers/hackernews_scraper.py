"""
Hacker News real-time scraper.
Uses the official HN Algolia API — completely free, no API key needed.
Polls every 1 minute for top stories.
"""
import os
import sys
import time
import logging
import schedule
import requests
from datetime import datetime, timezone

# Add parent to path for common imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.kafka_publisher import publish_to_kafka
from common.rate_limiter import rate_limit, BackoffRetry

logging.basicConfig(level=logging.INFO, format='%(asctime)s [HackerNews] %(message)s')
logger = logging.getLogger(__name__)

HN_API = "https://hacker-news.firebaseio.com/v3"
HN_ALGOLIA = "https://hn.algolia.com/api/v1"

seen_ids = set()

@BackoffRetry(max_retries=3, base_delay=2.0)
@rate_limit(calls_per_minute=20)
def scrape_hackernews():
    """Scrape top Hacker News stories."""
    logger.info("🔍 Scraping Hacker News...")
    
    try:
        # Use Algolia API for top stories with more details
        resp = requests.get(
            f"{HN_ALGOLIA}/search",
            params={
                "tags": "front_page",
                "hitsPerPage": 15,
                "attributesToRetrieve": "title,url,points,num_comments,author,created_at,objectID,story_text"
            },
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        
        posted = 0
        for hit in data.get("hits", []):
            story_id = hit.get("objectID")
            if story_id in seen_ids:
                continue
            
            points = hit.get("points", 0) or 0
            if points < 10:  # Quality filter
                continue
            
            seen_ids.add(story_id)
            
            title = hit.get("title", "")
            url = hit.get("url", f"https://news.ycombinator.com/item?id={story_id}")
            content = hit.get("story_text") or f"🔗 {url}"
            
            publish_to_kafka({
                "type": "hackernews",
                "title": f"🔥 HN: {title}",
                "content": f"{content[:500]}\n\n📊 {points} points · {hit.get('num_comments', 0)} comments · by {hit.get('author', 'unknown')}",
                "source": "Hacker News",
                "url": url,
                "upvotes": points,
                "comments": hit.get("num_comments", 0),
                "author": hit.get("author", ""),
                "platform": "hackernews",
                "topic_hint": "technology",
            })
            posted += 1
        
        logger.info(f"✅ Published {posted} new HN stories")
    
    except Exception as e:
        logger.error(f"❌ HackerNews scrape failed: {e}")


def main():
    logger.info("🚀 Hacker News scraper starting...")
    scrape_hackernews()  # Run immediately
    schedule.every(1).minutes.do(scrape_hackernews)
    
    while True:
        schedule.run_pending()
        time.sleep(10)


if __name__ == "__main__":
    main()
