import feedparser
from datetime import datetime, timedelta

YOUTUBE_RSS = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
channel_id = "UC5Ar503t-pLtfvV5kEIIpQA"  # Matthew Berman

url = YOUTUBE_RSS.format(channel_id=channel_id)
feed = feedparser.parse(url)

print(f"Status: {feed.get('status')}")
print(f"Entries found: {len(feed.entries)}")
if feed.entries:
    for entry in feed.entries[:3]:
        print(f"Title: {entry.title}")
        print(f"Published Parsed: {entry.published_parsed}")
        if entry.published_parsed:
            published = datetime(*entry.published_parsed[:6])
            print(f"Parsed datetime: {published}")
            cutoff = datetime.utcnow() - timedelta(hours=72)
            print(f"Cutoff datetime: {cutoff}")
            print(f"Is published > cutoff? {published > cutoff}")
