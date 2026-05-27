"""Script khởi tạo SQLite database sau khi tái cấu trúc."""
from dotenv import load_dotenv
load_dotenv()

from app.db.models import init_db, DATABASE_URL

print(f"📂 Đang tạo database tại: {DATABASE_URL}")
init_db()
print("✅ Tạo database thành công!")
print("   Các bảng đã tạo:")
print("   - articles (Bảng gộp chung cho tất cả các nguồn)")
print("   - digests (Bảng lưu các tóm tắt tin tức)")
print("   - users (Bảng lưu danh sách người dùng nhận tin)")
print("   - user_digests (Bảng lưu vết gửi tin của từng người dùng)")
