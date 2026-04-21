import streamlit as st
from utils.auth import logout_user


def _nav(page):
    """Navigate to a different page by updating session state and rerunning."""
    st.session_state.current_page = page
    st.rerun()


def render():
    """
    Renders the Dashboard — the main landing page after login.
    Displays a personalised welcome header, a three-card profile snapshot,
    a suggested learning flow banner, and a 2x2 grid of tool cards.
    All user preferences are read from st.session_state["pref"].
    """

    # Pull user preferences from session state, with safe fallbacks
    pref    = st.session_state.get("pref", {})
    name    = pref.get("name", "there").split()[0]  # first name only
    domains = pref.get("domains", [])
    pace    = pref.get("pace_key", "Steady")
    goal    = pref.get("goal", "—")

    # ----------------------------------------------------------------
    # Top bar — logout button pinned to the far right
    # ----------------------------------------------------------------
    top_col1, top_col2 = st.columns([8, 1])

    with top_col2:
        st.markdown("<div style='margin-top:1.2rem'></div>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()  # rerun so the session-state check redirects to the login page

    # ----------------------------------------------------------------
    # Welcome header — personalised with the user's first name
    # ----------------------------------------------------------------
    st.markdown(f"""
    <div style="margin-bottom:2rem;">
        <h1 style="margin-bottom:.25rem;">Welcome back, {name} 👋</h1>
        <p style="color:var(--text-muted);font-size:1rem;margin:0;">
            Your personalised AI learning hub. Pick up where you left off.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ----------------------------------------------------------------
    # Profile snapshot — three stat cards (Goal, Pace, Domains)
    # ----------------------------------------------------------------
    col1, col2, col3 = st.columns(3)

    # Zip the column objects with their card data for a clean loop
    cards = [
        ("🎯", "Goal",    goal),
        ("⏱️", "Pace",    pace),
        ("📚", "Domains", ", ".join(domains) if domains else "—"),
    ]

    for col, (icon, label, value) in zip([col1, col2, col3], cards):
        with col:
            st.markdown(f"""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:1.1rem 1.4rem;
                box-shadow:var(--shadow-sm);">
                <div style="font-size:.72rem;font-weight:600;letter-spacing:.07em;
                    text-transform:uppercase;color:var(--text-muted);margin-bottom:.35rem;">
                    {icon} {label}
                </div>
                <div style="font-size:.9375rem;font-weight:500;color:var(--text);">
                    {value}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)

    # ----------------------------------------------------------------
    # Suggested learning flow banner
    # Guides new users through the intended step-by-step workflow
    # ----------------------------------------------------------------
    st.markdown("""
    <div style="background:var(--accent-light);border:1px solid #A7F3D0;
        border-radius:var(--radius-lg);padding:1rem 1.5rem;margin-bottom:2rem;
        display:flex;align-items:center;gap:.75rem;">
        <span style="font-size:1.25rem;">💡</span>
        <div>
            <div style="font-size:.875rem;font-weight:600;color:var(--accent);">
                Suggested learning flow
            </div>
            <div style="font-size:.82rem;color:var(--accent-mid);margin-top:.15rem;">
                Web Scraper → AI Summarizer → Quiz Generator → Chatbot
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ----------------------------------------------------------------
    # Tool cards — 2x2 grid, one card per app feature
    # Each entry: (page key, icon, title, description, step badge)
    # ----------------------------------------------------------------
    st.markdown("""
    <div style="font-size:.72rem;font-weight:600;letter-spacing:.08em;
        text-transform:uppercase;color:var(--text-muted);margin-bottom:.75rem;">
        Your Tools
    </div>
    """, unsafe_allow_html=True)

    tools = [
        ("scraper",       "🌐", "Web Scraper",    "Scrape Wikipedia & docs by topic. Download as PDF to use in other tools.", "Step 1"),
        ("summarization", "📄", "AI Summarizer",  "Upload any PDF and get a concise, AI-generated summary in seconds.",       "Step 2"),
        ("quiz",          "🧩", "Quiz Generator", "Turn any PDF into a multiple-choice quiz. Test what you've learned.",      "Step 3"),
        ("chatbot",       "💬", "Chatbot",        "Chat with your PDF documents or ask the AI any question you have.",        "Step 4"),
    ]

    # Two columns, tools alternate: [0,2] go in col_a, [1,3] go in col_b
    col_a, col_b = st.columns(2)
    cols = [col_a, col_b, col_a, col_b]

    for (page, icon, title, desc, badge), col in zip(tools, cols):
        with col:
            # Card body — rendered as HTML for full styling control.
            # The "Open" button is a separate Streamlit widget rendered
            # directly below so it remains interactive (HTML buttons can't
            # trigger Python callbacks).
            st.markdown(f"""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:1.4rem 1.5rem;
                box-shadow:var(--shadow-sm);margin-bottom:1rem;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:.75rem;">
                    <span style="font-size:1.75rem;">{icon}</span>
                    <span style="font-size:.7rem;font-weight:600;
                        background:var(--accent-light);color:var(--accent);
                        border-radius:20px;padding:.2rem .65rem;">{badge}</span>
                </div>
                <div style="font-size:.9375rem;font-weight:600;
                    color:var(--text);margin-bottom:.35rem;">{title}</div>
                <div style="font-size:.85rem;color:var(--text-muted);
                    line-height:1.5;margin-bottom:1rem;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

            # "Open" button — navigates to the tool's page on click
            if st.button(f"Open {title}", key=f"dash_{page}", use_container_width=True):
                _nav(page)