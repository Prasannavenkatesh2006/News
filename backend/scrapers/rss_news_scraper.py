"""
RSS News Scraper - 100% FREE, NO API KEYS REQUIRED
Aggregates 50+ news sources via public RSS feeds.
Covers: International, Indian, Tamil Nadu, Business, Tech.
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s [RSS-News] %(message)s')
logger = logging.getLogger(__name__)

seen_urls: set = set()

# ---------------------------------------------------------------------------
# 50+ FREE RSS Sources  (zero API keys)
# ---------------------------------------------------------------------------
FREE_NEWS_SOURCES = {
    # ── International ──────────────────────────────────────────────────────
    "BBC World":         ("http://feeds.bbci.co.uk/news/world/rss.xml",          "Global", None,          "world"),
    "BBC Technology":    ("http://feeds.bbci.co.uk/news/technology/rss.xml",     "Global", None,          "technology"),
    "Reuters":           ("https://feeds.reuters.com/reuters/topNews",            "Global", None,          "world"),
    "Al Jazeera":        ("https://www.aljazeera.com/xml/rss/all.xml",            "Global", None,          "world"),
    "The Guardian":      ("https://www.theguardian.com/world/rss",               "Global", None,          "world"),
    "Guardian Tech":     ("https://www.theguardian.com/technology/rss",          "Global", None,          "technology"),
    "NPR News":          ("https://feeds.npr.org/1001/rss.xml",                   "Global", None,          "world"),
    "Ars Technica":      ("http://feeds.arstechnica.com/arstechnica/index",       "Global", None,          "technology"),
    "TechCrunch":        ("https://techcrunch.com/feed/",                         "Global", None,          "technology"),
    "Wired":             ("https://www.wired.com/feed/rss",                       "Global", None,          "technology"),
    "MIT Tech Review":   ("https://www.technologyreview.com/feed/",              "Global", None,          "technology"),
    "Science Daily":     ("https://www.sciencedaily.com/rss/all.xml",            "Global", None,          "science"),
    "Space.com":         ("https://www.space.com/feeds/all",                      "Global", None,          "science"),
    "NASA":              ("https://www.nasa.gov/rss/dyn/breaking_news.rss",       "Global", None,          "science"),
    "Hacker News":       ("https://hnrss.org/frontpage",                          "Global", None,          "technology"),
    "Product Hunt":      ("https://www.producthunt.com/feed",                     "Global", None,          "technology"),
    "Reddit r/world":    ("https://www.reddit.com/r/worldnews/.rss",             "Global", None,          "world"),
    "Reddit Science":    ("https://www.reddit.com/r/science/.rss",               "Global", None,          "science"),

    # ── Indian National ────────────────────────────────────────────────────
    "The Hindu":         ("https://www.thehindu.com/news/feeder/default.rss",     "India",  None,          "world"),
    "The Hindu Tech":    ("https://www.thehindu.com/sci-tech/technology/feeder/default.rss", "India", None, "technology"),
    "Times of India":    ("https://timesofindia.indiatimes.com/rssfeedstopstories.cms", "India", None,    "world"),
    "NDTV Top":          ("https://feeds.feedburner.com/ndtvnews-top-stories",    "India",  None,          "world"),
    "NDTV India":        ("https://feeds.feedburner.com/ndtvnews-india-news",     "India",  None,          "world"),
    "India Today":       ("https://www.indiatoday.in/rss/home",                   "India",  None,          "world"),
    "India Today Tech":  ("https://www.indiatoday.in/technology/rss",             "India",  None,          "technology"),
    "Economic Times":    ("https://economictimes.indiatimes.com/rssfeedstopstories.cms", "India", None,   "economy"),
    "ET Markets":        ("https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms", "India", None, "economy"),
    "The Wire":          ("https://thewire.in/feed",                              "India",  None,          "politics"),
    "Scroll.in":         ("https://scroll.in/feed",                               "India",  None,          "world"),
    "LiveMint":          ("https://www.livemint.com/rss/homepage",                "India",  None,          "economy"),
    "FirstPost India":   ("https://www.firstpost.com/rss/india.xml",              "India",  None,          "world"),
    "News18 India":      ("https://www.news18.com/rss/india.xml",                 "India",  None,          "world"),
    "News18 Tech":       ("https://www.news18.com/rss/tech.xml",                  "India",  None,          "technology"),
    "Business Standard": ("https://www.business-standard.com/rss/home_page_top_stories.rss", "India", None, "economy"),
    "Moneycontrol":      ("https://www.moneycontrol.com/rss/latestnews.xml",      "India",  None,          "economy"),
    "MediaNama":         ("https://www.medianama.com/feed/",                      "India",  None,          "technology"),
    "YourStory":         ("https://yourstory.com/feed",                           "India",  None,          "technology"),
    "Inc42":             ("https://inc42.com/feed/",                              "India",  None,          "technology"),
    "NDTV Profit":       ("https://feeds.feedburner.com/ndtv/NDTVProfit",         "India",  None,          "economy"),

    # ── Tamil Nadu / Regional ──────────────────────────────────────────────
    "Dinamalar":         ("https://www.dinamalar.com/rss/",                       "India",  "Tamil Nadu",  "world"),
    "Daily Thanthi":     ("https://www.dailythanthi.com/rss/",                    "India",  "Tamil Nadu",  "world"),
    "Deccan Herald KA":  ("https://www.deccanherald.com/rss/",                    "India",  "Karnataka",   "world"),
    "The Hindu TN":      ("https://www.thehindu.com/news/cities/chennai/feeder/default.rss", "India", "Tamil Nadu", "world"),

    # ── Business / Finance ─────────────────────────────────────────────────
    "Bloomberg Markets": ("https://feeds.bloomberg.com/markets/news.rss",         "Global", None,          "economy"),
    "Financial Times":   ("https://www.ft.com/?format=rss",                       "Global", None,          "economy"),

    # ── Health / Science ───────────────────────────────────────────────────
    "WHO News":          ("https://www.who.int/rss-feeds/news-english.xml",       "Global", None,          "health"),
    "Nature":            ("https://www.nature.com/nature.rss",                    "Global", None,          "science"),
}

ITEMS_PER_SOURCE = int(os.getenv("RSS_ITEMS_PER_SOURCE", "5"))
SCRAPE_INTERVAL_MINUTES = int(os.getenv("RSS_INTERVAL_MINUTES", "10"))


def scrape_rss_news():
    total_posted = 0
    sources = list(FREE_NEWS_SOURCES.items())

    for source_name, (rss_url, country, state, topic) in sources:
        try:
            feed = feedparser.parse(rss_url)
            if feed.bozo and not feed.entries:
                logger.warning(f"Bad feed ({source_name}): {feed.bozo_exception}")
                continue

            posted = 0
            for entry in feed.entries[:ITEMS_PER_SOURCE]:
                url = getattr(entry, "link", "") or ""
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                title  = (getattr(entry, "title", "") or "").strip()
                content = (getattr(entry, "summary", "") or
                           getattr(entry, "description", "") or "").strip()
                pub_raw = getattr(entry, "published", None) or datetime.now(timezone.utc).isoformat()

                if not title:
                    continue

                payload = {
                    "type":        "rss_news",
                    "title":       title,
                    "content":     content,
                    "url":         url,
                    "source":      source_name,
                    "platform":    "rss",
                    "topic_hint":  topic,
                    "source_name": source_name,
                    "source_type": "rss",
                    "country":     country,
                    "state":       state,
                    "published_at": pub_raw,
                    "metadata": {
                        "rss_source": source_name,
                        "country":    country,
                        "state":      state,
                    },
                }
                publish_to_kafka(payload)
                posted += 1
                time.sleep(0.3)  # gentle pace

            if posted:
                logger.info(f"[+] {source_name}: published {posted} articles")
            total_posted += posted

        except Exception as e:
            logger.error(f"Error scraping {source_name}: {e}")

        time.sleep(1)  # 1-second gap between sources

    logger.info(f"=== RSS cycle complete: {total_posted} articles from {len(sources)} sources ===")
    return total_posted


def main():
    logger.info("RSS News Scraper started — NO API KEY NEEDED")
    logger.info(f"Sources: {len(FREE_NEWS_SOURCES)}  |  Items per source: {ITEMS_PER_SOURCE}  |  Interval: {SCRAPE_INTERVAL_MINUTES}m")
    scrape_rss_news()
    schedule.every(SCRAPE_INTERVAL_MINUTES).minutes.do(scrape_rss_news)
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
