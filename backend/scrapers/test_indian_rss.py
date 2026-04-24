import feedparser
import requests

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

headers = {'User-Agent': 'Mozilla/5.0'}

for name, url in INDIAN_SOURCES.items():
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
