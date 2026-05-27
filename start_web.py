import os
import sys
import traceback
from dotenv import load_dotenv
load_dotenv()

import uvicorn

if __name__ == "__main__":
    print("=== Khởi tạo Cơ sở dữ liệu (nếu chưa có) ===")
    try:
        from app.db.models import init_db
        init_db()
    except Exception as e:
        print("!!! LỖI KHỞI TẠO CƠ SỞ DỮ LIỆU CHÍNH !!!", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    
    try:
        # Cấu hình Host và Port động cho Local và Render
        port = int(os.getenv("PORT", 8000))
        host = "0.0.0.0" if os.getenv("PORT") else "127.0.0.1"
        reload = False if os.getenv("PORT") else True
        
        print(f"=== Khởi động FastAPI Web Dashboard tại http://{host}:{port} ===")
        uvicorn.run("app.web.main:app", host=host, port=port, reload=reload)
    except Exception as e:
        print("!!! LỖI KHỞI ĐỘNG SERVER WEB !!!", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
