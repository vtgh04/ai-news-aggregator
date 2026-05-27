import hashlib
import binascii
from fastapi import Request
from sqlalchemy.orm import Session
from app.db.models import engine, User

SALT = b"news_aggregator_saas_secure_salt"
ITERATIONS = 100000

def hash_password(password: str) -> str:
    """Mã hóa mật khẩu bằng PBKDF2-HMAC-SHA256."""
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), SALT, ITERATIONS)
    return binascii.hexlify(dk).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    """Xác minh mật khẩu có khớp hay không."""
    return hash_password(password) == hashed

def get_current_user(request: Request) -> User | None:
    """Lấy thông tin người dùng đang đăng nhập từ Session."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    with Session(engine) as s:
        user = s.get(User, user_id)
        if user:
            # Loại bỏ _sa_instance_state của SQLAlchemy để có thể dùng an toàn ngoài session
            return user
        return None
