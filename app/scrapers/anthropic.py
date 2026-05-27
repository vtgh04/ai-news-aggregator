import re
import requests
import feedparser
import html_to_markdown
from datetime import datetime
from .base import BaseScraper

# Danh sách URL RSS để thử nghiệm
ANTHROPIC_RSS_URLS = [
    "https://rsshub.app/anthropic/news",
    "https://rsshub.app/anthropic/blog",
    "https://www.anthropic.com/rss.xml",
    "https://www.anthropic.com/news.rss",
]


class AnthropicScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "anthropic"

    def fetch_articles(self) -> list[dict]:
        # 1. Thử qua các kênh RSS trước
        feed = None
        for rss_url in ANTHROPIC_RSS_URLS:
            try:
                feed = feedparser.parse(rss_url)
                if feed.entries:
                    print(f"   Anthropic RSS OK: {rss_url} ({len(feed.entries)} entries)")
                    break
            except Exception as e:
                print(f"   Error parsing Anthropic RSS {rss_url}: {e}")

        articles = []
        if feed and feed.entries:
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
                    "author": "Anthropic",
                    "summary": entry.get("summary", ""),
                    "content": None,  # Sẽ cào chi tiết ở Giai đoạn 2
                    "published_at": published_at,
                })
            return articles

        # 2. Nếu tất cả RSS đều hỏng, cào trực tiếp HTML từ https://www.anthropic.com/news
        print("   ⚠️ RSS hỏng, chuyển sang cào trực tiếp website Anthropic...")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = requests.get("https://www.anthropic.com/news", headers=headers, timeout=10)
            if resp.status_code == 200:
                # Tìm các liên kết /news/slug trong file HTML
                paths = re.findall(r'href="(/news/[a-zA-Z0-9\-]+)"', resp.text)
                seen_urls = set()
                for path in paths:
                    url = f"https://www.anthropic.com{path}"
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    # Tạo title tạm thời từ slug
                    slug = path.split("/")[-1]
                    title = slug.replace("-", " ").title()

                    articles.append({
                        "url": url,
                        "source": self.source_name,
                        "title": title,
                        "author": "Anthropic",
                        "summary": "",
                        "content": None,
                        "published_at": datetime.utcnow(),
                    })
                    if len(articles) >= 5:
                        break
        except Exception as e:
            print(f"   ⚠️ Lỗi cào trực tiếp Anthropic: {e}")

        return articles

    def fetch_content(self, url: str) -> str | None:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                result = html_to_markdown.convert(resp.text)
                return result.content
        except Exception as e:
            print(f"   ⚠️ Không lấy được nội dung Anthropic {url}: {e}")
        return None


def get_anthropic_articles() -> list[dict]:
    """Hàm legacy để tương thích ngược."""
    return AnthropicScraper().fetch_articles()
