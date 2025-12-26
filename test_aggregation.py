from services.db.database import SessionLocal
from services.db.models import Player, Match, MatchPlayer, AggPlayerCiv
from services.analysis.aggregator import Aggregator
from sqlalchemy import text
from datetime import datetime

def test_aggregation():
    db = SessionLocal()
    try:
        # 1. Clean up
        db.execute(text("DELETE FROM agg_player_civ"))
        db.execute(text("DELETE FROM match_players"))
        db.execute(text("DELETE FROM matches"))
        db.execute(text("DELETE FROM players"))
        db.commit()

        # 2. Add Test Data
        p1 = Player(player_id="uid1", aoe_profile_id=100, display_name="Gamer1", steam_id="s1")
        db.add(p1)
        
        m1 = Match(match_id=1, started_at=datetime.now(), map_name="Arabia", map_id=9)
        db.add(m1)
        
        mp1 = MatchPlayer(match_id=1, aoe_profile_id=100, civ_id=1, civ_name="Britons", won=True, team=1)
        db.add(mp1)
        
        m2 = Match(match_id=2, started_at=datetime.now(), map_name="Arena", map_id=12)
        db.add(m2)
        
        mp2 = MatchPlayer(match_id=2, aoe_profile_id=100, civ_id=1, civ_name="Britons", won=False, team=1)
        db.add(mp2)

        db.commit()
        print("Test data inserted.")

        # 3. Run Aggregator
        agg = Aggregator(db)
        agg.refresh_all()

        # 4. Verify Results
        res = db.query(AggPlayerCiv).filter_by(player_id="uid1", civ_name="Britons").first()
        if res:
            print(f"AggPlayerCiv: Britons -> Total: {res.total_games}, Wins: {res.wins}, WinRate: {res.win_rate}%")
            if res.total_games == 2 and res.wins == 1 and res.win_rate == 50:
                print("SUCCESS: Aggregation logic verified.")
            else:
                print("FAILURE: Stats mismatch.")
        else:
            print("FAILURE: No aggregation record found.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_aggregation()
