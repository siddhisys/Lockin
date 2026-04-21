import streamlit as st

# Navigation items in order: (session_state key, display label)
NAV_ITEMS = [
    ("dashboard",     "🏠 Dashboard"),
    ("scraper",       "🌐 Web Scraper"),
    ("summarization", "📄 Summarizer"),
    ("quiz",          "🧩 Quiz"),
    ("chatbot",       "💬 Chatbot"),
    ("profile",       "✏️ Profile"),
]


def render_navbar():
    """
    Renders the fixed top brand bar and the horizontal navigation button row.
    Returns the current active page key so the caller knows which page to render.
    """

    # Default to dashboard if no page has been set yet
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "dashboard"

    current = st.session_state["current_page"]

    # ------------------------------------------------------------------
    # Fixed top bar (brand only)
    # Dynamic content is intentionally kept out of this HTML block to
    # avoid quote-escaping issues with f-strings inside unsafe HTML.
    # ------------------------------------------------------------------
    st.markdown("""
    <style>
    /* Hide Streamlit's default header and sidebar chrome */
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }

    /* Fixed brand bar pinned to the top of the viewport */
    .lk-fixed-nav {
        position:      fixed;
        top:           0; left: 0; right: 0;
        height:        52px;
        background:    #FFFFFF;
        border-bottom: 1px solid #E9E7E2;
        display:       flex;
        align-items:   center;
        padding:       0 1.5rem;
        z-index:       999999;
        box-shadow:    0 1px 4px rgba(0,0,0,0.05);
    }

    /* Brand wordmark style */
    .lk-brand {
        font-family:    Georgia, serif;
        font-size:      1.05rem;
        font-weight:    400;
        color:          #18181B;
        letter-spacing: -0.02em;
    }

    /* Push page content down so it isn't hidden behind the fixed bar */
    .main .block-container {
        padding-top: 4.5rem !important;
    }
    </style>
    <div class="lk-fixed-nav">
        <div class="lk-brand">🔒 Lockin</div>
    </div>
    """, unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # Navigation button row — one column per nav item
    # ------------------------------------------------------------------
    cols = st.columns(len(NAV_ITEMS))

    for i, (key, label) in enumerate(NAV_ITEMS):
        with cols[i]:
            if current == key:
                # Active page: render a styled highlight pill instead of
                # a clickable button (no point navigating to current page)
                st.markdown(
                    f"<div style='text-align:center;padding:.35rem .1rem;'>"
                    f"<span style='background:#D1FAE5;color:#7fb099;"
                    f"border-radius:8px;padding:.35rem .7rem;"
                    f"font-size:.82rem;font-weight:600;"
                    f"font-family:sans-serif;white-space:nowrap;'>"
                    f"{label}</span></div>",
                    unsafe_allow_html=True
                )
            else:
                # Inactive page: real Streamlit button that triggers navigation
                if st.button(label, key=f"nav_{key}",
                             use_container_width=True):
                    st.session_state["current_page"] = key

                    # Clear footer sub-page flags so About/Contact pages
                    # don't persist when the user navigates away
                    st.session_state["show_about"]   = False
                    st.session_state["show_contact"] = False

                    st.rerun()

    # Thin divider line separating the nav row from the page content below
    st.markdown(
        "<div style='height:1px;background:#E9E7E2;margin:.25rem 0 1.5rem;'></div>",
        unsafe_allow_html=True
    )

    # Return the active page key so the caller can render the correct page
    return st.session_state["current_page"]