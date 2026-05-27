"""Xem nhanh dữ liệu trong database sau khi tái cấu trúc."""
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.orm import Session
from app.db.models import engine, Article, Digest, User, UserDigest

with Session(engine) as s:
    # Đếm tổng số bài viết của từng nguồn trong bảng articles
    yt   = s.query(Article).filter(Article.source == "youtube").count()
    oai  = s.query(Article).filter(Article.source == "openai").count()
    anth = s.query(Article).filter(Article.source == "anthropic").count()
    hf   = s.query(Article).filter(Article.source == "huggingface").count()
    
    total_articles = s.query(Article).count()
    dg   = s.query(Digest).count()
    
    total_users = s.query(User).count()
    total_user_digests = s.query(UserDigest).count()

    print(f"📊 Thống kê database mới (Unified articles table):")
    print(f"   YouTube Videos      : {yt}")
    print(f"   OpenAI Articles     : {oai}")
    print(f"   Anthropic Articles  : {anth}")
    print(f"   HuggingFace Articles: {hf}")
    print(f"   Tổng số Article     : {total_articles}")
    print(f"   Digests (tổng)      : {dg}")
    print(f"   Số người nhận tin   : {total_users}")
    print(f"   Số UserDigests (gửi): {total_user_digests}")
    print()

    print("👥 Danh sách người dùng nhận tin:")
    users = s.query(User).order_by(User.created_at.desc()).all()
    for u in users:
        print(f"   - {u.name} <{u.email}>")
    print()

    print("📨 10 Digest gần nhất:")
    digests = s.query(Digest).order_by(Digest.created_at.desc()).limit(10).all()
    for d in digests:
        print(f"   [{d.category}] {d.title[:60]}...")
