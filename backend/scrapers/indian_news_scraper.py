"""
Indian news RSS scraper — publishes items to Kafka via common.kafka_publisher

Runs periodically and publishes top items from a list of Indian sources.
"""
import time
from datetime import datetime
import feedparser
import schedule
import logging

from common.kafka_publisher import publish_to_kafka

logging.basicConfig(level=logging.INFO, format='%(asctime)s [indian-news] %(message)s')
logger = logging.getLogger(__name__)

INDIAN_SOURCES = {
    'The Hindu': 'https://www.thehindu.com/news/feeder/default.rss',
    'Times of India': 'https://timesofindia.indiatimes.com/rssfeedstopstories.cms',
    'NDTV': 'https://feeds.feedburner.com/ndtvnews-top-stories',
    'India Today': 'https://www.indiatoday.in/rss/home',
    'Economic Times': 'https://economictimes.indiatimes.com/rssfeedstopstories.cms',
    'The Wire': 'https://thewire.in/feed',
    'Scroll.in': 'https://scroll.in/feed',
    'LiveMint': 'https://www.livemint.com/rss/homepage',
    'FirstPost': 'https://www.firstpost.com/rss/india.xml',
    'News18': 'https://www.news18.com/rss/india.xml',
}

# State keywords for location extraction
STATE_KEYWORDS = {
    'Tamil Nadu': ['Tamil Nadu', 'Chennai', 'Tamilnadu', 'Tamil', 'DMK', 'AIADMK', 'Madras', 'TN'],
    'Telangana': ['Telangana', 'Hyderabad', 'KCR', 'BRS', 'Telangana', 'TG'],
    'West Bengal': ['West Bengal', 'Kolkata', 'Bengal', 'Mamata', 'TMC', 'WB'],
    'Karnataka': ['Karnataka', 'Bangalore', 'Bengaluru', 'Siddaramaiah', 'KA'],
    'Maharashtra': ['Maharashtra', 'Mumbai', 'Maha', 'Shiv Sena', 'MH'],
    'Delhi': ['Delhi', 'New Delhi', 'AAP', 'Arvind Kejriwal', 'DL'],
    'Gujarat': ['Gujarat', 'Ahmedabad', 'Guj', 'Modi', 'GJ'],
    'Rajasthan': ['Rajasthan', 'Jaipur', 'RJ'],
    'Punjab': ['Punjab', 'Chandigarh', 'PB'],
    'Uttar Pradesh': ['Uttar Pradesh', 'UP', 'Lucknow'],
}


def extract_state(title, content):
    """Extract state from article title and content."""
    text = f"{title} {content}".lower()
    for state, keywords in STATE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return state
    return None


def scrape_indian_news():
    logger.info("🇮🇳 Scraping Indian news sources...")
    for source_name, rss_url in INDIAN_SOURCES.items():
        try:
            feed = feedparser.parse(rss_url)
            entries = getattr(feed, 'entries', []) or []
            posted = 0
            for entry in entries[:10]:
                title = getattr(entry, 'title', '') or ''
                content = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                url = getattr(entry, 'link', '') or ''
                published_at = getattr(entry, 'published', datetime.utcnow().isoformat())
                
                # Extract state from content
                state = extract_state(title, content)
                
                item = {
                    'type': 'indian_news',
                    'title': title,
                    'url': url,
                    'content': content,
                    'source': source_name,
                    'source_name': source_name,
                    'platform': 'indian_news',
                    'topic_hint': 'politics',
                    'source_type': 'indian_news',
                    'country': 'India',
                    'state': state,  # Add extracted state
                    'published_at': published_at,
                }
                publish_to_kafka(item)
                posted += 1
                time.sleep(0.5)

            logger.info(f"✅ {source_name}: published {posted}")
        except Exception as e:
            logger.error(f"❌ Error scraping {source_name}: {e}")


def main():
    logger.info("Indian news scraper started")
    scrape_indian_news()
    schedule.every(5).minutes.do(scrape_indian_news)
    while True:
        schedule.run_pending()
        time.sleep(5)


if __name__ == '__main__':
    main()
