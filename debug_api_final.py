import requests
import json

url = "https://aoe-api.worldsedgelink.com/community/leaderboard/getRecentMatchHistory"
profile_id = 5587599 

print("--- DEBUG INITIALIZED ---")

# TEST 1: GET with params dict (Standard)
print("\n--- TEST 1: GET with params dict ---")
try:
    resp = requests.get(url, params={"title": "age2", "profile_id": profile_id}, timeout=10)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(resp.text[:500])
    else:
        print("Error:", resp.text[:200].replace("\n", " "))
except Exception as e: print(e)

# TEST 2: POST Form Data (Singular)
print("\n--- TEST 2: POST Form (Singular) ---")
try:
    resp = requests.post(url, data={"title": "age2", "profile_id": profile_id}, timeout=10)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(resp.text[:500])
    else:
        print("Error:", resp.text[:200].replace("\n", " "))
except Exception as e: print(e)

# TEST 3: POST Form Data (Plural List)
print("\n--- TEST 3: POST Form (Plural List) request-style ---")
try:
    # requests sends 'profile_ids': [123] as 'profile_ids=123'
    resp = requests.post(url, data={"title": "age2", "profile_ids": [profile_id]}, timeout=10)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(resp.text[:500])
    else:
        print("Error:", resp.text[:200].replace("\n", " "))
except Exception as e: print(e)

# TEST 4: POST Form Data (Plural explicit list brackets)
print("\n--- TEST 4: POST Form (Plural brackets) ---")
try:
    # Maybe it wants 'profile_ids[]'
    resp = requests.post(url, data={"title": "age2", "profile_ids[]": profile_id}, timeout=10)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(resp.text[:500])
    else:
        print("Error:", resp.text[:200].replace("\n", " "))
except Exception as e: print(e)
