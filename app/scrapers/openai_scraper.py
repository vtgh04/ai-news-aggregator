from datetime import datetime
import feedparser
from .base import BaseScraper


class OpenAIScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "openai"

    def fetch_articles(self) -> list[dict]:
        feed = feedparser.parse("https://openai.com/blog/rss.xml")
        articles = []
        for entry in feed.entries[:10]:
            published_at = None
            if entry.get("published_parsed"):
                try:
                    published_at = datetime(*entry.published_parsed[:6])
                except Exception:
                    pass

            articles.append({
                "url": entry.link,
                "source": self.source_name,
                "title": entry.title,
                "author": entry.get("author", "OpenAI"),
                "summary": entry.get("summary", ""),
                "content": entry.get("summary", "") or entry.title,
                "published_at": published_at,
            })
        return articles


def get_openai_articles() -> list[dict]:
    """Hàm legacy để tương thích ngược nếu cần."""
    return OpenAIScraper().fetch_articles()
