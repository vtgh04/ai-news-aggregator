import os
from dotenv import load_dotenv
load_dotenv()

import uvicorn
from app.db.models import init_db

if __name__ == "__main__":
    print("=== Khởi tạo Cơ sở dữ liệu (nếu chưa có) ===")
    init_db()
    
    # Cấu hình Host và Port động cho Local và Render
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0" if os.getenv("PORT") else "127.0.0.1"
    reload = False if os.getenv("PORT") else True
    
    print(f"=== Khởi động FastAPI Web Dashboard tại http://{host}:{port} ===")
    uvicorn.run("app.web.main:app", host=host, port=port, reload=reload)
