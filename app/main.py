
import streamlit as st
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import settings

from services.i18n import get_text

def main():
    st.set_page_config(
        page_title="AoE2:DE Stats Tracker",
        page_icon="⚔️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Language
    if "language" not in st.session_state:
        st.session_state["language"] = "tr"
        
    from app.components.sidebar import render_sidebar
    render_sidebar()
    lang = st.session_state["language"]
    
    st.title(f"⚔️ {get_text('home.title', lang)}")
    
    st.markdown(f"""
    ### {get_text('home.welcome', lang)}
    {get_text('home.intro', lang)}
    
    **Features:**
    - 📊 **{get_text('sidebar.overview', lang)}**
    - 👤 **{get_text('sidebar.profile', lang)}**
    - 🆚 **{get_text('sidebar.matchups', lang)}**
    - 🤝 **{get_text('sidebar.synergy', lang)}**
    """)
    
    st.info(get_text('home.intro', lang))

    # Steam Auth Handler
    query_params = st.query_params
    if "openid.mode" in query_params:
        st.write("Verifying Login...")
        from services.auth_steam import SteamAuth
        
        auth = SteamAuth(realm="http://localhost:8501", return_to="http://localhost:8501")
        steam_id = auth.validate(dict(query_params))
        
        if steam_id:
            st.session_state["user_steam_id"] = steam_id
            st.success(f"Logged in successfully! Steam ID: {steam_id}")
            # Clear params to clean URL
            st.query_params.clear()
            st.rerun()
        else:
            st.error("Login verification failed.")


if __name__ == "__main__":
    main()
