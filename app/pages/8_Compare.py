
import streamlit as st
import pandas as pd
import sys
import os
from sqlalchemy import text
from services.db.database import get_db
from services.db.models import Player, Match, MatchPlayer

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.components.sidebar import render_sidebar
# from app.components.charts import plot_civ_win_rates # Not used?
from services.i18n import get_text

st.set_page_config(page_title="Compare Players", layout="wide")

filters = render_sidebar()
lang = filters.get("language", "tr")

st.title(f"⚖️ {get_text('compare.title', lang)}")
st.markdown(get_text("compare.desc", lang))

db = next(get_db())

# 1. Select Two Players
players = db.query(Player).filter(Player.added_at.isnot(None)).all()
p_map = {(p.display_name or str(p.aoe_profile_id)): p for p in players}
p_names = list(p_map.keys())

if len(p_names) < 2:
    st.warning("Need at least 2 tracked players.")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    p1_name = st.selectbox(get_text("rivalry.player_a", lang), p_names, index=0)
with col2:
    p2_name = st.selectbox(get_text("rivalry.player_b", lang), p_names, index=1 if len(p_names)>1 else 0)

if p1_name == p2_name:
    st.info(get_text("rivalry.select_players", lang))
    st.stop()

p1 = p_map[p1_name]
p2 = p_map[p2_name]

# 2. Fetch Aggregated Stats (Global)
# We can reuse queries from Profile page but tailored for side-by-side.
# Metrics: Current 1v1 ELO, Team ELO, Total 1v1 Games, Win Rate, Best Civ, Best Map.

def get_player_summary(pid):
    # ELO & Games
    # Fetch 1v1 stats
    stmt = text("""
        SELECT 
            count(*) as games,
            sum(case when mp.won = 1 then 1 else 0 end) as wins,
            avg(case when mp.won = 1 then 1 else 0 end) as win_rate
        FROM matches m
        JOIN match_players mp ON m.match_id = mp.match_id
        WHERE mp.aoe_profile_id = :pid
          AND m.is_1v1 = 1
    """)
    res = db.execute(stmt, {"pid": pid}).first()
    
    # Best Civ
    stmt_civ = text("""
        SELECT civ_name, count(*) as cnt 
        FROM match_players
        WHERE aoe_profile_id = :pid AND won = 1
        GROUP BY civ_name
        ORDER BY cnt DESC LIMIT 1
    """)
    res_civ = db.execute(stmt_civ, {"pid": pid}).first()
    best_civ = res_civ.civ_name if res_civ else "N/A"
    
    return {
        "games": res.games,
        "wr": (res.win_rate or 0) * 100,
        "best_civ": best_civ
    }

s1 = get_player_summary(p1.aoe_profile_id)
s2 = get_player_summary(p2.aoe_profile_id)

# 3. Display Comparison
st.divider()

c1, c2, c3 = st.columns([1, 0.2, 1])

with c1:
    st.markdown(f"### {p1_name}")
    st.metric(get_text("profile.stats.current_elo", lang), p1.elo_rm_1v1 or "N/A", delta=f"{p1.elo_rm_1v1 - (p2.elo_rm_1v1 or 0)}" if p1.elo_rm_1v1 and p2.elo_rm_1v1 else None)
    st.metric(get_text("common.win_rate", lang), f"{s1['wr']:.1f}%", f"{s1['games']} {get_text('common.games', lang)}")
    st.metric(get_text("profile.stats.best_civ", lang), s1['best_civ'])

with c2:
    st.markdown("<h2 style='text-align: center;'>VS</h2>", unsafe_allow_html=True)

with c3:
    st.markdown(f"### {p2_name}")
    st.metric(get_text("profile.stats.current_elo", lang), p2.elo_rm_1v1 or "N/A", delta=f"{p2.elo_rm_1v1 - (p1.elo_rm_1v1 or 0)}" if p2.elo_rm_1v1 and p1.elo_rm_1v1 else None)
    st.metric(get_text("common.win_rate", lang), f"{s2['wr']:.1f}%", f"{s2['games']} {get_text('common.games', lang)}")
    st.metric(get_text("profile.stats.best_civ", lang), s2['best_civ'])

st.divider()

# Comparative Charts
# Civ Pools
# Fetch top 5 civs for both
stmt_top_civs = text("""
    SELECT 
        civ_name, 
        count(*) as games, 
        sum(case when won=1 then 1 else 0 end) as wins,
        (sum(case when won=1 then 1.0 else 0.0 end) / count(*) * 100) as win_rate
    FROM match_players mp
    JOIN matches m ON m.match_id = mp.match_id
    WHERE mp.aoe_profile_id = :pid
    GROUP BY civ_name
    HAVING games >= 10
    ORDER BY win_rate DESC
    LIMIT 5
""")

def get_top_civs(pid):
    rows = db.execute(stmt_top_civs, {"pid": pid}).fetchall()
    return pd.DataFrame(rows, columns=["Civ", "Games", "Wins", "win_rate"])

df1 = get_top_civs(p1.aoe_profile_id)
df2 = get_top_civs(p2.aoe_profile_id)

st.subheader(f"🛡️ {get_text('compare.most_played_civs', lang)}")
cc1, cc2 = st.columns(2)
with cc1:
    if not df1.empty:
        # Win Rate is already calculated in SQL as "win_rate"
        st.bar_chart(df1.set_index("Civ")["win_rate"], color="#4CAF50")
    else:
        st.info(get_text("common.no_data", lang))

with cc2:
    if not df2.empty:
        st.bar_chart(df2.set_index("Civ")["win_rate"], color="#FF5722")
    else:
        st.info(get_text("common.no_data", lang))

# Insight: Who is the specialist?
# Simply check unique civ played count?
