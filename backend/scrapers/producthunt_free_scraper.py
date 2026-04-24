"""
Product Hunt Free Scraper — NO API KEY REQUIRED
Uses Product Hunt's public RSS feed and web scraping.
"""
import os
import sys
import time
import logging
import schedule
from datetime import datetime, timezone

import feedparser

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.kafka_publisher import publish_to_kafka

logging.basicConfig(level=logging.INFO, format='%(asctime)s [ProductHunt] %(message)s')
logger = logging.getLogger(__name__)

seen_urls: set = set()
INTERVAL_MINUTES = int(os.getenv("PH_INTERVAL_MINUTES", "30"))

PRODUCT_HUNT_FEEDS = [
    ("https://www.producthunt.com/feed", "Top Products"),
    ("https://www.producthunt.com/topics/artificial-intelligence.rss", "AI Tools"),
]


def scrape_product_hunt():
    posted = 0
    for rss_url, label in PRODUCT_HUNT_FEEDS:
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:10]:
                url = getattr(entry, "link", "") or ""
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                title   = (getattr(entry, "title",   "") or "").strip()
                content = (getattr(entry, "summary", "") or "").strip()
                pub_raw = getattr(entry, "published", datetime.now(timezone.utc).isoformat())

                if not title:
                    continue

                publish_to_kafka({
                    "type":        "product_hunt",
                    "title":       f"Product Hunt — {label}: {title}",
                    "content":     content,
                    "source":      "Product Hunt",
                    "platform":    "product_hunt",
                    "url":         url,
                    "topic_hint":  "technology",
                    "published_at": pub_raw,
                    "metadata":    {"label": label},
                })
                posted += 1
                time.sleep(0.5)
        except Exception as e:
            logger.error(f"Product Hunt RSS error ({label}): {e}")

    logger.info(f"[+] Product Hunt: {posted} products published")
    return posted


def main():
    logger.info("=== Product Hunt Scraper started (NO API KEY) ===")
    scrape_product_hunt()
    schedule.every(INTERVAL_MINUTES).minutes.do(scrape_product_hunt)
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
