from services.db.database import SessionLocal, engine
from services.db.models import Base, Player, Match
from sqlalchemy import text

def verify_db():
    print("Verifying database schema...")
    with SessionLocal() as db:
        # Check if tables exist
        try:
            db.execute(text("SELECT 1 FROM players LIMIT 1"))
            print("Players table exists.")
        except Exception as e:
            print(f"Error accessing players: {e}")

        # Insert a dummy player
        try:
            player = Player(player_id="test_uuid", aoe_profile_id=12345, display_name="TestPlayer", steam_id="steam_123")
            db.add(player)
            db.commit()
            print("Dummy player inserted.")
            
            p = db.query(Player).filter_by(aoe_profile_id=12345).first()
            print(f"Retrieved player: {p.display_name}")
        except Exception as e:
            print(f"Error inserting/querying player: {e}")

if __name__ == "__main__":
    verify_db()
