import feedparser

feeds = [
    "https://rsshub.app/anthropic/news",
    "https://rsshub.app/anthropic/blog",
]

for url in feeds:
    print(f"Testing {url}...")
    feed = feedparser.parse(url)
    print(f"Status: {feed.get('status')}")
    print(f"Number of entries: {len(feed.entries)}")
    for e in feed.entries[:2]:
        print(f"  - {e.title} ({e.link})")
