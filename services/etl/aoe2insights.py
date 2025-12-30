import logging
import time
import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup

from services.mappings import CIV_ID_TO_NAME

logger = logging.getLogger(__name__)

BASE_URL = "https://www.aoe2insights.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Reverse mapping for Civ Name -> ID
CIV_NAME_TO_ID = {v.lower(): k for k, v in CIV_ID_TO_NAME.items()}

def parse_duration(dur_str: str) -> int:
    """Parse '1:23:45' or '23:45' into seconds."""
    if not dur_str: return 0
    parts = list(map(int, dur_str.split(':')))
    if len(parts) == 3:
        return parts[0]*3600 + parts[1]*60 + parts[2]
    elif len(parts) == 2:
        return parts[0]*60 + parts[1]
    return 0

def fetch_full_match_history(profile_id: int, max_pages: int = 100, known_match_ids: set = None) -> List[Dict[str, Any]]:
    """
    Scrape full match history from aoe2insights.com for a given profile_id.
    Returns specific parsed match objects compatible with services.etl.fetcher.process_matches.
    """
    logger.info(f"Starting full history backfill for Profile ID: {profile_id}")
    
    matches_out = []
    page = 1
    
    # Try direct URL assuming Profile ID matches aoe2insights User ID (validated via probe)
    # URL Format: https://www.aoe2insights.com/user/{id}/matches
    
    while page <= max_pages:
        url = f"{BASE_URL}/user/{profile_id}/matches/?page={page}"
        logger.info(f"Fetching page {page}: {url}")
        
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            logger.info(f"Response URL: {resp.url} Status: {resp.status_code}")
            if resp.status_code == 404:
                logger.warning(f"Page {page} not found or user not found. Stopping.")
                break
            if resp.status_code != 200:
                logger.error(f"Failed to fetch page {page}: Status {resp.status_code}")
                break
            
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Find all match tiles
            tiles = soup.find_all('div', class_=['match-summary-card', 'match-tile'])
            logger.info(f"Found {len(tiles)} match tiles.")
            
            if not tiles:
                logger.info("No match tiles found.")
                break
                
            for tile in tiles:
                try:
                    # 1. Match ID
                    link = tile.find('a', class_='stretched-link')
                    if not link: continue
                    match_id_match = re.search(r'/match/(\d+)', link['href'])
                    if not match_id_match: continue
                    match_id = int(match_id_match.group(1))
                    
                    # --- OPTIMIZATION: Stop if match already exists ---
                    # --- OPTIMIZATION: Stop if match already exists ---
                    if known_match_ids and match_id in known_match_ids:
                        logger.info(f"Match {match_id} already exists. Stopping fetch early (User requested optimization).")
                        # We found a match we already have. Assuming chronological order (newest first),
                        # everything after this is also old. So we can stop.
                        return matches_out
                        
                    
                    # 2. Ladder / Type (Map 1v1, RM Team etc)
                    # Old: div.ladder-type
                    # New: inside the stretched-link -> strong -> em -> text
                    ladder_text = "Unknown"
                    ladder_div = tile.find('div', class_='ladder-type')
                    if ladder_div:
                        # Old logic
                        icon = ladder_div.find('i')
                        if icon and icon.next_sibling:
                            ladder_text = icon.next_sibling.strip()
                        else:
                            ladder_text = ladder_div.get_text(strip=True)
                    else:
                        # New logic: Extracts text from the link itself
                        # Usually "RM 1v1" or similar
                        text = link.get_text(" ", strip=True)
                        ladder_text = text.strip()
                    
                    # 3. Map Name
                    map_name = "Unknown"
                    # Inspect column 1 for map name in new layout
                    col1 = tile.find('div', class_='col-md-3')
                    if col1:
                        flex_col = col1.find('div', class_='d-flex flex-column')
                        if flex_col:
                            divs = flex_col.find_all('div', recursive=False)
                            if len(divs) > 1:
                                map_name = divs[1].get_text(strip=True)
                    
                    # 3. Time / Duration
                    duration_sec = 0
                    # Default to 1970 to push failed parses to the bottom of the list instead of "just now"
                    date_val = datetime(1970, 1, 1, tzinfo=timezone.utc)
                    
                    clock_icon = tile.find('i', class_='fa-clock')

                    if clock_icon:
                         dur_text = clock_icon.parent.get_text().strip() # "92m 56s"
                         # Parse "Xm Ys" or "Xh Ym"
                         parts = re.findall(r'(\d+)([hms])', dur_text)
                         d_sec = 0
                         for val, unit in parts:
                             if unit == 'h': d_sec += int(val) * 3600
                             elif unit == 'm': d_sec += int(val) * 60
                             elif unit == 's': d_sec += int(val)
                         duration_sec = d_sec
                    
                    # Date from tooltip
                    # Look for span with title inside the info block
                    date_span = tile.find('span', title=True)
                    if date_span:
                        date_str = date_span['title']
                        # Format: "Dec. 28, 2025, 11:08 p.m."
                        # 1. Normalize AM/PM
                        date_str_clean = date_str.lower().replace("p.m.", "PM").replace("a.m.", "AM").replace("pm", "PM").replace("am", "AM")
                        # 2. Remove dots from month (Dec. -> Dec)
                        # Be careful not to break other things, but simple replace of . should be fine if no other dots matter.
                        # Actually timestamp has comma.
                        date_str_clean = date_str_clean.replace(".", "")
                        
                        # Try parsing
                        try:
                            # Simple month map for English scrap
                            MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, 
                                      "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
                            
                            parts = re.split(r'[ ,:]+', date_str_clean)
                            # Expected: ['dec', '28', '2025', '11', '08', 'PM']
                            # Filter empty strings
                            parts = [p for p in parts if p]
                            
                            if len(parts) >= 6:
                                mon_str = parts[0][:3].lower()
                                if mon_str in MONTHS:
                                    mon = MONTHS[mon_str]
                                    day = int(parts[1])
                                    year = int(parts[2])
                                    hr = int(parts[3])
                                    mn = int(parts[4])
                                    ampm = parts[5].upper()
                                    
                                    if ampm == 'PM' and hr != 12: hr += 12
                                    if ampm == 'AM' and hr == 12: hr = 0
                                    
                                    date_val = datetime(year, mon, day, hr, mn, 0, tzinfo=timezone.utc)

                            elif len(parts) == 5:
                                # Case: Jan 6, 2023, 8 PM (No minutes)
                                mon_str = parts[0][:3].lower()
                                if mon_str in MONTHS:
                                    mon = MONTHS[mon_str]
                                    day = int(parts[1])
                                    year = int(parts[2])
                                    hr = int(parts[3])
                                    mn = 0
                                    ampm = parts[4].upper()
                                    
                                    if ampm == 'PM' and hr != 12: hr += 12
                                    if ampm == 'AM' and hr == 12: hr = 0
                                    
                                    date_val = datetime(year, mon, day, hr, mn, 0, tzinfo=timezone.utc)

                            else:
                                 # Fallback to strptime if regex split fails
                                 date_val = datetime.strptime(date_str_clean, "%b %d, %Y, %I:%M %p").replace(tzinfo=timezone.utc)
                                 
                        except Exception as e:
                            logger.warning(f"Date parse failed for '{date_str}': {e}")
                            pass

                    
                    # 4. Players & Teams
                    players_list = []
                    teams_col = tile.find('div', class_='teams')
                    if teams_col:
                        team_uls = teams_col.find_all('ul', class_='team')
                        for t_idx, ul in enumerate(team_uls):
                            team_num = t_idx + 1
                            is_winner = 'won' in ul.get('class', [])
                            
                            lis = ul.find_all('li')
                            for li in lis:
                                p_div = li.find('div', class_='team-player')
                                if not p_div: continue
                                
                                # Name & ID
                                p_link = p_div.find('a')
                                if not p_link: continue
                                p_name = p_link.get_text().strip()
                                p_href = p_link['href']
                                p_id_match = re.search(r'/user/(\d+)', p_href)
                                if not p_id_match: continue
                                p_pid = int(p_id_match.group(1))
                                
                                # Civ
                                civ_name = "Unknown"
                                civ_id = None
                                civ_icon = p_div.find('i', class_='image-icon')
                                if civ_icon and civ_icon.get('title'):
                                    civ_name = civ_icon['title'].strip()
                                    if civ_name.lower() in CIV_NAME_TO_ID:
                                        civ_id = CIV_NAME_TO_ID[civ_name.lower()]
                                
                                    if civ_name.lower() in CIV_NAME_TO_ID:
                                        civ_id = CIV_NAME_TO_ID[civ_name.lower()]
                                
                                # Rating
                                rating = None
                                rat_small = p_div.find('small', class_='rating')
                                if rat_small:
                                    # Look for direct text or first span
                                    # Usually <span>1606</span>
                                    # If spans exist, use first one
                                    spans = rat_small.find_all('span')
                                    rating_txt = ""
                                    if spans:
                                        rating_txt = spans[0].get_text()
                                    else:
                                        # Fallback to direct text if no spans
                                        rating_txt = rat_small.get_text()
                                    
                                    # Clean up
                                    rating_txt = rating_txt.strip().replace('#', '')
                                    try:
                                        rating = int(rating_txt)
                                    except:
                                        pass

                                
                                players_list.append({
                                    "profile_id": p_pid,
                                    "civ": civ_name,
                                    "civ_id": civ_id,
                                    "team": team_num,
                                    "won": is_winner,
                                    "name": p_name,
                                    "rating": rating,
                                    "rating_after": rating, # Assume shown is resulting elo
                                    "rating_before": None # Can infer if delta present
                                })
                    
                    player_count = len(players_list)
                    unique_teams = set(p['team'] for p in players_list)
                    team_count = len(unique_teams)
                    
                    is_1v1 = (player_count == 2 and team_count == 2)
                    is_team = (player_count > 2 and team_count == 2)
                    
                    ladder_guess = "Random Map"
                    if is_1v1: ladder_guess = "RM 1v1"
                    elif is_team: ladder_guess = "RM Team"
                    
                    # Construct Match Object
                    match_obj = {
                        "id": match_id,
                        "started_at": date_val,
                        "ended_at": date_val + timedelta(seconds=duration_sec),
                        "duration_seconds": duration_sec,
                        "map_name": map_name,
                        "ladder_type": ladder_guess,
                        "is_1v1": is_1v1,
                        "is_team_game": is_team,
                        "is_ranked": True, # Assume ranked default
                        "player_count": player_count,
                        "team_count": team_count,
                        "players": players_list
                    }
                    
                    matches_out.append(match_obj)
                    
                except Exception as row_e:
                    logger.warning(f"Error parsing match tile: {row_e}")
                    continue



            
            page += 1
            time.sleep(1) # Polite delay
            
        except Exception as e:
            logger.error(f"Error scraping aoe2insights: {e}")
            break
            
    logger.info(f"Scraped {len(matches_out)} matches total.")
    return matches_out
