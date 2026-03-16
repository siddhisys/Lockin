import streamlit as st
from utils.auth import logout_user

def render_sidebar():
    with st.sidebar:
        st.markdown("## 🔒 Lockin")
        st.markdown("---")

        user = st.session_state.get("user", {})
        pref = st.session_state.get("pref", {})
        name = pref.get("name") or user.get("full_name", "User")

        st.markdown(f"👤 **{name}**")
        st.markdown(f"<small>{user.get('email','')}</small>", unsafe_allow_html=True)
        st.markdown("---")

        nav_items = [
            ("dashboard",     "🏠 Dashboard"),
            ("scraper",       "🌐 Web Scraper"),
            ("summarization", "📄 Summarizer"),
            ("quiz",          "🧩 Quiz Generator"),
            ("chatbot",       "💬 Chatbot"),
            ("profile",       "✏️ Edit Profile")
        ]

        current = st.session_state.get("current_page", "dashboard")
        selected = current

        for key, label in nav_items:
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                selected = key
                st.session_state.current_page = key
                st.rerun()

        st.markdown("---")

        domains = pref.get("domains", [])
        if domains:
            st.markdown("**Studying:**")
            for d in domains[:3]:
                st.markdown(f"• {d}")

        st.markdown("---")
        if st.button("🚪 Sign Out", use_container_width=True):
            logout_user()
            st.rerun()

    return selected