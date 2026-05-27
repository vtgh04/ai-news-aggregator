from datetime import datetime
import feedparser
from .base import BaseScraper


class HuggingFaceScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "huggingface"

    def fetch_articles(self) -> list[dict]:
        feed = feedparser.parse("https://huggingface.co/blog/feed.xml")
        articles = []
        for entry in feed.entries[:5]:
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
                "author": entry.get("author", "Hugging Face"),
                "summary": entry.get("summary", ""),
                "content": entry.get("summary", "") or entry.title,
                "published_at": published_at,
            })
        return articles
