
import sqlite3
import requests
import json

conn = sqlite3.connect("aoe2stats.db")
cursor = conn.cursor()
cursor.execute("SELECT aoe_profile_id FROM match_players LIMIT 1")
row = cursor.fetchone()
conn.close()

if row:
    pid = row[0]
    print(f"Fetching for PID: {pid}")
    
    url = "https://aoe-api.worldsedgelink.com/community/leaderboard/getRecentMatchHistory"
    params = {"title": "age2", "profile_ids": json.dumps([pid]), "count": 1}
    
    resp = requests.get(url, params=params)
    data = resp.json()
    
    stats = data.get("matchHistoryStats", [])
    if stats:
        m = stats[0]
        results = m.get("matchhistoryreportresults", [])
        if results:
            print(json.dumps(results[0], indent=2))
        else:
            print("No report results")
    else:
        print("No stats")
else:
    print("No players in DB")
