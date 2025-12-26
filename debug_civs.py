
import sqlite3
import pandas as pd

conn = sqlite3.connect("aoe2stats.db")
query = "SELECT civ_name, count(*) as cnt FROM match_players GROUP BY civ_name"
df = pd.read_sql_query(query, conn)
print(df)
conn.close()
