import streamlit as st

NAV_ITEMS = [
    ("dashboard",     "🏠 Dashboard"),
    ("scraper",       "🌐 Web Scraper"),
    ("summarization", "📄 Summarizer"),
    ("quiz",          "🧩 Quiz"),
    ("chatbot",       "💬 Chatbot"),
    ("profile",       "✏️ Profile"),
]

def render_navbar():
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "dashboard"

    current = st.session_state["current_page"]

    # ----- Fixed top bar (brand only — no dynamic content to avoid quote issues)
    st.markdown("""
    <style>
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }

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
    .lk-brand {
        font-family:    Georgia, serif;
        font-size:      1.05rem;
        font-weight:    400;
        color:          #18181B;
        letter-spacing: -0.02em;
    }
    .main .block-container {
        padding-top: 4.5rem !important;
    }
    </style>
    <div class="lk-fixed-nav">
        <div class="lk-brand">🔒 Lockin</div>
    </div>
    """, unsafe_allow_html=True)

    # -------- Nav buttons as real Streamlit buttons ----------------------------
    cols = st.columns(len(NAV_ITEMS))
    for i, (key, label) in enumerate(NAV_ITEMS):
        with cols[i]:
            if current == key:
                # Active — styled div, no button
                st.markdown(
                    f"<div style='text-align:center;padding:.35rem .1rem;'>"
                    f"<span style='background:#D1FAE5;color:#1C4532;"
                    f"border-radius:8px;padding:.35rem .7rem;"
                    f"font-size:.82rem;font-weight:600;"
                    f"font-family:sans-serif;white-space:nowrap;'>"
                    f"{label}</span></div>",
                    unsafe_allow_html=True
                )
            else:
                if st.button(label, key=f"nav_{key}",
                             use_container_width=True):
                    st.session_state["current_page"] = key
                    # Clear footer page flags when navigating
                    st.session_state["show_about"]   = False
                    st.session_state["show_contact"] = False
                    st.rerun()

    st.markdown(
        "<div style='height:1px;background:#E9E7E2;margin:.25rem 0 1.5rem;'></div>",
        unsafe_allow_html=True
    )

    return st.session_state["current_page"]