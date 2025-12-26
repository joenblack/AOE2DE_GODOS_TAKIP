import requests
import json

url = "https://aoe-api.worldsedgelink.com/community/leaderboard/getRecentMatchHistory"
# Profile ID from user's list
profile_id = 5587599 
payload = {"title": "age2", "profile_id": profile_id}



# 2. POST JSON (Plural list)
print("\n--- TEST 2: POST JSON (Plural List) ---")
try:
    # Note: requests.post(json=...) sets Content-Type: application/json
    resp = requests.post(url, json={"title": "age2", "profile_ids": [profile_id]}, timeout=10)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(resp.text[:500])
    else:
        print("Error:", resp.text[:200])
except Exception as e: print(e)

# 3. POST FORM (Plural list)
print("\n--- TEST 3: POST FORM (Plural List) ---")
try:
    # requests handles list in data as multiple keys: profile_ids=X&profile_ids=Y
    resp = requests.post(url, data={"title": "age2", "profile_ids": [profile_id]}, timeout=10)
    print(f"Status: {resp.status_code}")
    print(resp.text[:500])
except Exception as e: print(e)


