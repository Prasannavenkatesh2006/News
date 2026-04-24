"""
Tamil / Tamil Nadu focused scraper.
Parses RSS feeds where available and publishes Tamil items with `state` and `language` metadata.
"""
import time
from datetime import datetime
import feedparser
import schedule
import logging

from common.kafka_publisher import publish_to_kafka

logging.basicConfig(level=logging.INFO, format='%(asctime)s [tamil-news] %(message)s')
logger = logging.getLogger(__name__)

TAMIL_SOURCES = {
    'Dinamalar': {'rss': 'https://www.dinamalar.com/rss.asp', 'language': 'Tamil'},
    'Daily Thanthi': {'rss': 'https://www.dailythanthi.com/rss/allnews', 'language': 'Tamil'},
    'The Hindu Tamil': {'rss': 'https://www.hindutamil.in/rss/allcontent', 'language': 'Tamil'},
    'Deccan Herald (TN)': {'rss': 'https://www.deccanherald.com/rss/state/tamil-nadu', 'language': 'English'},
}


def scrape_tamil_news():
    logger.info("📰 Scraping Tamil / TN sources...")
    for source_name, cfg in TAMIL_SOURCES.items():
        rss = cfg.get('rss')
        try:
            import requests
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            resp = requests.get(rss, headers=headers, timeout=15)
            feed = feedparser.parse(resp.text)
            entries = getattr(feed, 'entries', []) or []
            posted = 0
            for entry in entries[:8]:
                item = {
                    'type': 'tamil_news',
                    'title': getattr(entry, 'title', '') or '',
                    'url': getattr(entry, 'link', '') or '',
                    'content': getattr(entry, 'summary', '') or getattr(entry, 'description', ''),
                    'published_at': getattr(entry, 'published', datetime.utcnow().isoformat()),
                    'source_name': source_name,
                    'source_type': 'tamil_news',
                    'country': 'India',
                    'state': 'Tamil Nadu',
                    'language': cfg.get('language', 'Tamil'),
                }
                publish_to_kafka(item)
                posted += 1
                time.sleep(0.6)

            logger.info(f"✅ {source_name}: published {posted}")
        except Exception as e:
            logger.error(f"❌ Tamil scraper error for {source_name}: {e}")


def main():
    logger.info("Tamil news scraper started")
    scrape_tamil_news()
    schedule.every(15).minutes.do(scrape_tamil_news)
    while True:
        schedule.run_pending()
        time.sleep(5)


if __name__ == '__main__':
    main()
