import requests

profile_id = 199325 # TheViper

endpoints = [
    # Suggested by user
    ("GET", "https://api.ageofempires.com/api/v2/AgeII/GetMatchHistory", {"profileId": profile_id, "resultCount": 1}, None),
    ("POST", "https://api.ageofempires.com/api/v2/AgeII/GetMatchHistory", None, {"profileId": profile_id, "resultCount": 1}),
    
    # Alternative naming
    ("GET", "https://api.ageofempires.com/api/v2/AgeII/Match/History", {"profileId": profile_id, "resultCount": 1}, None),
    ("POST", "https://api.ageofempires.com/api/v2/AgeII/Match/History", None, {"profileId": profile_id, "resultCount": 1}),
    
    # Maybe v4 API for fun? No, AgeII.
    
    # Common community API?
    #("GET", "https://aoe2.net/api/player/matches", {"game": "aoe2de", "profile_id": profile_id, "count": 1}, None),
    
    # WorldsEdgeLink (LibreMatch)
    ("GET", "https://aoe-api.worldsedgelink.com/community/leaderboard/getRecentMatchHistory", {"title": "nm", "profile_id": 199325}, None),
    # Official v2 maybe?
    #("POST", "https://api.ageofempires.com/api/v2/AgeII/GetMPMatchList", None, {"profileId": profile_id, "resultCount": 1}),
]

print("Testing API Endpoints...")
for method, url, params, json_body in endpoints:
    try:
        if method == "GET":
            resp = requests.get(url, params=params, timeout=5)
        else:
            resp = requests.post(url, json=json_body, timeout=5)
            
        print(f"[{method}] {url} -> Status: {resp.status_code}")
        if resp.status_code == 200:
            print("   SUCCESS! Response snippet:", resp.text[:100])
    except Exception as e:
        print(f"[{method}] {url} -> Error: {e}")
