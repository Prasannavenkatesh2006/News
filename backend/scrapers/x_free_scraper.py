"""
X (Twitter) Free Scraper — NO API KEY REQUIRED
Combines multiple fallback strategies:
  1. Nitter RSS feeds for popular Indian/global accounts
  2. Twitter search via Nitter public instances
  3. ntscraper library (if installed)
"""
import os
import sys
import time
import logging
import schedule
from datetime import datetime, timezone

import requests
import feedparser

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.kafka_publisher import publish_to_kafka

logging.basicConfig(level=logging.INFO, format='%(asctime)s [X-Free] %(message)s')
logger = logging.getLogger(__name__)

seen_ids: set = set()

# Curated list of relevant public accounts (no auth needed via Nitter RSS)
NITTER_ACCOUNTS = [
    # Indian politics / news
    ("narendramodi",   "India", None,        "politics"),
    ("PMOIndia",       "India", None,        "politics"),
    ("ANI",            "India", None,        "world"),
    ("PTI_News",       "India", None,        "world"),
    ("ndtv",           "India", None,        "world"),
    ("TOINewsNow",     "India", None,        "world"),
    ("the_hindu",      "India", None,        "world"),
    ("IndiaToday",     "India", None,        "world"),
    # Global tech / science
    ("elonmusk",       "Global", None,       "technology"),
    ("OpenAI",         "Global", None,       "technology"),
    ("NASA",           "Global", None,       "science"),
    ("BBCBreaking",    "Global", None,       "world"),
    ("Reuters",        "Global", None,       "world"),
    ("WSJ",            "Global", None,       "economy"),
]

# Public Nitter instances (used in rotation; first responsive one wins)
NITTER_INSTANCES = [
    "https://nitter.poast.org",
    "https://nitter.1d4.us",
    "https://nitter.privacydev.net",
    "https://nitter.net",
]

def _working_nitter() -> str:
    """Return first responsive Nitter instance."""
    for base in NITTER_INSTANCES:
        try:
            r = requests.get(f"{base}/narendramodi/rss", timeout=8)
            if r.status_code == 200:
                return base
        except Exception:
            pass
    return ""


def scrape_x_via_nitter_rss(nitter_base: str) -> int:
    """Fetch tweets via Nitter RSS (no auth)."""
    posted = 0
    for account, country, state, topic in NITTER_ACCOUNTS:
        rss_url = f"{nitter_base}/{account}/rss"
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:5]:
                tweet_url = getattr(entry, "link", "") or ""
                tweet_id = tweet_url.rstrip("/").split("/")[-1].split("#")[0]
                if not tweet_id or tweet_id in seen_ids:
                    continue
                seen_ids.add(tweet_id)

                title   = (getattr(entry, "title", "") or "").strip()
                content = (getattr(entry, "summary", "") or title).strip()

                publish_to_kafka({
                    "type":        "x_trending",
                    "title":       f"X @{account}: {title[:100]}",
                    "content":     content,
                    "source":      f"X (@{account})",
                    "platform":    "x",
                    "url":         tweet_url.replace(nitter_base, "https://twitter.com"),
                    "topic_hint":  topic,
                    "country":     country,
                    "state":       state,
                    "published_at": getattr(entry, "published", datetime.now(timezone.utc).isoformat()),
                    "metadata":    {"account": account, "country": country},
                })
                posted += 1
                time.sleep(0.4)
        except Exception as e:
            logger.debug(f"Nitter RSS error @{account}: {e}")
        time.sleep(1)
    return posted


def scrape_x_via_ntscraper() -> int:
    """Use ntscraper library if installed."""
    try:
        from ntscraper import Nitter
        scraper = Nitter(log_level=0, skip_instance_check=False)
        topics  = ["AI India", "breaking news India", "technology", "science"]
        posted  = 0
        for topic in topics:
            try:
                tweets = scraper.get_tweets(topic, mode="hashtag", number=5)
                for tw in tweets.get("tweets", []):
                    tid = tw.get("link", "").split("/")[-1]
                    if not tid or tid in seen_ids:
                        continue
                    seen_ids.add(tid)
                    likes = tw.get("stats", {}).get("likes", 0)
                    if likes < 50:
                        continue
                    text = tw.get("text", "")
                    publish_to_kafka({
                        "type":       "x_trending",
                        "title":      f"X Trending: {text[:100]}",
                        "content":    f"{text}\n\nLikes: {likes}",
                        "source":     "X (Twitter)",
                        "platform":   "x",
                        "url":        tw.get("link", ""),
                        "topic_hint": "technology",
                        "upvotes":    likes,
                    })
                    posted += 1
            except Exception:
                pass
            time.sleep(2)
        return posted
    except ImportError:
        return 0


def scrape_x():
    logger.info("Scraping X (Twitter) — FREE mode...")
    nitter = _working_nitter()
    if nitter:
        count = scrape_x_via_nitter_rss(nitter)
        logger.info(f"[+] X Nitter RSS: {count} tweets")
    else:
        logger.warning("No Nitter instance available, trying ntscraper...")
        count = scrape_x_via_ntscraper()
        logger.info(f"[+] X ntscraper: {count} tweets")


def main():
    logger.info("=== X Free Scraper started (NO API KEY) ===")
    scrape_x()
    schedule.every(15).minutes.do(scrape_x)
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
