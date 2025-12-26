
import sqlite3
import os

DB_PATH = "aoe2stats.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print("Database not found, skipping migration.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    columns_to_add = [
        ("country", "TEXT"),
        ("elo_rm_1v1", "INTEGER"),
        ("elo_rm_team", "INTEGER"),
        ("last_match_at", "DATETIME")
    ]
    
    # Check existing columns
    cursor.execute("PRAGMA table_info(players)")
    existing_cols = [row[1] for row in cursor.fetchall()]
    
    for col_name, col_type in columns_to_add:
        if col_name not in existing_cols:
            print(f"Adding column {col_name}...")
            try:
                cursor.execute(f"ALTER TABLE players ADD COLUMN {col_name} {col_type}")
                print("Done.")
            except Exception as e:
                print(f"Failed to add {col_name}: {e}")
        else:
            print(f"Column {col_name} already exists.")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
