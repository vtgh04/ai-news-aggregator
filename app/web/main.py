import os
from dotenv import load_dotenv
load_dotenv()

import threading
import uuid
from datetime import datetime
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from app.db.repository import (
    get_all_digests,
    get_all_articles,
    get_dashboard_stats,
    get_user_profile,
    save_user_profile,
    get_all_users,
    save_user,
    delete_user,
)
from app.web.auth import hash_password, verify_password, get_current_user
from app.runner import run_pipeline

app = FastAPI(title="AI News Aggregator Dashboard")

# Cấu hình Session Middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "news_aggregator_session_secret_key_2026"),
    max_age=86400 * 7  # 7 ngày
)

# Cấu hình đường dẫn
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")
templates_dir = os.path.join(current_dir, "templates")

# Tạo thư mục static và templates nếu chưa có
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Quản lý luồng chạy Pipeline
is_running = False
running_lock = threading.Lock()


def execute_pipeline():
    global is_running
    try:
        run_pipeline()
    except Exception as e:
        try:
            with open("pipeline.log", "a", encoding="utf-8") as f:
                f.write(f"\n[ERROR] Lỗi hệ thống khi chạy pipeline: {e}\n")
        except Exception:
            pass
    finally:
        with running_lock:
            is_running = False


def to_dict(obj):
    """Helper chuyển đổi SQLAlchemy model sang dict có hỗ trợ datetime."""
    res = {}
    for k, v in obj.__dict__.items():
        if k.startswith("_"):
            continue
        if isinstance(v, datetime):
            res[k] = v.strftime("%Y-%m-%d %H:%M:%S")
        else:
            res[k] = v
    return res


# ── Custom Exception Handlers ────────────────────────────────────────────────

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


# ── Pydantic Models ──────────────────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    name: str = None
    email: str = None
    profile: str


class UserCreate(BaseModel):
    name: str
    email: str
    profile: str


class UserUpdate(BaseModel):
    name: str
    email: str
    profile: str


class AuthLogin(BaseModel):
    email: str
    password: str


class AuthRegister(BaseModel):
    name: str
    email: str
    password: str
    profile: str


# ── Web Router ────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="dashboard.html")


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request=request, name="login.html")


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login")


# ── API Endpoints ─────────────────────────────────────────────────────────────

@app.post("/api/auth/login")
def api_login(request: Request, data: AuthLogin):
    from sqlalchemy.orm import Session
    from app.db.models import engine, User
    
    with Session(engine) as s:
        user = s.query(User).filter(User.email == data.email).first()
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Email hoặc mật khẩu không chính xác.")
        
        request.session["user_id"] = user.id
        return {"status": "success", "message": "Đăng nhập thành công!"}


@app.post("/api/auth/register")
def api_register(request: Request, data: AuthRegister):
    from sqlalchemy.orm import Session
    from app.db.models import engine, User
    
    with Session(engine) as s:
        existing = s.query(User).filter(User.email == data.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email này đã được sử dụng.")
        
        user_id = str(uuid.uuid4())
        new_user = User(
            id=user_id,
            name=data.name,
            email=data.email,
            hashed_password=hash_password(data.password),
            profile=data.profile
        )
        s.add(new_user)
        s.commit()
        
        request.session["user_id"] = user_id
        return {"status": "success", "message": "Đăng ký thành công!"}


@app.get("/api/auth/me")
def api_me(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "profile": user.profile
    }


@app.get("/api/stats")
def api_stats(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
        
    try:
        stats = get_dashboard_stats()
        # Đè số tin chờ gửi bằng chính số tin chưa gửi của user hiện tại
        from app.db.repository import get_unsent_digests_for_user
        unsent_count = len(get_unsent_digests_for_user(user.id))
        stats["unsent_digests"] = unsent_count
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/digests")
def api_digests(request: Request, category: str = None, status: str = None, search: str = None, limit: int = 50):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
        
    try:
        digests = get_all_digests(limit=limit, category=category, status=None, search=search)
        
        # Lấy lịch sử gửi tin của user này
        from sqlalchemy.orm import Session
        from app.db.models import engine, UserDigest
        with Session(engine) as s:
            sent_digest_ids = {
                ud.digest_id for ud in s.query(UserDigest.digest_id).filter(UserDigest.user_id == user.id).all()
            }
            
        result = []
        for d in digests:
            d_dict = to_dict(d)
            is_sent = d.id in sent_digest_ids
            d_dict["sent_at"] = "2026-05-27 12:00:00" if is_sent else None
            
            # Lọc theo filter status
            if status == "sent" and not is_sent:
                continue
            if status == "unsent" and is_sent:
                continue
                
            result.append(d_dict)
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/articles")
def api_articles(request: Request, source: str = None, limit: int = 50):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
    try:
        articles = get_all_articles(limit=limit, source=source)
        return [to_dict(a) for a in articles]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profile")
def api_get_profile(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
    return {
        "name": user.name,
        "email": user.email,
        "profile": user.profile
    }


@app.post("/api/profile")
def api_save_profile(request: Request, data: ProfileUpdate):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
    try:
        save_user({
            "id": user.id,
            "name": data.name or user.name,
            "email": data.email or user.email,
            "profile": data.profile
        })
        return {"status": "success", "message": "Đã cập nhật hồ sơ cá nhân thành công!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/email/send-manual")
def api_send_manual_email(request: Request, background_tasks: BackgroundTasks):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
        
    from app.db.repository import get_unsent_digests_for_user
    digests = get_unsent_digests_for_user(user.id)
    if not digests:
        return {"status": "success", "message": "Không có tin mới nào cần gửi!"}
        
    def worker():
        from app.db.repository import get_unsent_digests_for_user, mark_digests_sent_for_user
        from app.agents.curator_agent import curate
        from app.agents.email_agent import send_digest
        
        cur_digests = get_unsent_digests_for_user(user.id)
        if len(cur_digests) > 30:
            cur_digests = cur_digests[:30]
            
        clean = [{k: v for k, v in d.__dict__.items() if not k.startswith("_")} for d in cur_digests]
        top = curate(clean, user.profile)
        if top:
            send_digest(user.email, top, user.name)
            mark_digests_sent_for_user(user.id, [d["id"] for d in top])
            
    background_tasks.add_task(worker)
    return {"status": "started", "message": f"Đang tóm tắt và gửi {len(digests)} bản tin mới vào email của bạn dưới nền."}


@app.get("/api/users")
def api_users(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
    try:
        users = get_all_users()
        return [to_dict(u) for u in users]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/users")
def api_create_user(request: Request, user: UserCreate):
    user_me = get_current_user(request)
    if not user_me:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
    try:
        user_id = str(uuid.uuid4())
        data = {
            "id": user_id,
            "name": user.name,
            "email": user.email,
            "profile": user.profile,
            "hashed_password": hash_password("123456")  # Mật khẩu mặc định
        }
        save_user(data)
        return {"status": "success", "message": "Thêm người dùng thành công!", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/users/{user_id}")
def api_update_user(request: Request, user_id: str, user: UserUpdate):
    user_me = get_current_user(request)
    if not user_me:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
    try:
        data = {
            "id": user_id,
            "name": user.name,
            "email": user.email,
            "profile": user.profile,
        }
        save_user(data)
        return {"status": "success", "message": "Cập nhật người dùng thành công!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/users/{user_id}")
def api_delete_user(request: Request, user_id: str):
    user_me = get_current_user(request)
    if not user_me:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
    try:
        delete_user(user_id)
        return {"status": "success", "message": "Xóa người dùng thành công!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pipeline/run")
def api_run_pipeline(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
        
    global is_running
    with running_lock:
        if is_running:
            return JSONResponse(
                status_code=400,
                content={"status": "running", "message": "Pipeline hiện đang chạy nền, không thể chạy thêm!"}
            )
        is_running = True
        
    thread = threading.Thread(target=execute_pipeline)
    thread.daemon = True
    thread.start()
    return {"status": "started", "message": "Đã bắt đầu chạy Pipeline ở chế độ nền."}


@app.get("/api/pipeline/status")
def api_pipeline_status(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
        
    log_content = ""
    log_file = "pipeline.log"
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                log_content = "".join(lines[-40:])  # Trả về 40 dòng log cuối cùng
        except Exception as e:
            log_content = f"Lỗi khi đọc file log: {e}"
    else:
        log_content = "Không tìm thấy logs. Hãy bấm chạy pipeline để bắt đầu."

    return {
        "is_running": is_running,
        "logs": log_content
    }


