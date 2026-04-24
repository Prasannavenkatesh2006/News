import requests

# Test API with state filtering
print("Testing regional news API...\n")

for state in ["Tamil Nadu", "Telangana", "West Bengal"]:
    url = f"http://localhost:8000/api/v1/social/feed?state={state}&limit=10"
    try:
        r = requests.get(url, timeout=5)
        feed_items = r.json()  # API returns a list directly
        print(f"✅ {state}: {len(feed_items)} items")
        if feed_items:
            article_items = [item for item in feed_items if item.get('type') == 'article']
            print(f"   └─ Articles: {len(article_items)}")
            if article_items:
                print(f"   └─ First: {article_items[0]['title'][:60]}...")
    except Exception as e:
        print(f"❌ {state}: {e}")

print("\nTesting general feed (no state filter)...")
try:
    r = requests.get("http://localhost:8000/api/v1/social/feed?limit=5", timeout=5)
    feed_items = r.json()  # API returns a list directly
    articles = [item for item in feed_items if item.get('type') == 'article']
    posts = [item for item in feed_items if item.get('type') == 'post']
    print(f"✅ Total feed items: {len(feed_items)} (Articles: {len(articles)}, Posts: {len(posts)})")
except Exception as e:
    print(f"❌ Error: {e}")
