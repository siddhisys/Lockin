import streamlit as st

st.set_page_config(
    page_title="Lockin",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from components.style import apply_global_styles
apply_global_styles()

from utils.db import init_db
from utils.auth import init_auth
from utils.state import init_app_state

init_db()
init_auth()      # restores authenticated=True from ?lockin_email= if present
init_app_state()

# -------- Footer nav query params ----------------------------
_page_param = st.query_params.get("page")
if _page_param == "about":
    st.query_params.pop("page")
    st.session_state["show_about"]   = True
    st.session_state["show_contact"] = False
elif _page_param == "contact":
    st.query_params.pop("page")
    st.session_state["show_contact"] = True
    st.session_state["show_about"]   = False

# -------- Footer pages bypass auth ----------------------------
if st.session_state.get("show_about") or st.session_state.get("show_contact"):
    from components.footer import render_footer
    render_footer()
    st.stop()

if not st.session_state.get("authenticated"):
    from modules import auth_page
    auth_page.render()

elif not st.session_state.get("onboarding_complete"):
    from modules import onboarding_page
    onboarding_page.render()

else:
    from components.navbar import render_navbar
    from components.footer import render_footer

    page = render_navbar()

    import importlib
    pages = {
        "dashboard":     "modules.dashboard_page",
        "scraper":       "modules.scraper_page",
        "summarization": "modules.summarization_page",
        "quiz":          "modules.quiz_page",
        "chatbot":       "modules.chatbot_page",
        "profile":       "modules.profile_page",
    }
    mod = importlib.import_module(pages.get(page, "modules.dashboard_page"))
    mod.render()
    render_footer()