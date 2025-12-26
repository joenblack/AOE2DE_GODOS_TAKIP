import sys
import os
from sqlalchemy import text

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from services.db.database import get_db

def fix_data():
    db = next(get_db())
    print("Starting DB Data Fix...")
    
    try:
        # 1. Clean Duplicates
        print("Cleaning duplicate match_players...")
        # SQLite dialect specific deduplication
        stmt_dedupe = text("""
            WITH ranked AS (
              SELECT
                id,
                ROW_NUMBER() OVER (
                  PARTITION BY match_id, aoe_profile_id
                  ORDER BY
                    (won IS NOT NULL) DESC,
                    (elo_after IS NOT NULL) DESC,
                    id ASC
                ) AS rn
              FROM match_players
            )
            DELETE FROM match_players
            WHERE id IN (SELECT id FROM ranked WHERE rn > 1);
        """)
        res = db.execute(stmt_dedupe)
        print(f"Duplicates cleaned. Rows affected: {res.rowcount}")
        db.commit()
        
        # 2. Add Unique Constraint
        print("Adding Unique Index...")
        stmt_index = text("""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_match_players_match_profile
            ON match_players(match_id, aoe_profile_id);
        """)
        db.execute(stmt_index)
        db.commit()
        print("Unique Index ensured.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_data()
