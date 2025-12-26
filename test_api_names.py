
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WORLDSEDGE_BASE_URL = "https://aoe-api.worldsedgelink.com"
TITLE = "age2"

def test_get_personal_stat_ids(profile_ids):
    path = "/community/leaderboard/GetPersonalStat"
    url = f"{WORLDSEDGE_BASE_URL}{path}"
    # Try passing profile_ids list
    params = {
        "title": TITLE, 
        "profile_ids": json.dumps(profile_ids)
    }
    
    print(f"Requesting: {url} with params {params}")
    resp = requests.get(url, params=params)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {resp.text}")

if __name__ == "__main__":
    # Test with a known ID from user's image, e.g., 4308371
    test_id = 4308371
    test_get_personal_stat_ids([test_id])
