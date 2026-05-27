import requests
import re

url = "https://www.anthropic.com/news"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
try:
    r = requests.get(url, headers=headers, timeout=10)
    print(f"Status code: {r.status_code}")
    print("Length:", len(r.text))
    # Find all links starting with /news/
    links = re.findall(r'href="(/news/[^"]+)"', r.text)
    print("Found links:")
    for link in set(links)[:10]:
        print("  -", link)
except Exception as e:
    print("Error:", e)
