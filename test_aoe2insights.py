import requests
import json

BASE_URL = "https://www.aoe2insights.com/api/v1"
HEADERS = {"User-Agent": "AOE2DE_GODO_TAKIP/1.0"}

PID = 5587599 # DaRKN'

def test_aoe2insights():
    print("--- Probing AOE2Insights API ---")
    
    # Attempt 1: Matches by Profile ID directly
    # Often params are 'player_id' or 'profile_id'
    print("\n1. Testing matches endpoint with profile_id...")
    url1 = f"{BASE_URL}/matches"
    try:
        r = requests.get(url1, params={"player_id": PID}, headers=HEADERS)
        print(f"URL: {r.url}")
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print(r.text[:500])
        else:
            # Try specific user endpoint?
            pass
    except Exception as e: print(e)

    # Attempt 2: Search for player to find internal ID
    print("\n2. Testing player search...")
    url2 = f"{BASE_URL}/players" # or /search/players
    try:
        r = requests.get(url2, params={"q": "DaRKN'"}, headers=HEADERS) # generic search param q
        if r.status_code != 200:
             # Try search endpoint
             url2 = f"{BASE_URL}/players/search"
             r = requests.get(url2, params={"q": "DaRKN'"}, headers=HEADERS)
             
        print(f"URL: {r.url}")
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print(r.text[:500])
    except Exception as e: print(e)

if __name__ == "__main__":
    test_aoe2insights()
