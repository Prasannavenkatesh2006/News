import requests

# Get articles from API like the page does
r = requests.get('http://localhost:8000/api/v1/social/feed?state=Tamil%20Nadu&country=India&limit=5')
data = r.json()

print(f"Total items returned: {len(data)}\n")
# Show structure
for i, item in enumerate(data[:3]):
    print(f"{i+1}. Type: {item['type']}")
    print(f"   Title: {item['title'][:50]}...")
    print(f"   created_at: {item['created_at']}")
    print(f"   topic: {item.get('topic', 'None')}")
    print(f"   source: {item.get('source', 'None')}")
    print(f"   community: {item.get('community', 'None')}")
    print()
