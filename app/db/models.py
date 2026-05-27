from sqlalchemy import Column, String, Text, DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///news.db")
engine = create_engine(DATABASE_URL)


class Base(DeclarativeBase):
    pass


class Article(Base):
    __tablename__ = "articles"

    url          = Column(String, primary_key=True)
    source       = Column(String, nullable=False)    # "youtube", "openai", "anthropic", "huggingface"
    title        = Column(String, nullable=False)
    author       = Column(String, nullable=True)     # Tên kênh YouTube hoặc tác giả
    summary      = Column(Text, nullable=True)       # Tóm tắt ban đầu hoặc mô tả ngắn
    content      = Column(Text, nullable=True)       # Transcript hoặc nội dung đầy đủ (markdown)
    published_at = Column(DateTime, nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)


class Digest(Base):
    __tablename__ = "digests"

    id          = Column(String, primary_key=True)  # uuid
    source_url  = Column(String, nullable=False)
    title       = Column(String, nullable=False)
    summary     = Column(Text, nullable=False)
    category    = Column(String, nullable=False)
    score       = Column(String, nullable=True)
    sent_at     = Column(DateTime, nullable=True)   # None = chưa gửi
    created_at  = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id              = Column(String, primary_key=True)  # uuid
    email           = Column(String, unique=True, nullable=False)
    name            = Column(String, nullable=False)
    profile         = Column(Text, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)


class UserDigest(Base):
    __tablename__ = "user_digests"

    user_id    = Column(String, primary_key=True)
    digest_id  = Column(String, primary_key=True)
    sent_at    = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(engine)
    
    # Khởi tạo người dùng mặc định nếu chưa có
    from sqlalchemy.orm import Session
    import uuid
    with Session(engine) as session:
        try:
            user_exists = session.query(User).first() is not None
            if not user_exists:
                admin_email = os.getenv("GMAIL_ADDRESS") or "admin@example.com"
                default_profile = """Tên: [Huy]
Nghề nghiệp: Sinh viên CNTT, học AI/ML
Chủ đề quan tâm: LLM, AI agents, Python, career in AI
Không quan tâm: crypto, NFT, tin tức chính trị
"""
                profile_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents", "user_profile.txt")
                if os.path.exists(profile_path):
                    try:
                        with open(profile_path, "r", encoding="utf-8") as f:
                            default_profile = f.read()
                    except Exception:
                        pass
                
                from app.web.auth import hash_password
                admin_user = User(
                    id=str(uuid.uuid4()),
                    email=admin_email,
                    name="Admin (Bạn)",
                    profile=default_profile,
                    hashed_password=hash_password("admin123")
                )
                session.add(admin_user)
                session.commit()
                print("   [DB] Đã khởi tạo người dùng Admin mặc định (mật khẩu: admin123).")
        except Exception as e:
            print(f"   [DB ERROR] Không thể khởi tạo người dùng mặc định: {e}")

