
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WORLDSEDGE_BASE_URL = "https://aoe-api.worldsedgelink.com"
TITLE = "age2"

def test_fetch_limit(profile_id: int):
    url = f"{WORLDSEDGE_BASE_URL}/community/leaderboard/getRecentMatchHistory"
    params = {
        "title": TITLE,
        "profile_ids": json.dumps([profile_id]),
        "count": 10000 
    }
    
    logger.info(f"Requesting matches for Profile ID: {profile_id} with count=10000")
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        matches = data.get("matchHistoryStats", [])
        print(f"Matches returned: {len(matches)}")
        
        if matches:
            # Print first and last match date to see range
            first = matches[0].get("startgametime")
            last = matches[-1].get("startgametime")
            from datetime import datetime
            print(f"Newest Match: {datetime.fromtimestamp(first)}")
            print(f"Oldest Match: {datetime.fromtimestamp(last)}")
            
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    # Using one of the profile IDs seen in previous logs (sinx or darkn likely one of these)
    # Profile IDs from previous log: 2738674, 4308371, 5525181, 5587599
    # Let's try 2738674
    test_fetch_limit(2738674)
