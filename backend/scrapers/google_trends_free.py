"""
Google Trends Free Scraper — NO API KEY REQUIRED
Uses pytrends (unofficial, free) to pull trending searches in India.
Also surfaces trending topics as live articles.
"""
import os
import sys
import time
import logging
import schedule
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.kafka_publisher import publish_to_kafka

logging.basicConfig(level=logging.INFO, format='%(asctime)s [GoogleTrends] %(message)s')
logger = logging.getLogger(__name__)

INTERVAL_MINUTES = int(os.getenv("TRENDS_INTERVAL_MINUTES", "20"))
seen_terms: set = set()


def scrape_trending_india():
    """Fetch India trending searches via pytrends (completely free)."""
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl="en-IN", tz=330)  # IST

        india_trends = pytrends.trending_searches(pn="india")
        posted = 0
        for term in india_trends[0].head(20).tolist():
            if term in seen_terms:
                continue
            seen_terms.add(term)

            try:
                # Get related news queries for context
                pytrends.build_payload([term], timeframe="now 4-H", geo="IN")
                related = pytrends.related_queries()
                top_related = []
                if related and term in related:
                    rq = related[term].get("top")
                    if rq is not None and not rq.empty:
                        top_related = rq["query"].head(5).tolist()
            except Exception:
                top_related = []

            related_str = ", ".join(top_related) if top_related else "—"
            content = (
                f'"{term}" is currently trending in India on Google Search.\n\n'
                f"Related queries: {related_str}\n\n"
                f"Search on Google: https://www.google.com/search?q={requests_encode(term)}"
            )

            publish_to_kafka({
                "type":        "google_trends",
                "title":       f"Trending in India: {term}",
                "content":     content,
                "source":      "Google Trends",
                "platform":    "google_trends",
                "url":         f"https://trends.google.com/trends/explore?q={requests_encode(term)}&geo=IN",
                "topic_hint":  "world",
                "country":     "India",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "metadata":    {
                    "trend_term":    term,
                    "related":       top_related,
                    "geo":           "IN",
                },
            })
            posted += 1
            time.sleep(3)  # Required delay to avoid pytrends rate-limit

        logger.info(f"[+] Google Trends India: {posted} trends published")
        return posted

    except ImportError:
        logger.error("pytrends not installed — run: pip install pytrends")
        return 0
    except Exception as e:
        logger.error(f"Google Trends error: {e}")
        return 0


def scrape_trending_global():
    """Fetch global real-time trending searches."""
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl="en-US", tz=0)

        global_trends = pytrends.trending_searches(pn="p1")  # Global
        posted = 0
        for term in global_trends[0].head(10).tolist():
            if f"global:{term}" in seen_terms:
                continue
            seen_terms.add(f"global:{term}")

            publish_to_kafka({
                "type":        "google_trends",
                "title":       f"Global Trending: {term}",
                "content":     f'"{term}" is trending globally on Google Search.\n\nExplore: https://trends.google.com/trends/explore?q={requests_encode(term)}',
                "source":      "Google Trends",
                "platform":    "google_trends",
                "url":         f"https://trends.google.com/trends/explore?q={requests_encode(term)}",
                "topic_hint":  "world",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "metadata":    {"trend_term": term, "geo": "Global"},
            })
            posted += 1
            time.sleep(2)

        logger.info(f"[+] Google Trends Global: {posted} trends published")
        return posted

    except Exception as e:
        logger.error(f"Global trends error: {e}")
        return 0


def requests_encode(text: str) -> str:
    """Simple URL-encoding."""
    return text.replace(" ", "+").replace("&", "%26")


def scrape_trends():
    logger.info("Scraping Google Trends (NO API KEY, pytrends)...")
    scrape_trending_india()
    time.sleep(5)
    scrape_trending_global()


def main():
    logger.info("=== Google Trends Scraper started (NO API KEY) ===")
    scrape_trends()
    schedule.every(INTERVAL_MINUTES).minutes.do(scrape_trends)
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
