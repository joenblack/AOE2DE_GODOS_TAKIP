from services.db.database import get_db
from sqlalchemy import text
import pandas as pd

db = next(get_db())

print("--- CHECKING MATCH PLAYERS ELO DATA ---")
sql = text("""
    SELECT count(*) as total_rows, count(elo_after) as elo_present 
    FROM match_players
""")
row = db.execute(sql).fetchone()
print(f"Total MatchPlayers: {row[0]}, With ELO: {row[1]}")

if row[1] == 0:
    print("NO ELO DATA FOUND. The fetcher might not be saving 'rating' correctly.")
else:
    print("ELO data found. Sampling...")
    sql_sample = text("""
        SELECT mp.aoe_profile_id, p.display_name, mp.elo_after, m.started_at 
        FROM match_players mp
        JOIN matches m ON mp.match_id = m.match_id
        LEFT JOIN players p ON mp.aoe_profile_id = p.aoe_profile_id
        WHERE mp.elo_after IS NOT NULL
        ORDER BY m.started_at DESC
        LIMIT 5
    """)
    rows = db.execute(sql_sample).fetchall()
    for r in rows:
        print(r)
