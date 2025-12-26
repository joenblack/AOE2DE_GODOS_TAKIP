import streamlit as st
import sys
import os

# Add project root to sys.path (parent of parent of this file -> ../..)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.components.sidebar import render_sidebar
from services.db.database import get_db
from services.db.models import Player, AggPlayerDaily
from services.db.models import Player, AggPlayerDaily
import services.i18n
import importlib
importlib.reload(services.i18n)
from services.i18n import get_text
from sqlalchemy import func, desc, case, text
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Overview", layout="wide")

filters = render_sidebar()
lang = filters.get("language", "tr")

st.title(f"📊 {get_text('overview.title', lang)}")

db = next(get_db())

# Tab Layout
tab1, tab2, tab3 = st.tabs([
    f"🏆 {get_text('overview.leaderboard', lang)}", 
    f"⚡ {get_text('overview.power_rankings', lang)}", 
    f"🏅 {get_text('overview.hall_of_fame', lang)}"
])

# =============================================================================
# TAB 1: STANDARD LEADERBOARD
# =============================================================================
with tab1:
    try:
        # Query Player table directly (now enriched with ELO)
        # Apply Sidebar Filter
        selected_ids = filters.get("selected_player_ids", [])
        
        if selected_ids:
            players = db.query(Player).filter(
                Player.added_at.isnot(None),
                Player.aoe_profile_id.in_(selected_ids)
            ).order_by(desc(Player.elo_rm_1v1)).all()
        else:
            players = []
            st.warning(get_text("common.no_data", lang) + " (Oyuncu seçilmedi)")
        
        # Calculate stats for each player
        from services.db.models import MatchPlayer
        
        # Fetch agg stats manually to ensure freshness
        stats_rows = db.query(
            MatchPlayer.aoe_profile_id,
            func.count().label("total_games"),
            func.sum(case((MatchPlayer.won == True, 1), else_=0)).label("wins")
        ).filter(MatchPlayer.won.isnot(None)).group_by(MatchPlayer.aoe_profile_id).all()
        
        stats_map = {r.aoe_profile_id: r for r in stats_rows}
        
        data = []
        for r in players:
            p_stat = stats_map.get(r.aoe_profile_id)
            total_games = p_stat.total_games if p_stat else 0
            wins = p_stat.wins if p_stat else 0
            win_rate = (wins / total_games * 100) if total_games > 0 else 0
            
            data.append({
                get_text("common.player", lang): r.display_name or str(r.aoe_profile_id),

                "1v1 ELO": r.elo_rm_1v1,
                "Team ELO": r.elo_rm_team,
                get_text("common.games", lang): total_games,
                get_text("common.win_rate", lang): f"{win_rate:.1f}%",
                get_text("label.last_match", lang): r.last_match_at.strftime("%Y-%m-%d") if r.last_match_at else "–"
            })
        
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info(get_text("common.no_data", lang))
    
    except Exception as e:
        st.error(f"{get_text('common.error', lang)}: {e}")

    # --- ELO ARENA (Fun Charts) - Moved to Tab 1 ---
    st.markdown("---")
    st.markdown("---")
    
    # Prepare data for Altair
    import altair as alt
    from services.image_utils import get_image_base64
    from sqlalchemy import func, case
    from services.db.models import MatchPlayer
    
    # Re-fetch players to ensure we have latest ELOs
    # Apply Sidebar Filter
    selected_ids = filters.get("selected_player_ids", [])
    
    if selected_ids:
        arena_players = db.query(Player).filter(
            Player.added_at.isnot(None),
            Player.aoe_profile_id.in_(selected_ids)
        ).order_by(desc(Player.elo_rm_1v1)).all()
    else:
         arena_players = [] # Should not happen if default is all, but handle empty selection
    
    if arena_players:
        # 1. Prepare Base Data
        arena_data = []
        base_assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/profiles"))
        
        # Pre-fetch Stats for Pie Chart
        # Query: Player ID -> Win Count, Total Games
        win_stats = db.query(
            MatchPlayer.aoe_profile_id,
            func.count().label("total"),
            func.sum(case((MatchPlayer.won == True, 1), else_=0)).label("wins")
        ).filter(
            MatchPlayer.aoe_profile_id.in_([p.aoe_profile_id for p in arena_players])
        ).group_by(MatchPlayer.aoe_profile_id).all()
    
        stats_map = {r.aoe_profile_id: r for r in win_stats}

        for p in arena_players:
            img_path = os.path.join(base_assets_dir, f"{p.aoe_profile_id}.png")
            img_b64 = get_image_base64(img_path)
            
            s = stats_map.get(p.aoe_profile_id)
            wins = s.wins if s else 0
            total = s.total if s else 0
            wr = (wins / total * 100) if total > 0 else 0
            
            arena_data.append({
                "Player": p.display_name,
                "ELO": p.elo_rm_1v1 or 1000,
                "Wins": wins,
                "Games": total,
                "Win Rate": round(wr, 1),
                "Image": img_b64 if img_b64 else "https://raw.githubusercontent.com/vega/vega-datasets/master/data/ffox.png",
            })
        
        df_arena = pd.DataFrame(arena_data)

        col_arena, col_pie = st.columns([2, 1])

        with col_arena:
            st.markdown(f"#### ⚔️ {get_text('overview.elo_gladiators', lang)}")
            # Base chart
            base = alt.Chart(df_arena).encode(
                x=alt.X('Player', sort='-y', axis=alt.Axis(labelAngle=-45, labelFontWeight='bold', labelColor='black', labelFontSize=12), title=get_text("common.player", lang)),
                y=alt.Y('ELO', scale=alt.Scale(domain=[min(df_arena["ELO"])-50, max(df_arena["ELO"])+50]))
            )
            
            bars = base.mark_bar(color='#5b9bd5').encode(
                tooltip=['Player', 'ELO', 'Wins', 'Win Rate']
            )
            
            text_elo = base.mark_text(dy=-30, color='black', fontWeight='bold', fontSize=14).encode(
                text=alt.Text('ELO', format='d'),
                y='ELO' # Align with image
            )

            images = base.mark_image(width=50, height=50).encode(
                url='Image',
                y='ELO'
            )

            chart_bar = (bars + text_elo + images).properties(height=450).interactive()
            st.altair_chart(chart_bar, use_container_width=True)

        with col_pie:
            # Selectbox for Pie Chart Metric
            # Options: Win Rate, Wins, Games
            metric_map = {
                "Kazanma Oranı" if lang == "tr" else "Win Rate": "Win Rate",
                "Galibiyet Sayısı" if lang == "tr" else "Wins": "Wins",
                "Oynadığı Maç" if lang == "tr" else "Total Games": "Games"
            }
            
            selected_label = st.selectbox(get_text("common.select_chart", lang), list(metric_map.keys()))
            selected_metric = metric_map[selected_label]
            
            # Bar Chart instead of Pie Chart (Requested by User)
            base_interactive = alt.Chart(df_arena).encode(
                x=alt.X('Player', sort='-y' if selected_label in ["Kazanma Oranı", "Win Rate"] else '-y', 
                        axis=alt.Axis(labelFontWeight='bold', labelColor='black', labelFontSize=12)), 
                # X axis sorted by the metric
                y=alt.Y(selected_metric)
            )
            
            # Color by Player to be consistent or just one color? 
            # User requested "Excel-like blue bars".
            
            bars_int = base_interactive.mark_bar(color='#5b9bd5').encode(
                tooltip=['Player', selected_metric, "ELO"]
            )
            
            text_int = base_interactive.mark_text(dy=-10, color='black').encode(
                text=alt.Text(selected_metric, format='.1f' if 'Rate' in selected_metric else 'd')
            )
            
            chart_int = (bars_int + text_int).properties(height=450).interactive()
            st.altair_chart(chart_int, use_container_width=True)

# =============================================================================
# TAB 2: POWER RANKINGS
# =============================================================================
with tab2:
    st.markdown(f"### ⚡ {get_text('overview.power_rankings', lang)}")
    # Logic: Calculate Form Rating based on Opponent Elo + Result using Performance Rating formula.
    
    # 1. Get Tracked Players
    t_players = db.query(Player).filter(Player.added_at.isnot(None)).all()
    
    power_data = []
    
    for p in t_players:
        # Get last 20 1v1 matches (Ladder type 1v1 or match players count = 2)
        # We need opponent ELO.
        # Query: Joined MatchPlayers filters
        
        # This query gets My Stats and Opponent Stats for last 20 1v1 games
        # We use strict is_1v1 flag to ensure we have exactly one opponent and correct stats
        stmt = text("""
            SELECT 
                mp_me.won,
                mp_opp.elo_before as opp_elo,
                mp_opp.elo_after as opp_elo_after
            FROM matches m
            JOIN match_players mp_me ON m.match_id = mp_me.match_id
            JOIN match_players mp_opp ON m.match_id = mp_opp.match_id
            WHERE mp_me.aoe_profile_id = :pid
              AND mp_opp.aoe_profile_id != :pid
              AND m.is_1v1 = 1
              AND m.started_at IS NOT NULL
            ORDER BY m.started_at DESC
            LIMIT 20
        """)
        
        rows = db.execute(stmt, {"pid": p.aoe_profile_id}).fetchall()
        
        if not rows:
            continue
            
        total_games = len(rows)
        wins = 0
        losses = 0
        total_opp_elo = 0
        upset_count = 0
        
        # My current ELO (from DB)
        my_current_elo = p.elo_rm_1v1 or 1000
        
        valid_elo_games = 0
        
        for r in rows:
            is_won = r.won
            # Prefer elo_before, if null use after, if null ignore for calc
            op_elo = r.opp_elo if r.opp_elo else r.opp_elo_after
            
            if is_won: wins += 1
            if is_won is False: losses += 1 # None is draw/unknown
            
            if op_elo:
                total_opp_elo += op_elo
                valid_elo_games += 1
                
                # Upset: Won against someone with > (My ELO + 25) ? Or just Higher?
                # Let's say strictly higher is an upset for now, or maybe significant difference.
                # User said "Upset count: wins against higher Elo".
                if is_won and op_elo > my_current_elo:
                    upset_count += 1
        
        # Form Rating (Performance Rating)
        # PR = (Total Opponent ELO + 400 * (Wins - Losses)) / Games
        # Only calc over games with ELO
        if valid_elo_games > 0:
            avg_opp_elo = total_opp_elo / valid_elo_games
            # Adjust W-L for ONLY valid games? Or assume missing elo matches don't count for PR?
            # Let's simple approximation using valid games stats
            
            # Simplified PR:
            form_rating = (total_opp_elo + 400 * (wins - losses)) / total_games
            sos_rating = avg_opp_elo
        else:
            form_rating = 0
            sos_rating = 0
            
        win_rate = (wins / total_games * 100) if total_games > 0 else 0
        
        power_data.append({
            get_text("common.player", lang): p.display_name,
            get_text("common.games", lang): total_games,
            get_text("common.win_rate", lang): f"{win_rate:.1f}%",
            get_text("overview.form_rating", lang): int(form_rating),
            get_text("overview.sos", lang): int(sos_rating),
            get_text("overview.upsets", lang): upset_count,
            get_text("label.current_elo", lang): p.elo_rm_1v1
        })
        
    if power_data:
        # Sort by Form Rating by default
        df_power = pd.DataFrame(power_data)
        col_form = get_text("overview.form_rating", lang)
        col_sos = get_text("overview.sos", lang)
        
        df_power = df_power.sort_values(col_form, ascending=False)
        
        st.dataframe(
            df_power,
            column_config={
                col_form: st.column_config.ProgressColumn(
                    col_form,
                    help=get_text("overview.tooltip_form_rating", lang),
                    format="%d",
                    min_value=0,
                    max_value=3000,
                ),
                 col_sos: st.column_config.NumberColumn(
                    col_sos,
                    help=get_text("overview.tooltip_sos", lang),
                    format="%d"
                ),
            },
            use_container_width=True
        )
        st.caption(f"*{get_text('table.perf_context', lang)} (1v1)*")
    else:
        st.info(get_text("common.no_data", lang))

# =============================================================================
# TAB 3: HALL OF FAME
# =============================================================================
with tab3:
    st.markdown(f"### 🏅 {get_text('overview.hall_of_fame', lang)}")
    st.caption(get_text("overview.subtext", lang))

    col_hof1, col_hof2 = st.columns(2)
    col_hof3, col_hof4 = st.columns(2)
    
    # 1. MARATHONER (Longest Match)
    tracked_pids = [p.aoe_profile_id for p in t_players]
    
    if tracked_pids:
        # Safe to inject for trusted integers to avoid SQLite binding issues with IN clause tuples
        ids_str = ",".join(str(pid) for pid in tracked_pids)
        
        stmt_marathon = text(f"""
            SELECT 
                m.duration_sec, 
                m.started_at, 
                mp.civ_name, 
                m.map_name,
                mp.aoe_profile_id 
            FROM matches m
            JOIN match_players mp ON m.match_id = mp.match_id
            WHERE mp.aoe_profile_id IN ({ids_str})
            ORDER BY m.duration_sec DESC
            LIMIT 1
        """)
        row_mar = db.execute(stmt_marathon).first()
        
        with col_hof1:
            st.markdown(f"#### 🏃 {get_text('overview.marathoner', lang)}")
            if row_mar:
                dur_min = int(row_mar.duration_sec / 60)
                p_name = next((p.display_name for p in t_players if p.aoe_profile_id == row_mar.aoe_profile_id), "Unknown")
                
                # Handle datetime conversion (SQLite via raw query returns str)
                started = row_mar.started_at
                if isinstance(started, str):
                    try:
                        started = datetime.fromisoformat(started)
                    except ValueError:
                        started = datetime.now() # Fallback

                st.metric(f"{p_name}", f"{dur_min} {get_text('common.duration_min', lang) if 'common.duration_min' in locals() else 'dk'}", f"{row_mar.map_name}")
                st.caption(get_text("table.saved_at", lang).format(date=started.strftime('%Y-%m-%d'), civ=row_mar.civ_name))
            else:
                st.info(get_text("common.no_data", lang))

        # 2. SPEEDRUNNER (Fastest Win > 5 min)
        stmt_speed = text(f"""
            SELECT 
                m.duration_sec, 
                m.started_at, 
                mp.civ_name, 
                m.map_name,
                mp.aoe_profile_id 
            FROM matches m
            JOIN match_players mp ON m.match_id = mp.match_id
            WHERE mp.aoe_profile_id IN ({ids_str})
              AND mp.won = 1
              AND m.duration_sec > 300
            ORDER BY m.duration_sec ASC
            LIMIT 1
        """)
        row_speed = db.execute(stmt_speed).first()
        
        with col_hof2:
            st.markdown(f"#### ⚡ {get_text('overview.speedrunner', lang)}")
            if row_speed:
                dur_min = row_speed.duration_sec // 60
                dur_sec = row_speed.duration_sec % 60
                p_name = next((p.display_name for p in t_players if p.aoe_profile_id == row_speed.aoe_profile_id), "Unknown")
                
                started = row_speed.started_at
                if isinstance(started, str):
                    try:
                        started = datetime.fromisoformat(started)
                    except ValueError:
                        started = datetime.now()

                st.metric(f"{p_name}", f"{dur_min}m {dur_sec}s", f"{row_speed.map_name}")
                st.caption(get_text("table.saved_at", lang).format(date=started.strftime('%Y-%m-%d'), civ=row_speed.civ_name))
            else:
                st.info(get_text("common.no_data", lang))
    else:
        with col_hof1: st.info(get_text("common.no_data", lang))
        with col_hof2: st.info(get_text("common.no_data", lang))

    # 3. GIANT SLAYER (Max Upsets)
    col_upsets = get_text("overview.upsets", lang)
    if power_data:
        # We used localized keys in power_data, so we must access via col_upsets
        # power_data is a list of dicts. Keys are localized.
        
        # Need to be careful: max() key function needs to access the correct key
        try:
            slayer = max(power_data, key=lambda x: x[col_upsets])
            
            with col_hof3:
                st.markdown(f"#### 🗡️ {get_text('overview.giant_slayer', lang)}")
                if slayer[col_upsets] > 0:
                    st.metric(f"{slayer[get_text('common.player', lang)]}", f"{slayer[col_upsets]} {get_text('overview.upsets', lang)}", get_text("overview.high_elo_wins", lang))
                    st.caption(get_text("overview.upsets_desc", lang))
                else:
                        st.metric("Yok", f"0 {get_text('overview.upsets', lang)}")
        except KeyError:
                with col_hof3: st.text("Data Error")
    else:
         with col_hof3:
             st.markdown(f"#### 🗡️ {get_text('overview.giant_slayer', lang)}") 
             st.info(get_text("common.no_data", lang))
    
    # 4. STREAK KING (Longest Active Streak)
    max_streak = -1
    streak_king = None
    
    for p in t_players:
        stmt_str = text("""
            SELECT mp.won
            FROM matches m
            JOIN match_players mp ON m.match_id = mp.match_id
            WHERE mp.aoe_profile_id = :pid
                AND m.started_at IS NOT NULL
                AND mp.won IS NOT NULL
            ORDER BY m.started_at DESC
            LIMIT 50
        """)
        outcomes = [r.won for r in db.execute(stmt_str, {"pid": p.aoe_profile_id}).fetchall()]
        
        current_streak = 0
        for w in outcomes:
            if w: current_streak += 1
            else: break
        
        if current_streak > max_streak:
            max_streak = current_streak
            streak_king = p.display_name
    
    with col_hof4:
        st.markdown(f"#### 🔥 {get_text('overview.streak_king', lang)}")
        if max_streak > 0:
            st.metric(f"{streak_king}", f"{max_streak} {get_text('common.wins', lang)}", get_text("rivalry.streak", lang))
            # st.caption("Currently on the hottest winning streak of the group.")
        else:
                st.metric("None", f"0 {get_text('common.wins', lang)}")



st.markdown("---")
st.subheader(get_text("label.recent_activity", lang))

from services.db.models import Match, MatchPlayer

# Get ID set of tracked players for highlighting
tracked_ids = {p.aoe_profile_id for p in players}

# Query last 20 matches involving any tracked player
# We first find distinct match_ids involving tracked players
subq = db.query(MatchPlayer.match_id).filter(MatchPlayer.aoe_profile_id.in_(list(tracked_ids))).distinct().subquery()
recent_matches = db.query(Match).join(subq, Match.match_id == subq.c.match_id).order_by(desc(Match.started_at)).limit(20).all()

if recent_matches:
    activity_data = []
    for m in recent_matches:
        # Sort players by team then name
        # m.players is a list of MatchPlayer objects
        mps = sorted(m.players, key=lambda x: (x.team if x.team is not None else 99, x.id))
        
        # Build participants string
        # Team 1 vs Team 2
        # We can group by team
        teams = {}
        for mp in mps:
            t = mp.team if mp.team is not None else 1
            if t not in teams: teams[t] = []
            
            p_name = mp.player.display_name if mp.player else str(mp.aoe_profile_id)
            if p_name.startswith("PID "): p_name = str(mp.aoe_profile_id) # fallback cleanup
            
            # Add Civ
            civ = mp.civ_name or "?"
            
            # Result Icon
            icon = ""
            if mp.won is True: icon = "✅"
            elif mp.won is False: icon = "❌"
            
            # Highlight tracked
            if mp.aoe_profile_id in tracked_ids:
                entry = f"**{p_name}** ({civ}) {icon}"
            else:
                entry = f"{p_name} ({civ}) {icon}"
            
            teams[t].append(entry)
        
        # Join teams with ' vs '
        team_strings = []
        for t_id in sorted(teams.keys()):
            team_strings.append(", ".join(teams[t_id]))
            
        summary = " ⚔️ ".join(team_strings)
        
        activity_data.append({
            get_text("common.date", lang): m.started_at.strftime("%Y-%m-%d %H:%M") if m.started_at else "—",
            get_text("common.map", lang): m.map_name.replace('.rms', '') if m.map_name else "—",
            get_text("filter.ladder", lang): m.ladder_type,
            get_text("label.matchup", lang): summary
        })
        
    st.dataframe(pd.DataFrame(activity_data), use_container_width=True)
else:
    st.info(get_text("common.no_data", lang))
