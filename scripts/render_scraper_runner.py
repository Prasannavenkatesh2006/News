import os
import sys
import time
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [master-scraper] %(message)s')
logger = logging.getLogger(__name__)

# Add backend/scrapers to path
scraper_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'scrapers'))
sys.path.insert(0, scraper_dir)

SCRAPER_FILES = [
    'indian_news_scraper.py',
    'rss_news_scraper.py',
    'wikipedia_scraper.py',
    'x_scraper.py',
]

def run_scrapers():
    """Run all scrapers sequentially in a loop."""
    logger.info("Starting Background Scraper Runner...")
    
    # Check if we are running inside the API container
    api_url = os.getenv("API_URL", "http://localhost:8000")
    os.environ["API_URL"] = api_url # Ensure sub-processes see it
    
    while True:
        for scraper in SCRAPER_FILES:
            full_path = os.path.join(scraper_dir, scraper)
            if not os.path.exists(full_path):
                logger.warning(f"Scraper not found: {full_path}")
                continue
                
            logger.info(f"🚀 Launching scraper: {scraper}")
            try:
                # Run each scraper and wait for it to complete one cycle
                # Note: These scrapers usually have an internal loop, so we run them for a bit then rotate
                # OR we modify them to run once. For now, let's just start them.
                subprocess.run([sys.executable, full_path], timeout=300) # Give each 5 mins
            except subprocess.TimeoutExpired:
                logger.info(f"⏰ Scraper {scraper} timeout (normal rotation)")
            except Exception as e:
                logger.error(f"Failed to start {scraper}: {e}")
        
        logger.info("💤 Scraper cycle complete. Sleeping for 10 minutes...")
        time.sleep(600) 

if __name__ == "__main__":
    run_scrapers()
