import duckdb
from ..db.database import SessionLocal
from ..db.models import Match, MatchPlayer, Player
from sqlalchemy.dialects.postgresql import insert
import pandas as pd

def process_matches(parquet_path, watchlist_profile_ids):
    """
    Query the matches parquet file for matches involving watchlist players.
    Using DuckDB for efficient querying of the parquet file.
    """
    if not watchlist_profile_ids:
        print("Watchlist is empty.")
        return

    con = duckdb.connect()
    
    # We need to find match_ids where ANY of the players in the watchlist participated.
    # The structure of aoestats matches.parquet usually has a 'players' column which is a list of structs or similar,
    # OR there is a separate match_players table. 
    # AoEStats provides 'matches.parquet' and 'players.parquet'.
    # Usually matches.parquet has flattened info or we need to join.
    # Let's assume matches.parquet has the match info and players.parquet (from dump) has player-match stats.
    # Wait, the user said: "matches.parquet and players.parquet".
    # Let's verify the schema of these dumps if possible, or assume standard schema.
    # Common schema: matches.parquet (match_id, ...) and players.parquet (match_id, profile_id, ...).
    
    # Let's filter players.parquet first to get match_ids for our watchlist.
    ids_str = ",".join(map(str, watchlist_profile_ids))
    
    # This query finds all match_ids where our watchlist players played
    query_match_ids = f"""
    SELECT DISTINCT match_id 
    FROM read_parquet('{parquet_path}') 
    WHERE profile_id IN ({ids_str})
    """
    
    try:
        relevant_matches_df = con.execute(query_match_ids).df()
        match_ids = relevant_matches_df['match_id'].tolist()
        print(f"Found {len(match_ids)} relevant matches for watchlist.")
        return match_ids
    except Exception as e:
        print(f"Error querying parquet: {e}")
        return []

def sync_to_db(match_ids, matches_parquet, players_parquet):
    # This is a placeholder for the actual sync logic
    # getting details from parquet files for the filtered match_ids
    pass
