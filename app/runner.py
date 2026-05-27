from app.scrapers import SCRAPER_REGISTRY
from app.agents.digest_agent import summarize
from app.agents.curator_agent import curate
from app.agents.email_agent import send_digest
from app.db.models import init_db
from app.db.repository import (
    save_article,
    get_unprocessed_articles,
    update_article_content,
    get_unprocessed_content_for_digest,
    save_digest,
    get_unsent_digests,
    mark_digests_sent,
)


def run_pipeline():
    # Ghi đè print cục bộ để ghi logs ra file phục vụ Dashboard
    def print(*args, **kwargs):
        msg = " ".join(str(a) for a in args)
        import builtins
        builtins.print(msg, **kwargs)
        try:
            with open("pipeline.log", "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except Exception:
            pass

    # Xóa file log cũ khi bắt đầu chạy
    try:
        with open("pipeline.log", "w", encoding="utf-8") as f:
            f.write("")
    except Exception:
        pass

    print("=== Khởi tạo DB ===")
    init_db()

    print("=== Giai đoạn 1: Thu thập metadata ===")
    for scraper in SCRAPER_REGISTRY:
        print(f"   Đang chạy {scraper.source_name} scraper...")
        articles = scraper.fetch_articles()
        for art in articles:
            save_article(art)
        print(f"   ✅ {scraper.source_name.capitalize()}: Đã thu thập {len(articles)} bài")

    print("=== Giai đoạn 2: Lấy nội dung chi tiết ===")
    for scraper in SCRAPER_REGISTRY:
        unprocessed = get_unprocessed_articles(source=scraper.source_name)
        if unprocessed:
            print(f"   Lấy nội dung cho nguồn {scraper.source_name} ({len(unprocessed)} bài)...")
        for art in unprocessed:
            content = scraper.fetch_content(art.url)
            if content:
                update_article_content(art.url, content)
            else:
                # Nếu không có phương thức fetch_content đặc biệt (như các RSS thông thường đã có content)
                # hoặc fetch thất bại, ta đánh dấu content = summary để chuyển qua bước tóm tắt
                if not art.content:
                    update_article_content(art.url, art.summary or art.title)

    print("=== Giai đoạn 3: Tóm tắt bằng AI ===")
    unprocessed_content = get_unprocessed_content_for_digest()
    if unprocessed_content:
        print(f"   Tìm thấy {len(unprocessed_content)} nội dung mới cần tóm tắt...")
    for content in unprocessed_content:
        digest = summarize(content.url, content.content)
        if digest:
            save_digest(digest)

    print("=== Giai đoạn 4: Giám tuyển & gửi email ===")
    digests = get_unsent_digests()
    if not digests:
        print("Không có tin mới hôm nay.")
        return

    # Loại bỏ _sa_instance_state của SQLAlchemy
    clean_digests = [
        {k: v for k, v in d.__dict__.items() if not k.startswith("_")}
        for d in digests
    ]
    top = curate(clean_digests)
    send_digest(top)
    mark_digests_sent([d["id"] for d in top])
    print("Pipeline hoàn tất.")
