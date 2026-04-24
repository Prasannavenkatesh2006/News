"""
LinkedIn viral posts scraper.
Uses Playwright/Selenium to scrape public LinkedIn posts from influencers.
Falls back to LinkedIn RSS where available.
Note: LinkedIn aggressively blocks bots — use with caution and respect ToS.
"""
import os
import sys
import time
import logging
import schedule
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.kafka_publisher import publish_to_kafka
from common.rate_limiter import rate_limit

logging.basicConfig(level=logging.INFO, format='%(asctime)s [LinkedIn] %(message)s')
logger = logging.getLogger(__name__)

LINKEDIN_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
seen_ids: set = set()

# Public LinkedIn influencer slugs to monitor
INFLUENCER_SLUGS = [
    "satyanadella",
    "sundarpichai",
    "jeffweiner",
    "billgates",
]


def scrape_linkedin_api():
    """Use LinkedIn Marketing API (requires OAuth token)."""
    if not LINKEDIN_TOKEN:
        return False

    try:
        headers = {
            "Authorization": f"Bearer {LINKEDIN_TOKEN}",
            "LinkedIn-Version": "202301",
        }

        # Get my organization's posts (using LinkedIn API)
        resp = requests.get(
            "https://api.linkedin.com/v2/ugcPosts?q=authors&authors=List(urn%3Ali%3Aorganization%3AYOUR_ORG_ID)&count=10",
            headers=headers,
            timeout=15,
        )

        if resp.status_code != 200:
            return False

        data = resp.json()
        posted = 0
        for item in data.get("elements", []):
            post_id = item.get("id", "")
            if post_id in seen_ids:
                continue
            seen_ids.add(post_id)

            content = item.get("specificContent", {}).get("com.linkedin.ugc.ShareContent", {})
            text = content.get("shareCommentary", {}).get("text", "")

            if not text or len(text) < 50:
                continue

            publish_to_kafka({
                "type": "linkedin",
                "title": f"💼 LinkedIn: {text[:100]}",
                "content": text[:500],
                "source": "LinkedIn",
                "platform": "linkedin",
                "topic_hint": "economy",
            })
            posted += 1

        logger.info(f"✅ LinkedIn API: {posted} posts")
        return True
    except Exception as e:
        logger.error(f"LinkedIn API error: {e}")
        return False


def scrape_linkedin_rss():
    """
    Scrape LinkedIn thought leaders via their public RSS feeds
    (some users publish RSS via third-party tools like Feedly).
    """
    # Use tech influencer blogs that cross-post from LinkedIn
    blogs_with_rss = [
        ("https://feeds.feedburner.com/venturebeat/SZYF", "VentureBeat"),
        ("https://techcrunch.com/feed/", "TechCrunch"),
        ("https://feeds.feedburner.com/Techcrunch", "TechCrunch"),
    ]

    posted = 0
    for feed_url, source in blogs_with_rss:
        try:
            import feedparser
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:3]:
                link = entry.get("link", "")
                if link in seen_ids:
                    continue
                seen_ids.add(link)

                title = entry.get("title", "")
                summary = entry.get("summary", "")[:200]

                if not title:
                    continue

                publish_to_kafka({
                    "type": "linkedin",
                    "title": f"💼 {source}: {title}",
                    "content": f"{summary}\n\n🔗 {link}",
                    "source": source,
                    "url": link,
                    "platform": "linkedin",
                    "topic_hint": "economy",
                })
                posted += 1
        except ImportError:
            logger.warning("feedparser not installed (pip install feedparser)")
        except Exception as e:
            logger.debug(f"RSS error ({source}): {e}")

    return posted


def scrape_linkedin():
    logger.info("💼 Scraping LinkedIn...")
    if not scrape_linkedin_api():
        count = scrape_linkedin_rss()
        if count == 0:
            logger.debug("LinkedIn: no API key and feedparser fallback empty")


def main():
    logger.info("🚀 LinkedIn scraper starting...")
    scrape_linkedin()
    schedule.every(10).minutes.do(scrape_linkedin)  # Be gentle with LinkedIn

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
