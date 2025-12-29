import requests
import json
import logging
import sys
import subprocess

# Dependencies
try:
    from pydantic_settings import BaseSettings
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pydantic-settings", "sqlalchemy", "psycopg2-binary"])

TITLE = "age2"
BASE_URL = "https://aoe-api.worldsedgelink.com"

# DaRKN' ID
PID = 5587599 

def run_tests():
    print(f"Testing Profile ID: {PID}")
    
    # TEST 1: getRecentMatchHistory (POST) - Baseline
    print("\n--- TEST 1: getRecentMatchHistory (POST Default) ---")
    url = f"{BASE_URL}/community/leaderboard/getRecentMatchHistory"
    try:
        r = requests.post(url, data={"title": TITLE, "profile_ids": json.dumps([PID])})
        if r.status_code == 200:
            d = r.json()
            matches = d.get("matchHistoryStats", [])
            print(f"Count: {len(matches)}")
            if matches:
                print(f"Oldest: {matches[-1].get('startgametime')}")
        else:
            print(f"Failed: {r.status_code}")
    except Exception as e: print(e)

    # TEST 2: getRecentMatchHistory (POST with Count)
    print("\n--- TEST 2: getRecentMatchHistory (POST match_count=1000) ---")
    try:
        r = requests.post(url, data={"title": TITLE, "profile_ids": json.dumps([PID]), "match_count": 1000, "count": 1000})
        if r.status_code == 200:
            d = r.json()
            matches = d.get("matchHistoryStats", [])
            print(f"Count: {len(matches)}")
        else:
            print(f"Failed: {r.status_code}")
    except Exception as e: print(e)

    # TEST 3: getRecentMatchHistory (GET with Count) -> From debug_api_limit.py idea
    print("\n--- TEST 3: getRecentMatchHistory (GET count=1000) ---")
    try:
        # Note: requests.get params are URL query string
        params = {"title": TITLE, "profile_ids": json.dumps([PID]), "count": 1000}
        r = requests.get(url, params=params)
        if r.status_code == 200:
            d = r.json()
            matches = d.get("matchHistoryStats", [])
            print(f"Count: {len(matches)}")
        else:
            print(f"Failed: {r.status_code}")
    except Exception as e: print(e)

    # TEST 4: getMatchHistory (POST/GET Variations)
    print("\n--- TEST 4: getMatchHistory Variations ---")
    url_hist = f"{BASE_URL}/community/leaderboard/getMatchHistory"
    variations = [
        {"title": TITLE, "profile_id": PID},
        {"title": TITLE, "profile_id": str(PID)},
        {"title": TITLE, "profile_ids": json.dumps([PID])}, # Try plural JSON on singular endpoint?
        {"game": TITLE, "profile_id": PID}, # Maybe 'game' param?
        {"title": TITLE, "gamertag": "DaRKN'"}
    ]
    
    for i, v in enumerate(variations):
        # Try POST
        try:
            r = requests.post(url_hist, data=v)
            if r.status_code == 200:
                print(f"Var {i} POST SUCCESS! Count: {len(r.json().get('matchHistoryStats', []))}")
            else:
                pass # print(f"Var {i} POST Fail: {r.status_code}")
        except: pass
        
        # Try GET
        try:
            r = requests.get(url_hist, params=v)
            if r.status_code == 200:
                print(f"Var {i} GET SUCCESS! Count: {len(r.json().get('matchHistoryStats', []))}")
            else:
                pass # print(f"Var {i} GET Fail: {params}")
        except: pass

if __name__ == "__main__":
    run_tests()
