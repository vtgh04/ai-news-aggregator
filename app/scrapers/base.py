from abc import ABC, abstractmethod


class BaseScraper(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Tên nguồn tin (ví dụ: 'youtube', 'openai', 'anthropic')."""
        pass

    @abstractmethod
    def fetch_articles(self) -> list[dict]:
        """Thu thập danh sách bài viết mới dưới dạng metadata chuẩn hóa.

        Mỗi bài viết trả về là một dict có dạng:
        {
            "url": str,
            "source": str,
            "title": str,
            "author": str or None,
            "summary": str or None,
            "content": str or None,          # None nếu cần lấy chi tiết ở Giai đoạn 2
            "published_at": datetime or None
        }
        """
        pass

    def fetch_content(self, url: str) -> str | None:
        """Lấy nội dung chi tiết của bài viết (ví dụ: transcript YouTube).

        Trả về chuỗi nội dung (markdown/văn bản thô) hoặc None nếu không lấy được.
        """
        return None
