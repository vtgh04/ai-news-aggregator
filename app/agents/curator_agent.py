import os, json, re
from groq import Groq
from app.db.repository import get_user_profile

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def curate(digests: list[dict]) -> list[dict]:
    user_profile = get_user_profile()
    items_text = "\n".join(
        f"{i+1}. [{d['category']}] {d['title']}: {d['summary']}"
        for i, d in enumerate(digests)
    )
    prompt = f"""Hồ sơ người dùng:
{user_profile}

Danh sách tin tức hôm nay:
{items_text}

Chọn tối đa 10 tin phù hợp nhất với người dùng. Trả về JSON array gồm các số thứ tự (1-based).
Ví dụ: [1, 3, 5, 7]"""

    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system", 
                "content": "You are a curator agent. You must output ONLY a raw JSON array of integers (e.g. [1, 3, 5]) representing selected 1-based indices. Do NOT write any introduction, markdown, explanation or text. Just the raw array."
            },
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
    )
    raw = resp.choices[0].message.content.strip()
    print(f"Curator response: {raw!r}")

    try:
        indices = json.loads(raw)
    except json.JSONDecodeError:
        # Thử tìm mảng JSON trong response
        match = re.search(r"\[[\d,\s]+\]", raw)
        if match:
            indices = json.loads(match.group())
        else:
            print("⚠️ Curator không parse được response, dùng toàn bộ digest.")
            return digests[:10]

    return [digests[i - 1] for i in indices if 1 <= i <= len(digests)]
