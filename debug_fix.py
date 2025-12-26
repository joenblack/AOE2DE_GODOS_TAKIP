import requests
import json

url = "https://aoe-api.worldsedgelink.com/community/leaderboard/getRecentMatchHistory"
profile_id = 5587599 

print(f"--- TESTING FIX for {profile_id} ---")

# Hypothesis: profile_ids expects a JSON-encoded string within Form Data
# payload = title=age2 & profile_ids=[5587599]
payload = {
    "title": "age2",
    "profile_ids": json.dumps([profile_id])
}

try:
    print(f"Sending POST with data={payload}")
    resp = requests.post(url, data=payload, timeout=10)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        stats = data.get("matchHistoryStats", [])
        print(f"Match Count: {len(stats)}")
        if stats:
            print("First match sample:")
            print(json.dumps(stats[0], indent=2)[:500])
    else:
        print("Error Response:")
        print(resp.text[:500])

except Exception as e:
    print(f"Exception: {e}")
