"""
Google Trends scraper using pytrends (unofficial API — free).
Polls every 2 minutes for trending searches globally and in India.
"""
import os
import sys
import time
import logging
import schedule

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.kafka_publisher import publish_to_kafka

logging.basicConfig(level=logging.INFO, format='%(asctime)s [GoogleTrends] %(message)s')
logger = logging.getLogger(__name__)

seen_terms = set()


def scrape_google_trends():
    """Scrape Google Trends trending searches."""
    logger.info("🔍 Scraping Google Trends...")
    
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='en-US', tz=330, timeout=(10, 15))  # India timezone, increased timeout
        
        posted = 0
        
        # Trending searches in India
        for geo, geo_name in [('india', 'India'), ('united_states', 'US')]:
            try:
                trending_df = pytrends.trending_searches(pn=geo)
                
                for i, term in enumerate(trending_df[0].head(5).tolist()):
                    if term in seen_terms:
                        continue
                    seen_terms.add(term)
                    
                    # Get related data
                    try:
                        pytrends.build_payload([term], timeframe='now 1-H')
                        related = pytrends.related_queries()
                        rising = related.get(term, {}).get('rising')
                        top = related.get(term, {}).get('top')
                        
                        extra = ""
                        if rising is not None and not rising.empty:
                            top_rising = rising.head(3)['query'].tolist()
                            extra = f"\n📈 Rising: {', '.join(top_rising)}"
                    except:
                        extra = ""
                    
                    rank_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i] if i < 5 else "🔥"
                    
                    publish_to_kafka({
                        "type": "google_trends",
                        "title": f"🔍 Google Trending ({geo_name}): {term}",
                        "content": f"{rank_emoji} '{term}' is trending #{i+1} on Google {geo_name} right now{extra}\n\n🌐 Search: https://www.google.com/search?q={term.replace(' ', '+')}",
                        "source": "Google Trends",
                        "platform": "google_trends",
                        "topic_hint": "technology",
                        "metadata": {"rank": i + 1, "geo": geo_name, "term": term},
                    })
                    posted += 1
                
                time.sleep(3)  # Be polite between requests
            
            except Exception as e:
                logger.warning(f"Failed for geo {geo}: {e}")
        
        logger.info(f"✅ Published {posted} Google Trends items")
    
    except ImportError:
        logger.warning("pytrends not installed — skipping Google Trends scraper")
    except Exception as e:
        logger.error(f"❌ Google Trends failed: {e}")


def main():
    logger.info("🚀 Google Trends scraper starting...")
    scrape_google_trends()
    schedule.every(2).minutes.do(scrape_google_trends)
    
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
