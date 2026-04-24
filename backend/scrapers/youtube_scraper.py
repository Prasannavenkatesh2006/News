"""
YouTube Trending scraper.
Uses YouTube Data API v3 (free, 10K quota/day).
Falls back to scraping trending page if no API key.
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s [YouTube] %(message)s')
logger = logging.getLogger(__name__)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
seen_ids: set = set()

REGION_CODES = ["IN", "US"]  # India + US
CATEGORY_IDS = {
    "25": "News & Politics",
    "28": "Science & Technology",
    "22": "People & Blogs",
    "24": "Entertainment",
}


@BackoffRetry(max_retries=3, base_delay=5.0)
@rate_limit(calls_per_minute=5)
def scrape_youtube_api():
    """Scrape trending videos using YouTube Data API v3."""
    if not YOUTUBE_API_KEY or YOUTUBE_API_KEY in ("", "your_youtube_api_key_here"):
        logger.debug("YouTube API key not configured, skipping API mode")
        return 0

    posted = 0
    for region in REGION_CODES:
        try:
            resp = requests.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={
                    "part": "snippet,statistics,contentDetails",
                    "chart": "mostPopular",
                    "regionCode": region,
                    "maxResults": 10,
                    "key": YOUTUBE_API_KEY,
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("items", []):
                vid_id = item["id"]
                if vid_id in seen_ids:
                    continue
                seen_ids.add(vid_id)

                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})
                title = snippet.get("title", "")
                channel = snippet.get("channelTitle", "")
                desc = snippet.get("description", "")[:200]
                views = int(stats.get("viewCount", 0))
                likes = int(stats.get("likeCount", 0))
                comments = int(stats.get("commentCount", 0))

                if views < 100_000:
                    continue

                category_id = snippet.get("categoryId", "")
                topic_hint = "technology" if category_id in ("28", "25") else "technology"

                content = (
                    f"{desc}\n\n"
                    f"📺 Channel: {channel}\n"
                    f"👁️ {views:,} views · 👍 {likes:,} likes · 💬 {comments:,} comments\n"
                    f"🎬 Watch: https://youtube.com/watch?v={vid_id}"
                )

                publish_to_kafka({
                    "type": "youtube",
                    "title": f"📹 YouTube Trending: {title}",
                    "content": content,
                    "source": f"YouTube/{channel}",
                    "url": f"https://youtube.com/watch?v={vid_id}",
                    "platform": "youtube",
                    "upvotes": likes,
                    "topic_hint": topic_hint,
                    "metadata": {
                        "video_id": vid_id,
                        "views": views,
                        "region": region,
                    },
                })
                posted += 1

            time.sleep(1)
        except Exception as e:
            logger.error(f"YouTube API error ({region}): {e}")

    return posted


def scrape_youtube_rss():
    """Fallback: Scrape YouTube RSS feeds for popular channels (no API key needed)."""
    # Public RSS feeds for major news channels
    news_channels = {
        "UC16niRr50-MSBwiO3YDb3RA": "BBC News",
        "UCBi2mrWuNuyYy4gbM6fU18Q": "ABC News",
        "UCaXkIU1QidjPwiAYu6GcHjg": "MSNBC",
    }

    posted = 0
    for channel_id, channel_name in news_channels.items():
        try:
            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            resp = requests.get(feed_url, timeout=10)
            resp.raise_for_status()

            # Parse Atom XML
            from xml.etree import ElementTree as ET
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "yt": "http://www.youtube.com/xml/schemas/2015",
                "media": "http://search.yahoo.com/mrss/",
            }
            root = ET.fromstring(resp.text)

            for entry in root.findall("atom:entry", ns)[:3]:
                vid_id_el = entry.find("yt:videoId", ns)
                title_el = entry.find("atom:title", ns)
                published_el = entry.find("atom:published", ns)

                if vid_id_el is None or title_el is None:
                    continue

                vid_id = vid_id_el.text
                if vid_id in seen_ids:
                    continue

                # Only recent videos (last 2 hours)
                if published_el is not None:
                    try:
                        pub_time = datetime.fromisoformat(published_el.text.replace("Z", "+00:00"))
                        if datetime.now(timezone.utc) - pub_time > timedelta(hours=2):
                            continue
                    except Exception:
                        pass

                seen_ids.add(vid_id)
                title = title_el.text or ""

                publish_to_kafka({
                    "type": "youtube",
                    "title": f"📹 YouTube Breaking: {title}",
                    "content": f"New video from {channel_name}\n🎬 Watch: https://youtube.com/watch?v={vid_id}",
                    "source": channel_name,
                    "url": f"https://youtube.com/watch?v={vid_id}",
                    "platform": "youtube",
                    "topic_hint": "technology",
                })
                posted += 1
        except Exception as e:
            logger.error(f"YouTube RSS error ({channel_name}): {e}")

    return posted


def scrape_youtube():
    logger.info("📹 Scraping YouTube...")
    count = scrape_youtube_api()
    if count == 0:
        count = scrape_youtube_rss()
    logger.info(f"✅ YouTube: {count} videos published")


def main():
    logger.info("🚀 YouTube scraper starting...")
    scrape_youtube()
    schedule.every(5).minutes.do(scrape_youtube)  # YouTube trending updates ~every 15 min

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
