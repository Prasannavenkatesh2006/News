import feedparser
import requests

TAMIL_SOURCES = {
    'Dinamalar': 'https://www.dinamalar.com/rss.asp',
    'Daily Thanthi': 'https://www.dailythanthi.com/rss/allnews',
    'The Hindu Tamil': 'https://www.hindutamil.in/rss/allcontent',
    'Deccan Herald (TN)': 'https://www.deccanherald.com/rss/state/tamil-nadu',
}

headers = {'User-Agent': 'Mozilla/5.0'}

for name, url in TAMIL_SOURCES.items():
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
