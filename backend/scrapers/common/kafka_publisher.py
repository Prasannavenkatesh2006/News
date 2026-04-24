"""
Kafka publisher for scraped content.
Publishes scraped items to the raw-scraped-content topic.
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092")
TOPIC_RAW = "raw-scraped-content"

# Try to import kafka-python, fall back gracefully
try:
    from kafka import KafkaProducer
    _producer = None

    def get_producer():
        global _producer
        if _producer is None:
            _producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                retries=3,
                acks="all",
            )
        return _producer

    def publish_to_kafka(item: dict, topic: str = TOPIC_RAW):
        """Publish a scraped item to Kafka."""
        try:
            item.setdefault("scraped_at", datetime.now(timezone.utc).isoformat())
            get_producer().send(topic, value=item)
            logger.info(f"✅ Published to {topic}: {item.get('title', '')[:60]}")
        except Exception as e:
            logger.error(f"❌ Kafka publish failed: {e}")
            # Fallback: post directly via HTTP
            _direct_post(item)

except ImportError:
    logger.warning("kafka-python not installed — using direct HTTP fallback")

    def publish_to_kafka(item: dict, topic: str = TOPIC_RAW):
        """Direct HTTP fallback when Kafka is not available."""
        item.setdefault("scraped_at", datetime.now(timezone.utc).isoformat())
        _direct_post(item)


def _direct_post(item: dict):
    """Directly post to the auto-poster API (fallback when Kafka is unavailable)."""
    try:
        import httpx
        # Use localhost instead of 'api' when running outside Docker
        api_url = os.getenv("API_URL", "http://localhost:8010")
        token = os.getenv("AI_BOT_TOKEN", "anip-ai-bot-secret-2024")
        
        url = f"{api_url}/api/v1/scraper/ingest"
        logger.debug(f"Attempting direct post to {url}")
        
        response = httpx.post(
            url,
            json=item,
            headers={"X-Scraper-Token": token},
            timeout=10.0,
        )
        if response.status_code == 200:
            logger.info(f"✅ Direct-posted: {item.get('title', '')[:60]}")
        else:
            logger.error(f"❌ Direct post failed: {response.status_code} - {response.text[:100]}")
    except Exception as e:
        # Provide more helpful error message for common dev issues
        error_msg = str(e)
        if "getaddrinfo failed" in error_msg or "NameResolutionError" in error_msg:
            logger.error(f"❌ DNS Error connecting to API: {api_url}. Is the backend running? If not in Docker, use API_URL=http://localhost:8000")
        elif "ConnectError" in error_msg:
             logger.error(f"❌ Connection Refused: Could not reach {api_url}. Is the backend service started?")
        else:
            logger.error(f"❌ Direct post exception: {e}")
