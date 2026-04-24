import sys, os
sys.path.insert(0, r'C:\Users\bpras\Downloads\Pulse---ANIP-main\Pulse---ANIP-main/src')
os.chdir(r'C:\Users\bpras\Downloads\Pulse---ANIP-main\Pulse---ANIP-main/backend/scrapers')
import feedparser

sources = {
    'BBC World': 'http://feeds.bbci.co.uk/news/world/rss.xml',
    'The Hindu': 'https://www.thehindu.com/news/feeder/default.rss',
    'NDTV':      'https://feeds.feedburner.com/ndtvnews-top-stories',
    'Dinamalar': 'https://www.dinamalar.com/rss/',
    'YourStory': 'https://yourstory.com/feed',
}

for name, url in sources.items():
    try:
        f = feedparser.parse(url)
        first = f.entries[0].title[:70] if f.entries else 'NO ENTRIES'
        print(f"[OK] {name}: {len(f.entries)} entries | {first}")
    except Exception as e:
        print(f"[ERR] {name}: {e}")
