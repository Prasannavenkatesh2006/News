import requests
import json

try:
    r = requests.get('http://127.0.0.1:8001/api/social/feed?limit=100')
    if r.status_code != 200:
        print(f"Error {r.status_code}: {r.text}")
    else:
        feed = r.json()
        print(f"Total feed items: {len(feed)}")
        for x in feed[:20]:
            print(f"[{x['type']}] ({x.get('platform', 'N/A')}) - {x['title']}")
            # Check for location in item
            if 'metadata' in x and x['metadata']:
                 print(f"  Location: {x['metadata']}")
except Exception as e:
    print(f"Error: {e}")
