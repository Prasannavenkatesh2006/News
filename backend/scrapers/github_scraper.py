"""
GitHub Trending scraper.
Scrapes github.com/trending — no API key needed.
Polls every 5 minutes (trending doesn't change that fast).
"""
import os
import sys
import time
import logging
import schedule
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.kafka_publisher import publish_to_kafka
from common.rate_limiter import rate_limit, BackoffRetry

logging.basicConfig(level=logging.INFO, format='%(asctime)s [GitHub] %(message)s')
logger = logging.getLogger(__name__)

GITHUB_TRENDING_URL = "https://github.com/trending"
seen_repos = set()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ANIPBot/1.0; +https://anip.social)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


@BackoffRetry(max_retries=3, base_delay=5.0)
@rate_limit(calls_per_minute=5)
def scrape_github_trending():
    """Scrape GitHub trending repos."""
    logger.info("📊 Scraping GitHub Trending...")
    
    try:
        resp = requests.get(
            GITHUB_TRENDING_URL,
            headers=HEADERS,
            timeout=15
        )
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        repos = soup.select("article.Box-row")
        
        posted = 0
        for repo in repos[:8]:
            # Repo name
            h2 = repo.select_one("h2.h3")
            if not h2:
                continue
            repo_link = h2.select_one("a")
            if not repo_link:
                continue
            
            repo_path = repo_link.get("href", "").strip("/")
            if repo_path in seen_repos:
                continue
            seen_repos.add(repo_path)
            
            repo_name = repo_path
            repo_url = f"https://github.com/{repo_path}"
            
            # Description
            desc_el = repo.select_one("p.col-9")
            description = desc_el.get_text(strip=True) if desc_el else "No description"
            
            # Language
            lang_el = repo.select_one("[itemprop='programmingLanguage']")
            language = lang_el.get_text(strip=True) if lang_el else ""
            
            # Stars
            stars_el = repo.select("a.Link--muted")
            stars = ""
            for el in stars_el:
                text = el.get_text(strip=True).replace(",", "")
                if text.isdigit():
                    stars = f"{int(text):,}"
                    break
            
            # Stars today
            stars_today_el = repo.select_one("span.d-inline-block.float-sm-right")
            stars_today = stars_today_el.get_text(strip=True) if stars_today_el else ""
            
            lang_badge = f" · {language}" if language else ""
            stars_info = f"⭐ {stars} stars" if stars else ""
            today_info = f" ({stars_today})" if stars_today else ""
            
            publish_to_kafka({
                "type": "github_trending",
                "title": f"📊 GitHub Trending: {repo_name}",
                "content": f"{description}\n\n{stars_info}{today_info}{lang_badge}\n🔗 {repo_url}",
                "source": "GitHub Trending",
                "url": repo_url,
                "platform": "github",
                "topic_hint": "technology",
                "metadata": {
                    "repo": repo_path,
                    "language": language,
                    "stars_today": stars_today,
                },
            })
            posted += 1
        
        logger.info(f"✅ Published {posted} GitHub trending repos")
    
    except Exception as e:
        logger.error(f"❌ GitHub scrape failed: {e}")


def main():
    logger.info("🚀 GitHub Trending scraper starting...")
    scrape_github_trending()
    schedule.every(5).minutes.do(scrape_github_trending)
    
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
