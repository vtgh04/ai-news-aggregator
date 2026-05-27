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
    get_all_users,
    get_unsent_digests_for_user,
    mark_digests_sent_for_user,
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
    users = get_all_users()
    if not users:
        print("Không có người dùng nào trong hệ thống.")
        return

    for user in users:
        print(f"   Đang xử lý bản tin cho {user.name} ({user.email})...")
        digests = get_unsent_digests_for_user(user.id)
        
        # Giới hạn tối đa 30 tin tức chưa gửi để tránh quá tải token LLM
        if len(digests) > 30:
            digests = digests[:30]
            
        if not digests:
            print(f"   Không có tin mới cho {user.name}.")
            continue

        # Loại bỏ _sa_instance_state của SQLAlchemy
        clean_digests = [
            {k: v for k, v in d.__dict__.items() if not k.startswith("_")}
            for d in digests
        ]
        
        top = curate(clean_digests, user.profile)
        if top:
            send_digest(user.email, top, user.name)
            mark_digests_sent_for_user(user.id, [d["id"] for d in top])
            print(f"   ✅ Đã gửi email cho {user.name} với {len(top)} bài chọn lọc.")
        else:
            print(f"   Không chọn được bài nào phù hợp cho {user.name}.")
            
    print("Pipeline hoàn tất.")

