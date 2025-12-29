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
from services.analysis.aggregator import Aggregator
from services.i18n import get_text
from app.components.sidebar import render_sidebar

st.set_page_config(page_title="Admin Settings", layout="wide")

filters = render_sidebar()
lang = filters.get("language", "tr")

st.title(f"🛠 {get_text('admin.title', lang)}")

st.markdown(f"### {get_text('admin.data_management', lang)}")

with st.expander(f"🚨 {get_text('admin.data_repair', lang)}", expanded=False):
    st.warning(get_text('admin.data_repair_warn', lang))
    if st.button(get_text('admin.data_repair_btn', lang)):
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
            
            st.success(get_text('admin.data_repair_success', lang).format(count=cleaned_count))
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            db.close()

with st.expander(f"📚 {get_text('admin.backfill_history', lang)}", expanded=False):
    st.info(get_text('admin.backfill_info', lang))
    
    # Select players
    db_bf = SessionLocal()
    tracked_bf = db_bf.query(Player).filter(Player.added_at.isnot(None)).all()
    db_bf.close()
    
    bf_options = {p.aoe_profile_id: f"{p.display_name}" for p in tracked_bf}
    safe_bf_ids = list(bf_options.keys())
    
    selected_bf_ids = st.multiselect(get_text("profile.select_player", lang), options=safe_bf_ids, format_func=lambda x: bf_options[x], default=safe_bf_ids)
    
    if st.button(get_text("admin.start_backfill", lang)):
        if not selected_bf_ids:
            st.warning(get_text("common.no_data", lang))
        else:
            import services.etl.aoe2insights as a2i
            import services.etl.fetcher as fetcher
            from services.db.database import SessionLocal
            from services.db.models import Match
            
            # Progress bar
            pbar = st.progress(0.0)
            status_text = st.empty()
            
            total_players = len(selected_bf_ids)
            total_inserted = 0
            
            db = SessionLocal()
            
            # Pre-fetch known match IDs to stop scraping early
            # Pre-fetch known match IDs to stop scraping early
            known_ids = {m[0] for m in db.query(Match.match_id).all()}
            st.text(f"DEBUG: Found {len(known_ids)} existing matches in DB for optimization check.")
            
            try:
                for idx, pid in enumerate(selected_bf_ids):
                    player_name = bf_options.get(pid, pid)
                    status_text.text(get_text("admin.fetching_history", lang).format(player=player_name, current=idx+1, total=total_players))
                    
                    # Determine which ID to use for scraping
                    scrape_pid = pid
                    p_obj = db.query(Player).filter(Player.aoe_profile_id == pid).first()
                    if p_obj and p_obj.aoe2insights_id:
                        scrape_pid = p_obj.aoe2insights_id
                        st.info(f"Using AoE2Insights ID: {scrape_pid} (Relic ID: {pid})")
                    
                    # Fetch
                    # Note: Increased max_pages to 5000 to cover very active players.
                    matches_data = a2i.fetch_full_match_history(scrape_pid, max_pages=5000, known_match_ids=known_ids)
                    status_text.text(get_text("admin.fetched_processing", lang).format(count=len(matches_data), player=player_name))
                    
                    if matches_data:
                        # Process
                        stats = fetcher.process_matches(db, [pid], matches_data)
                        
                        # Fix any potential ID mismatches for existing data
                        if p_obj:
                            fetcher.fix_match_player_ids(db, p_obj)
                            
                            # Fetch current ELO from Relic (Ensuring we use Relic ID)
                            # User Requirement: Use WorldsEdgeLink for ELO, A2I for history.
                            st.text(f"Fetching current ELO from WorldsEdgeLink (ID: {p_obj.aoe_profile_id})...")
                            fetcher.update_player_elo_from_relic(db, p_obj)
                            
                        inserted = stats.get("inserted_matches", 0)
                        updated = stats.get("backfilled_matches", 0)
                        total_inserted += inserted
                        st.write(f"✅ {player_name}: Scraped {len(matches_data)} matches. New: {inserted}, Updated: {updated}")
                    else:
                        st.write(f"⚠️ {player_name}: No matches found via scraper.")
                    
                    pbar.progress((idx + 1) / total_players)
                    time.sleep(0.5) 
                
                st.success(get_text("admin.backfill_complete", lang).format(count=total_inserted))
                
                # Force refresh of all aggregates
                st.info("İstatistik tabloları yeniden hesaplanıyor (Aggregates)...")
                Aggregator(db).refresh_all()
                st.success("Tüm istatistikler güncellendi.")
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                db.close()



# Daily Update Removed per request
st.write("")




st.markdown("---")
st.markdown(f"### {get_text('admin.player_management', lang)}")

with st.form("add_player_form"):
    st.write(get_text("admin.add_player_title", lang))
    c1, c2 = st.columns(2)
    with c1:
        new_name = st.text_input(get_text("common.player_name", lang))
    with c2:
        new_steam_id = st.text_input("SteamID64 (Optional)", help="If provided, we will attempt to auto-fill WorldsEdgeLink ID.")

    c3, c4 = st.columns(2)
    with c3:
        new_profile_id = st.text_input("WorldsEdgeLink Profile ID", help="The official Relic/AoE IV/DE profile ID.")
    with c4:
        new_a2i_id = st.text_input("AoE2Insights Profile ID (Optional)", help="If different from WorldsEdgeLink ID.")

    submitted = st.form_submit_button(get_text("admin.add_player_btn", lang))

    if submitted:
        new_name = (new_name or "").strip()
        new_profile_id = (new_profile_id or "").strip()
        new_steam_id = (new_steam_id or "").strip()
        new_a2i_id = (new_a2i_id or "").strip()

        resolved_alias = None

        # Logic: If Profile ID missing but SteamID present -> Try Resolve
        if not new_profile_id and new_steam_id:
            # Force reload to ensure resolution logic
            import importlib
            import services.etl.fetcher
            importlib.reload(services.etl.fetcher)
            from services.etl.fetcher import resolve_profile_from_steam_id
            
            resolved = resolve_profile_from_steam_id(new_steam_id)
            if not resolved:
                st.error("SteamID64 üzerinden WorldsEdgeLink Profil ID bulunamadı. Lütfen WorldsEdgeLink Profil ID'yi manuel girin.")
                st.stop()
            pid, alias = resolved
            new_profile_id = str(pid)
            resolved_alias = alias
            if not new_name:
                new_name = alias
            st.success(f"WorldsEdgeLink üzerinden profile_id={new_profile_id} (alias={alias}) çözüldü.")

        if not new_profile_id:
            st.error("WorldsEdgeLink Profile ID gereklidir.")
            st.stop()

        try:
            pid_int = int(new_profile_id)
        except ValueError:
            st.error("WorldsEdgeLink Profile ID sayı olmalıdır.")
            st.stop()
            
        a2i_int = None
        if new_a2i_id:
            try:
                a2i_int = int(new_a2i_id)
            except ValueError:
                st.error("AoE2Insights ID sayı olmalıdır.")
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
                    if a2i_int: exists.aoe2insights_id = a2i_int # Update A2I ID
                    exists.added_at = datetime.utcnow()
                    db.commit()
                    st.success(f"Mevcut {new_name} (profile_id={pid_int}) oyuncusu İzleme Listesine terfi ettirildi.")
                else:
                    st.error(f"Oyuncu zaten mevcut: {exists.display_name} (profile_id={exists.aoe_profile_id})")
            else:
                p = Player(
                    player_id=str(pid_int),
                    aoe_profile_id=pid_int,
                    steam_id=new_steam_id if new_steam_id else None,
                    aoe2insights_id=a2i_int, # New field
                    display_name=new_name,
                    added_at=datetime.utcnow(),
                )
                db.add(p)
                db.commit()
                st.success(f"{new_name} (profile_id={pid_int}) İzleme listesine eklendi.")
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
                "WorldsEdge ID": p.aoe_profile_id,
                "AoE2Insights ID": p.aoe2insights_id or "",
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
                st.error("Seçilen oyuncu artık mevcut değil.")
            else:
                with st.form("edit_player_form"):
                    edit_name = st.text_input("Görünen İsim / Display Name", value=p.display_name or "")
                    
                    c_edit_1, c_edit_2 = st.columns(2)
                    with c_edit_1:
                        edit_we_id = st.text_input("WorldsEdgeLink Profile ID", value=str(p.aoe_profile_id))
                    with c_edit_2:
                        edit_a2i_id = st.text_input("AoE2Insights Profile ID", value=str(p.aoe2insights_id) if p.aoe2insights_id else "")
                        
                    edit_steam = st.text_input("SteamID64", value=p.steam_id or "")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        lbl_save = get_text("profile.save_changes", lang)
                        save = st.form_submit_button(lbl_save)
                    with col_b:
                        lbl_del = get_text("profile.remove_player", lang)
                        delete = st.form_submit_button(lbl_del)

                    if save:
                        try:
                            new_pid_int = int(edit_we_id)
                        except ValueError:
                            st.error("WorldsEdgeLink ID must be a number.")
                            new_pid_int = p.aoe_profile_id
                        
                        new_a2i_int = None
                        if edit_a2i_id.strip():
                            try:
                                new_a2i_int = int(edit_a2i_id)
                            except ValueError:
                                st.error("AoE2Insights ID must be a number.")
                                new_a2i_int = p.aoe2insights_id # Revert or fail? Let's keep old if fail or stop.
                                st.stop()

                        # Check if PID changed
                        if new_pid_int != p.aoe_profile_id:
                            # Check conflict
                            existing = db.query(Player).filter(Player.aoe_profile_id == new_pid_int).first()
                            if existing:
                                st.error(f"Cannot update: Profile ID {new_pid_int} is already assigned to {existing.display_name}.")
                            else:

                                # Safe to update.
                                # User REQUEST: "Profil ID değiştirmek oyuncunun diğer hiçbir verilerini değiştirmesin (ne elosu, ne yaptığı maçlar)."
                                # Strategy: MIGRATE data from old ID to new ID.
                                # Because Player.player_id is PK, we can't just change it if there are FKs (unless cascade update, which we can't rely on).
                                # Steps:
                                # 1. Create NEW Player with new IDs
                                # 2. Update all child tables to point to NEW IDs
                                # 3. Delete OLD Player
                                
                                from services.db.models import MatchPlayer, AggPlayerDaily, AggPlayerCiv, AggPlayerMap, AggCombat
                                from sqlalchemy import text

                                # 0. Pre-flight: Nullify old Steam ID to prevent Unique Constraint Error
                                # Because steam_id is unique, we must free it up before creating the new record with the same steam_id.
                                p.steam_id = None
                                # Remove unique constraint on aoe2insights_id too if needed? unique=True nullable=True
                                # If we are keeping same A2I ID, we must free it.
                                temp_a2i = p.aoe2insights_id
                                p.aoe2insights_id = None
                                db.flush()

                                # 1. Create New Player
                                new_p = Player(

                                    player_id=str(new_pid_int),
                                    aoe_profile_id=new_pid_int,
                                    steam_id=edit_steam.strip() or None,
                                    aoe2insights_id=new_a2i_int if new_a2i_int else temp_a2i, # Use new if provided, else keep old
                                    display_name=edit_name.strip() or p.display_name,
                                    added_at=p.added_at,
                                    last_seen_at=p.last_seen_at,
                                    country=p.country,
                                    elo_rm_1v1=p.elo_rm_1v1,
                                    elo_rm_team=p.elo_rm_team,
                                    last_match_at=p.last_match_at
                                )
                                db.add(new_p)
                                db.flush() # Persist new_p so FKs can point to it
                                
                                # 2. Migrate Data
                                # MatchPlayer (references aoe_profile_id)
                                db.query(MatchPlayer).filter(MatchPlayer.aoe_profile_id == p.aoe_profile_id).update({MatchPlayer.aoe_profile_id: new_pid_int})
                                
                                # Aggregates (references player_id)
                                old_pid_str = p.player_id
                                new_pid_str = str(new_pid_int)
                                
                                db.query(AggPlayerDaily).filter(AggPlayerDaily.player_id == old_pid_str).update({AggPlayerDaily.player_id: new_pid_str})
                                db.query(AggPlayerCiv).filter(AggPlayerCiv.player_id == old_pid_str).update({AggPlayerCiv.player_id: new_pid_str})
                                db.query(AggPlayerMap).filter(AggPlayerMap.player_id == old_pid_str).update({AggPlayerMap.player_id: new_pid_str})
                                
                                # AggCombat (player_a and player_b)
                                db.query(AggCombat).filter(AggCombat.player_id == old_pid_str).update({AggCombat.player_id: new_pid_str})
                                db.query(AggCombat).filter(AggCombat.opponent_id == old_pid_str).update({AggCombat.opponent_id: new_pid_str})
                                
                                # 3. Delete Old Player
                                db.delete(p)
                                
                                db.commit()
                                st.success(f"Oyuncu ID değiştirildi ve veriler taşındı: {p.aoe_profile_id} -> {new_pid_int}")
                                st.rerun()

                        else:
                            # Just update metadata
                            p.display_name = edit_name.strip()
                            p.steam_id = edit_steam.strip() or None
                            # Update A2I ID
                            # Check conflict if new_a2i_int != None
                            if new_a2i_int and new_a2i_int != p.aoe2insights_id:
                                conflict = db.query(Player).filter(Player.aoe2insights_id == new_a2i_int).first()
                                if conflict:
                                    st.error(f"Bu AoE2Insights ID ({new_a2i_int}) zaten başka bir oyuncuya ait: {conflict.display_name}")
                                    st.stop()
                            p.aoe2insights_id = new_a2i_int
                            
                            db.commit()
                            st.success(get_text("common.success", lang))
                            time.sleep(1)
                            st.rerun()


                    if delete:
                        # Deep Clean: Remove all associated data
                        from services.db.models import MatchPlayer, Match, AggPlayerDaily, AggPlayerCiv, AggPlayerMap, AggCombat
                        from sqlalchemy import text
                        
                        # 1. Delete Aggregates
                        db.query(AggPlayerDaily).filter(AggPlayerDaily.player_id == p.player_id).delete()
                        db.query(AggPlayerCiv).filter(AggPlayerCiv.player_id == p.player_id).delete()
                        db.query(AggPlayerMap).filter(AggPlayerMap.player_id == p.player_id).delete()
                        
                        # AggCombat has two FKs (player_a, player_b). Delete if player is either.
                        db.query(AggCombat).filter((AggCombat.player_a_id == p.player_id) | (AggCombat.player_b_id == p.player_id)).delete()
                        
                        # 2. Delete Player (Cascades to MatchPlayer if configured, but let's be explicitly safe to avoid FK errors if missing)
                        # We rely on ORM cascade for MatchPlayer usually, but explicit query is robust.
                        # Note: matches are many-to-many via MatchPlayer.
                        # We delete the player, which deletes MatchPlayers.
                        
                        db.delete(p)
                        db.flush() # Execute deletes
                        
                        # 3. Garbage Collection: Delete Matches that have no players left
                        # Using raw SQL for efficiency/clarity on the "NOT EXISTS" logic
                        stmt_gc_matches = text("""
                            DELETE FROM matches 
                            WHERE match_id NOT IN (SELECT DISTINCT match_id FROM match_players)
                        """)
                        db.execute(stmt_gc_matches)
                        
                        db.commit()
                        st.success(get_text("profile.removed", lang))
                        time.sleep(1.0)
                        st.rerun()
        finally:
            db.close()


st.markdown("---")
st.markdown(f"### 🔧 {get_text('admin.fix_names_title', lang)}")

if st.button(f"🔍 {get_text('admin.fix_names_btn', lang)}"):
    import requests
    import json
    from services.db.database import SessionLocal
    from services.db.models import Player
    
    status_cont = st.empty()
    status_cont.info(get_text('admin.fix_names_info', lang))
    
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
            status_cont.success(get_text('admin.no_missing_names', lang))
        else:
            status_cont.info(f"{len(target_players)} oyuncu bulundu. API çağrılıyor...")
            
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
            
            status_cont.success(get_text('admin.resolved_names', lang).format(count=updated_count))
            
    finally:
        db.close()

st.markdown("---")

# --- PLAYER IMAGE UPLOAD SECTION ---
st.markdown(f"### 🖼️ {get_text('admin.player_images', lang)}")
st.caption("Grafikler için oyuncu profil resimleri yükleyin.")

with st.expander(get_text('admin.upload_image', lang), expanded=True):
    db_img = SessionLocal()
    try:
        all_players_img = db_img.query(Player).filter(Player.added_at.isnot(None)).all()
    finally:
        db_img.close()

    if not all_players_img:
        st.info(get_text('common.no_data', lang))
    else:
        p_options = {p.aoe_profile_id: f"{p.display_name} ({p.aoe_profile_id})" for p in all_players_img}
        selected_pid_img = st.selectbox(get_text('admin.select_player_img', lang), options=list(p_options.keys()), format_func=lambda x: p_options[x], key="img_uploader_select")
        
        uploaded_file = st.file_uploader(get_text('admin.choose_image', lang), type=['png', 'jpg', 'jpeg'], key="img_uploader_file")
        
        if uploaded_file is not None and selected_pid_img:
            from PIL import Image
            import os
            
            # Create dir if not exists
            base_dir = os.path.join(os.path.dirname(__file__), "../assets/profiles")
            os.makedirs(base_dir, exist_ok=True)
            
            save_path = os.path.join(base_dir, f"{selected_pid_img}.png")
            
            if st.button(get_text('admin.upload_btn', lang)):
                try:
                    image = Image.open(uploaded_file)
                    image = image.convert("RGBA")
                    image.thumbnail((200, 200)) 
                    image.save(save_path, "PNG")
                    st.success(get_text('admin.saved_image', lang).format(name=p_options[selected_pid_img]))
                except Exception as e:
                    st.error(f"{get_text('common.error', lang)}: {e}")
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
        
        if st.button(get_text('admin.save_civs', lang), key="btn_save_civ"):
            # We can't easily detect which rows changed from dataframe alone without tracking state or comparing.
            # But since it's small, we just save all displayed rows (or original full DF if we filtered).
            # Wait, if we filtered, edited_civs is partial. We should only update those.
            # Correct approach:
            cnt = save_ref_changes(RefCiv, edited_civs, db, "civ_id")
            st.success(get_text('admin.updated_rows', lang).format(count=cnt))
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
        
        if st.button(get_text('admin.save_maps', lang), key="btn_save_map"):
            cnt = save_ref_changes(RefMap, edited_maps, db, "map_id")
            st.success(get_text('admin.updated_rows', lang).format(count=cnt))
            time.sleep(1)
            st.rerun()

finally:
    db.close()

st.markdown("---")
st.markdown("### ⚠️ Danger Zone")

with st.expander("🗑️ Delete All Match Data (Reset Database)", expanded=False):
    st.error("WARNING: This will delete ALL matches, statistics, and history. Players (watchlist) will remain, but their history will be wiped.")
    
    del_pass = st.text_input("Enter Password to confirm deletion:", type="password", value="delete123")
    
    if st.button("🚨 DELETE ALL MATCH DATA 🚨", type="primary"):
        if del_pass == "delete123":
            from services.db.models import Match, MatchPlayer, AggCombat, AggPlayerDaily, AggPlayerCiv, AggPlayerMap
            from sqlalchemy import text
            
            db = SessionLocal()
            try:
                # Disable foreign key checks for faster/cleaner wipe (sqlite specific, but generic delete is safer)
                # We will just delete in order.
                
                st.info("Deleting aggregates...")
                db.query(AggCombat).delete()
                db.query(AggPlayerDaily).delete()
                db.query(AggPlayerCiv).delete()
                db.query(AggPlayerMap).delete()
                
                st.info("Deleting match players...")
                # Raw SQL for speed on large tables
                db.execute(text("DELETE FROM match_players"))
                
                st.info("Deleting matches...")
                db.execute(text("DELETE FROM matches"))
                
                db.commit()
                st.success("✅ Database Wiped Successfully! All match data is gone.")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error executing delete: {e}")
            finally:
                db.close()
        else:
            st.warning("Incorrect Password!")


