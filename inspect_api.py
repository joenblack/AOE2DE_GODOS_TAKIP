import requests
import json

profile_id = 2738674
headers = {"User-Agent": "Mozilla/5.0"}

profile_id = 2738674
headers = {"User-Agent": "Mozilla/5.0"}

urls = [
    # Official API User mentioned
    f"https://api.ageofempires.com/api/v2/AgeII/GetMatchHistory?profileId={profile_id}&resultCount=10",
    f"https://api.ageofempires.com/api/v2/AgeII/Match/History?profileId={profile_id}&resultCount=10",
    
    # AoE2 Insights (Guessing v1 API or similar)
    f"https://www.aoe2insights.com/user/{profile_id}/matches", # This is HTML, but checking if we can scrape easily
    
    # Try WorldEdgeLink with POST?
    # Usually it's GET for history.
]

print("Starting checks...")
for url in urls:
    print(f"Checking: {url}")
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        print(f"Status: {resp.status_code}")
        print(f"Content Type: {resp.headers.get('Content-Type')}")
        if resp.status_code == 200:
            if "application/json" in resp.headers.get('Content-Type', ''):
                try:
                    data = resp.json()
                    print(json.dumps(data, indent=2)[:500])
                except:
                    print("JSON Decode Failed")
            else:
                print(f"Text Content Start: {resp.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 20)
