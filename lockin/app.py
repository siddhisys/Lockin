import streamlit as st

# Configure Streamlit page settings (must be the first Streamlit command)
st.set_page_config(
    page_title="Lockin",                    # Browser tab title
    page_icon="🔒",                         # Browser tab icon
    layout="wide",                          # Use full width of the browser
    initial_sidebar_state="collapsed",      # Hide sidebar by default
)

# Import and apply custom CSS styles
from components.style import apply_global_styles
apply_global_styles()

# Import database, auth, and state management utilities
from utils.db import init_db
from utils.auth import init_auth
from utils.state import init_app_state

# Initialize database tables if they don't exist
init_db()
# Restore authentication session from query parameter (if present)
init_auth()      # restores authenticated=True from ?lockin_email= if present
# Initialize all session state variables with defaults
init_app_state()

# -------- Footer nav query params ----------------------------
# Handle navigation to footer pages (About, Contact) via URL query parameters
# These pages don't require authentication
_page_param = st.query_params.get("page")
if _page_param == "about":
    st.query_params.pop("page")              # Remove param to clean URL
    st.session_state["show_about"]   = True
    st.session_state["show_contact"] = False
elif _page_param == "contact":
    st.query_params.pop("page")
    st.session_state["show_contact"] = True
    st.session_state["show_about"]   = False

# -------- Footer pages bypass auth ----------------------------
# Render footer-only pages (About, Contact) without requiring login
if st.session_state.get("show_about") or st.session_state.get("show_contact"):
    from components.footer import render_footer
    render_footer()
    st.stop()  # Stop execution here, don't show login or main app

# Authentication check - user must be logged in
if not st.session_state.get("authenticated"):
    from modules import auth_page
    auth_page.render()  # Show login/signup page

# Onboarding check - new users must complete setup
elif not st.session_state.get("onboarding_complete"):
    from modules import onboarding_page
    onboarding_page.render()  # Show preferences and knowledge setup

# Main application - user is authenticated and onboarded
else:
    from components.navbar import render_navbar
    from components.footer import render_footer

    # Render navigation bar and get the selected page
    page = render_navbar()

    # Dynamic page routing using importlib
    import importlib
    
    # Map page names to their module paths
    pages = {
        "dashboard":     "modules.dashboard_page",
        "scraper":       "modules.scraper_page",
        "summarization": "modules.summarization_page",
        "quiz":          "modules.quiz_page",
        "chatbot":       "modules.chatbot_page",
        "profile":       "modules.profile_page",
    }
    
    # Dynamically import and render the selected page module
    # Default to dashboard if page not found
    mod = importlib.import_module(pages.get(page, "modules.dashboard_page"))
    mod.render()  # Call the render() function of the imported module
    
    # Render footer on all main app pages
    render_footer()