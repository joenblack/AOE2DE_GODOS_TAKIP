import streamlit as st
import pandas as pd
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.components.sidebar import render_sidebar
from services.db.database import get_db
from services.db.models import Player, AggCombat
from services.i18n import get_text
from sqlalchemy import text

st.set_page_config(page_title="Rivalries", layout="wide")

filters = render_sidebar()
lang = filters.get("language", "tr")

st.title(f"🆚 {get_text('sidebar.matchups', lang)}")

db = next(get_db())

st.markdown(f"### {get_text('rivalry.title', lang)}")

players = db.query(Player).filter(Player.added_at.isnot(None)).all()
options = {(p.display_name or str(p.aoe_profile_id)): p.player_id for p in players}


col_sel1, col_sel2, col_sel3 = st.columns([2, 2, 1])
with col_sel1:
    p1_name = st.selectbox(get_text("rivalry.player_a", lang), options.keys(), key="p1")
with col_sel2:
    p2_name = st.selectbox(get_text("rivalry.player_b", lang), options.keys(), key="p2")
with col_sel3:
    mode_sel = st.radio("Mode", ["All", "1v1", "Team"], key="mode_sel", horizontal=True)

if p1_name and p2_name and p1_name != p2_name:
    # Get Profile IDs (Assuming player_id == aoe_profile_id in our simplified model logic, or look it up)
    # The 'options' dict stores player_id (which is a string of profile_id)
    # let's be safe.
    p1 = db.query(Player).filter(Player.player_id == str(options[p1_name])).first()
    p2 = db.query(Player).filter(Player.player_id == str(options[p2_name])).first()
    
    if p1 and p2:
        pid1 = p1.aoe_profile_id
        pid2 = p2.aoe_profile_id
        
        # Mode Filter Logic
        mode_filter = ""
        if mode_sel == "1v1":
             mode_filter = "AND m.is_1v1 = 1"
        elif mode_sel == "Team":
             mode_filter = "AND m.is_team_game = 1"
        
        # Query matches where both are present and on DIFFERENT teams
        stmt = text(f"""
            SELECT 
                m.match_id, 
                m.started_at, 
                m.duration_sec,
                m.map_name,
                mp1.civ_name as civ1,
                mp2.civ_name as civ2,
                mp1.won as won1,
                mp2.won as won2
            FROM matches m
            JOIN match_players mp1 ON m.match_id = mp1.match_id
            JOIN match_players mp2 ON m.match_id = mp2.match_id
            WHERE mp1.aoe_profile_id = :p1
              AND mp2.aoe_profile_id = :p2
              AND mp1.team != mp2.team
              AND m.started_at IS NOT NULL
              {mode_filter}
            ORDER BY m.started_at DESC
        """)
        
        rows = db.execute(stmt, {"p1": pid1, "p2": pid2}).fetchall()
        
        if rows:
            df = pd.DataFrame(rows, columns=["match_id", "started_at", "duration", "map_name", "civ1", "civ2", "won1", "won2"])
            df["started_at"] = pd.to_datetime(df["started_at"])
            df["map_name"] = df["map_name"].astype(str).str.replace(".rms", "") # Clean .rms
            
            # --- 1. Basic Stats ---
            total_games = len(df)
            wins1 = df["won1"].sum()
            wins2 = df["won2"].sum() # Should be total - wins1 mostly (except draws/crashes)
            
            st.markdown(f"### {get_text('common.overall', lang)}: {p1_name} vs {p2_name}")
            c1, c2, c3 = st.columns(3)
            c1.metric(f"{p1_name} {get_text('common.wins', lang)}", f"{wins1}", f"{(wins1/total_games*100):.1f}%")
            c2.metric(get_text("profile.stats.total_games", lang), total_games)
            c3.metric(f"{p2_name} {get_text('common.wins', lang)}", f"{wins2}", f"{(wins2/total_games*100):.1f}%")
            
            st.progress(wins1/total_games)
            
            # --- 2. Streak ---
            # df is ordered DESC (newest first).
            current_streak = 0
            streak_holder = None
            
            if not df.empty:
                last_won = df.iloc[0]["won1"] # True if P1 won
                streak_holder = p1_name if last_won else p2_name
                
                for w1 in df["won1"]:
                    if w1 == last_won:
                        current_streak += 1
                    else:
                        break
            
            st.info(f"🔥 **{get_text('rivalry.streak', lang)}:** {streak_holder} ({current_streak} {get_text('common.games', lang)})")
            
            # --- 3. Trend (Last 30/60/90 Days) ---
            st.markdown(f"#### 📅 {get_text('rivalry.trend', lang)}")
            now = pd.Timestamp.now(tz=df["started_at"].iloc[0].tz) # Use same TZ
            days_lbl = get_text("common.days", lang)
            periods = {f"30 {days_lbl}": 30, f"60 {days_lbl}": 60, f"90 {days_lbl}": 90}
            trend_cols = st.columns(3)
            
            for i, (label, days) in enumerate(periods.items()):
                cutoff = now - pd.Timedelta(days=days)
                subset = df[df["started_at"] > cutoff]
                if not subset.empty:
                    w1 = subset["won1"].sum()
                    t = len(subset)
                    wr = (w1/t * 100)
                    trend_cols[i].metric(label, f"{wr:.1f}% ({p1_name})", f"{t} {get_text('common.games', lang)}")
                else:
                    trend_cols[i].metric(label, get_text("common.no_data", lang), "-")

            # --- 4. Clutch Index (40+ mins) ---
            # 40 mins = 2400 seconds
            st.markdown(f"#### ⏳ {get_text('rivalry.clutch', lang)} (40+ min)")
            clutch_df = df[df["duration"] > 2400]
            if not clutch_df.empty:
                c_w1 = clutch_df["won1"].sum()
                c_total = len(clutch_df)
                c_wr = (c_w1 / c_total * 100)
                
                cc1, cc2 = st.columns([1, 3])
                cc1.metric(f"{get_text('common.win_rate', lang)} (40+ min)", f"{c_wr:.1f}%", f"{c_w1}/{c_total} {get_text('common.games', lang)}")
                cc2.progress(c_w1/c_total)
            else:
                st.caption(get_text("common.no_data", lang))

            # --- 5. Context Breakdowns (Map / Civ) ---
            st.markdown(f"#### 🗺️ & 🛡️ {get_text('table.perf_context', lang)}")
            t1, t2 = st.tabs([f"{get_text('common.map', lang)} {get_text('table.map_stats', lang)}", get_text('table.civ_matchups', lang)])
            
            with t1:
                # Group by Map and Calc Win Rate for P1
                map_stats = df.groupby("map_name")["won1"].agg(['count', 'sum']).reset_index()
                # Localized Columns
                c_map = get_text("common.map", lang)
                c_games = get_text("common.games", lang)
                c_wins = f"{p1_name} {get_text('common.wins', lang)}"
                
                map_stats.columns = [c_map, c_games, c_wins]
                map_stats["P1_WinRate"] = (map_stats[c_wins] / map_stats[c_games] * 100).round(1)
                map_stats = map_stats.sort_values(c_games, ascending=False).head(10)
                st.dataframe(map_stats.style.format({"P1_WinRate": "{:.1f}%"}), use_container_width=True)
                
            with t2:
                # Civ vs Civ matrix maybe too sparse. Let's show P1 Civ WinRates vs P2
                # Group by (Civ1) -> WR
                civ_stats = df.groupby("civ1")["won1"].agg(['count', 'sum']).reset_index()
                civ_stats.columns = [get_text("common.civ", lang), get_text("common.games", lang), get_text("common.wins", lang)]
                civ_stats["WinRate"] = (civ_stats[get_text("common.wins", lang)] / civ_stats[get_text("common.games", lang)] * 100).round(1)
                civ_stats = civ_stats.sort_values(get_text("common.games", lang), ascending=False).head(10)
                st.write(f"**{p1_name} {get_text('profile.stats.best_civ', lang)} vs {p2_name}**")
                st.dataframe(civ_stats, use_container_width=True)
                
            # Recent Games List
            st.markdown(f"#### 📜 {get_text('table.recent_matches', lang)}")
            recent_disp = df.head(10).copy()
            
            lbl_won = get_text("common.wins", lang)
            lbl_lost = get_text("common.losses", lang)
            recent_disp["Result"] = recent_disp["won1"].apply(lambda x: f"✅ {lbl_won}" if x else f"❌ {lbl_lost}")
            
            recent_disp["Date"] = recent_disp["started_at"].dt.strftime("%Y-%m-%d")
            recent_disp["Duration"] = (recent_disp["duration"] / 60).astype(int).astype(str) + " min"
            
            # Rename columns for display
            col_map = {"Date": get_text("common.date", lang), "map_name": get_text("common.map", lang), "civ1": f"{p1_name}", "civ2": f"{p2_name}", "Result": get_text("table.result", lang), "Duration": get_text("common.duration", lang)}
            recent_disp = recent_disp.rename(columns=col_map)
            
            disp_cols = [col_map["Date"], col_map["map_name"], col_map["civ1"], col_map["civ2"], col_map["Result"], col_map["Duration"]]
            st.dataframe(recent_disp[disp_cols], use_container_width=True)

        else:
            st.warning(get_text("common.no_data", lang))
    else:
        st.error(get_text("common.error", lang))

else:
    st.info(get_text("rivalry.select_players", lang))
