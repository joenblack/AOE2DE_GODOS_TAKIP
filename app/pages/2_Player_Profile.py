import streamlit as st
import sys
import os
import pandas as pd
import math
from datetime import datetime, timedelta
from sqlalchemy import text

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.components.sidebar import render_sidebar
from app.components.charts import plot_civ_win_rates
from services.db.database import get_db
from services.db.models import Player, Match, MatchPlayer
from services.i18n import get_text

st.set_page_config(page_title="Player Profile", layout="wide")

filters = render_sidebar()
lang = filters.get("language", "tr")

st.title(f"👤 {get_text('sidebar.profile', lang)}")
st.markdown(get_text("profile.subtitle", lang))

db = next(get_db())

# --- HELPER: Wilson Score Interval ---
def wilson_score_interval(wins, n, z=1.96):
    """
    Calculate Wilson Score Interval for Binomial Proportion.
    z=1.96 for 95% confidence.
    Returns (lower_bound, upper_bound, margin_of_error_percent)
    """
    if n == 0: return 0, 0, 0
    p = wins / n
    
    denominator = 1 + z**2/n
    center_adjusted_probability = p + z**2 / (2*n)
    adjusted_standard_deviation = math.sqrt((p*(1 - p) + z**2 / (4*n)) / n)
    
    lower_bound = (center_adjusted_probability - z * adjusted_standard_deviation) / denominator
    upper_bound = (center_adjusted_probability + z * adjusted_standard_deviation) / denominator
    
    # Margin of error approx for display (half width)
    moe = (upper_bound - lower_bound) / 2
    return lower_bound, upper_bound, moe * 100

# --- 1. Select Player & Filters ---
col_p, col_mode, col_time = st.columns([2, 1, 1])

players = db.query(Player).filter(Player.added_at.isnot(None)).all()
player_map = {(p.display_name or str(p.aoe_profile_id)): p for p in players}

with col_p:
    selected_name = st.selectbox(get_text("profile.select_player", lang), options=list(player_map.keys()))

with col_mode:
    ladder_mode = st.selectbox(get_text("filter.ladder", lang), ["Ranked 1v1", "Team Games", "Empire Wars", "Unranked/Lobby", "All"])

with col_time:
    time_filter = st.selectbox(get_text("filter.time_period", lang), ["All Time", "Last 30 Days", "Last 90 Days", "Last 6 Months"])

if not selected_name:
    st.info(get_text("profile.select_player", lang))
    st.stop()

player = player_map[selected_name]
pid = player.aoe_profile_id

# Build Query filters
ladder_sql = ""
if ladder_mode == "Ranked 1v1":
    ladder_sql = "AND m.is_1v1 = 1 AND m.is_ranked = 1"
elif ladder_mode == "Team Games":
    ladder_sql = "AND m.is_team_game = 1"
elif ladder_mode == "Empire Wars":
    ladder_sql = "AND m.ladder_type LIKE '%ew%'"
elif ladder_mode == "Unranked/Lobby":
    ladder_sql = "AND m.ladder_type LIKE '%lobby%'"
# 'All' adds no filter

date_sql = ""
params = {"pid": pid}
now = datetime.now()

if time_filter == "Last 30 Days":
    date_sql = "AND m.started_at >= :start_date"
    params["start_date"] = now - timedelta(days=30)
elif time_filter == "Last 90 Days":
    date_sql = "AND m.started_at >= :start_date"
    params["start_date"] = now - timedelta(days=90)
elif time_filter == "Last 6 Months":
    date_sql = "AND m.started_at >= :start_date"
    params["start_date"] = now - timedelta(days=180)

# Fetch Data
stmt = text(f"""
    SELECT 
        m.match_id,
        m.map_name,
        m.duration_sec,
        m.started_at,
        mp_me.civ_name as my_civ,
        mp_me.won as won,
        mp_opp.civ_name as opp_civ
    FROM matches m
    JOIN match_players mp_me ON m.match_id = mp_me.match_id
    LEFT JOIN match_players mp_opp ON m.match_id = mp_opp.match_id AND mp_opp.aoe_profile_id != :pid
    WHERE mp_me.aoe_profile_id = :pid
      AND m.started_at IS NOT NULL
      AND mp_me.won IS NOT NULL
      {ladder_sql}
      {date_sql}
""")

rows = db.execute(stmt, params).fetchall()

if not rows:
    st.warning(f"{get_text('common.no_data', lang)} ({selected_name})")
    st.stop()

df = pd.DataFrame(rows, columns=["match_id", "map_name", "duration", "started_at", "my_civ", "won", "opp_civ"])
df["map_name"] = df["map_name"].astype(str).str.replace(".rms", "")
df["duration_min"] = df["duration"] / 60

# --- INSIGHT CARDS ---
# Calculate quick insights
avg_wr = (df["won"].sum() / len(df)) * 100
insights = []

# 1. Recent Form (Last 10)
recent_10 = df.sort_values("started_at", ascending=False).head(10)
recent_wr = (recent_10["won"].sum() / len(recent_10)) * 100
trend_diff = recent_wr - avg_wr

# Manual localization for streak labels since I missed them in i18n
streak_label = get_text("profile.stable", lang)
if recent_wr >= 70: streak_label = get_text("profile.hot_streak", lang)
elif recent_wr <= 30: streak_label = get_text("profile.cold_streak", lang)
else: streak_label = get_text("profile.stable", lang)

# Use generic format if hot_streak key can't be repurposed easily, or construct manually
# I'll use a manual construction to ensure correctness
diff_text = f"({trend_diff:+.1f}% vs {get_text('synergy.avg', lang)})"
stats_text = f"**{recent_wr:.0f}% {get_text('common.win_rate', lang)}**" # WR
msg = f"{streak_label}: {stats_text} {diff_text}" 
insights.append(msg)

# 2. Best Phase
df["Period"] = df["duration_min"].apply(lambda x: "Early" if x<20 else ("Mid" if x<35 else "Late"))
phase_wr = df.groupby("Period")["won"].mean() * 100
if not phase_wr.empty:
    best_phase = phase_wr.idxmax()
    # "Strongest in Early Game"
    # Localize Period name
    p_map = {"Early": "Erken", "Mid": "Orta", "Late": "Geç"}
    p_name = p_map.get(best_phase, best_phase) if lang == "tr" else best_phase
    
    # We have a key: insight.strongest_early -> "Strongest in Early Game: {win_rate}% WR"
    if best_phase == "Early":
        msg = get_text("insight.strongest_early", lang).format(win_rate=f"{phase_wr.max():.1f}")
    else:
        # Fallback/Construct for Mid/Late
        prefix = get_text("profile.strongest_in", lang)
        msg = f"⏱️ {prefix} **{p_name}**: **{phase_wr.max():.1f}% {get_text('common.win_rate', lang)}**"
    insights.append(msg)

# 3. Map Specialty
map_counts = df["map_name"].value_counts()
valid_maps = map_counts[map_counts >= 3].index
if not valid_maps.empty:
    map_wr = df[df["map_name"].isin(valid_maps)].groupby("map_name")["won"].mean() * 100
    best_map = map_wr.idxmax()
    # insight.map_specialist
    insights.append(get_text("insight.map_specialist", lang).format(map_name=best_map, win_rate=f"{map_wr.max():.1f}"))

# Display Insights
st.markdown(f"### 🏎️ {get_text('label.at_a_glance', lang)}")
ic1, ic2, ic3 = st.columns(3)
for i, card in enumerate(insights[:3]):
    if i==0: ic1.info(card)
    elif i==1: ic2.success(card)
    elif i==2: ic3.warning(card)

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    get_text("profile.tabs.overview", lang), 
    f"🗺️ {get_text('profile.tabs.maps_civs', lang)}", 
    f"⚔️ {get_text('profile.tabs.matchups', lang)}", 
    f"⏱️ {get_text('profile.tabs.timings', lang)}"
])

# ================= Tabs 1: Overview =================
with tab1:
    c1, c2, c3 = st.columns(3)
    total_games = len(df)
    wins = df["won"].sum()
    wr = (wins/total_games)*100
    
    # Confidence Interval for Global WR
    _, _, moe = wilson_score_interval(wins, total_games)
    
    c1.metric(get_text("profile.stats.total_games", lang), total_games)
    c2.metric(get_text("common.win_rate", lang), f"{wr:.1f}%", f"±{moe:.1f}% (95% CI)")
    c3.metric(get_text("label.current_elo", lang), player.elo_rm_1v1 or "N/A")
    
    # helper for CI
    ci_low = max(0, wr-moe)
    ci_high = min(100, wr+moe)
    st.caption(f"ℹ️ {get_text('insight.confidence', lang).format(low=f'{ci_low:.1f}', high=f'{ci_high:.1f}')}")
    
    # Match Timeline Chart
    st.markdown(f"#### 📅 {get_text('chart.match_timeline', lang)}")
    import plotly.express as px
    
    # Localize Legend Categories
    w_str = get_text("common.wins", lang)
    l_str = get_text("common.losses", lang)
    
    df["Result"] = df["won"].apply(lambda x: w_str if x else l_str)
    
    color_map = {w_str: "#2E7D32", l_str: "#C62828"}
    
    fig_time = px.scatter(
        df, 
        x="started_at", 
        y="duration_min", 
        color="Result", 
        color_discrete_map=color_map,
        symbol="Period",
        hover_data=["map_name", "my_civ", "opp_civ"],
        title=get_text("chart.match_history", lang)
    )
    fig_time.update_layout(yaxis_title=f"{get_text('common.duration', lang)} (min)", xaxis_title=get_text('common.date', lang))
    st.plotly_chart(fig_time, use_container_width=True)

# ================= Tabs 2: Maps & Civs =================
with tab2:
    col_map, col_civ = st.columns(2)
    
    MIN_SAMPLE = 5
    
    with col_map:
        st.markdown(f"### 🗺️ {get_text('profile.best_worst', lang)} {get_text('common.map', lang)}")
        map_stats = df.groupby("map_name")["won"].agg(['count', 'sum']).reset_index()
        map_stats.columns = [get_text("common.map", lang), get_text("common.games", lang), "Wins"]
        map_stats["WinRate"] = (map_stats["Wins"] / map_stats[get_text("common.games", lang)] * 100)
        
        # Calculate CI for each
        map_stats[get_text("profile.ci_moe", lang)] = map_stats.apply(lambda x: wilson_score_interval(x["Wins"], x[get_text("common.games", lang)])[2], axis=1)
        map_stats[get_text("profile.display_wr", lang)] = map_stats.apply(lambda x: f"{x['WinRate']:.1f}% ±{x[get_text('profile.ci_moe', lang)]:.1f}%", axis=1)
        
        valid_maps = map_stats[map_stats[get_text("common.games", lang)] >= MIN_SAMPLE].sort_values("WinRate", ascending=False)
        insufficient = map_stats[map_stats[get_text("common.games", lang)] < MIN_SAMPLE]
        
        if not valid_maps.empty:
            st.dataframe(
                valid_maps[[get_text("common.map", lang), get_text("common.games", lang), "Wins", get_text("profile.display_wr", lang)]],  
                use_container_width=True
            )
        else:
            st.info(get_text("profile.no_maps_min", lang).format(min=MIN_SAMPLE))
            
        if not insufficient.empty:
            with st.expander(get_text("profile.maps_insufficient", lang).format(min=MIN_SAMPLE)):
                st.dataframe(insufficient, use_container_width=True)
            
    with col_civ:
        st.markdown(f"### 🛡️ {get_text('profile.stats.best_civ', lang)}")
        civ_stats = df.groupby("my_civ")["won"].agg(['count', 'sum']).reset_index()
        civ_stats.columns = [get_text("common.civ", lang), get_text("common.games", lang), "Wins"]
        civ_stats["WinRate"] = (civ_stats["Wins"] / civ_stats[get_text("common.games", lang)] * 100)
        
        civ_stats[get_text("profile.ci_moe", lang)] = civ_stats.apply(lambda x: wilson_score_interval(x["Wins"], x[get_text("common.games", lang)])[2], axis=1)
        civ_stats[get_text("profile.display_wr", lang)] = civ_stats.apply(lambda x: f"{x['WinRate']:.1f}% ±{x[get_text('profile.ci_moe', lang)]:.1f}%", axis=1)
        
        # User Feedback: Min 10 for Civs
        MIN_SAMPLE_CIV = 10
        valid_civs = civ_stats[civ_stats[get_text("common.games", lang)] >= MIN_SAMPLE_CIV].sort_values("WinRate", ascending=False)
        
        if not valid_civs.empty:
            fig = plot_civ_win_rates(valid_civs.head(10).rename(columns={get_text("common.civ", lang): "civ_name", "WinRate": "win_rate", get_text("common.games", lang): "total_games"}))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(valid_civs[[get_text("common.civ", lang), get_text("common.games", lang), "Wins", get_text("profile.display_wr", lang)]], use_container_width=True)
        else:
            st.info(get_text("profile.no_civs_min", lang).format(min=MIN_SAMPLE_CIV))

# ================= Tabs 3: Matchups =================
with tab3:
    c_m1, c_m2 = st.columns(2)
    
    with c_m1:
        st.markdown(f"### ⚔️ {get_text('table.civ_matchups', lang)}")
        
        # Filter out None/Unknown
        df_match = df[df["opp_civ"].notna()]
        
        opp_civ_stats = df_match.groupby("opp_civ")["won"].agg(['count', 'sum']).reset_index()
        opp_civ_stats.columns = ["Opponent Civ", get_text("common.games", lang), "Wins Against"]
        opp_civ_stats["WinRate"] = (opp_civ_stats["Wins Against"] / opp_civ_stats[get_text("common.games", lang)] * 100)
        
        opp_civ_stats[get_text("profile.ci_moe", lang)] = opp_civ_stats.apply(lambda x: wilson_score_interval(x["Wins Against"], x[get_text("common.games", lang)])[2], axis=1)
        opp_civ_stats[get_text("profile.display_wr", lang)] = opp_civ_stats.apply(lambda x: f"{x['WinRate']:.1f}% ±{x[get_text('profile.ci_moe', lang)]:.1f}%", axis=1)

        valid_matchups = opp_civ_stats[opp_civ_stats[get_text("common.games", lang)] >= MIN_SAMPLE].sort_values("WinRate", ascending=True)
        
        if not valid_matchups.empty:
            st.markdown(f"**{get_text('matchup.most_difficult', lang)}** (Civ)")
            st.dataframe(valid_matchups.head(5)[["Opponent Civ", get_text("common.games", lang), get_text("profile.display_wr", lang)]], use_container_width=True)
            
            st.markdown(f"**{get_text('matchup.easiest', lang)}** (Civ)")
            st.dataframe(valid_matchups.tail(5).sort_values("WinRate", ascending=False)[["Opponent Civ", get_text("common.games", lang), get_text("profile.display_wr", lang)]], use_container_width=True)
        else:
            st.info(get_text("matchup.need_civ_games", lang).format(min=MIN_SAMPLE))
            
    with c_m2:
        st.markdown(f"### 🤼 {get_text('profile.tabs.matchups', lang)}")
        
        st.info(get_text("matchup.specific_players", lang))
        
        if not df["match_id"].empty:
            mids = df["match_id"].tolist()
            # Safe IN clause injection for integers
            if len(mids) > 0:
                mids_str = ",".join(str(m) for m in mids)
                
                stmt_rivals_direct = text(f"""
                    SELECT 
                        mp_opp.aoe_profile_id,
                        COALESCE(p.display_name, CAST(mp_opp.aoe_profile_id AS TEXT)) as display_name,
                        count(*) as games,
                        sum(case when mp_me.won=1 then 1 else 0 end) as wins
                    FROM matches m
                    JOIN match_players mp_me ON m.match_id = mp_me.match_id
                    JOIN match_players mp_opp ON m.match_id = mp_opp.match_id AND mp_opp.aoe_profile_id != :pid
                    LEFT JOIN players p ON mp_opp.aoe_profile_id = p.aoe_profile_id
                    WHERE mp_me.aoe_profile_id = :pid
                      AND m.match_id IN ({mids_str})
                    GROUP BY mp_opp.aoe_profile_id
                    HAVING games >= 5
                    ORDER BY games DESC
                """)
                
                r_rows = db.execute(stmt_rivals_direct, {"pid": pid}).fetchall()
                
                if r_rows:
                    df_rivals = pd.DataFrame(r_rows, columns=["pid", get_text("common.opponent", lang), get_text("common.games", lang), "Wins"])
                    df_rivals["WinRate"] = (df_rivals["Wins"] / df_rivals[get_text("common.games", lang)] * 100)
                    
                    # Nemesis (Min WR)
                    nemesis = df_rivals.sort_values("WinRate", ascending=True).iloc[0]
                    st.error(f"💀 **{get_text('profile.nemesis', lang)}:** {nemesis[get_text('common.opponent', lang)]} ({nemesis['WinRate']:.1f}% WR in {nemesis[get_text('common.games', lang)]} games)")
                    
                    # Prey (Max WR)
                    prey = df_rivals.sort_values("WinRate", ascending=False).iloc[0]
                    st.success(f"🐰 **{get_text('profile.prey', lang)}:** {prey[get_text('common.opponent', lang)]} ({prey['WinRate']:.1f}% WR in {prey[get_text('common.games', lang)]} games)")
                    
                    # Most Played
                    most = df_rivals.sort_values(get_text("common.games", lang), ascending=False).iloc[0]
                    st.info(f"🤝 **{get_text('profile.most_played', lang)}:** {most[get_text('common.opponent', lang)]} ({most[get_text('common.games', lang)]} games)")
                    
                    with st.expander(get_text("profile.full_rivalry_list", lang)):
                         st.dataframe(df_rivals.sort_values(get_text("common.games", lang), ascending=False).style.format({"WinRate": "{:.1f}%"}), use_container_width=True)
                else:
                     st.info(get_text("common.no_data", lang))
            else:
                 st.info(get_text("common.no_data", lang))
        else:
             st.info(get_text("common.no_data", lang))

# ================= Tabs 4: Timings =================
with tab4:
    st.markdown(f"### ⏱️ {get_text('duration.title', lang)}")
    
    lbl_early = get_text("duration.early", lang)
    lbl_mid = get_text("duration.mid", lang)
    lbl_late = get_text("duration.late", lang)

    def classify_duration(mins):
        if mins < 20: return lbl_early
        elif mins < 35: return lbl_mid
        else: return lbl_late
        
    df["Period"] = df["duration_min"].apply(classify_duration)
    # Ideally localize these "Early", "Mid", "Late" labels too if used in Chart
    # But using the key for now.
    
    period_order = [lbl_early, lbl_mid, lbl_late]
    df["Period"] = pd.Categorical(df["Period"], categories=period_order, ordered=True)
    
    time_stats = df.groupby("Period")["won"].agg(['count', 'sum']).reset_index()
    time_stats.columns = ["Phase", get_text("common.games", lang), "Wins"]
    time_stats["WinRate"] = (time_stats["Wins"] / time_stats[get_text("common.games", lang)] * 100).fillna(0)
    
    # CI
    time_stats["CI_MoE"] = time_stats.apply(lambda x: wilson_score_interval(x["Wins"], x[get_text("common.games", lang)])[2], axis=1)
    
    import plotly.express as px
    fig = px.bar(
        time_stats, 
        x="Phase", 
        y="WinRate", 
        error_y="CI_MoE",
        title=get_text("duration.win_rate_phase", lang),
        color="WinRate",
        color_continuous_scale="RdYlGn"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(
        time_stats.style.format({"WinRate": "{:.1f}%", "CI_MoE": "±{:.1f}%"}),
        use_container_width=True
    )
