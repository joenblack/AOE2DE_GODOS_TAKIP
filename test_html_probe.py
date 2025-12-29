import requests
import re

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
BASE_URL = "https://www.aoe2insights.com"

def probe_html():
    print("--- Probing AOE2Insights HTML ---")
    
    # Step 1: Search for user to resolve ID
    # Query: DaRKN' (Profile ID: 5587599)
    # Search URL usually: https://www.aoe2insights.com/search?q=...
    search_url = f"{BASE_URL}/search"
    params = {"q": "DaRKN'"} 
    
    print(f"\n1. Searching for user: {search_url}")
    try:
        r = requests.get(search_url, params=params, headers=HEADERS)
        print(f"Status: {r.status_code}")
        # Look for the link to user profile: href="/user/5587599/"
        # Ideally, if inputs are correct, it might redirect or show list.
        # Let's simple regex for /user/(\d+)
        
        matches = re.findall(r'/user/(\d+)', r.text)
        print(f"Found User IDs: {list(set(matches))}")
        
        # Assume 5587599 is the one we want if found (often internal ID == Profile ID or distinct)
        # Check if 5587599 is in the matches.
        # Actually, let's just Try directly accessing /user/5587599/matches 
        # to see if they use the official Profile ID as the URL slug.
    except Exception as e: print(e)

    # Step 2: Test Direct URL with Official Profile ID
    test_id = 5587599
    matches_url = f"{BASE_URL}/user/{test_id}/matches"
    print(f"\n2. Testing Direct URL: {matches_url}")
    try:
        r = requests.get(matches_url, headers=HEADERS)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print("Direct URL worked! Analyzing content...")
            # Check for "Matches" table or data
            if "Matches" in r.text or "table" in r.text:
                print("Found 'Matches' or 'table' in response.")
            # Check for pagination: ?page=2
            if "page=2" in r.text:
                print("Found pagination links.")
        else:
            print("Direct URL failed (Profile ID != Internal ID likely).")
            # If 5587599 failed, maybe one of the IDs found in search (if any) is the internal one.
            
    except Exception as e: print(e)

if __name__ == "__main__":
    probe_html()
