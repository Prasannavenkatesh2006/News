import feedparser
import requests

NEW_SOURCES = {
    'Kumudam TN': 'https://v1.kumudam.com/rss/category/tamil-nadu',
    'Oneindia Tamil': 'https://tamil.oneindia.com/rss/tamil-news-fb.xml',
    'Dinamani': 'https://www.dinamani.com/all-sections/tamil-nadu/rssfeed/',
    'Deccan Herald (TN)': 'https://www.deccanherald.com/rss/state/tamil-nadu/index.xml',
}

headers = {'User-Agent': 'Mozilla/5.0'}

for name, url in NEW_SOURCES.items():
    print(f"Checking {name} at {url}")
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {r.status_code}")
        feed = feedparser.parse(r.text)
        print(f"Entries: {len(feed.entries)}")
        if len(feed.entries) > 0:
            print(f"First title: {feed.entries[0].get('title')}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 20)
