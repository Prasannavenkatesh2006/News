"""
NewsAPI (free) + GDELT aggregator — enhanced version of existing ANIP scraper.
Runs every 1 minute (instead of 6 hours) and pushes to Kafka.
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
from common.rate_limiter import rate_limit

logging.basicConfig(level=logging.INFO, format='%(asctime)s [NewsAPI] %(message)s')
logger = logging.getLogger(__name__)

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
NEWSDATA_KEY = os.getenv("NEWSDATA_KEY", "")
seen_urls = set()

CATEGORIES = ["technology", "business", "science", "health", "general"]


def scrape_newsapi():
    """Scrape NewsAPI for top headlines."""
    if not NEWSAPI_KEY or NEWSAPI_KEY == "your_newsapi_key_here":
        logger.debug("NewsAPI key not configured, skipping")
        return
    
    logger.info("📡 Scraping NewsAPI...")
    posted = 0
    
    for category in CATEGORIES:
        try:
            resp = requests.get(
                "https://newsapi.org/v2/top-headlines",
                params={
                    "category": category,
                    "language": "en",
                    "pageSize": 5,
                    "apiKey": NEWSAPI_KEY,
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            
            for article in data.get("articles", []):
                url = article.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                
                title = article.get("title", "")
                description = article.get("description", "")
                source = article.get("source", {}).get("name", "NewsAPI")
                author = article.get("author", "")
                
                if not title or "[Removed]" in title:
                    continue
                
                content = description or ""
                if author:
                    content += f"\n\n✍️ By {author}"
                content += f"\n🔗 {url}"
                
                topic_map = {
                    "technology": "technology",
                    "business": "economy",
                    "science": "science",
                    "health": "health",
                    "general": "technology",
                }
                
                publish_to_kafka({
                    "type": "newsapi",
                    "title": f"📡 Breaking: {title}",
                    "content": content,
                    "source": source,
                    "url": url,
                    "platform": "newsapi",
                    "topic_hint": topic_map.get(category, "technology"),
                })
                posted += 1
            
            time.sleep(1)
        
        except Exception as e:
            logger.error(f"NewsAPI {category} failed: {e}")
    
    logger.info(f"✅ NewsAPI: {posted} articles")


def scrape_india_newsapi():
    """Scrape NewsAPI for top India headlines."""
    if not NEWSAPI_KEY or NEWSAPI_KEY == "your_newsapi_key_here":
        return
    
    logger.info("📡 Scraping NewsAPI India...")
    try:
        resp = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={
                "country": "in",
                "pageSize": 10,
                "apiKey": NEWSAPI_KEY,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        
        posted = 0
        for article in data.get("articles", []):
            url = article.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            
            title = article.get("title", "")
            if not title or "[Removed]" in title:
                continue
            
            publish_to_kafka({
                "type": "newsapi",
                "title": f"🇮🇳 India: {title}",
                "content": article.get("description", "") + f"\n🔗 {url}",
                "source": article.get("source", {}).get("name", "NewsAPI"),
                "url": url,
                "platform": "newsapi",
                "topic_hint": "politics",
                "metadata": {"country": "India"}
            })
            posted += 1
        logger.info(f"✅ NewsAPI India: {posted} articles")
    except Exception as e:
        logger.error(f"NewsAPI India failed: {e}")


def scrape_gdelt():
    """Scrape GDELT for recent news events — completely free."""
    logger.info("🌍 Scraping GDELT...")
    
    try:
        # GDELT Article Search API - iterate through regional interests
        queries = [
            ("AI technology business economy", "technology"),
            ("India politics economy cricket", "politics"),
            ("Tamil Nadu Chennai politics", "politics")
        ]
        
        total_posted = 0
        for query_str, topic_hint in queries:
            resp = requests.get(
                "https://api.gdeltproject.org/api/v2/doc/doc",
                params={
                    "query": query_str,
                    "mode": "artlist",
                    "maxrecords": 10,
                    "format": "json",
                    "timespan": "15min",
                },
                timeout=15,
            )
            # resp.raise_for_status() # GDELT sometimes returns 200 with error page, handle gracefully
            if resp.status_code != 200:
                continue
                
            try:
                data = resp.json()
            except:
                continue
            
            posted = 0
            for article in data.get("articles", []):
                url = article.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                
                title = article.get("title", "")
                domain = article.get("domain", "")
                
                if not title:
                    continue
                
                # Tag regional data based on query
                metadata = {}
                if "India" in query_str:
                    metadata["country"] = "India"
                if "Tamil Nadu" in query_str or "Chennai" in query_str:
                    metadata["state"] = "Tamil Nadu"
                    metadata["country"] = "India"
                
                publish_to_kafka({
                    "type": "gdelt",
                    "title": f"🌍 GDELT: {title}",
                    "content": f"Source: {domain}\n🔗 {url}",
                    "source": domain,
                    "url": url,
                    "platform": "gdelt",
                    "topic_hint": topic_hint,
                    "metadata": metadata
                })
                posted += 1
            total_posted += posted
        
        logger.info(f"✅ GDELT: {total_posted} articles total")
    
    except Exception as e:
        logger.error(f"❌ GDELT scrape failed: {e}")


def main():
    logger.info("🚀 NewsAPI/GDELT scraper starting...")
    scrape_newsapi()
    scrape_india_newsapi()
    scrape_gdelt()
    
    schedule.every(2).minutes.do(scrape_gdelt)
    schedule.every(10).minutes.do(scrape_india_newsapi)
    schedule.every(30).minutes.do(scrape_newsapi)
    
    while True:
        schedule.run_pending()
        time.sleep(10)


if __name__ == "__main__":
    main()
