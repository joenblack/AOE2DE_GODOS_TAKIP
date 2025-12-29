
import streamlit as st
import pandas as pd
import sys
import os
from sqlalchemy import text
from itertools import combinations
import math

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.components.sidebar import render_sidebar
from services.db.database import get_db
from services.db.models import Player, Match, MatchPlayer
from services.i18n import get_text

st.set_page_config(page_title="Team Synergy", layout="wide")

filters = render_sidebar()
lang = filters.get("language", "tr")

st.title(f"🤝 {get_text('sidebar.synergy', lang)}")
st.markdown(get_text("synergy.desc", lang))
st.caption(get_text("synergy.caption", lang))

db = next(get_db())

# UI Controls
min_games = st.sidebar.slider(get_text("synergy.min_games", lang), min_value=2, max_value=50, value=3)

def wilson_score_interval(wins, n, confidence=0.95):
    """
    Calculate Wilson Score Interval for a binomial proportion.
    Returns (lower_bound, upper_bound) as percentages.
    """
    if n == 0:
        return 0.0, 0.0

    z = 1.96 # approx for 95% confidence
    p = wins / n
    
    denominator = 1 + z**2/n
    center_adjusted_probability = p + z**2 / (2*n)
    adjusted_standard_deviation = z * math.sqrt((p*(1-p) + z**2/(4*n)) / n)
    
    lower_bound = (center_adjusted_probability - adjusted_standard_deviation) / denominator
    upper_bound = (center_adjusted_probability + adjusted_standard_deviation) / denominator
    
    return lower_bound * 100, upper_bound * 100


# 1. Fetch Data
# We need Team Games (Not 1v1)
# We need tracked players
tracked_players = db.query(Player).filter(Player.added_at.isnot(None)).all()
tracked_pids = {p.aoe_profile_id: (p.display_name or str(p.aoe_profile_id)) for p in tracked_players}
tracked_pid_set = set(tracked_pids.keys())

if len(tracked_pid_set) < 2:
    st.warning(get_text('synergy.min_games_warning', lang))
    st.stop()

ids_str = ",".join(str(pid) for pid in tracked_pid_set)

if not ids_str:
    ids_str = "NULL"

stmt = text(f"""
    SELECT 
        m.match_id,
        mp.aoe_profile_id,
        mp.team,
        mp.won,
        m.ladder_type
    FROM matches m
    JOIN match_players mp ON m.match_id = mp.match_id
    WHERE mp.aoe_profile_id IN ({ids_str})
      AND m.is_team_game = 1 
      AND m.started_at IS NOT NULL
      AND mp.team IS NOT NULL
""")

rows = db.execute(stmt).fetchall()

# Process in Python
match_teams = {} 
indiv_stats = {pid: {"games": 0, "wins": 0} for pid in tracked_pid_set}

for r in rows:
    pid = r.aoe_profile_id
    tid = r.team
    mid = r.match_id
    won = r.won
    
    # Update Indiv Stats
    indiv_stats[pid]["games"] += 1
    if won:
        indiv_stats[pid]["wins"] += 1
        
    if mid not in match_teams:
        match_teams[mid] = {}
    
    if tid not in match_teams[mid]:
        match_teams[mid][tid] = {"players": [], "won": won}
    
    match_teams[mid][tid]["players"].append(pid)

# Mode Selector
mode_options = {
    get_text("synergy.mode_general", lang): "general",
    get_text("synergy.mode_internal", lang): "internal"
}

# Default to Internal as requested ("Aktif Lobi olsun" implies importance, but usually General is default. Let's make Internal default if user emphasized it, or General standard. User said "seçilene göre". I'll default to General as it has more data usually.)
# Actually user said: "Oyuncuların birbirlerine karşı olan duolarının ismi 'AKTİF LOBİ' olsun".
# I'll add the radio button.
# Should be visible in main area
selected_mode_label = st.radio(get_text("synergy.mode_title", lang), list(mode_options.keys()), horizontal=True)
selected_mode = mode_options[selected_mode_label]

# 2. Extract Duos
duo_stats = {} 

for mid, teams in match_teams.items():
    # Filter based on Mode
    # Internal: Match has > 1 team with tracked players (meaning tracked players vs tracked players)
    # General: Match has only 1 team with tracked players (tracked vs randoms)
    is_internal = len(teams) > 1
    
    if selected_mode == "internal" and not is_internal:
        continue
    if selected_mode == "general" and is_internal:
        continue

    for tid, info in teams.items():

        p_list = sorted(list(set(info["players"]))) 
        is_won = info["won"]
        
        if len(p_list) < 2:
            continue
            
        for p1, p2 in combinations(p_list, 2):
            key = (p1, p2)
            if key not in duo_stats:
                duo_stats[key] = {"games": 0, "wins": 0}
            
            duo_stats[key]["games"] += 1
            if is_won:
                duo_stats[key]["wins"] += 1

# 3. Calculate Synergy
synergy_list = []

col_duo = get_text("synergy.duo", lang)
col_games = get_text("common.games", lang)
col_wins = get_text("common.wins", lang)
col_actual_wr = get_text("synergy.actual_wr", lang)
col_exp_wr = get_text("synergy.expected_wr", lang)
col_score = get_text("synergy.score", lang)

for (p1, p2), stats in duo_stats.items():
    games = stats["games"]
    if games < min_games: 
        continue
        
    wins = stats["wins"]
    actual_wr = (wins / games) * 100
    
    # Calculate Confidence Interval (95%)
    ci_low, ci_high = wilson_score_interval(wins, games)
    margin_of_error = (ci_high - ci_low) / 2
    
    p1_indiv = indiv_stats[p1]
    p2_indiv = indiv_stats[p2]
    
    p1_wr = (p1_indiv["wins"] / p1_indiv["games"] * 100) if p1_indiv["games"] > 0 else 50
    p2_wr = (p2_indiv["wins"] / p2_indiv["games"] * 100) if p2_indiv["games"] > 0 else 50
    
    expected_wr = (p1_wr + p2_wr) / 2
    
    synergy_score = actual_wr - expected_wr
    
    synergy_list.append({
        col_duo: f"{tracked_pids[p1]} & {tracked_pids[p2]}",
        col_games: games,
        col_wins: wins,
        # col_actual_wr: actual_wr, # Replaced by string with CI
        "WR_Value": actual_wr, # Keep numeric for sorting
        col_actual_wr: f"{actual_wr:.1f}% ±{margin_of_error:.1f}%",
        col_exp_wr: expected_wr,
        col_score: synergy_score
    })

# 4. Display
if not synergy_list:
    st.info(get_text("common.no_data", lang))
else:
    df = pd.DataFrame(synergy_list)
    
    st.subheader(f"🌟 {get_text('synergy.top_synergy', lang)}")
    df_sorted = df.sort_values(col_score, ascending=False)
    
    # Hide WR_Value from display
    display_cols = [col_duo, col_games, col_wins, col_actual_wr, col_exp_wr, col_score]
    
    st.dataframe(
        df_sorted[display_cols].style.format({
            # col_actual_wr: "{:.1f}%", # Now a string
            col_exp_wr: "{:.1f}%",
            col_score: "{:+.1f}"
        }).background_gradient(subset=[col_score], cmap="RdYlGn", vmin=-20, vmax=20),
        use_container_width=True
    )
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### 🔥 {get_text('synergy.highest_wr', lang)}")
        # Sort by numeric WR_Value
        st.dataframe(
            df.sort_values("WR_Value", ascending=False).head(5)[[col_duo, col_actual_wr, col_games]],
            use_container_width=True
        )
        
    with col2:
        st.markdown(f"### 🧊 {get_text('synergy.lowest_wr', lang)}")
        st.dataframe(
            df.sort_values("WR_Value", ascending=True).head(5)[[col_duo, col_actual_wr, col_games]],
            use_container_width=True
        )

# --- ROLE / COMPOSITION ANALYSIS ---
st.markdown("---")
st.subheader(f"🛡️ {get_text('synergy.comp_analysis', lang)}")
st.caption(get_text("synergy.role_analysis", lang))

CIV_ROLES = {
    "Britons": "Archer", "Mayans": "Archer", "Ethiopians": "Archer", "Vietnamese": "Archer", "Koreans": "Archer",
    "Franks": "Cavalry", "Magyars": "Cavalry", "Lithuanians": "Cavalry", "Huns": "Cavalry", "Persians": "Cavalry",
    "Berbers": "Cavalry", "Poles": "Cavalry", "Burgundians": "Cavalry",
    "Goths": "Infantry", "Celts": "Infantry", "Japanese": "Infantry", "Vikings": "Infantry", "Teutons": "Infantry",
    "Aztecs": "Infantry" , "Incas": "Infantry", "Slavs": "Infantry", "Romans": "Infantry", "Dravidians": "Infantry",
    "Spanish": "Conquistador (Cav)", "Turks": "Gunpowder", "Portuguese": "Gunpowder", "Hindustanis": "Camel",
    "Gurjaras": "Camel", "Saracens": "Camel/Archer", "Byzantines": "Defensive", "Khmers": "Boom/Cav",
    "Malay": "Archer/Inf", "Mongols": "Mangudai (Cav Archer)", "Tatars": "Cav Archer", "Cumans": "Cavalry",
    "Bohemians": "Gunpowder", "Bengalis": "Elephant", "Burmese": "Monk/Inf", "Sicilians": "Cavalry",
    "Malians": "Infantry/Cav", "Chinese": "Jack-of-all-trades", "Italians": "Archer/Naval",
    "Armenians": "Infantry/Naval", "Georgians": "Cavalry"
}

comp_stats = {}

# Re-query with Civs for Composition
stmt_comp = text(f"""
    SELECT 
        m.match_id,
        mp.team,
        mp.civ_name,
        mp.won
    FROM matches m
    JOIN match_players mp ON m.match_id = mp.match_id
    WHERE mp.aoe_profile_id IN ({ids_str})
      AND m.is_team_game = 1 
      AND m.started_at IS NOT NULL
""")

rows_comp = db.execute(stmt_comp).fetchall()

team_civs = {} 

for r in rows_comp:
    mid = r.match_id
    tid = r.team
    civ = r.civ_name
    won = r.won
    
    if mid not in team_civs: team_civs[mid] = {}
    if tid not in team_civs[mid]: team_civs[mid][tid] = {"civs": [], "won": won}
    
    team_civs[mid][tid]["civs"].append(civ)

role_stats = {}

for mid, teams_in_match in team_civs.items():
    for tid, info in teams_in_match.items():
        civs = info["civs"]
        if len(civs) < 2: continue
        
        roles = []
        for c in civs:
            role = CIV_ROLES.get(c, "Flexible")
            roles.append(role)
        
        for r1, r2 in combinations(roles, 2):
            key = tuple(sorted([r1, r2]))
            if key not in role_stats: role_stats[key] = {"games": 0, "wins": 0}
            role_stats[key]["games"] += 1
            if info["won"]:
                role_stats[key]["wins"] += 1

comp_list = []
col_comp = get_text("synergy.composition", lang)
col_win_rate = get_text("common.win_rate", lang)

for (r1, r2), stats in role_stats.items():
    g = stats["games"]
    if g < 5: continue 
    
    wr = (stats["wins"] / g) * 100
    comp_list.append({
        col_comp: f"{r1} + {r2}",
        col_games: g,
        col_win_rate: wr
    })

if comp_list:
    df_comp = pd.DataFrame(comp_list).sort_values(col_win_rate, ascending=False)
    
    c_best, c_metrics = st.columns([2, 1])
    
    with c_best:
        st.dataframe(
            df_comp.style.format({col_win_rate: "{:.1f}%"}).background_gradient(subset=[col_win_rate], cmap="RdYlGn"),
            use_container_width=True
        )
    
    with c_metrics:
        best_combo = df_comp.iloc[0]
        st.success(f"🏆 **{get_text('synergy.best_combo', lang)}:**\n\n{best_combo[col_comp]}\n\n({best_combo[col_win_rate]:.1f}% {get_text('synergy.avg', lang)})")
        
        if len(df_comp) > 1:
            worst_combo = df_comp.iloc[-1]
            st.error(f"⚠️ **{get_text('synergy.weakest_combo', lang)}:**\n\n{worst_combo[col_comp]}\n\n({worst_combo[col_win_rate]:.1f}% {get_text('synergy.avg', lang)})")

else:
    st.info(get_text("common.no_data", lang))
