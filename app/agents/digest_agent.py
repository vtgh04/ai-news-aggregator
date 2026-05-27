import os, json, uuid
from groq import Groq
from app.db.repository import save_digest

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """Bạn là biên tập viên tin tức AI. Tóm tắt nội dung sau thành JSON.
Chỉ trả về JSON, không có markdown, không có giải thích.
Format: {"title": "...", "summary": "2-3 câu tóm tắt", "category": "Research|Product|Tutorial|News"}"""


def summarize(source_url: str, content: str) -> dict | None:
    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content[:4000]},
            ],
            max_tokens=300,
        )
        raw = resp.choices[0].message.content
        data = json.loads(raw)
        return {
            "id": str(uuid.uuid4()),
            "source_url": source_url,
            "title": data["title"],
            "summary": data["summary"],
            "category": data["category"],
        }
    except Exception as e:
        print(f"Digest error: {e}")
        return None
