"""
Wikipedia Recent Changes scraper.
Uses the free MediaWiki API — no API key needed.
Polls every 1 minute for recently edited/created articles.
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s [Wikipedia] %(message)s')
logger = logging.getLogger(__name__)

WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKI_HEADERS = {
    "User-Agent": "ANIPSocialBot/1.0 (https://anip.social; anip@example.com) python-requests",
}
seen_titles = set()


@BackoffRetry(max_retries=3, base_delay=2.0)
@rate_limit(calls_per_minute=10)
def scrape_wikipedia():
    """Scrape Wikipedia recent changes for high-edit-count pages."""
    logger.info("📚 Scraping Wikipedia recent changes...")
    
    try:
        # Get pages with most edits in the last 10 minutes
        since = (datetime.now(timezone.utc) - timedelta(minutes=10)).strftime("%Y%m%d%H%M%S")
        
        resp = requests.get(WIKI_API, headers=WIKI_HEADERS, params={
            "action": "query",
            "list": "recentchanges",
            "rctype": "edit|new",
            "rclimit": 50,
            "rcnamespace": 0,  # Main articles only
            "rcprop": "title|timestamp|sizes|user|comment",
            "rcstart": since,
            "format": "json",
            "rcsort": "newer",
        }, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # Count edits per article
        edit_counts = {}
        articles = {}
        for change in data.get("query", {}).get("recentchanges", []):
            title = change.get("title", "")
            if not title or ":" in title:  # Skip non-article pages
                continue
            edit_counts[title] = edit_counts.get(title, 0) + 1
            if title not in articles:
                articles[title] = change
        
        # Post heavily-edited articles (trending)
        posted = 0
        for title, count in sorted(edit_counts.items(), key=lambda x: -x[1]):
            if count < 2:  # Only if edited multiple times (hot topic)
                continue
            if title in seen_titles:
                continue
            seen_titles.add(title)
            
            change = articles[title]
            wiki_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
            
            # Get short description
            summary = get_article_summary(title)
            
            publish_to_kafka({
                "type": "wikipedia",
                "title": f"📚 Wikipedia Trending: {title}",
                "content": f"{summary}\n\n✏️ Edited {count} times in last 10 minutes · Last editor: {change.get('user', 'unknown')}\n🔗 {wiki_url}",
                "source": "Wikipedia",
                "url": wiki_url,
                "platform": "wikipedia",
                "topic_hint": "technology",
                "metadata": {"edit_count": count, "article": title},
            })
            posted += 1
            if posted >= 3:
                break
        
        logger.info(f"✅ Published {posted} Wikipedia trending articles")
    
    except Exception as e:
        logger.error(f"❌ Wikipedia scrape failed: {e}")


def get_article_summary(title: str) -> str:
    """Fetch short extract from Wikipedia."""
    try:
        resp = requests.get(WIKI_API, headers=WIKI_HEADERS, params={
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "exintro": True,
            "exsentences": 3,
            "format": "json",
        }, timeout=5)
        pages = resp.json().get("query", {}).get("pages", {})
        for page in pages.values():
            extract = page.get("extract", "")
            # Strip HTML tags
            import re
            clean = re.sub('<[^<]+?>', '', extract)
            return clean[:400]
    except:
        pass
    return ""


def main():
    logger.info("🚀 Wikipedia scraper starting...")
    scrape_wikipedia()
    schedule.every(1).minutes.do(scrape_wikipedia)
    
    while True:
        schedule.run_pending()
        time.sleep(10)


if __name__ == "__main__":
    main()
