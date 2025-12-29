
import sqlite3

def migrate():
    print("Migrating database...")
    try:
        conn = sqlite3.connect("aoe2stats.db")
        cur = conn.cursor()
        # Add column if not exists. 
        # Check first?
        try:
            cur.execute("ALTER TABLE players ADD COLUMN aoe2insights_id INTEGER")
            conn.commit()
            print("Successfully added aoe2insights_id column.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("Column aoe2insights_id already exists.")
            else:
                raise e
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    migrate()
