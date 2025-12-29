import requests
import json
import sys

TITLE = "age2"
BASE_URL = "https://aoe-api.worldsedgelink.com"
PID = 5587599

def debug_400():
    url = f"{BASE_URL}/community/leaderboard/getMatchHistory"
    
    # Try singular profile_id
    payload = {"title": TITLE, "profile_id": PID}
    print(f"Testing POST to {url} with {payload}")
    
    try:
        r = requests.post(url, data=payload)
        print(f"Status: {r.status_code}")
        print(f"Headers: {r.headers}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_400()
