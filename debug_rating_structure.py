import requests
import json

url = "https://aoe-api.worldsedgelink.com/community/leaderboard/getRecentMatchHistory"
profile_id = 5587599 
payload = {
    "title": "age2",
    "profile_ids": json.dumps([profile_id])
}

try:
    print(f"Fetching match history for {profile_id}...", flush=True)
    resp = requests.post(url, data=payload, timeout=20)
    
    print(f"Status: {resp.status_code}", flush=True)
    
    if resp.status_code == 200:
        data = resp.json()
        stats = data.get("matchHistoryStats", [])
        if stats:
            m = stats[0]
            print("\n--- Match Object Keys ---", flush=True)
            print(list(m.keys()), flush=True)
            
            # Check matchhistorymember
            members = m.get("matchhistorymember", [])
            if members:
                print(f"\n--- Match Member Count: {len(members)} ---", flush=True)
                print(json.dumps(members[0], indent=2), flush=True)
            
            # Check reportresults
            reports = m.get("matchhistoryreportresults", [])
            if reports:
                print(f"\n--- Report Results Count: {len(reports)} ---", flush=True)
                print(json.dumps(reports[0], indent=2), flush=True)
                
        else:
            print("No matches found in matchHistoryStats.", flush=True)
    else:
        print(f"Error: {resp.status_code}", flush=True)
        print(resp.text[:200], flush=True)

except Exception as e:
    print(f"Exception: {e}")
