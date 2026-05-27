import os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def build_email_body(top_articles: list[dict]) -> str:
    lines = ["Xin chào!\n\nĐây là digest AI hôm nay của bạn:\n"]
    for i, a in enumerate(top_articles, 1):
        lines.append(f"{i}. **{a['title']}**")
        lines.append(f"   {a['summary']}")
        lines.append(f"   Đọc thêm: {a['source_url']}\n")
    lines.append("\n---\nAI News Aggregator · Tự động tạo bởi hệ thống của bạn")
    return "\n".join(lines)


def send_digest(top_articles: list[dict]):
    sender    = os.getenv("GMAIL_ADDRESS")
    password  = os.getenv("GMAIL_APP_PASSWORD")
    recipient = sender  # Gửi cho chính mình

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"AI Digest hôm nay — {len(top_articles)} bài chọn lọc"
    msg["From"]    = sender
    msg["To"]      = recipient
    msg.attach(MIMEText(build_email_body(top_articles), "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())
    print(f"Email đã gửi: {len(top_articles)} bài")
