import requests
import sys

# Set encoding to utf-8 for stdout
sys.stdout.reconfigure(encoding='utf-8')

try:
    API_URL = "http://127.0.0.1:8000"
    FEED_URL = f"{API_URL}/api/social/feed?limit=100"
    STATS_URL = f"{API_URL}/api/scraper/stats"
    r = requests.get(FEED_URL)
    if r.status_code != 200:
        print(f"Error {r.status_code}: {r.text}")
    else:
        feed = r.json()
        print(f"Total feed items: {len(feed)}")
        for x in feed:
            print(f"[{x['type']}] ({x.get('platform', 'N/A')}) - {x['title']}")
except Exception as e:
    print(f"Error: {e}")
