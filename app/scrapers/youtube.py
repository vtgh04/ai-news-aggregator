import time
import urllib.parse as urlparse
from datetime import datetime, timedelta
import feedparser
from youtube_transcript_api import YouTubeTranscriptApi
from .base import BaseScraper

YOUTUBE_RSS = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

CHANNEL_IDS = [
    "UCbmNph6atAoGfqLoCL_duAg",  # Andrej Karpathy
    "UCWX3yGbOBM1PUm4RmBVjTSQ",  # Two Minute Papers
    "UC5Ar503t-pLtfvV5kEIIpQA",  # Matthew Berman
    "UCxLOcNw52Vw18-tO1Pspk0A",  # Wes Roth
    "UCNjDgaxzyS9gG3dBt-eh1Dg",  # AI Explained
]


class YouTubeScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "youtube"

    def fetch_articles(self, hours: int = 72) -> list[dict]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        videos = []

        for cid in CHANNEL_IDS:
            url = YOUTUBE_RSS.format(channel_id=cid)
            try:
                feed = feedparser.parse(url)
                if not feed.entries:
                    print(f"   YouTube: Feed trống cho channel {cid}")
                    continue

                matched_count = 0
                for entry in feed.entries:
                    # Convert published_parsed to naive datetime
                    published_at = datetime.utcnow()
                    if entry.get("published_parsed"):
                        try:
                            published_at = datetime(*entry.published_parsed[:6])
                        except Exception:
                            pass

                    # Lọc theo thời gian cutoff
                    if published_at < cutoff:
                        continue

                    # Lấy video_id từ yt_videoid
                    video_id = entry.get("yt_videoid")
                    if not video_id:
                        continue

                    videos.append({
                        "url": entry.link,
                        "source": self.source_name,
                        "title": entry.title,
                        "author": entry.author,
                        "summary": entry.title,      # YouTube không có summary đầy đủ
                        "content": None,              # Lấy transcript ở Giai đoạn 2
                        "published_at": published_at,
                    })
                    matched_count += 1

                print(f"   YouTube channel {cid[:10]}...: tìm thấy {matched_count} video mới (trong {hours}h qua)")
            except Exception as e:
                print(f"   ⚠️ Lỗi load YouTube channel {cid}: {e}")

        return videos

    def fetch_content(self, url: str) -> str | None:
        try:
            # Trích xuất video_id từ URL
            parsed = urlparse.urlparse(url)
            video_id = urlparse.parse_qs(parsed.query).get("v")
            if not video_id:
                return None
            video_id = video_id[0]

            # Tránh bị chặn IP
            time.sleep(2)
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
            return " ".join([t["text"] for t in transcript])
        except Exception as e:
            print(f"   ⚠️ Không lấy được transcript YouTube {url}: {e}")
            return None


def get_recent_videos(channel_id: str, hours: int = 24) -> list[dict]:
    """Hàm legacy để tương thích ngược."""
    global CHANNEL_IDS
    scraper = YouTubeScraper()
    # Tạm thời đổi danh sách channel để chỉ quét 1 channel được truyền vào
    original_channels = CHANNEL_IDS
    CHANNEL_IDS = [channel_id]
    res = scraper.fetch_articles(hours=hours)
    CHANNEL_IDS = original_channels
    return res


def get_transcript(video_id: str) -> str | None:
    """Hàm legacy để tương thích ngược."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    return YouTubeScraper().fetch_content(url)
