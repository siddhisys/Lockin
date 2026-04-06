import streamlit as st

def _nav(page):
    st.session_state.current_page = page
    st.rerun()

def render():
    pref    = st.session_state.get("pref", {})
    name    = pref.get("name", "there").split()[0]
    domains = pref.get("domains", [])
    pace    = pref.get("pace_key", "Steady")
    goal    = pref.get("goal", "—")

    # ---------- Welcome header ----------------------------
    st.markdown(f"""
    <div style="margin-bottom:2rem;">
        <h1 style="margin-bottom:.25rem;">Welcome back, {name} 👋</h1>
        <p style="color:var(--text-muted);font-size:1rem;margin:0;">
            Your personalised AI learning hub. Pick up where you left off.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ------- Profile snapshot ----------------------------
    col1, col2, col3 = st.columns(3)
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

    # -------- Learning flow banner ----------------------------
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

    # -------- Tool cards ----------------------------
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
        ("chatbot",       "💬", "Chatbot",         "Chat with your PDF documents or ask the AI any question you have.",        "Step 4"),
    ]

    col_a, col_b = st.columns(2)
    cols = [col_a, col_b, col_a, col_b]

    for (page, icon, title, desc, badge), col in zip(tools, cols):
        with col:
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
            if st.button(f"Open {title}", key=f"dash_{page}", use_container_width=True):
                _nav(page)