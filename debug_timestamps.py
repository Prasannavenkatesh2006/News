import requests
import json
from datetime import datetime

# Get articles from API
r = requests.get('http://localhost:8000/api/v1/social/feed?state=Tamil%20Nadu&limit=20', timeout=5)
items = r.json()

# Filter for articles only
articles = [item for item in items if item['type'] == 'article']
print(f'Found {len(articles)} articles out of {len(items)} items\n')

if not articles:
    print("No articles found! Showing first few items:")
    for item in items[:3]:
        print(f"  - {item['type']}: {item['title'][:50]}... ({item['source']})")
else:
    print("Sample Articles with Timestamps:")
    for i, a in enumerate(articles[:3]):
        print(f"\n{i+1}. {a['title'][:60]}...")
        print(f"   Type: {a['type']}")
        print(f"   Source: {a['source']}")
        print(f"   created_at: {a['created_at']}")
        print(f"   State in metadata: {a['metadata'].get('state', 'None')}")
