import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os
from sqlalchemy import text

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.components.sidebar import render_sidebar
from services.db.database import get_db
from services.db.models import Player
from services.i18n import get_text

st.set_page_config(page_title="Analytics Explorer", layout="wide")

filters = render_sidebar()
lang = filters.get("language", "tr")

st.title(f"🔎 {get_text('analytics.title', lang)}")

db = next(get_db())

tab1, tab2, tab3 = st.tabs([
    f"📈 {get_text('analytics.elo_race', lang)}", 
    f"🗺️ {get_text('analytics.map_stats', lang)}", 
    f"📝 {get_text('analytics.raw_data', lang)}"
])

# -----------------------------------------------------------------------------
# TAB 1: ELO Racing Bar Chart
# -----------------------------------------------------------------------------
with tab1:
    st.header(get_text('analytics.elo_race', lang))
    st.info(get_text('analytics.visualizing_elo', lang))
    
    # query matches timestamps and ELOs
    # We need: date, player_name, elo_after
    
    # Apply Sidebar Filter
    selected_ids = filters.get("selected_player_ids", [])
    
    # If using IN clause with list, we need to handle empty list or valid list
    # SQLAlchemy text binding for list might vary, safe way is injecting if trusted or strictly verifying.
    # But since selected_ids comes from internal logic, let's use binding with tuple if possible or dynamic text.
    
    if selected_ids:
        # Convert to tuple for SQL IN clause
        # If single item, tuple need trailing comma, but python tuple(list) handles it.
        # Actually sqlalchemy params handles lists usually with IN operator if structured right, 
        # but let's just construct the IDs part or filter in python if data is small?
        # Data might be large (matches). Better SQL.
        
        # Safe string formatting for IDs since they are integers
        ids_str = ",".join(str(pid) for pid in selected_ids)
        
        query_elo = text(f"""
            SELECT 
                m.started_at,
                p.display_name,
                mp.elo_after
            FROM matches m
            JOIN match_players mp ON m.match_id = mp.match_id
            JOIN players p ON mp.aoe_profile_id = p.aoe_profile_id
            WHERE mp.elo_after IS NOT NULL
              AND p.aoe_profile_id IN ({ids_str})
            ORDER BY m.started_at ASC
        """)
    else:
        # Fallback if no selection (e.g. cleared), maybe show nothing or just tracked?
        # User said "Added players".
        query_elo = text("""
            SELECT 
                m.started_at,
                p.display_name,
                mp.elo_after
            FROM matches m
            JOIN match_players mp ON m.match_id = mp.match_id
            JOIN players p ON mp.aoe_profile_id = p.aoe_profile_id
            WHERE mp.elo_after IS NOT NULL
              AND p.added_at IS NOT NULL
            ORDER BY m.started_at ASC
        """)
    
    try:
        rows = db.execute(query_elo).fetchall()
        if rows:
            df_elo = pd.DataFrame(rows, columns=["date", "player", "elo"])
            df_elo["date"] = pd.to_datetime(df_elo["date"])
            
            # Resample to daily frequency to smooth out the animation
            # 1. Pivot to have players as columns
            df_pivot = df_elo.pivot_table(index="date", columns="player", values="elo", aggfunc="last")
            
            # 2. Resample daily (or weekly if too heavy) and forward fill
            # If data is sparse, 'D' might be too much frames. Let's try 'W' (Weekly) or 'D' depending on length.
            # Let's try Daily for smoothness, if distinct days < 100, else Weekly.
            days_span = (df_elo["date"].max() - df_elo["date"].min()).days
            freq = 'D' if days_span < 365 else 'W' # If more than a year, do weekly
            
            df_resampled = df_pivot.resample(freq).last().ffill()
            
            # 3. Melt back to long format for Plotly
            df_racing = df_resampled.reset_index().melt(id_vars="date", var_name="player", value_name="elo")
            
            # Remove rows where ELO is still NaN (before player started playing)
            df_racing = df_racing.dropna(subset=["elo"])
            
            # Format date for slider
            df_racing["date_str"] = df_racing["date"].dt.strftime("%Y-%m-%d")
            
            # Create Plotly Animation
            fig = px.bar(
                df_racing, 
                x="elo", 
                y="player", 
                animation_frame="date_str", 
                orientation='h',
                range_x=[0, 2500], # AoE2 ELO range typically up to 2800, but let's be dynamic or fixed
                title=f"ELO Progression ({freq} Frequency)",
                height=600
            )
            
            # Improving UI/speed
            fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 100 # ms per frame
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning(get_text("common.no_data", lang))
            
    except Exception as e:
        st.error(f"{get_text('common.error', lang)}: {e}")

# -----------------------------------------------------------------------------
# TAB 2: Map Stats (Heatmap Alternative)
# -----------------------------------------------------------------------------
with tab2:
    st.header(get_text('analytics.map_stats', lang))
    
    col_map1, col_map2 = st.columns(2)
    
    with col_map1:
        st.subheader(get_text("analytics.play_count", lang))
        query_map = text("""
            SELECT map_name, count(*) as play_count 
            FROM matches 
            GROUP BY map_name 
            ORDER BY play_count DESC
            LIMIT 20
        """)
        map_rows = db.execute(query_map).fetchall()
        if map_rows:
            df_map = pd.DataFrame(map_rows, columns=["map_name", "count"])
            # Clean map names
            df_map["map_name"] = df_map["map_name"].astype(str).str.replace(".rms", "")
            # Treemap or Pie or Bar
            fig_map = px.treemap(df_map, path=['map_name'], values='count', title=get_text("analytics.most_played", lang))
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info(get_text("common.no_data", lang))
            
    with col_map2:
        st.subheader(get_text("analytics.win_rate", lang))
        # Need match_players joined
        # This might be heavy if many rows
        # Prepare IDs safely
        sel_ids = filters.get("selected_player_ids", [])
        if sel_ids:
            ids_str = ",".join(str(pid) for pid in sel_ids)
            filter_clause = f"AND mp.aoe_profile_id IN ({ids_str})"
        else:
            # Fallback to all tracked players
            t_players = db.query(Player.aoe_profile_id).filter(Player.added_at.isnot(None)).all()
            if t_players:
                ids_str = ",".join(str(p.aoe_profile_id) for p in t_players)
                filter_clause = f"AND mp.aoe_profile_id IN ({ids_str})"
            else:
                 filter_clause = "AND 1=0" # No data

        query_win = text(f"""
            SELECT 
                m.map_name,
                count(*) as total_games,
                sum(case when mp.won = 1 then 1 else 0 end) as wins,
                avg(case when mp.won = 1 then 1.0 else 0.0 end) * 100 as win_rate
            FROM matches m
            JOIN match_players mp ON m.match_id = mp.match_id
            WHERE mp.won IS NOT NULL
              {filter_clause}
            GROUP BY m.map_name
            HAVING count(*) >= 1
            ORDER BY total_games DESC, win_rate DESC
            LIMIT 20
        """)
        win_rows = db.execute(query_win).fetchall()
        if win_rows:
            # Safe way:
            df_win = pd.DataFrame(win_rows, columns=["map_name", "total_games", "wins", "win_rate"])
            # Clean map names
            df_win["map_name"] = df_win["map_name"].astype(str).str.replace(".rms", "")
            
            # Formatting
            df_win["win_rate"] = df_win["win_rate"].apply(lambda x: f"{x:.1f}%")
            
            st.write(get_text("analytics.top_5", lang))
            st.dataframe(df_win, use_container_width=True)
            st.caption(f"*{get_text('analytics.footer_note', lang)}*")
        else:
             st.info(get_text("common.no_data", lang))

# -----------------------------------------------------------------------------
# TAB 3: Raw Data
# -----------------------------------------------------------------------------
with tab3:
    st.subheader(f"{get_text('analytics.raw_data', lang)} ({get_text('common.all', lang)})")
    query_raw = text("""
        SELECT 
            m.match_id, 
            m.started_at, 
            m.map_name, 
            p.display_name as player, 
            mp.civ_name, 
            mp.won,
            mp.elo_after,
            mp.team,
            m.is_ranked
        FROM matches m
        JOIN match_players mp ON m.match_id = mp.match_id
        JOIN players p ON mp.aoe_profile_id = p.aoe_profile_id
        ORDER BY m.started_at DESC
        -- LIMIT removed as requested
    """)
    try:
        results = db.execute(query_raw).fetchall()
        if results:
            df_raw = pd.DataFrame(results, columns=["match_id", "started_at", "map_name", "player", "civ_name", "won", "elo", "team", "is_ranked"])
            
            # --- INFERENCE LOGIC (Fill None based on opponents) ---
            # Group by match_id to find known results
            for mid, group in df_raw.groupby("match_id"):
                # Find known team outcomes
                team_outcomes = {}
                teams = group["team"].unique()
                
                # Check for explicit wins/losses in the group
                for idx, row in group.iterrows():
                    w = row["won"]
                    if w == 1:
                        team_outcomes[row["team"]] = 1
                    elif w == 0:
                        team_outcomes[row["team"]] = 0
                
                # If we have 2 teams and one result is known, infer the other
                if len(teams) == 2:
                    t1, t2 = teams[0], teams[1]
                    res1 = team_outcomes.get(t1)
                    res2 = team_outcomes.get(t2)
                    
                    if res1 is not None and res2 is None:
                        team_outcomes[t2] = 1 - res1 # If 1->0, If 0->1
                    elif res2 is not None and res1 is None:
                        team_outcomes[t1] = 1 - res2
                
                # Apply inferred results to None rows
                for idx, row in group.iterrows():
                    if pd.isna(row["won"]): # None/NaN
                        inferred = team_outcomes.get(row["team"])
                        if inferred is not None:
                            df_raw.at[idx, "won"] = inferred

            # Map is_ranked to string
            df_raw["ranking_type"] = df_raw["is_ranked"].apply(lambda x: "RANKED" if x else "UNRANKED")

            # Result formatting
            # ...

            # Drop team and raw is_ranked column, keep ranking_type
            df_display = df_raw.drop(columns=["team", "is_ranked"])
            
            # Localize Columns
            df_display.rename(columns={
                "match_id": "Maç ID", 
                "started_at": get_text("common.date", lang),
                "map_name": get_text("common.map", lang),
                "player": get_text("common.player", lang),
                "civ_name": get_text("common.civ", lang),
                "won": get_text("table.result", lang),
                "elo": get_text("analytics.col_elo", lang),
                "ranking_type": "Tip" if lang == "tr" else "Type"
            }, inplace=True)
            
            st.dataframe(df_display, use_container_width=True)
            
            csv = df_display.to_csv(index=False).encode('utf-8')
            st.download_button(get_text("analytics.download_csv", lang), csv, "matches_dump.csv", "text/csv")
        else:
            st.info(get_text("common.no_data", lang))
    except Exception as e:
        st.error(f"{get_text('common.error', lang)}: {e}")
