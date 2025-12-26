import streamlit as st
from datetime import datetime, timedelta
from services.auth_steam import SteamAuth
from services.db.database import SessionLocal
from services.db.models import Player
from services.i18n import get_text

def render_sidebar():
    # --- LANGUAGE SELECTOR ---
    # Default to Turkish as requested
    if "language" not in st.session_state:
        st.session_state["language"] = "tr"
        
    lang_map = {"Türkçe": "tr", "English": "en"}
    rev_lang_map = {"tr": "Türkçe", "en": "English"}
    
    selected_label = st.sidebar.selectbox(
        "Dil / Language",
        options=["Türkçe", "English"],
        index=0 if st.session_state["language"] == "tr" else 1
    )
    st.sidebar.markdown("**Designed by L**")
    
    st.session_state["language"] = lang_map[selected_label]
    lang = st.session_state["language"]
    
    # --- NAVIGATION ---
    st.sidebar.markdown("---")
    st.sidebar.header(get_text("sidebar.nav_title", lang))
    
    st.sidebar.page_link("main.py", label=get_text("sidebar.home", lang), icon="🏠")
    st.sidebar.page_link("pages/1_Overview.py", label=get_text("sidebar.overview", lang), icon="📊")
    st.sidebar.page_link("pages/2_Player_Profile.py", label=get_text("sidebar.profile", lang), icon="👤")
    st.sidebar.page_link("pages/3_Rivalries.py", label=get_text("sidebar.matchups", lang), icon="⚔️")
    st.sidebar.page_link("pages/4_Team_Synergy.py", label=get_text("sidebar.synergy", lang), icon="🤝")
    st.sidebar.page_link("pages/5_Analytics_Explorer.py", label=get_text("analytics.title", lang), icon="📈")
    st.sidebar.page_link("pages/7_League.py", label=get_text("sidebar.league", lang), icon="🏆")
    st.sidebar.page_link("pages/8_Compare.py", label=get_text("sidebar.compare", lang), icon="⚖️")
    st.sidebar.page_link("pages/6_Admin.py", label=get_text("sidebar.admin", lang), icon="🛠")

    st.sidebar.markdown("---")
    
    st.sidebar.header(get_text("sidebar.filters", lang))
    
    # Auth Status
    if "user_steam_id" in st.session_state:
        steam_id = st.session_state['user_steam_id']
        
        # Fetch linked player
        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.steam_id == str(steam_id)).first()
            if player:
                st.sidebar.success(f"👤 {player.display_name or str(player.aoe_profile_id)}")
            else:
                st.sidebar.info(f"👤 Guest (Unlinked)")
        except Exception:
            st.sidebar.warning(get_text("common.error", lang))
        finally:
            db.close()
 
        st.sidebar.caption(f"Steam ID: {steam_id}")
        
        if st.sidebar.button("Logout"):
            del st.session_state["user_steam_id"]
            st.rerun()
    else:
        auth = SteamAuth(realm="http://localhost:8501", return_to="http://localhost:8501")
        login_url = auth.get_login_url()
        st.sidebar.markdown(f"[![Login with Steam](https://community.akamai.steamstatic.com/public/images/signinthroughsteam/sits_01.png)]({login_url})")
 
    st.sidebar.markdown("---")
    
    # Date Range
    today = datetime.now().date()
    last_month = today - timedelta(days=30)
    
    date_range = st.sidebar.date_input(
        get_text("filter.time_period", lang),
        value=(last_month, today),
        max_value=today
    )
    
    # Ladder Type
    ladder_type = st.sidebar.multiselect(
        get_text("filter.ladder", lang),
        options=["RM_1v1", "RM_TEAM", "EW_1v1", "EW_TEAM", "Unranked"],
        default=["RM_1v1", "RM_TEAM"]
    )
    
    # Player Filter
    st.sidebar.markdown("---")
    db = SessionLocal()
    try:
        # Fetch tracked players for filter
        # Only show players that are tracked
        tracked_players = db.query(Player).filter(Player.added_at.isnot(None)).all()
        
        # Sort by display name
        tracked_players.sort(key=lambda x: x.display_name or str(x.aoe_profile_id))
        
        player_options = {p.display_name or str(p.aoe_profile_id): p.aoe_profile_id for p in tracked_players}
        player_names = list(player_options.keys())
        
        selected_player_names = st.sidebar.multiselect(
            "Oyuncular / Players", # Simple bilingual label
            options=player_names,
            default=player_names # Default to all selected
        )
        
        selected_player_ids = [player_options[name] for name in selected_player_names]
        
    except Exception as e:
        st.sidebar.error(f"Error loading players: {e}")
        selected_player_ids = []
    finally:
        db.close()
    
    return {
        "date_range": date_range,
        "ladder_type": ladder_type,
        "language": lang,
        "selected_player_ids": selected_player_ids
    }
