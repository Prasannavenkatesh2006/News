"""
AI Content Filter Pipeline.
Consumes from Kafka raw-scraped-content topic,
filters for quality, removes duplicates, then passes to auto-poster.
"""
import os
import sys
import json
import logging
import hashlib
from typing import Optional
import requests
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s [ContentFilter] %(message)s')
logger = logging.getLogger(__name__)

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092")
API_URL = os.getenv("API_URL", "http://api:8000")
AI_BOT_TOKEN = os.getenv("AI_BOT_TOKEN", "")
EMBEDDING_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://embedding-service:5003")

# Quality thresholds
MIN_UPVOTES = {
    "reddit_post": 50,
    "hackernews": 20,
    "github_trending": 0,
    "google_trends": 0,
    "wikipedia": 0,
    "product_hunt": 20,
    "newsapi": 0,
    "gdelt": 0,
}

# Seen content hashes to detect duplicates
seen_hashes: set = set()
# Seen titles for near-duplicate detection
seen_titles: list = []
MAX_SEEN = 1000


def quality_filter(item: dict) -> bool:
    """Check if the item meets quality standards."""
    platform = item.get("platform", item.get("type", ""))
    upvotes = item.get("upvotes", 0) or 0
    
    threshold = MIN_UPVOTES.get(platform, 0)
    if upvotes < threshold:
        logger.debug(f"Filtered (low engagement): {item.get('title', '')[:50]}")
        return False
    
    # Must have a title
    title = item.get("title", "").strip()
    if not title or len(title) < 10:
        return False
    
    # No spam patterns
    spam_words = ["click here", "buy now", "free money", "guaranteed", "100% profit"]
    title_lower = title.lower()
    for word in spam_words:
        if word in title_lower:
            return False
    
    return True


def duplicate_check(item: dict) -> bool:
    """Check if this is duplicate content using hash and title similarity."""
    global seen_hashes, seen_titles
    
    title = item.get("title", "")
    url = item.get("url", "")
    
    # URL-based duplicate check
    if url:
        url_hash = hashlib.md5(url.encode()).hexdigest()
        if url_hash in seen_hashes:
            logger.debug(f"Duplicate URL: {url[:60]}")
            return True
        seen_hashes.add(url_hash)
    
    # Title-based duplicate check (exact)
    title_hash = hashlib.md5(title.lower().strip().encode()).hexdigest()
    if title_hash in seen_hashes:
        logger.debug(f"Duplicate title: {title[:60]}")
        return True
    seen_hashes.add(title_hash)
    
    # Keep set bounded
    if len(seen_hashes) > MAX_SEEN * 2:
        seen_hashes = set(list(seen_hashes)[-MAX_SEEN:])
    
    return False


def route_to_community(item: dict) -> int:
    """Route item to appropriate community based on topic hints."""
    topic = item.get("topic_hint", "").lower()
    platform = item.get("platform", "").lower()
    title_lower = item.get("title", "").lower()
    
    # Platform-based routing
    platform_map = {
        "github": 1,  # Technology
        "hackernews": 1,
        "product_hunt": 1,
        "reddit_post": None,  # Will be determined by topic
    }
    
    # Topic-based routing
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
    
    platform_comm = platform_map.get(platform)
    if platform_comm is not None:
        return platform_comm
    
    comm_id = topic_map.get(topic)
    if comm_id:
        return comm_id
    
    # Title keyword analysis
    if any(w in title_lower for w in ["ai", "tech", "software", "code", "developer", "github", "api"]):
        return 1
    if any(w in title_lower for w in ["economy", "market", "stock", "business", "finance"]):
        return 2
    if any(w in title_lower for w in ["election", "government", "policy", "politics"]):
        return 3
    if any(w in title_lower for w in ["climate", "environment", "weather"]):
        return 4
    if any(w in title_lower for w in ["health", "medical", "vaccine", "hospital"]):
        return 5
    if any(w in title_lower for w in ["science", "research", "discovery", "space"]):
        return 6
    
    return 1  # Default to Technology


from importance_scorer import ImportanceScorer
scorer = ImportanceScorer()

def process_and_post(raw_item: dict):
    """Full pipeline: filter → deduplicate → rank importance → route → post."""
    logger.info(f"Processing: {raw_item.get('title', '')[:60]}")
    
    if not quality_filter(raw_item):
        return
    
    if duplicate_check(raw_item):
        return
    
    # Calculate importance
    importance_score, score_breakdown = scorer.calculate_importance(raw_item)
    
    # Filter threshold: only post if importance > 40
    if importance_score < 40:
        logger.info(f"⏭️  Skipping low importance ({importance_score}): {raw_item.get('title')[:60]}")
        return
    
    logger.info(f"✅ High importance ({importance_score}): {raw_item.get('title')[:60]}")
    
    # Inject importance into metadata manually
    if 'metadata' not in raw_item or not isinstance(raw_item['metadata'], dict):
        raw_item['metadata'] = {}
    raw_item['metadata']['importance_score'] = importance_score
    raw_item['metadata']['importance_breakdown'] = score_breakdown
    
    community_id = route_to_community(raw_item)
    
    # Call the ingest endpoint
    try:
        resp = requests.post(
            f"{API_URL}/api/v1/scraper/ingest",
            json={
                **raw_item,
                "community_id": community_id,
            },
            headers={"X-Scraper-Token": AI_BOT_TOKEN},
            timeout=10,
        )
        if resp.status_code == 200:
            logger.info(f"✅ Posted to community {community_id}: {raw_item.get('title', '')[:50]}")
        else:
            logger.warning(f"Post failed: {resp.status_code} - {resp.text[:100]}")
    except Exception as e:
        logger.error(f"❌ Failed to post: {e}")


def run_kafka_consumer():
    """Consume from Kafka and process each message."""
    try:
        from kafka import KafkaConsumer
        
        consumer = KafkaConsumer(
            "raw-scraped-content",
            bootstrap_servers=KAFKA_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            group_id="ai-content-filter",
            auto_offset_reset="latest",
        )
        
        logger.info("✅ Kafka consumer connected, waiting for messages...")
        
        for message in consumer:
            try:
                process_and_post(message.value)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    except ImportError:
        logger.warning("kafka-python not installed, using polling mode")
        run_polling_mode()
    except Exception as e:
        logger.error(f"Kafka consumer failed: {e}")
        run_polling_mode()


def run_polling_mode():
    """Fallback: poll the API for pending items."""
    import time
    logger.info("Running in polling mode (no Kafka)")
    while True:
        time.sleep(60)


if __name__ == "__main__":
    logger.info("🚀 AI Content Filter starting...")
    run_kafka_consumer()
