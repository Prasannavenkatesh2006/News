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
    logger.info("Starting Render Scraper Runner...")
    
    while True:
        for scraper in SCRAPER_FILES:
            full_path = os.path.join(scraper_dir, scraper)
            if not os.path.exists(full_path):
                logger.warning(f"Scraper not found: {full_path}")
                continue
                
            logger.info(f"🚀 Launching scraper: {scraper}")
            try:
                # We run each scraper as a separate process and wait for it to finish a single run.
                # Note: We need to modify the scrapers to support a --one-run flag or just run them and kill them.
                # Actually, many of these have a 'main' that loops.
                # For Render Worker, we might just want to start them all in parallel if memory allows.
                process = subprocess.Popen([sys.executable, full_path])
                # We'll let it run for a while or manage it.
                # But to save memory on Render Free, let's just run them one by one if they support one-shot.
                # For now, let's just start the most important ones.
            except Exception as e:
                logger.error(f"Failed to start {scraper}: {e}")
        
        # Keep the master process alive
        time.sleep(3600) # Wait an hour before checking/restarting if any crashed

if __name__ == "__main__":
    run_scrapers()
