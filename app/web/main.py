import os
from dotenv import load_dotenv
load_dotenv()

import threading
from datetime import datetime
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

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
from app.runner import run_pipeline

app = FastAPI(title="AI News Aggregator Dashboard")

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


class ProfileUpdate(BaseModel):
    profile: str


class UserCreate(BaseModel):
    name: str
    email: str
    profile: str


class UserUpdate(BaseModel):
    name: str
    email: str
    profile: str


# ── Web Router ────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")


# ── API Endpoints ─────────────────────────────────────────────────────────────

@app.get("/api/stats")
def api_stats():
    try:
        stats = get_dashboard_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/digests")
def api_digests(category: str = None, status: str = None, search: str = None, limit: int = 50):
    try:
        digests = get_all_digests(limit=limit, category=category, status=status, search=search)
        return [to_dict(d) for d in digests]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/articles")
def api_articles(source: str = None, limit: int = 50):
    try:
        articles = get_all_articles(limit=limit, source=source)
        return [to_dict(a) for a in articles]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profile")
def api_get_profile():
    try:
        profile_text = get_user_profile()
        return {"profile": profile_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/profile")
def api_save_profile(data: ProfileUpdate):
    try:
        save_user_profile(data.profile)
        return {"status": "success", "message": "Đã cập nhật User Profile thành công!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users")
def api_users():
    try:
        users = get_all_users()
        return [to_dict(u) for u in users]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/users")
def api_create_user(user: UserCreate):
    try:
        import uuid
        user_id = str(uuid.uuid4())
        data = {
            "id": user_id,
            "name": user.name,
            "email": user.email,
            "profile": user.profile,
        }
        save_user(data)
        return {"status": "success", "message": "Thêm người dùng thành công!", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/users/{user_id}")
def api_update_user(user_id: str, user: UserUpdate):
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
def api_delete_user(user_id: str):
    try:
        delete_user(user_id)
        return {"status": "success", "message": "Xóa người dùng thành công!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pipeline/run")
def api_run_pipeline():
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
def api_pipeline_status():
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

