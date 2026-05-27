from dotenv import load_dotenv
load_dotenv()

import uvicorn
from app.db.models import init_db

if __name__ == "__main__":
    print("=== Khởi tạo Cơ sở dữ liệu (nếu chưa có) ===")
    init_db()
    
    print("=== Khởi động FastAPI Web Dashboard tại http://127.0.0.1:8000 ===")
    uvicorn.run("app.web.main:app", host="127.0.0.1", port=8000, reload=True)
