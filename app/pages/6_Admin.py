import os
import sys
import time
from datetime import datetime

import streamlit as st

# Ensure project root is on path (Streamlit pages run from /app/pages)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from services.db.database import SessionLocal
from services.db.models import Player
from services.etl.fetcher import resolve_profile_from_steam_id
from services.worker import run_daily_update
from services.i18n import get_text
from app.components.sidebar import render_sidebar

st.set_page_config(page_title="Admin Settings", layout="wide")

filters = render_sidebar()
lang = filters.get("language", "tr")

st.title(f"🛠 {get_text('admin.title', lang)}")

st.markdown(f"### {get_text('admin.data_management', lang)}")

with st.expander("🚨 Data Repair Tool (Advanced)", expanded=False):
    st.warning("This tool deduplicates match_players and adds a UNIQUE constraint. Run only once if you suspect data duplication.")
    if st.button("Fix Duplicates & Add Constraint"):
        from sqlalchemy import text
        from services.db.database import SessionLocal
        
        db = SessionLocal()
        try:
            # 1. Clean Duplicates
            stmt_dedupe = text("""
                WITH ranked AS (
                  SELECT
                    id,
                    ROW_NUMBER() OVER (
                      PARTITION BY match_id, aoe_profile_id
                      ORDER BY
                        (won IS NOT NULL) DESC,
                        (elo_after IS NOT NULL) DESC,
                        id ASC
                    ) AS rn
                  FROM match_players
                )
                DELETE FROM match_players
                WHERE id IN (SELECT id FROM ranked WHERE rn > 1);
            """)
            res = db.execute(stmt_dedupe)
            cleaned_count = res.rowcount
            db.commit()
            
            # 2. Add Unique Constraint
            stmt_index = text("""
                CREATE UNIQUE INDEX IF NOT EXISTS ux_match_players_match_profile
                ON match_players(match_id, aoe_profile_id);
            """)
            db.execute(stmt_index)
            db.commit()
            
            st.success(f"Operation Complete! Cleared {cleaned_count} duplicates. Unique Index ensured.")
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            db.close()

col1, col2 = st.columns([1, 3])

with col1:
    if st.button(get_text("admin.trigger_update", lang), use_container_width=True):
        with st.spinner(get_text("admin.updating", lang)):
            # Force reload worker and fetcher to pick up hotfixes
            import importlib
            import services.etl.fetcher
            import services.worker
            importlib.reload(services.etl.fetcher)
            importlib.reload(services.worker)
            from services.worker import run_daily_update
            
            st.session_state["update_summary"] = run_daily_update()
            st.rerun()

    # Display update summary if available
    if "update_summary" in st.session_state:
        summary = st.session_state["update_summary"]
        
        st.markdown(f"### 🛠 {get_text('admin.update_diagnostics', lang)}")
        
        # Primary success / warning messaging
        errors = summary.get("errors") or []
        inserted_matches = int(summary.get("inserted_matches") or 0)
        backfilled_matches = int(summary.get("backfilled_matches") or 0)
        inserted_mps = int(summary.get("inserted_match_players") or 0)
        matches_fetched = int(summary.get("matches_fetched") or 0)
        tracked = int(summary.get("players_tracked") or 0)

        if errors:
            st.error(get_text("admin.update_issues", lang))
            for e in errors:
                st.write(f"- {e}")
        else:
            st.success(get_text("admin.update_success", lang))

        st.info(
            f"Tracked players: {tracked} | Matches fetched: {matches_fetched} | "
            f"Inserted matches: {inserted_matches} | Backfilled matches: {backfilled_matches} | "
            f"Inserted match-player rows: {inserted_mps}"
        )

        with st.expander("Raw update summary"):
            st.json(summary)

        if st.button(get_text("admin.close_diagnostics", lang)):
            del st.session_state["update_summary"]
            st.rerun()

with col2:
    st.info(get_text("admin.manual_trigger_info", lang))

st.markdown("---")
st.markdown(f"### {get_text('admin.player_management', lang)}")

with st.form("add_player_form"):
    st.write(get_text("admin.add_player_title", lang))
    c1, c2, c3 = st.columns(3)
    with c1:
        new_name = st.text_input(f"{get_text('common.player', lang)} (Optional)")
    with c2:
        new_profile_id = st.text_input("AoE2 Profile ID (RelicLink)", help="Numeric profile_id used by AoE2 DE.")
    with c3:
        new_steam_id = st.text_input("SteamID64 (Optional)", help="If provided, we will resolve profile_id via WorldsEdgeLink.")

    submitted = st.form_submit_button(get_text("admin.add_player_btn", lang))

    if submitted:
        new_name = (new_name or "").strip()
        new_profile_id = (new_profile_id or "").strip()
        new_steam_id = (new_steam_id or "").strip()

        resolved_alias = None

        # If profile id is missing but steam id exists -> resolve via WorldsEdgeLink
        if not new_profile_id and new_steam_id:
            # Force reload to ensure we have the latest resolution logic (in case of hotfix)
            import importlib
            import services.etl.fetcher
            importlib.reload(services.etl.fetcher)
            from services.etl.fetcher import resolve_profile_from_steam_id
            
            resolved = resolve_profile_from_steam_id(new_steam_id)
            if not resolved:
                st.error("Could not resolve Profile ID from SteamID64 via WorldsEdgeLink. Please enter Profile ID manually.")
                st.stop()
            pid, alias = resolved
            new_profile_id = str(pid)
            resolved_alias = alias
            if not new_name:
                new_name = alias
            st.success(f"Resolved profile_id={new_profile_id} (alias={alias}) via WorldsEdgeLink.")

        if not new_profile_id:
            st.error("AoE2 Profile ID is required (directly or resolved from SteamID64).")
            st.stop()

        try:
            pid_int = int(new_profile_id)
        except ValueError:
            st.error("Profile ID must be a number.")
            st.stop()

        if not new_name:
            new_name = resolved_alias or f"PID {pid_int}"

        db = SessionLocal()
        try:
            exists = db.query(Player).filter(Player.aoe_profile_id == pid_int).first()
            if exists:
                if exists.added_at is None:
                    # Player exists as a stub (from matches), promote to watchlist
                    exists.display_name = new_name
                    exists.steam_id = new_steam_id if new_steam_id else exists.steam_id
                    exists.added_at = datetime.utcnow()
                    db.commit()
                    st.success(f"Promoted existing match-player {new_name} (profile_id={pid_int}) to Watchlist.")
                else:
                    st.error(f"Player already exists: {exists.display_name} (profile_id={exists.aoe_profile_id})")
            else:
                p = Player(
                    player_id=str(pid_int),
                    aoe_profile_id=pid_int,
                    steam_id=new_steam_id if new_steam_id else None,
                    display_name=new_name,
                    added_at=datetime.utcnow(),
                )
                db.add(p)
                db.commit()
                st.success(f"Added {new_name} (profile_id={pid_int}) to watchlist.")
        finally:
            db.close()

st.markdown("---")
st.markdown(f"### {get_text('admin.watchlist', lang)}")

db = SessionLocal()
try:
    players = db.query(Player).filter(Player.added_at.isnot(None)).order_by(Player.added_at.desc()).all()
finally:
    db.close()

if not players:
    st.warning(get_text("common.no_data", lang))
else:
    # Simple table view
    st.dataframe(
        [
            {
                get_text("common.player", lang): p.display_name,
                "Profile ID": p.aoe_profile_id,
                "SteamID64": p.steam_id or "",
                "Added At (UTC)": getattr(p, "added_at", None),
            }
            for p in players
        ],
        use_container_width=True,
    )

    st.markdown(f"#### {get_text('admin.edit_remove', lang)}")

    option_map = {f"{p.display_name} (profile_id={p.aoe_profile_id})": p.aoe_profile_id for p in players if p.aoe_profile_id is not None}
    selected_label = st.selectbox(get_text("profile.select_player", lang), [""] + list(option_map.keys()))
    if selected_label:
        selected_pid = int(option_map[selected_label])

        db = SessionLocal()
        try:
            p = db.query(Player).filter(Player.aoe_profile_id == selected_pid).first()
            if not p:
                st.error("Selected player no longer exists.")
            else:
                with st.form("edit_player_form"):
                    edit_name = st.text_input("Display Name", value=p.display_name or "")
                    edit_steam = st.text_input("SteamID64", value=p.steam_id or "")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        lbl_save = "Kaydet" if lang == "tr" else "Save Changes"
                        save = st.form_submit_button(lbl_save)
                    with col_b:
                        lbl_del = "Sil" if lang == "tr" else "Remove Player"
                        delete = st.form_submit_button(lbl_del)

                    if save:
                        p.display_name = edit_name.strip() or p.display_name
                        p.steam_id = edit_steam.strip() or None
                        db.add(p)
                        db.commit()
                        st.success("Updated player.")
                        time.sleep(0.5)
                        st.rerun()

                    if delete:
                        db.delete(p)
                        db.commit()
                        st.success("Removed player.")
                        time.sleep(0.5)
                        st.rerun()
        finally:
            db.close()

st.markdown("---")
st.markdown(f"### 🔧 {get_text('admin.fix_names', lang) if 'admin.fix_names' in locals() else 'Fix Missing Names'}")

if st.button("🔍 Find and Resolve Missing Player Names"):
    import requests
    import json
    from services.db.database import SessionLocal
    from services.db.models import Player
    
    status_cont = st.empty()
    status_cont.info("Scanning for players with missing names...")
    
    db = SessionLocal()
    try:
        # Find players with PID... or purely numeric names
        # SQLite doesn't support REGEXP easily, so filter in Python
        all_players = db.query(Player).all()
        target_players = []
        for p in all_players:
            name = p.display_name or ""
            if not name or name.startswith("PID ") or name.isdigit():
                target_players.append(p)
        
        if not target_players:
            status_cont.success("No players found with missing names.")
        else:
            status_cont.info(f"Found {len(target_players)} players to resolve. Calling API...")
            
            # Batch them
            ids_to_resolve = [p.aoe_profile_id for p in target_players]
            chunk_size = 50
            
            updated_count = 0
            
            for i in range(0, len(ids_to_resolve), chunk_size):
                batch = ids_to_resolve[i:i+chunk_size]
                
                # Manual API call to ensure fresh code
                url = "https://aoe-api.worldsedgelink.com/community/leaderboard/getPersonalStat"
                payload = {
                    "title": "age2",
                    "profile_ids": json.dumps(batch)
                }
                
                try:
                    resp = requests.post(url, data=payload, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        groups = data.get("statGroups", [])
                        resolved_map = {}
                        for g in groups:
                            for m in g.get("members", []):
                                pid = m.get("profile_id")
                                if pid and m.get("alias"):
                                    resolved_map[int(pid)] = m.get("alias")
                        
                        # Update DB
                        # This part was accidentally removed in previous step, restoring basic update loop
                        for p in target_players:
                             if p.aoe_profile_id in resolved_map:
                                 # simplified restoration
                                 p.display_name = resolved_map[p.aoe_profile_id]
                                 updated_count += 1
                        db.commit()

                except Exception as e:
                    st.error(f"Request failed: {e}")
            
            status_cont.success(f"Resolved names for {updated_count} players.")
            
    finally:
        db.close()

st.markdown("---")

# --- PLAYER IMAGE UPLOAD SECTION ---
st.markdown("### 🖼️ Player Images")
st.caption("Upload profile pictures for Fun Charts.")

with st.expander("Upload Player Image", expanded=True):
    db_img = SessionLocal()
    try:
        all_players_img = db_img.query(Player).filter(Player.added_at.isnot(None)).all()
    finally:
        db_img.close()

    if not all_players_img:
        st.info("No players found.")
    else:
        p_options = {p.aoe_profile_id: f"{p.display_name} ({p.aoe_profile_id})" for p in all_players_img}
        selected_pid_img = st.selectbox("Select Player", options=list(p_options.keys()), format_func=lambda x: p_options[x], key="img_uploader_select")
        
        uploaded_file = st.file_uploader("Choose an image...", type=['png', 'jpg', 'jpeg'], key="img_uploader_file")
        
        if uploaded_file is not None and selected_pid_img:
            from PIL import Image
            import os
            
            # Create dir if not exists
            base_dir = os.path.join(os.path.dirname(__file__), "../assets/profiles")
            os.makedirs(base_dir, exist_ok=True)
            
            save_path = os.path.join(base_dir, f"{selected_pid_img}.png")
            
            if st.button("Save Image"):
                try:
                    image = Image.open(uploaded_file)
                    image = image.convert("RGBA")
                    image.thumbnail((200, 200)) 
                    image.save(save_path, "PNG")
                    st.success(f"Saved image for {p_options[selected_pid_img]}!")
                except Exception as e:
                    st.error(f"Error saving image: {e}")
st.markdown(f"### 📚 {get_text('admin.ref_data', lang)}")

import pandas as pd
from services.db.models import RefCiv, RefMap

# Helper to load/save ref data
def load_ref_df(model, db):
    query = db.query(model)
    return pd.read_sql(query.statement, db.bind)

def save_ref_changes(model, edited_df, db, pk_col):
    # This is a bit manual. Typically we iterate over changes.
    # Streamlit data_editor can return changed rows if we use session state properly or just diff.
    # Simpler: Iterate over edited_df and upsert.
    # For large datasets this is slow, but mappings are small (<100 rows).
    try:
        count = 0
        for _, row in edited_df.iterrows():
            pk_val = row[pk_col]
            obj = db.query(model).get(pk_val)
            if obj:
                # Update attributes
                for col in edited_df.columns:
                    if col != pk_col and hasattr(obj, col):
                        setattr(obj, col, row[col])
                count += 1
            else:
                # Insert new (if supported, primarily for maps)
                # For now assuming we are editing existing.
                pass 
        db.commit()
        return count
    except Exception as e:
        st.error(f"Error saving: {e}")
        return 0

db = SessionLocal()
try:
    c_ref1, c_ref2 = st.tabs([get_text("admin.ref_civs", lang), get_text("admin.ref_maps", lang)])
    
    # --- CIVS ---
    with c_ref1:
        # Load
        df_civs = load_ref_df(RefCiv, db)
        
        # Filter toggle
        show_missing_civ = st.checkbox(get_text("admin.only_missing", lang), key="chk_civ")
        if show_missing_civ:
            df_civs = df_civs[df_civs["civ_name"].str.contains("Unknown", na=True)]
            
        edited_civs = st.data_editor(
            df_civs, 
            hide_index=True, 
            column_config={"civ_id": st.column_config.NumberColumn(disabled=True)},
            key="editor_civs",
            use_container_width=True
        )
        
        if st.button("Save Civilizations", key="btn_save_civ"):
            # We can't easily detect which rows changed from dataframe alone without tracking state or comparing.
            # But since it's small, we just save all displayed rows (or original full DF if we filtered).
            # Wait, if we filtered, edited_civs is partial. We should only update those.
            # Correct approach:
            cnt = save_ref_changes(RefCiv, edited_civs, db, "civ_id")
            st.success(f"Updated {cnt} rows.")
            time.sleep(1)
            st.rerun()

    # --- MAPS ---
    with c_ref2:
        df_maps = load_ref_df(RefMap, db)
        
        show_missing_map = st.checkbox(get_text("admin.only_missing", lang), key="chk_map")
        if show_missing_map:
            # Check for Unknown or Map ID placeholders
            # Assuming logic "Unknown Map (123)" or just "Unknown"
            df_maps = df_maps[df_maps["map_name"].str.contains("Unknown", na=True, case=False)]

        edited_maps = st.data_editor(
            df_maps, 
            hide_index=True, 
            column_config={"map_id": st.column_config.NumberColumn(disabled=True)},
            key="editor_maps",
            use_container_width=True
        )
        
        if st.button("Save Maps", key="btn_save_map"):
            cnt = save_ref_changes(RefMap, edited_maps, db, "map_id")
            st.success(f"Updated {cnt} rows.")
            time.sleep(1)
            st.rerun()

finally:
    db.close()

