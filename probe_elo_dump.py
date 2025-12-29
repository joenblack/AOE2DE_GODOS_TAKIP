
import requests
from bs4 import BeautifulSoup

URL = "https://www.aoe2insights.com/user/11729559/matches/?page=1"

def dump_html():
    print(f"Fetching {URL}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    resp = requests.get(URL, headers=headers)
    print(f"Status: {resp.status_code}")
    
    with open("debug.html", "wb") as f:
        f.write(resp.content)
    print("Saved to debug.html")

if __name__ == "__main__":
    dump_html()
