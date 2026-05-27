from sqlalchemy.orm import Session
from .models import engine, Article, Digest
from datetime import datetime


# ── Articles ─────────────────────────────────────────────────────────────────

def save_article(data: dict):
    """Lưu bài viết vào DB nếu chưa tồn tại."""
    with Session(engine) as s:
        if not s.get(Article, data["url"]):
            s.add(Article(**data))
            s.commit()


def get_unprocessed_articles(source: str = None) -> list[Article]:
    """Lấy các bài viết chưa có nội dung chi tiết (ví dụ: chưa có transcript)."""
    with Session(engine) as s:
        q = s.query(Article).filter(Article.content == None)
        if source:
            q = q.filter(Article.source == source)
        return q.all()


def update_article_content(url: str, content: str):
    """Cập nhật nội dung chi tiết (Markdown hoặc Transcript)."""
    with Session(engine) as s:
        article = s.get(Article, url)
        if article:
            article.content = content
            s.commit()


def get_unprocessed_content_for_digest() -> list[Article]:
    """Lấy các bài viết đã có nội dung chi tiết nhưng chưa được tóm tắt (Digest)."""
    with Session(engine) as s:
        processed_urls = {d.source_url for d in s.query(Digest.source_url).all()}
        return (
            s.query(Article)
            .filter(Article.content != None)
            .filter(~Article.url.in_(processed_urls))
            .all()
        )


# ── Digests ───────────────────────────────────────────────────────────────────

def save_digest(data: dict):
    """Lưu tóm tắt tin tức."""
    with Session(engine) as s:
        if not s.get(Digest, data["id"]):
            s.add(Digest(**data))
            s.commit()


def get_unsent_digests() -> list[Digest]:
    """Lấy danh sách các tóm tắt chưa gửi email."""
    with Session(engine) as s:
        return s.query(Digest).filter(Digest.sent_at == None).all()


def mark_digests_sent(ids: list[str]):
    """Đánh dấu các digest là đã gửi email."""
    with Session(engine) as s:
        s.query(Digest).filter(Digest.id.in_(ids)).update(
            {"sent_at": datetime.utcnow()}, synchronize_session=False
        )
        s.commit()


def get_all_digests(limit: int = 50, category: str = None, status: str = None, search: str = None) -> list[Digest]:
    """Lấy danh sách các tóm tắt với các bộ lọc."""
    with Session(engine) as s:
        q = s.query(Digest)
        if category:
            q = q.filter(Digest.category == category)
        if status == "sent":
            q = q.filter(Digest.sent_at != None)
        elif status == "unsent":
            q = q.filter(Digest.sent_at == None)
        if search:
            q = q.filter(
                (Digest.title.like(f"%{search}%")) | 
                (Digest.summary.like(f"%{search}%"))
            )
        return q.order_by(Digest.created_at.desc()).limit(limit).all()


def get_all_articles(limit: int = 50, source: str = None) -> list[Article]:
    """Lấy danh sách các bài viết gốc."""
    with Session(engine) as s:
        q = s.query(Article)
        if source:
            q = q.filter(Article.source == source)
        return q.order_by(Article.created_at.desc()).limit(limit).all()


def get_dashboard_stats() -> dict:
    """Lấy các thông tin thống kê cho Dashboard."""
    import os
    with Session(engine) as s:
        total_articles = s.query(Article).count()
        total_digests = s.query(Digest).count()
        unsent_digests = s.query(Digest).filter(Digest.sent_at == None).count()
        
        # Thống kê theo nguồn
        sources = ["youtube", "openai", "anthropic", "huggingface"]
        source_stats = {}
        for src in sources:
            source_stats[src] = s.query(Article).filter(Article.source == src).count()
            
        # Thống kê theo category
        categories = ["Research", "Product", "Tutorial", "News"]
        category_stats = {}
        for cat in categories:
            category_stats[cat] = s.query(Digest).filter(Digest.category == cat).count()
            
        return {
            "total_articles": total_articles,
            "total_digests": total_digests,
            "unsent_digests": unsent_digests,
            "source_stats": source_stats,
            "category_stats": category_stats
        }


def get_user_profile() -> str:
    """Lấy thông tin profile người dùng từ file."""
    import os
    profile_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents", "user_profile.txt")
    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass
    # Mặc định nếu không tồn tại hoặc lỗi
    return """Tên: [Huy]
Nghề nghiệp: Sinh viên CNTT, học AI/ML
Chủ đề quan tâm: LLM, AI agents, Python, career in AI
Không quan tâm: crypto, NFT, tin tức chính trị
"""


def save_user_profile(profile_text: str):
    """Lưu thông tin profile người dùng vào file."""
    import os
    profile_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents", "user_profile.txt")
    # Đảm bảo thư mục tồn tại
    os.makedirs(os.path.dirname(profile_path), exist_ok=True)
    with open(profile_path, "w", encoding="utf-8") as f:
        f.write(profile_text)

