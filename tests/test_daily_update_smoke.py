import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add project root to sys.path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.db.database import Base
from services.db.models import Player, Match, AggPlayerDaily
from services.worker import run_daily_update

# Use in-memory SQLite for testing to avoid polluting real DB
TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def test_db_session(monkeypatch):
    """
    Creates an in-memory DB, patches SessionLocal in worker, and yields session.
    """
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestingSessionLocal()
    
    # Patch worker.SessionLocal to return our test session
    # Note: run_daily_update calls SessionLocal(), so we need a callable that returns our session or a new one bound to our engine.
    # Since run_daily_update manages its own scope (db = SessionLocal() ... db.close()),
    # we should patch the class/factory.
    monkeypatch.setattr("services.worker.SessionLocal", TestingSessionLocal)
    
    # Also patch for database.py if needed?
    # worker imports process_matches which takes 'db' arg, so that's fine.
    # Aggregator takes 'db' arg.
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_daily_update_integration_smoke(test_db_session):
    """
    Smoke test:
    1. Seed a known active player (TheViper: 199325).
    2. Run daily update.
    3. Verify matches fetched and aggregation populated.
    """
    # 1. Seed Player
    # "TheViper" profile ID is 199325. This is a very active player.
    vip_id = 199325
    player = Player(
        player_id=str(vip_id),
        aoe_profile_id=vip_id,
        display_name="SmokeTestViper",
        added_at=datetime.utcnow()
    )
    test_db_session.add(player)
    test_db_session.commit()
    
    # 2. Run Update
    # force_update=True to ensure aggregation runs even if logic thinks no new data (though initially 0 matches so all are new).
    summary = run_daily_update(force_update=True)
    
    # 3. Assertions
    print(f"\nTest Summary: {summary}\n")
    
    assert summary["status"] == "success", f"Update failed with errors: {summary.get('errors')}"
    assert summary["players_checked"] == 1
    
    # Assume API is up and Viper has played recently. 
    # If API is down, this test fails (which is valid for an integration smoke test).
    # Check if we fetched anything
    fetched = summary.get("matches_fetched_total", 0)
    inserted = summary.get("new_matches", 0)
    
    # Warning if 0 matches, but asserting strict > 0 might be flaky if he really hasn't played in resultCount=10 window?
    # Actually fetcher fetches last 50 matches (as per our update). He definitely has 50 matches.
    assert fetched > 0, "No matches fetched from API"
    assert inserted > 0, "No new matches inserted into DB"
    
    # 4. Verify DB Content
    match_count = test_db_session.query(Match).count()
    assert match_count == inserted
    
    # Check Aggregation
    agg_count = test_db_session.query(AggPlayerDaily).count()
    # Should have at least one day of stats
    assert agg_count > 0, "AggPlayerDaily is empty, aggregation failed via worker"
    
    print("Smoke test passed successfully.")
