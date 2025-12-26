import logging
import json
from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional, Tuple

import requests
from sqlalchemy.orm import Session

from services.db.models import Match, MatchPlayer, Player, RefCiv, RefMap

logger = logging.getLogger(__name__)

# For troubleshooting: the last WorldsEdgeLink request URL and status.
from services.mappings import CIV_ID_TO_NAME
from services.db.models import Match, MatchPlayer, Player, RefCiv, RefMap

logger = logging.getLogger(__name__)

# For troubleshooting: the last WorldsEdgeLink request URL and status.
LAST_HTTP: Dict[str, Any] = {}

WORLDSEDGE_BASE_URL = "https://aoe-api.worldsedgelink.com"
TITLE = "age2"

# Removed hardcoded CIV_ID_TO_NAME from here


# Win/Loss mapping for "resulttype"
# 1 = Win, 2 = Loss
# Others (0, 3, 4) treated as Loss or Invalid, mostly Loss.
RESULTTYPE_TO_WON: Dict[int, bool] = {
    1: True,
    2: False,
    3: False, # Drop
    4: False, # Sync Error
}

def resolve_civ_from_player_data(p_data: dict) -> Tuple[Optional[int], Optional[str]]:
    """
    API'nin kullandığı farklı alanları dikkate alarak civ_id ve civ_name döner.
    """
    civ_val = (
        p_data.get("civilization")
        or p_data.get("civilizationID")
        or p_data.get("civilizationId")
        or p_data.get("civId")
        or p_data.get("civ")
        or p_data.get("civName")
        or p_data.get("race_id") # Common in this API
        or p_data.get("raceId")
        or p_data.get("civilization_id")
    )

    if civ_val is None:
        return None, None

    # Önce int ID olarak okumayı dene
    try:
        cid = int(civ_val)
        # Handle Random (0) special case if needed, or mapped in CIV_ID_TO_NAME
        civ_id = cid
        civ_name = CIV_ID_TO_NAME.get(cid, f"Unknown ({cid})")
        return civ_id, civ_name
    except (ValueError, TypeError):
        # Sayıya çevrilemiyorsa zaten isimdir
        civ_id = None
        civ_name = str(civ_val)
        return civ_id, civ_name


def _infer_team_results(players: List[Dict[str, Any]]) -> None:
    """
    Infers win/loss for players with unknown results based on teammates or opponents.
    Logic:
    - If any player in a team won, the whole team won.
    - If any player in a team lost, the whole team lost.
    - If one team won, the other lost (assuming 2 teams).
    """
    # team -> {has_win, has_loss}
    team_flags = {}
    for p in players:
        t = p.get("team")
        if t is None:
            continue
        team_flags.setdefault(t, {"win": False, "loss": False})
        if p.get("won") is True:
            team_flags[t]["win"] = True
        elif p.get("won") is False:
            team_flags[t]["loss"] = True

    teams = list(team_flags.keys())
    # Basic logic for 2 teams (most common)
    if len(teams) != 2:
        return

    t1, t2 = teams[0], teams[1]
    
    # Determine known status for each team
    t1_res = True if team_flags[t1]["win"] else (False if team_flags[t1]["loss"] else None)
    t2_res = True if team_flags[t2]["win"] else (False if team_flags[t2]["loss"] else None)

    # Cross-inference: If T1 won, T2 lost. If T1 lost, T2 won.
    if t1_res is None and t2_res is not None:
        t1_res = not t2_res
    elif t2_res is None and t1_res is not None:
        t2_res = not t1_res

    # If still unknown, we can't do much
    if t1_res is None and t2_res is None:
        # One last check: If we have explicit loss on one side? Already handled above.
        return

    # Apply to players
    for p in players:
        if p.get("won") is None:
            pt = p.get("team")
            if pt == t1 and t1_res is not None:
                p["won"] = t1_res
            elif pt == t2 and t2_res is not None:
                p["won"] = t2_res

def _parse_match(stat: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        match_id = str(stat["id"])
        started_at = datetime.fromtimestamp(int(stat["startgametime"]), tz=timezone.utc)
        ended_at = datetime.fromtimestamp(int(stat["completiontime"]), tz=timezone.utc)
        map_name_raw = str(stat.get("mapname") or "").replace(".rms", "")
        matchtype_id = stat.get("matchtype_id")
        
        # Mapping for matchtype_id (Based on community docs: 6=1v1, 7=2v2, 8=3v3, 9=4v4)
        MATCHTYPE_MAP = {
            0: "Unranked",
            1: "Deathmatch 1v1",
            2: "Deathmatch Team",
            3: "Ranked 1v1",
            4: "Ranked Team",
            5: "Random Map", # Generic?
            6: "Lobby 1v1",   # Often used for Ranked 1v1 in some contexts or Quick Play
            7: "Lobby 2v2",
            8: "Lobby 3v3",
            9: "Lobby 4v4",
            13: "Empire Wars 1v1",
            14: "Empire Wars Team"
        }
        
        if matchtype_id is not None:
             ladder_type = MATCHTYPE_MAP.get(int(matchtype_id), f"Type {matchtype_id}")
        else:
             ladder_type = "Unknown"

        # Prepare member data map for Rating info (found in matchhistorymember but not reports)
        member_map = {}
        for mem in stat.get("matchhistorymember") or []:
            if isinstance(mem, dict):
                mpid = mem.get("profile_id")
                if mpid:
                    member_map[str(mpid)] = mem

        players: List[Dict[str, Any]] = []
        
        # Group reports by profile_id to handle duplicates
        reports_map: Dict[int, List[Dict[str, Any]]] = {}
        for r in stat.get("matchhistoryreportresults") or []:
            if not isinstance(r, dict): continue
            pid = r.get("profile_id")
            if pid is None: continue
            try:
                pid_int = int(pid)
                if pid_int not in reports_map:
                    reports_map[pid_int] = []
                reports_map[pid_int].append(r)
            except ValueError:
                continue

        # Sort/Select best report for each player
        for pid_int, r_list in reports_map.items():
            # Scoring function for best record
            def rate_report(rep):
                score = 0
                # Result presence
                if rep.get("resulttype") is not None or rep.get("result") is not None:
                    score += 10
                # Rating presence (sometimes in report)
                if rep.get("new_rating") is not None:
                    score += 5
                return score
            
            # Sort descending by score
            r_list.sort(key=rate_report, reverse=True)
            r = r_list[0] # Best one

            # ... (civ resolution logic preserved) ...
            race_id = r.get("race_id")
            civ_id_raw = r.get("civilization_id")
            
            target_civ_val = race_id
            if (race_id is None or str(race_id) == "0") and civ_id_raw is not None:
                target_civ_val = civ_id_raw
                
            if target_civ_val is not None:
                 civ_id, civ_name = resolve_civ_from_player_data({"civilization": target_civ_val})
            else:
                 civ_id, civ_name = resolve_civ_from_player_data(r)

            team = r.get("teamid")
            
            # Improved Won/Loss Parsing
            won = None
            
            # 1. Try resulttype (numeric)
            if r.get("resulttype") is not None:
                won = RESULTTYPE_TO_WON.get(int(r.get("resulttype")))
            
            # 2. Try 'result' (string W/L/1/0)
            if won is None and r.get("result") is not None:
                res_val = r.get("result")
                if isinstance(res_val, str):
                    if res_val.upper() in ["W", "1"]: won = True
                    elif res_val.upper() in ["L", "0"]: won = False
                elif isinstance(res_val, (int, float)):
                    if int(res_val) == 1: won = True
                    elif int(res_val) in [0, 2]: won = False

            # Attempt to get rating from member_map (Preferred Source)
            rating_after = None
            rating_before = None
            
            mem_data = member_map.get(str(pid_int))
            if mem_data:
                rating_after = mem_data.get("newrating")
                rating_before = mem_data.get("oldrating")
                    
                # User reported mem_data might have result too?
                if won is None and mem_data.get("outcome") is not None: # Sometimes 'outcome' or 'result'
                     # Check mem_data 'result' if available
                     pass 
                
            # Fallback rating from report
            if rating_after is None:
                rating_after = r.get("new_rating")
            
            players.append(
                {
                    "profile_id": pid_int,
                    "civ": civ_name,
                    "civ_id": civ_id,
                    "team": int(team) if team is not None else None,
                    "won": won,
                    "name": r.get("_mapped_name"), 
                    "rating": rating_after, 
                    "rating_before": rating_before,
                    "rating_after": rating_after
                }
            )

        # Infer missing results based on team logic (NEW FIX)
        _infer_team_results(players)

        # Derived Flags Calculation
        unique_teams = set()
        max_team_size = 0
        team_sizes = {}
        
        has_rating_info = False
        
        for p in players:
            t = p.get("team")
            if t is not None:
                unique_teams.add(t)
                team_sizes[t] = team_sizes.get(t, 0) + 1
            
            # Check for rating presence
            if p.get("rating") is not None:
                has_rating_info = True

        player_count = len(players)
        team_count = len(unique_teams)
        if team_sizes:
            max_team_size = max(team_sizes.values())
        
        # is_ranked heuristic: if we have rating info OR ladder_type says Ranked
        # But user wants "derived", relying on data presence is safer.
        # Let's verify against ladder_type too if rating is missing for some reason but it is ranked.
        # Actually user said: "is_ranked (member’da rating delta var mı? oldrating/newrating dolu mu?)"
        # We already populate 'rating' in players list if found.
        is_ranked = has_rating_info
        
        # is_1v1: 2 players, 2 teams
        is_1v1 = (player_count == 2 and team_count == 2)
        
        # is_team_game: >2 players, 2 teams (standard team game), max_team_size > 1
        is_team_game = (player_count > 2 and team_count == 2 and max_team_size > 1)

        return {
            "id": match_id,
            "started_at": started_at,
            "ended_at": ended_at,
            "duration_seconds": max(0, int((ended_at - started_at).total_seconds())),
            "map_name": map_name_raw,
            "ladder_type": ladder_type,
            "players": players,
            "raw": stat,
            # Robust Flags
            "is_1v1": is_1v1,
            "is_team_game": is_team_game,
            "is_ranked": is_ranked,
            "player_count": player_count,
            "team_count": team_count
        }
    except Exception as e:
        logger.exception("Failed to parse match stat: %s", e)
        return None

def fetch_recent_matches_for_players(profile_ids: List[int], count: int = 10) -> List[Dict[str, Any]]:
    """fetch match history for a list of profile IDs."""
    if not profile_ids:
        return []
    
    url = f"{WORLDSEDGE_BASE_URL}/community/leaderboard/getRecentMatchHistory"
    
    results = []
    
    # Optimization: Iterate unique IDs.
    unique_ids = list(set(profile_ids))
    
    for pid in unique_ids:
        try:
            # Using POST with data payload (form-urlencoded)
            # API expects 'profile_ids' as a JSON-encoded string: profile_ids=[123]
            payload = {"title": TITLE, "profile_ids": json.dumps([int(pid)])}
            resp = requests.post(url, data=payload, timeout=5)
            
            LAST_HTTP["url"] = url + f" [POST data profile_ids={pid}]"
            LAST_HTTP["status_code"] = resp.status_code
            
            if resp.status_code == 200:
                data = resp.json()
                matches = data.get("matchHistoryStats", [])
                for m in matches:
                    parsed = _parse_match(m)
                    if parsed:
                        results.append(parsed)
            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error fetching for {pid}: {e}")
            
    return results

def resolve_players_bulk(profile_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """Resolve aliases/names for a list of profile IDs."""
    if not profile_ids:
        return {}
    
    url = f"{WORLDSEDGE_BASE_URL}/community/leaderboard/getPersonalStat"
    # POST with profile_ids
    # POST with profile_ids (as JSON string in form data)
    payload = {
        "title": TITLE,
        "profile_ids": json.dumps(profile_ids)
    }
    
    resolved = {}
    try:
        resp = requests.post(url, data=payload, timeout=5)
#         resp = requests.post(url, json=payload, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            # usually nested in statGroups
            groups = data.get("statGroups", [])
            for g in groups:
                 for m in g.get("members", []):
                     pid = m.get("profile_id")
                     if pid:
                         resolved[int(pid)] = {
                             "alias": m.get("alias"),
                             "country": m.get("country"),
                             "elo_rm_1v1": None, 
                         }
        return resolved
    except Exception as e:
        logger.error(f"Resolve bulk failed: {e}")
        return {}

def resolve_profile_from_steam_id(steam_id: str) -> Optional[Tuple[int, str]]:
    """Try to resolve SteamID64 to AoE Profile ID."""
    try:
        url = f"{WORLDSEDGE_BASE_URL}/community/leaderboard/getPersonalStat"
        steam_str = f"/steam/{steam_id}"
        
        # Use profile_names parameter with JSON string
        payload = {
            "title": TITLE,
            "profile_names": json.dumps([steam_str])
        }
        
        resp = requests.post(url, data=payload, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            groups = data.get("statGroups", [])
            for g in groups:
                for m in g.get("members", []):
                    # Check if this member matches our steam string (name field usually holds it)
                    # or simply take the first valid one if the API response is specific to our query
                    pid = m.get("profile_id")
                    if pid:
                         alias = m.get("alias")
                         return int(pid), alias
        return None
    except Exception as e:
        logger.error(f"Failed to resolve SteamID {steam_id}: {e}")
        return None

def _ensure_player(db: Session, aoe_profile_id: int, display_name: str = None, extra_data: dict = None) -> Player:
    p = db.query(Player).filter(Player.aoe_profile_id == aoe_profile_id).first()
    if not p:
        p = Player(
            player_id=str(aoe_profile_id),
            aoe_profile_id=aoe_profile_id,
            display_name=display_name or f"PID {aoe_profile_id}",
            added_at=None
        )
        db.add(p)
        db.flush()
    
    # Update logic
    if display_name and (not p.display_name or p.display_name.startswith("PID ")):
        p.display_name = display_name

    if extra_data:
        if extra_data.get("country"):
            p.country = extra_data["country"]
            
    return p

def process_matches(db: Session, tracked_profile_ids: List[int], matches_data: List[Dict[str, Any]]) -> Dict[str, int]:
    # ... (start of function same as before) ...
    tracked_set = set(int(x) for x in tracked_profile_ids or [])
    inserted_matches = 0
    inserted_match_players = 0
    backfilled_matches = 0

    # DEDUPLICATION: Matches might appear multiple times if fetched via multiple players
    # Keep only one instance per match ID
    unique_matches_data = []
    seen_match_ids = set()
    for m in matches_data:
        mid = str(m["id"])
        if mid not in seen_match_ids:
            seen_match_ids.add(mid)
            unique_matches_data.append(m)
            
    matches_data = unique_matches_data # Replace original list

    # --- REF DATA SYNC START ---
    # 0. Sync RefCiv and RefMap
    # Load existing refs
    existing_civs = {r.civ_id: r for r in db.query(RefCiv).all()}
    existing_maps = {r.map_name: r for r in db.query(RefMap).all()}
    
    # We need to collect all map names and civ IDs from batch
    batch_map_names = set()
    batch_civ_ids = set()
    
    for m in matches_data:
        m_name = m.get("map_name") or ""
        # Clean map name if needed, usually passed clean from _parse_match
        if m_name: batch_map_names.add(m_name)
        
        for p in m.get("players") or []:
            if p.get("civ_id") is not None:
                batch_civ_ids.add(p.get("civ_id"))
    
    # Sync Civs
    for cid in batch_civ_ids:
        if cid not in existing_civs:
            # Look up in mappings
            cname = CIV_ID_TO_NAME.get(cid, f"Unknown ({cid})")
            new_civ = RefCiv(civ_id=cid, civ_name=cname)
            db.add(new_civ)
            existing_civs[cid] = new_civ
            
    # Sync Maps
    for mname in batch_map_names:
        if mname and mname not in existing_maps:
            new_map = RefMap(map_name=mname)
            db.add(new_map)
            existing_maps[mname] = new_map
            
    db.flush() # Get IDs for new maps
    # --- REF DATA SYNC END ---

    # 1. Collect all unique profile IDs from the match batch (including opponents)
    all_participant_ids = set()
    for m in matches_data:
        for pl in m.get("players") or []:
            if pl.get("profile_id"):
                all_participant_ids.add(int(pl["profile_id"]))
    
    # 2. Batch resolve their aliases (real names) and expanded info
    # This ensures opponents get real names instead of PID...
    resolved_players = resolve_players_bulk(list(all_participant_ids))

    # 3. Pre-fetch existing players from DB to avoid N+1 and duplicate INSERTs
    existing_db_players = db.query(Player).filter(Player.aoe_profile_id.in_(all_participant_ids)).all()
    player_cache: Dict[int, Player] = {p.aoe_profile_id: p for p in existing_db_players}

    for m in matches_data:
        match_id = str(m["id"])
        newly_created = False

        match = db.query(Match).filter(Match.match_id == match_id).first()
        if not match:
            # ... (match creation logic same) ...
            # Resolve Map ID
            map_name_str = m.get("map_name") or ""
            ref_map_obj = existing_maps.get(map_name_str)
            resolved_map_id = ref_map_obj.map_id if ref_map_obj else None

            match = Match(
                match_id=match_id,
                started_at=m.get("started_at"),
                ended_at=m.get("ended_at"),
                duration_sec=m.get("duration_seconds"),
                map_name=map_name_str,
                map_id=resolved_map_id, # Store resolved ID
                ladder_type=m.get("ladder_type") or "unknown",
                # Robust Flags
                is_1v1=m.get("is_1v1", False),
                is_team_game=m.get("is_team_game", False),
                is_ranked=m.get("is_ranked", False),
                player_count=m.get("player_count", 0),
                team_count=m.get("team_count", 0),
            )
            db.add(match)
            db.flush()
            inserted_matches += 1
            newly_created = True
        else:
            # ... (match update logic same) ...
            if not match.started_at and m.get("started_at"):
                match.started_at = m.get("started_at")
            if not match.ended_at and m.get("ended_at"):
                match.ended_at = m.get("ended_at")
            if (match.duration_sec is None or match.duration_sec == 0) and m.get("duration_seconds"):
                match.duration_sec = m.get("duration_seconds")
            if (not match.map_name) and m.get("map_name"):
                match.map_name = m.get("map_name")
                
            # Update Map ID if missing or map name changed
            if not match.map_id and m.get("map_name"):
                ref_map = existing_maps.get(m.get("map_name"))
                if ref_map:
                    match.map_id = ref_map.map_id
            
            # Always update ladder_type if available (to fix "matchtype_6" issues)
            if m.get("ladder_type"):
                match.ladder_type = m.get("ladder_type")
            
            # Update Flags
            if m.get("player_count"): match.player_count = m.get("player_count")
            if m.get("team_count"): match.team_count = m.get("team_count")
            # Booleans - assign directly
            if "is_1v1" in m: match.is_1v1 = m["is_1v1"]
            if "is_team_game" in m: match.is_team_game = m["is_team_game"]
            if "is_ranked" in m: match.is_ranked = m["is_ranked"]

            db.add(match)

        # If we already have match players, skip (idempotent)
        existing_mp_map = {}
        existing_mps = db.query(MatchPlayer).filter(MatchPlayer.match_id == match_id).all()
        if existing_mps:
             existing_mp_map = {mp.aoe_profile_id: mp for mp in existing_mps}
             if not newly_created:
                 backfilled_matches += 1 


        for pl in m.get("players") or []:
            aoe_pid = int(pl["profile_id"])
            
            # Use resolved data
            r_data = resolved_players.get(aoe_pid) or {}
            resolved_alias = r_data.get("alias")
            match_alias = pl.get("name")
            
            p_name = resolved_alias or match_alias
            
            # Pass r_data as extra_data for enrichment
            # Use cache to prevent duplicate objects in session
            p_obj = player_cache.get(aoe_pid)
            if not p_obj:
                 # Create new and add to cache
                 p_obj = _ensure_player(db, aoe_profile_id=aoe_pid, display_name=p_name, extra_data=r_data)
                 player_cache[aoe_pid] = p_obj
            else:
                 # Manually trigger update logic if needed 
                 # We update if:
                 # 1. We have a new resolved name (p_name)
                 # 2. AND (Current name is empty, OR starts with "PID ", OR is just digits like "123456")
                 should_update = False
                 curr_name = p_obj.display_name
                 if p_name and p_name != curr_name:
                     if not curr_name:
                         should_update = True
                     elif curr_name.startswith("PID "):
                         should_update = True
                     elif curr_name.isdigit(): # Name is just the ID
                         should_update = True
                 
                 if should_update:
                     p_obj.display_name = p_name
                 
                 extra_data = r_data
                 if extra_data:
                    if extra_data.get("country"):
                        p_obj.country = extra_data["country"]
                    if extra_data.get("elo_rm_1v1") is not None:
                        p_obj.elo_rm_1v1 = extra_data["elo_rm_1v1"]
                    if extra_data.get("elo_rm_team") is not None:
                        p_obj.elo_rm_team = extra_data["elo_rm_team"]
                 db.add(p_obj)

            
            # Update last_match_at if this match is newer
            if m.get("started_at"):
                current_last = p_obj.last_match_at
                # If naive, assume UTC
                if current_last and current_last.tzinfo is None:
                    current_last = current_last.replace(tzinfo=timezone.utc)
                
                if not current_last or m["started_at"] > current_last:
                    p_obj.last_match_at = m["started_at"]
                    
                    # Update ELO from this match if it's the latest
                    rating = pl.get("rating")
                    if rating is not None:
                        ladder = m.get("ladder_type") or ""
                        # Simple heuristic for 1v1 vs Team
                        # Prioritize Ranked RM if possible, but for now update on any matching type
                        if "1v1" in ladder:
                            p_obj.elo_rm_1v1 = rating
                        elif "Team" in ladder or "2v2" in ladder or "3v3" in ladder or "4v4" in ladder:
                            p_obj.elo_rm_team = rating
                            
                    db.add(p_obj)

            if aoe_pid in existing_mp_map:
                # Update existing MatchPlayer if needed
                mp = existing_mp_map[aoe_pid]
                try:
                    changed = False
                    new_civ = str(pl.get("civ") or "Unknown")
                    if (not mp.civ_name or mp.civ_name == "Unknown") and new_civ != "Unknown":
                        mp.civ_name = new_civ
                        changed = True
                    
                    # Also update civ_id if missing
                    # pl.get("civ_id") comes from _parse_match
                    if mp.civ_id is None and pl.get("civ_id") is not None:
                        mp.civ_id = pl.get("civ_id")
                        changed = True
                    
                    new_rating_after = pl.get("rating_after")
                    if mp.elo_after is None and new_rating_after is not None:
                        mp.elo_after = new_rating_after
                        changed = True

                    new_rating_before = pl.get("rating_before")
                    if mp.elo_before is None and new_rating_before is not None:
                        mp.elo_before = new_rating_before
                        changed = True
                        
                    if changed:
                        db.add(mp)
                except Exception:
                    pass
            else:
                # Insert new MatchPlayer
                mp = MatchPlayer(
                    match_id=match_id,
                    aoe_profile_id=aoe_pid,
                    civ_name=str(pl.get("civ") or "Unknown"),
                    civ_id=pl.get("civ_id"), # NEW: Pass civ_id
                    team=pl.get("team"),
                    won=pl.get("won"),
                    result="W" if pl.get("won") is True else ("L" if pl.get("won") is False else None),
                    elo_after=pl.get("rating_after"),
                    elo_before=pl.get("rating_before"),
                )
                db.add(mp)
                # CRITICAL Fix: Update map so subsequent occurrences in same batch don't insert duplicate
                existing_mp_map[aoe_pid] = mp 
                inserted_match_players += 1
    
    db.commit()
    return {
        "inserted_matches": inserted_matches,
        "inserted_match_players": inserted_match_players,
        "backfilled_matches": backfilled_matches,
    }



def get_last_http() -> Dict[str, Any]:
    """Return the last WorldsEdgeLink request info (url/status_code) for debugging."""
    return dict(LAST_HTTP)
