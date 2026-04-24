"""
Product Hunt scraper using their public API v2.
Scrapes daily top products — no auth required for basic queries.
"""
import os
import sys
import time
import logging
import schedule
import requests
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.kafka_publisher import publish_to_kafka
from common.rate_limiter import rate_limit, BackoffRetry

logging.basicConfig(level=logging.INFO, format='%(asctime)s [ProductHunt] %(message)s')
logger = logging.getLogger(__name__)

PH_API = "https://api.producthunt.com/v2/api/graphql"
PH_TOKEN = os.getenv("PRODUCT_HUNT_TOKEN", "")

seen_ids = set()


@BackoffRetry(max_retries=3, base_delay=5.0)
@rate_limit(calls_per_minute=5)
def scrape_product_hunt():
    """Scrape Product Hunt trending products."""
    logger.info("🚀 Scraping Product Hunt...")
    
    try:
        # GraphQL query for today's top posts
        query = """
        query {
          posts(first: 10, order: VOTES) {
            edges {
              node {
                id
                name
                tagline
                description
                votesCount
                commentsCount
                url
                website
                topics {
                  edges {
                    node { name }
                  }
                }
              }
            }
          }
        }
        """
        
        headers = {"Content-Type": "application/json"}
        if PH_TOKEN:
            headers["Authorization"] = f"Bearer {PH_TOKEN}"
        
        resp = requests.post(
            PH_API,
            json={"query": query},
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        
        posts = data.get("data", {}).get("posts", {}).get("edges", [])
        
        posted = 0
        for edge in posts:
            node = edge.get("node", {})
            ph_id = node.get("id", "")
            
            if ph_id in seen_ids:
                continue
            
            votes = node.get("votesCount", 0)
            if votes < 20:
                continue
            
            seen_ids.add(ph_id)
            
            name = node.get("name", "")
            tagline = node.get("tagline", "")
            desc = node.get("description", "")[:300]
            url = node.get("url", "")
            website = node.get("website", "")
            comments = node.get("commentsCount", 0)
            
            topics = [e["node"]["name"] for e in node.get("topics", {}).get("edges", [])]
            topic_str = ", ".join(topics[:3]) if topics else "Technology"
            
            content = f"{tagline}\n\n{desc}\n\n🏷️ {topic_str}\n⬆️ {votes} upvotes · 💬 {comments} comments"
            if website:
                content += f"\n🌐 {website}"
            
            publish_to_kafka({
                "type": "product_hunt",
                "title": f"🚀 Product Hunt: {name}",
                "content": content,
                "source": "Product Hunt",
                "url": url,
                "platform": "product_hunt",
                "upvotes": votes,
                "topic_hint": "technology",
                "metadata": {"ph_id": ph_id, "name": name, "topics": topics},
            })
            posted += 1
        
        logger.info(f"✅ Published {posted} Product Hunt products")
    
    except Exception as e:
        logger.error(f"❌ Product Hunt scrape failed: {e}")


def main():
    logger.info("🚀 Product Hunt scraper starting...")
    scrape_product_hunt()
    schedule.every(10).minutes.do(scrape_product_hunt)  # PH updates hourly
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
