
import streamlit as st
import pandas as pd
import sys
import os
import random
import math
from datetime import datetime, timedelta
from sqlalchemy import text, desc

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.components.sidebar import render_sidebar
from services.db.database import get_db
from services.db.models import Player, Match, MatchPlayer
from services.i18n import get_text

st.set_page_config(page_title="AOE2 League", layout="wide")

filters = render_sidebar()
lang = filters.get("language", "tr")

st.title(f"🏆 {get_text('league.title', lang)}")
st.markdown(get_text("league.desc", lang))

db = next(get_db())

# --- 1. Season Selection ---
col_sel1, col_sel2 = st.columns([1, 2])
with col_sel1:
    # Manual localization for selector options as they are values
    # Or map them back
    s_options = {
        "This Week": get_text("league.this_week", lang),
        "Last Week": get_text("league.last_week", lang), 
        "This Month": get_text("league.this_month", lang),
        "Last Month": get_text("league.last_month", lang),
        "All Time": get_text("league.all_time", lang)
    }
    # Reverse map for logic
    s_rev = {v: k for k, v in s_options.items()}
    
    selected_label = st.selectbox(get_text("league.season_duration", lang), list(s_options.values()))
    season_type = s_rev[selected_label]

# Determine date range
today = datetime.now()
start_date = None
end_date = None

if season_type == "This Week":
    # Start of week (Monday)
    start_date = today - timedelta(days=today.weekday())
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
elif season_type == "Last Week":
    # Start of last week
    start_date = today - timedelta(days=today.weekday() + 7)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=7)
elif season_type == "This Month":
    start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
elif season_type == "Last Month":
    # First day of this month
    this_month_start = today.replace(day=1)
    # Last day of prev month
    end_date = this_month_start - timedelta(days=1)
    start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

# Query Matches
tracked_players = db.query(Player).filter(Player.added_at.isnot(None)).all()
tracked_ids = [p.aoe_profile_id for p in tracked_players]
players_map = {p.aoe_profile_id: p for p in tracked_players}

if not tracked_ids:
    st.error(get_text("common.no_data", lang))
    st.stop()

# Build query
date_filter = ""
params = {} 

if start_date:
    date_filter += " AND m.started_at >= :start_date"
    params["start_date"] = start_date
if end_date:
    date_filter += " AND m.started_at < :end_date"
    params["end_date"] = end_date

# Safe integer injection for IN clause
ids_str = ",".join(str(pid) for pid in tracked_ids)

stmt = text(f"""
    SELECT 
        mp.aoe_profile_id,
        mp.won,
        mp.civ_name,
        m.match_id,
        m.map_name,
        m.duration_sec,
        m.started_at
    FROM matches m
    JOIN match_players mp ON m.match_id = mp.match_id
    WHERE mp.aoe_profile_id IN ({ids_str})
      AND m.is_1v1 = 1
      {date_filter}
""")

rows = db.execute(stmt, params).fetchall()

# Aggregation in Python
league_table = {}

# Initialize for ALL tracked players (so they appear with 0 games)
for pid in tracked_ids:
    league_table[pid] = {"p": 0, "w": 0, "l": 0, "pts": 0, "elo": 0, "name": ""}

# For Weekly Report
match_registry = {} # match_id -> {map, duration, date}
civ_wins = {} # civ_name -> count
map_counts = {} # map_name -> count

for r in rows:
    pid = r.aoe_profile_id
    won = r.won
    mid = r.match_id
    
    # League Table Logic
    if pid in league_table:
        league_table[pid]["p"] += 1
        if won:
            league_table[pid]["w"] += 1
            league_table[pid]["pts"] += 3
            # Civ Stats (Only wins for 'Weekly Civ')
            c = r.civ_name or "Unknown"
            civ_wins[c] = civ_wins.get(c, 0) + 1
        else:
            # Assuming loss
            league_table[pid]["l"] += 1
            # 0 pts
        
    # Match Registry (Deduplicate by ID)
    if mid not in match_registry:
        m_map = (r.map_name or "Unknown").replace(".rms", "")
        match_registry[mid] = {
            "map": m_map,
            "duration": r.duration_sec or 0,
            "date": r.started_at
        }
        map_counts[m_map] = map_counts.get(m_map, 0) + 1

# Enrich with names and Elo
for pid, stats in league_table.items():
    player = players_map.get(pid)
    if player:
        stats["name"] = player.display_name
        stats["elo"] = player.elo_rm_1v1 or 1000
    
# Convert to List and Sort
league_data = []
for pid, stats in league_table.items():
    stats["gd"] = stats["w"] - stats["l"]
    stats["pid"] = pid
    league_data.append(stats)

# Sorting: Points DESC, GD DESC, Wins DESC
league_data.sort(key=lambda x: (x["pts"], x["gd"], x["w"]), reverse=True)

# --- 2. WEEKLY REPORT & LEAGUE TABLE ---
st.subheader(f"📅 {get_text('league.league_table', lang)}: {selected_label}")

# Weekly Report Metrics
if match_registry:
    # 1. Map of Week
    best_map = max(map_counts, key=map_counts.get) if map_counts else "N/A"
    
    # 2. Civ of Week (Most Wins)
    best_civ = max(civ_wins, key=civ_wins.get) if civ_wins else "N/A"
    
    # 3. Match of Week (Longest)
    longest_match_id = max(match_registry, key=lambda k: match_registry[k]["duration"])
    longest_m = match_registry[longest_match_id]
    dur_fmt = f"{int(longest_m['duration']/60)} min"
    
    # Display Report
    with st.expander(f"📊 {get_text('league.summary', lang)}", expanded=True):
        c_r1, c_r2, c_r3 = st.columns(3)
        c_r1.metric(f"🗺️ {get_text('common.map', lang)}", best_map, f"{map_counts[best_map]} {get_text('common.games', lang)}")
        c_r2.metric(f"🛡️ {get_text('common.civ', lang)}", best_civ, f"{civ_wins[best_civ]} {get_text('common.wins', lang)}")
        c_r3.metric(f"⏳ {get_text('common.duration', lang)}", dur_fmt, f"{longest_m['map']}")

if not league_data:
    st.info(get_text("common.no_data", lang))
else:
    # Prepare DataFrame
    disp_data = []
    # Localize Headers
    h_rank = get_text("common.rank", lang)
    h_player = get_text("common.player", lang)
    h_pts = get_text("league.points", lang)
    
    for i, d in enumerate(league_data):
        disp_data.append({
            h_rank: i + 1,
            h_player: d["name"],
            "P": d["p"],
            "W": d["w"],
            "L": d["l"],
            "Av": d["gd"],
            h_pts: d["pts"],
            "ELO": d["elo"]
        })
        
    df = pd.DataFrame(disp_data)
    
    # Column Config
    st.dataframe(
        df.set_index(h_rank), 
        use_container_width=True,
        column_config={
            h_pts: st.column_config.NumberColumn(format="%d"),
            "Av": st.column_config.NumberColumn(get_text('league.average', lang), help="Win-Loss Difference", format="%d")
        }
    )

# --- 3. Playoff Simulation (Monte Carlo) ---
st.markdown("---")
st.subheader(f"🎲 {get_text('league.playoff_sim', lang)}")
st.markdown(get_text("league.playoff_desc", lang))

if len(league_data) >= 2:
    # Take top 4 (or top 2 if less)
    top_n = min(4, len(league_data))
    qualified = league_data[:top_n]
    
    # Simulation Parameters
    SIM_COUNT = 1000
    
    # Helper to calculate win probability
    # P(A wins) = 1 / (1 + 10^((Rb - Ra)/400))
    def get_win_prob(elo_a, elo_b):
        return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))
    
    champion_counts = {p["name"]: 0 for p in qualified}
    
    if top_n == 4:
        # Bracket: (1v4) -> W1, (2v3) -> W2. Final: W1 v W2
        p1 = qualified[0]
        p2 = qualified[1]
        p3 = qualified[2]
        p4 = qualified[3]
        
        for _ in range(SIM_COUNT):
            # Semi 1: 1 vs 4
            prob14 = get_win_prob(p1["elo"], p4["elo"])
            winner_s1 = p1 if random.random() < prob14 else p4
            
            # Semi 2: 2 vs 3
            prob23 = get_win_prob(p2["elo"], p3["elo"])
            winner_s2 = p2 if random.random() < prob23 else p3
            
            # Final
            prob_final = get_win_prob(winner_s1["elo"], winner_s2["elo"])
            champion = winner_s1 if random.random() < prob_final else winner_s2
            
            champion_counts[champion["name"]] += 1
            
    elif top_n == 3:
        # 3 players case -> Fallback to Top 2 or warn
        st.warning(get_text("league.warn_3players", lang))
        top_n = 2
        
    if top_n == 2:
        p1 = qualified[0]
        p2 = qualified[1]
        
        for _ in range(SIM_COUNT):
            prob = get_win_prob(p1["elo"], p2["elo"])
            winner = p1 if random.random() < prob else p2
            champion_counts[winner["name"]] += 1

    # Visualization
    sim_results = []
    
    col_player = get_text("common.player", lang)
    col_prob = get_text("league.win_prob", lang)
    
    for name, wins in champion_counts.items():
        sim_results.append({col_player: name, col_prob: (wins/SIM_COUNT)*100})
        
    df_sim = pd.DataFrame(sim_results).sort_values(col_prob, ascending=False)
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.bar_chart(df_sim.set_index(col_player))
    with c2:
        st.dataframe(df_sim.style.format({col_prob: "{:.1f}%"}), use_container_width=True)
        st.caption(get_text("league.sim_caption", lang).format(n=SIM_COUNT))

else:
    st.warning(get_text("common.no_data", lang))
