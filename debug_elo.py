import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WORLDSEDGE_BASE_URL = "https://aoe-api.worldsedgelink.com"
TITLE = "age2"
PID = 11807473

def test_fetch_elo(pid):
    url = f"{WORLDSEDGE_BASE_URL}/community/leaderboard/getPersonalStat"
    payload = {"title": TITLE, "profile_ids": json.dumps([int(pid)])}
    print(f"Fetching from {url} with {payload}")
    
    try:
        resp = requests.post(url, data=payload, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print("Response Data:")
            print(json.dumps(data, indent=2))
        else:
            print(f"Error: {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

test_fetch_elo(PID)
