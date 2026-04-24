"""
Regional News Scraper - Fetches state-specific news for India using APIs
Supports: Tamil Nadu, Telangana, West Bengal, Karnataka, Maharashtra, Delhi, Gujarat
Publishes to Kafka every 2 minutes
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s [regional-news] %(message)s')
logger = logging.getLogger(__name__)

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
NEWSDATA_KEY = os.getenv("NEWSDATA_KEY", "")
THENEWSAPI_KEY = os.getenv("THENEWSAPI_KEY", "")

# State configurations for searching
STATES = {
    'Tamil Nadu': {
        'keywords': ['Tamil Nadu', 'Chennai', 'Tamilnadu', 'TN news', 'DMK', 'AIADMK'],
        'code': 'TN'
    },
    'Telangana': {
        'keywords': ['Telangana', 'Hyderabad', 'Hyd news', 'KCR', 'BRS'],
        'code': 'TG'
    },
    'West Bengal': {
        'keywords': ['West Bengal', 'Kolkata', 'Bengal news', 'Mamata', 'TMC'],
        'code': 'WB'
    },
    'Karnataka': {
        'keywords': ['Karnataka', 'Bangalore', 'Bengaluru', 'Siddaramaiah'],
        'code': 'KA'
    },
    'Maharashtra': {
        'keywords': ['Maharashtra', 'Mumbai', 'Maha news', 'Shiv Sena'],
        'code': 'MH'
    },
    'Delhi': {
        'keywords': ['Delhi', 'New Delhi', 'AAP', 'Arvind Kejriwal'],
        'code': 'DL'
    },
    'Gujarat': {
        'keywords': ['Gujarat', 'Ahmedabad', 'GJ news'],
        'code': 'GJ'
    },
}

seen_urls = set()


def scrape_newsapi_regional():
    """Scrape NewsAPI for state-specific headlines."""
    if not NEWSAPI_KEY or NEWSAPI_KEY == "your_newsapi_key_here":
        logger.debug("NewsAPI key not configured")
        return
    
    logger.info("📡 Scraping NewsAPI for regional news...")
    total_posted = 0
    
    for state, config in STATES.items():
        try:
            # Use primary keyword for search
            query = config['keywords'][0]
            
            resp = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": query,
                    "language": "en",
                    "pageSize": 8,
                    "sortBy": "publishedAt",
                    "apiKey": NEWSAPI_KEY,
                },
                timeout=15,
            )
            
            if resp.status_code != 200:
                logger.warning(f"NewsAPI: Got {resp.status_code} for {state}")
                continue
                
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
                
                description = article.get("description", "")
                source = article.get("source", {}).get("name", "NewsAPI")
                published_at = article.get("publishedAt", datetime.utcnow().isoformat())
                
                content = description or ""
                content += f"\n\n🔗 Source: {url}"
                
                publish_to_kafka({
                    "type": "regional_news",
                    "title": title,
                    "content": content,
                    "source": source,
                    "source_name": source,
                    "url": url,
                    "platform": "newsapi_regional",
                    "country": "India",
                    "state": state,
                    "city": None,
                    "topic_hint": "regional",
                    "published_at": published_at,
                })
                posted += 1
                time.sleep(0.2)
            
            if posted > 0:
                logger.info(f"  🇮🇳 {state}: {posted} articles")
            total_posted += posted
            time.sleep(1)
        
        except Exception as e:
            logger.error(f"NewsAPI regional ({state}) failed: {e}")
    
    logger.info(f"✅ NewsAPI Regional: {total_posted} total articles")


def scrape_newsdata_regional():
    """Scrape NewsData.io for state-specific news."""
    if not NEWSDATA_KEY or NEWSDATA_KEY == "your_newsdata_key_here":
        logger.debug("NewsData key not configured")
        return
    
    logger.info("📰 Scraping NewsData for regional news...")
    total_posted = 0
    
    for state, config in STATES.items():
        try:
            # Search for state using primary keyword
            query = config['keywords'][0]
            
            resp = requests.get(
                "https://newsdata.io/api/1/news",
                params={
                    "q": query,
                    "apikey": NEWSDATA_KEY,
                    "language": "en",
                    "size": "10",
                },
                timeout=15,
            )
            
            if resp.status_code != 200:
                logger.warning(f"NewsData: Got {resp.status_code} for {state}")
                continue
            
            data = resp.json()
            
            posted = 0
            for article in data.get("results", []):
                url = article.get("link", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                
                title = article.get("title", "")
                if not title or "[Removed]" in title:
                    continue
                
                description = article.get("description", "")
                source = article.get("source_id", "NewsData")
                published_at = article.get("pubDate", datetime.utcnow().isoformat())
                
                content = description or ""
                content += f"\n\n🔗 Source: {url}"
                
                publish_to_kafka({
                    "type": "regional_news",
                    "title": title,
                    "content": content,
                    "source": source,
                    "source_name": source,
                    "url": url,
                    "platform": "newsdata_regional",
                    "country": "India",
                    "state": state,
                    "city": None,
                    "topic_hint": "regional",
                    "published_at": published_at,
                })
                posted += 1
                time.sleep(0.2)
            
            if posted > 0:
                logger.info(f"  🇮🇳 {state}: {posted} articles")
            total_posted += posted
            time.sleep(1)
        
        except Exception as e:
            logger.error(f"NewsData regional ({state}) failed: {e}")
    
    logger.info(f"✅ NewsData Regional: {total_posted} total articles")


def main():
    logger.info("🌍 Regional News Scraper started - updating states every 2 minutes")
    
    # Run immediately on start
    scrape_newsapi_regional()
    scrape_newsdata_regional()
    
    # Schedule to run every 2 minutes
    schedule.every(2).minutes.do(scrape_newsapi_regional)
    schedule.every(3).minutes.do(scrape_newsdata_regional)
    
    while True:
        schedule.run_pending()
        time.sleep(10)


if __name__ == '__main__':
    main()
