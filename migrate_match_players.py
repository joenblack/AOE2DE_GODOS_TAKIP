
import sqlite3
import os

DB_PATH = "aoe2stats.db"

def migrate_match_players():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("Starting migration of match_players...")
        
        # 1. Rename existing table
        cursor.execute("ALTER TABLE match_players RENAME TO match_players_old")
        
        # 2. Create new table with surrogate PK match_player_id
        # Note: We use BigInt for match_id to match Match table.
        cursor.execute("""
        CREATE TABLE match_players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id BIGINT,
            aoe_profile_id INTEGER,
            team INTEGER,
            civ_id INTEGER,
            civ_name VARCHAR,
            result VARCHAR,
            won BOOLEAN,
            elo_before INTEGER,
            elo_after INTEGER,
            color INTEGER,
            position INTEGER,
            FOREIGN KEY(match_id) REFERENCES matches(match_id),
            FOREIGN KEY(aoe_profile_id) REFERENCES players(aoe_profile_id)
        )
        """)
        
        # 3. Create Indexes
        cursor.execute("CREATE INDEX ix_match_players_match_id ON match_players (match_id)")
        cursor.execute("CREATE INDEX ix_match_players_aoe_profile_id ON match_players (aoe_profile_id)")
        
        # 4. Copy Data
        # We explicitly list columns to ensure order, omitting 'id' to let it autoincrement
        columns = "match_id, aoe_profile_id, team, civ_id, civ_name, result, won, elo_before, elo_after, color, position"
        copy_sql = f"INSERT INTO match_players ({columns}) SELECT {columns} FROM match_players_old"
        cursor.execute(copy_sql)
        print(f"Copied {cursor.rowcount} rows.")
        
        # 5. Drop old table
        cursor.execute("DROP TABLE match_players_old")
        
        conn.commit()
        print("Migration successful.")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_match_players()
