"""
YouTube Free Scraper — NO API KEY REQUIRED
Uses YouTube's public Atom RSS feeds (works without any Google API key).
Covers Indian and global news / tech channels.
"""
import os
import sys
import time
import logging
import schedule
from datetime import datetime, timezone, timedelta
from xml.etree import ElementTree as ET

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.kafka_publisher import publish_to_kafka

logging.basicConfig(level=logging.INFO, format='%(asctime)s [YouTube-Free] %(message)s')
logger = logging.getLogger(__name__)

seen_ids: set = set()

# All YouTube channel RSS feeds are public — no API key!
# Format: channel_id -> (display_name, country, state, topic)
YOUTUBE_CHANNELS = {
    # ── Indian News ───────────────────────────────────────────────────────
    "UCZFMm1mMw0F81Z37aaEzTUA": ("NDTV",              "India", None,         "world"),
    "UCYfdidRxbB8Qhf0Nx7ioOYw": ("India Today",       "India", None,         "world"),
    "UCK7tptK9bsMDEZo83gkx4wQ": ("Times of India",    "India", None,         "world"),
    "UC_mYaQAE6-71rjSN6CeCA-g": ("Republic TV",       "India", None,         "world"),
    "UCtuhs0hr9dX7uFBDFQlQzaw": ("NDTV Tech",         "India", None,         "technology"),
    "UCwqusr8YDwM-3mEYTDeJHzw": ("Republic World",    "India", None,         "world"),
    "UCaXkIU1QidjPwiAYu6GcHjg": ("Deccan Chronicle",  "India", None,         "world"),
    "UCK28y5fMF2jFifhZ1rqfECA": ("The Wire",          "India", None,         "politics"),
    "UCtqjgNYMBgCHFOQyHw0gIqA": ("Scroll.in",         "India", None,         "world"),
    # ── Tamil Nadu ────────────────────────────────────────────────────────
    "UCkAOZmhz4Nt7iB3aQZRt40A": ("Sun News Tamil",    "India", "Tamil Nadu", "world"),
    "UCnbQLdIZC5I0DyoqNe1ZoBA": ("Puthiya Thalaimurai","India","Tamil Nadu", "world"),
    # ── Global & Tech ─────────────────────────────────────────────────────
    "UC16niRr50-MSBwiO3YDb3RA": ("BBC News",          "Global", None,        "world"),
    "UCBi2mrWuNuyYy4gbM6fU18Q": ("ABC News",          "Global", None,        "world"),
    "UCupvZG-5ko_eiXAupbDfxWw": ("CNN",               "Global", None,        "world"),
    "UCkUiMZpKhNDMvHQnxI9gpkg": ("CNBC",              "Global", None,        "economy"),
    "UCHdluULl5c7bilX1ae1ow2g": ("Al Jazeera English","Global", None,        "world"),
    "UCsooa4yRKGN_zEE8iknghZA": ("TED Talks",         "Global", None,        "science"),
    "UCnUYZLuoy1rq1aVMwx4aTzw": ("Guardian News",     "Global", None,        "world"),
    "UClLXZ6HCu4SKCWV6RygF5KA": ("Ars Technica",      "Global", None,        "technology"),
    "UCVHFbw7woebKtfvug_Wr-0A": ("Wired",             "Global", None,        "technology"),
    "UCddiUEpeqJcYeBxX1IVBKvQ": ("The Verge",         "Global", None,        "technology"),
}

FEED_BASE = "https://www.youtube.com/feeds/videos.xml?channel_id={}"
MAX_AGE_HOURS = int(os.getenv("YOUTUBE_MAX_AGE_HOURS", "24"))
INTERVAL_MINUTES = int(os.getenv("YOUTUBE_INTERVAL_MINUTES", "15"))


def scrape_channel(channel_id: str, channel_name: str, country: str, state, topic: str) -> int:
    feed_url = FEED_BASE.format(channel_id)
    posted = 0
    try:
        resp = requests.get(feed_url, timeout=15,
                            headers={"User-Agent": "Mozilla/5.0 (compatible; ANIPBot/1.0)"})
        resp.raise_for_status()

        ns = {
            "atom":  "http://www.w3.org/2005/Atom",
            "yt":    "http://www.youtube.com/xml/schemas/2015",
            "media": "http://search.yahoo.com/mrss/",
        }
        root = ET.fromstring(resp.text)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=MAX_AGE_HOURS)

        for entry in root.findall("atom:entry", ns)[:5]:
            vid_el   = entry.find("yt:videoId", ns)
            title_el = entry.find("atom:title", ns)
            pub_el   = entry.find("atom:published", ns)
            link_el  = entry.find("atom:link", ns)
            desc_el  = entry.find(".//media:description", ns)

            if vid_el is None or title_el is None:
                continue

            vid_id = vid_el.text
            if vid_id in seen_ids:
                continue

            # Age gate
            if pub_el is not None:
                try:
                    pub_dt = datetime.fromisoformat(pub_el.text.replace("Z", "+00:00"))
                    if pub_dt < cutoff:
                        continue
                except Exception:
                    pass

            seen_ids.add(vid_id)
            title   = (title_el.text or "").strip()
            desc    = (desc_el.text or "") if desc_el is not None else ""
            url     = f"https://www.youtube.com/watch?v={vid_id}"
            pub_str = pub_el.text if pub_el is not None else datetime.now(timezone.utc).isoformat()

            content = (
                f"{desc[:400]}\n\n"
                f"Channel: {channel_name}\n"
                f"Watch: {url}"
            ).strip()

            publish_to_kafka({
                "type":        "youtube",
                "title":       f"YouTube ({channel_name}): {title}",
                "content":     content,
                "source":      channel_name,
                "platform":    "youtube",
                "url":         url,
                "topic_hint":  topic,
                "country":     country,
                "state":       state,
                "published_at": pub_str,
                "metadata":    {
                    "video_id":     vid_id,
                    "channel_id":   channel_id,
                    "channel_name": channel_name,
                    "country":      country,
                },
            })
            posted += 1
            time.sleep(0.3)

    except Exception as e:
        logger.error(f"Error scraping {channel_name}: {e}")

    return posted


def scrape_youtube():
    logger.info("Scraping YouTube RSS feeds (NO API KEY)...")
    total = 0
    for ch_id, (name, country, state, topic) in YOUTUBE_CHANNELS.items():
        count = scrape_channel(ch_id, name, country, state, topic)
        if count:
            logger.info(f"[+] {name}: {count} videos")
        total += count
        time.sleep(1)
    logger.info(f"=== YouTube cycle complete: {total} videos ===")


def main():
    logger.info("=== YouTube Free Scraper started (NO API KEY) ===")
    scrape_youtube()
    schedule.every(INTERVAL_MINUTES).minutes.do(scrape_youtube)
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
