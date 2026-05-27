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


def init_db():
    Base.metadata.create_all(engine)
