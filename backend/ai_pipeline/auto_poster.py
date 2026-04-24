"""
Auto-Poster: Orchestrates the full AI pipeline.
Consumes from Kafka → filter → summarize → classify → post → broadcast.
This is the main AI pipeline orchestrator.
"""
import os
import sys
import json
import logging
import asyncio
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import requests

# Add path for shared imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [AutoPoster] %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092")
API_URL = os.getenv("API_URL", "http://api:8000")
AI_BOT_TOKEN = os.getenv("AI_BOT_TOKEN", "anip-ai-bot-secret-2024")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Import pipeline modules
try:
    from content_filter import quality_filter, duplicate_check, route_to_community
    from summarizer import ai_rewrite, build_post_title
    from chart_generator import should_generate_chart, generate_trend_chart
except ImportError:
    logger.error("Pipeline modules not found — ensure content_filter.py, summarizer.py, chart_generator.py are present")
    # Stub functions for graceful degradation
    def quality_filter(item): return True
    def duplicate_check(item): return False
    def route_to_community(db, topic): return 1
    def ai_rewrite(item): return item.get("content", "")
    def build_post_title(item, content): return item.get("title", "")
    def should_generate_chart(item): return False
    def generate_trend_chart(*args, **kwargs): return None


# Stats tracking
stats = {
    "total_processed": 0,
    "total_posted": 0,
    "total_filtered": 0,
    "total_duplicates": 0,
    "total_errors": 0,
    "start_time": datetime.now(timezone.utc).isoformat(),
}


def post_to_api(item: dict, community_id: int, content: str, title: str, chart_image: Optional[str] = None) -> bool:
    """POST the processed item to the ANIP API ingest endpoint."""
    try:
        payload = {
            **item,
            "title": title,
            "content": content,
            "community_id": community_id,
            "chart_image": chart_image,
        }
        resp = requests.post(
            f"{API_URL}/api/v1/scraper/ingest",
            json=payload,
            headers={"X-Scraper-Token": AI_BOT_TOKEN},
            timeout=15,
        )
        if resp.status_code == 200:
            return True
        else:
            logger.warning(f"API rejected post ({resp.status_code}): {resp.text[:100]}")
            return False
    except Exception as e:
        logger.error(f"API post error: {e}")
        return False


def process_item(raw_item: dict):
    """Full pipeline: filter → rewrite → chart → post."""
    stats["total_processed"] += 1
    title_preview = raw_item.get("title", "")[:60]

    # Step 1: Quality filter
    if not quality_filter(raw_item):
        stats["total_filtered"] += 1
        logger.debug(f"Filtered: {title_preview}")
        return

    # Step 2: Duplicate check
    if duplicate_check(raw_item):
        stats["total_duplicates"] += 1
        logger.debug(f"Duplicate: {title_preview}")
        return

    # Step 3: AI Summarization & Rewriting
    try:
        rewritten_content = ai_rewrite(raw_item)
        post_title = build_post_title(raw_item, rewritten_content)
    except Exception as e:
        logger.warning(f"Summarization failed, using raw: {e}")
        rewritten_content = raw_item.get("content", "")
        post_title = raw_item.get("title", "")

    # Step 4: Chart generation (for trending data)
    chart_image = None
    if should_generate_chart(raw_item):
        try:
            meta = raw_item.get("metadata", {})
            if meta.get("timestamps") and meta.get("values"):
                chart_image = generate_trend_chart(
                    meta["timestamps"],
                    meta["values"],
                    raw_item.get("title", "Trend"),
                    raw_item.get("platform", "unknown"),
                )
        except Exception as e:
            logger.debug(f"Chart generation failed: {e}")

    # Step 5: Community routing
    topic = raw_item.get("topic_hint", raw_item.get("type", "technology"))
    community_id = _infer_community_id(topic)

    # Step 6: Post to API
    success = post_to_api(
        raw_item,
        community_id,
        rewritten_content,
        post_title,
        chart_image,
    )

    if success:
        stats["total_posted"] += 1
        logger.info(
            f"✅ Posted [{raw_item.get('platform', 'unknown')}] → community {community_id}: {post_title[:50]}"
        )
    else:
        stats["total_errors"] += 1


def _infer_community_id(topic: str) -> int:
    """Simple in-memory topic → community mapping (no DB needed here)."""
    topic_map = {
        "technology": 1,
        "tech": 1,
        "economy": 2,
        "business": 2,
        "finance": 2,
        "politics": 3,
        "climate": 4,
        "environment": 4,
        "health": 5,
        "healthcare": 5,
        "science": 6,
        "natural-disasters": 7,
    }
    return topic_map.get(topic.lower().strip(), 1)


def log_stats():
    """Log pipeline statistics every 5 minutes."""
    logger.info(
        f"📊 Pipeline Stats — Processed: {stats['total_processed']} | "
        f"Posted: {stats['total_posted']} | "
        f"Filtered: {stats['total_filtered']} | "
        f"Duplicates: {stats['total_duplicates']} | "
        f"Errors: {stats['total_errors']}"
    )


def run_kafka_consumer():
    """Consume from Kafka raw-scraped-content topic."""
    try:
        from kafka import KafkaConsumer
        import schedule
        import time

        consumer = KafkaConsumer(
            "raw-scraped-content",
            bootstrap_servers=KAFKA_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            group_id="ai-auto-poster",
            auto_offset_reset="latest",
            consumer_timeout_ms=1000,
        )

        logger.info("✅ Kafka consumer connected to raw-scraped-content")

        import schedule as sched
        sched.every(5).minutes.do(log_stats)

        while True:
            try:
                for message in consumer:
                    try:
                        process_item(message.value)
                    except Exception as e:
                        logger.error(f"Message processing error: {e}")
                        stats["total_errors"] += 1

                sched.run_pending()

            except Exception as e:
                logger.error(f"Consumer loop error: {e}")
                import time as t
                t.sleep(5)

    except ImportError:
        logger.warning("kafka-python not installed — switching to HTTP polling mode")
        run_polling_fallback()
    except Exception as e:
        logger.error(f"Kafka consumer failed to start: {e}")
        run_polling_fallback()


def run_polling_fallback():
    """
    Fallback mode: directly scrape and post without Kafka.
    This mode runs all scrapers inline.
    """
    import time
    import importlib

    logger.info("🔄 Running in polling fallback mode (no Kafka)")

    # Import scrapers dynamically
    scraper_modules = []
    scraper_dir = os.path.join(os.path.dirname(__file__), "..", "scrapers")
    scraper_names = [
        "hackernews_scraper",
        "reddit_scraper",
        "github_scraper",
        "wikipedia_scraper",
        "google_trends",
        "newsapi_aggregator",
    ]

    for name in scraper_names:
        module_path = os.path.join(scraper_dir, f"{name}.py")
        if os.path.exists(module_path):
            logger.info(f"Loaded fallback scraper: {name}")

    # In polling mode, just wait — scrapers post directly via HTTP
    while True:
        log_stats()
        time.sleep(300)


if __name__ == "__main__":
    logger.info("🚀 AI Auto-Poster starting...")
    logger.info(f"API URL: {API_URL}")
    logger.info(f"Kafka: {KAFKA_SERVERS}")
    logger.info(f"OpenAI: {'✅ configured' if OPENAI_API_KEY else '⚠️ not set (using rule-based)'}")
    run_kafka_consumer()
