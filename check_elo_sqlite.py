import sqlite3
import datetime

db_path = "aoe2stats.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Check count of rows with ELO
    cursor.execute("SELECT count(*), count(elo_after) FROM match_players")
    row = cursor.fetchone()
    print(f"Total MatchPlayers: {row[0]}")
    print(f"MatchPlayers with ELO: {row[1]}")
    
    # 2. Sample 5
    print("\n--- Sample Last 5 Matches with ELO ---")
    cursor.execute("""
        SELECT mp.aoe_profile_id, mp.elo_after, m.started_at 
        FROM match_players mp
        JOIN matches m ON mp.match_id = m.match_id
        WHERE mp.elo_after IS NOT NULL
        ORDER BY m.started_at DESC
        LIMIT 5
    """)
    rows = cursor.fetchall()
    for r in rows:
        print(r)

    # 3. Check specific profile ID from before
    pid = 5587599
    print(f"\n--- Checking Profile {pid} ---")
    cursor.execute("SELECT count(elo_after) FROM match_players WHERE aoe_profile_id = ?", (pid,))
    row = cursor.fetchone()
    print(f"ELO entries for {pid}: {row[0]}")
    
    # 4. Check Date Range
    print("\n--- Date Range of ELO Data ---")
    cursor.execute("""
        SELECT min(m.started_at), max(m.started_at)
        FROM matches m
        JOIN match_players mp ON m.match_id = mp.match_id
        WHERE mp.elo_after IS NOT NULL
    """)
    row = cursor.fetchone()
    print(f"Min Date: {row[0]}")
    print(f"Max Date: {row[1]}")

    conn.close()

except Exception as e:
    print(f"Error: {e}")
