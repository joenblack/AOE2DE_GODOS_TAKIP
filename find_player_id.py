import sys
import os
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from services.db.database import get_db

def find_player(name_part):
    db = next(get_db())
    query = text("SELECT aoe_profile_id, display_name FROM players WHERE display_name LIKE :name")
    result = db.execute(query, {"name": f"%{name_part}%"}).fetchall()
    for row in result:
        print(f"Found: {row[1]} (ID: {row[0]})")

if __name__ == "__main__":
    find_player("DaRKN")
