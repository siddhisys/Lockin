import streamlit as st
from utils.db import init_db
from utils.auth import init_auth
from utils.state import init_app_state

init_db()
init_auth()
init_app_state()

if not st.session_state.get("authenticated"):
    from pages import auth_page
    auth_page.render()

elif not st.session_state.get("onboarding_complete"):
    from pages import onboarding_page
    onboarding_page.render()

else:
    from components.sidebar import render_sidebar
    page = render_sidebar()

    if page == "scraper":
        from pages import scraper_page
        scraper_page.render()
    elif page == "summarization":
        from pages import summarization_page
        summarization_page.render()
    elif page == "quiz":
        from pages import quiz_page
        quiz_page.render()
    elif page == "chatbot":
        from pages import chatbot_page
        chatbot_page.render()
    elif page == "profile":
        from pages import profile_page
        profile_page.render()
    else:
        from pages import dashboard_page
        dashboard_page.render()
