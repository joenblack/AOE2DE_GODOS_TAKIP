
import requests
import json
import logging
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WORLDSEDGE_BASE_URL = "https://aoe-api.worldsedgelink.com"
TITLE = "age2"

IDS = [2738674, 4308371, 5525181, 5587599]

def resolve_names(ids: List[int]):
    url = f"{WORLDSEDGE_BASE_URL}/community/leaderboard/GetPersonalStat"
    params = {"title": TITLE, "profile_ids": json.dumps(ids)}
    try:
        resp = requests.get(url, params=params, timeout=20)
        data = resp.json()
        groups = data.get("statGroups", [])
        mapping = {}
        for g in groups:
            for m in g.get("members", []):
                pid = m.get("profile_id")
                alias = m.get("alias")
                mapping[pid] = alias
        return mapping
    except Exception as e:
        logger.error(f"Resolution failed: {e}")
        return {}

def test_fetch(profile_id: int, label: str, extra_params: dict):
    url = f"{WORLDSEDGE_BASE_URL}/community/leaderboard/getRecentMatchHistory"
    params = {
        "title": TITLE,
        "profile_ids": json.dumps([profile_id]),
        "count": 200 # Standard chunk
    }
    params.update(extra_params)
    
    print(f"--- Testing {label} with params: {extra_params} ---")
    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        matches = data.get("matchHistoryStats", [])
        print(f"Matches returned: {len(matches)}")
        if matches:
            # Print timestamp of first and last
            print(f"Timestamp First: {matches[0].get('startgametime')}")
            print(f"Timestamp Last : {matches[-1].get('startgametime')}")
        else:
            print("No matches returned.")
            
    except Exception as e:
        logger.error(f"Fetch failed: {e}")

if __name__ == "__main__":
    current_map = resolve_names(IDS)
    print("Resolved Players:", current_map)
    
    # Find sinx (approximate match)
    sinx_id = None
    for pid, name in current_map.items():
        if "sinx" in name.lower():
            sinx_id = int(pid)
            print(f"Found 'sinx' -> ID: {sinx_id}")
            break
            
    if not sinx_id:
        # Fallback to first one
        sinx_id = IDS[0]
        print(f"Could not find sinx, using {sinx_id}")

    # Baseline
    test_fetch(sinx_id, "Baseline", {})
    
    # Pagination Attempts
    test_fetch(sinx_id, "Start=100", {"start": 100})
    test_fetch(sinx_id, "Offset=100", {"offset": 100})
    test_fetch(sinx_id, "Page=2", {"page": 2})
    
    # Time based (using an arbitrary timestamp from ~2024 to see if it filters)
    # 1704067200 is Jan 1 2024
    test_fetch(sinx_id, "SinceTimestamp", {"since": 1704067200})
    test_fetch(sinx_id, "StartGameTime", {"startgametime": 1704067200})
