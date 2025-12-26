import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    import schedule  # optional: only used if you run this file as a standalone worker
except Exception:  # pragma: no cover
    schedule = None

from services.analysis.aggregator import Aggregator
from services.db.database import SessionLocal
from services.db.models import Player
from services.etl import fetcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def run_daily_update() -> Dict[str, Any]:
    """Pull recent matches for all tracked players and refresh aggregates.

    Returns a structured summary so Streamlit Admin page can display what happened.
    """
    started = datetime.now(timezone.utc)
    summary: Dict[str, Any] = {
        "started_at_utc": started.isoformat(),
        "players_tracked": 0,
        "profile_ids": [],
        "matches_fetched": 0,
        "matches_unique": 0,
        "inserted_matches": 0,
        "backfilled_matches": 0,
        "inserted_match_players": 0,
        "aggregates_refreshed": False,
        "aggregates_refreshed": False,
        "players_resolved": 0,
        "errors": [],
    }

    logger.info("Starting daily update job...")
    db = SessionLocal()
    try:
        # Only fetch matches for players explicitly added to watchlist (added_at is not None)
        players = db.query(Player).filter(Player.added_at.isnot(None)).all()
        profile_ids = [int(p.aoe_profile_id) for p in players if p.aoe_profile_id is not None]
        profile_ids = sorted(set(profile_ids))

        summary["players_tracked"] = len(profile_ids)
        summary["profile_ids"] = profile_ids

        if not profile_ids:
            summary["errors"].append("No tracked players found (players table empty or missing aoe_profile_id).")
            return summary

        matches = fetcher.fetch_recent_matches_for_players(profile_ids)
        summary["worldsedgelink_last_http"] = fetcher.get_last_http()
        summary["matches_fetched"] = len(matches)
        unique_match_ids = sorted({m.get("id") for m in matches if m.get("id")})
        summary["matches_unique"] = len(unique_match_ids)

        if not matches:
            summary["errors"].append("WorldsEdgeLink returned 0 matches for the tracked profile IDs.")
            return summary

        stats = fetcher.process_matches(db, profile_ids, matches)
        summary.update(stats)

        
        # ---------------------------------------------------------
        # 5. Aggregation
        # ---------------------------------------------------------
        aggregator = Aggregator(db)
        aggregator.refresh_all()
        summary["aggregates_refreshed"] = True
        # summary["players_resolved"] = players_resolved_count # Undefined variable, removed.

        logger.info("Daily update completed.")
        return summary

    except Exception as e:
        logger.exception("Daily update failed: %s", e)
        summary["errors"].append(str(e))
        return summary
    finally:
        db.close()


def main(run_at: str = "04:00"):
    """Optional: run as a standalone worker (not needed on Streamlit Cloud)."""
    if schedule is None:
        raise RuntimeError("The 'schedule' package is not installed. Install it or run updates manually from Admin page.")

    logger.info("Worker started. Scheduling daily update for %s (server local time).", run_at)
    schedule.every().day.at(run_at).do(run_daily_update)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
