import streamlit as st
from config.taxonomy import DOMAINS, LEARNING_STYLES, GOALS, PACE
from components.ui import render_progress, section_header, card_open, card_close, domain_badge, divider
from utils.state import go_to


def render():
    render_progress(current=1)
    section_header(
        "Tell us about yourself",
        "Help us personalise your learning journey. This takes about 2 minutes.",
    )

    pref = st.session_state.pref

    # ── Basic Info ────────────────────────────────────────────────────────────
    card_open("👤  Basic Info", "We'll use this to personalise greetings and your profile.")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full name", value=pref.get("name", ""), placeholder="e.g. Siddhi Mehta")
    with col2:
        role = st.text_input("Current role / occupation", value=pref.get("role", ""), placeholder="e.g. CS Student")
    card_close()

    # ── Domain Selection ──────────────────────────────────────────────────────
    card_open("🎯  Domains of Interest", "Select one or more domains you want to focus on. You can change these later.")

    selected_domains = st.multiselect(
        "Choose domains",
        options=list(DOMAINS.keys()),
        default=pref.get("domains", []),
        placeholder="Pick at least one…",
    )

    selected_subdomains = pref.get("subdomains", {})

    if selected_domains:
        divider()
        st.markdown(
            '<div style="font-size:0.82rem;color:var(--muted);margin-bottom:1rem;">'
            "Now pick your focus subdomains within each:</div>",
            unsafe_allow_html=True,
        )
        for domain in selected_domains:
            meta = DOMAINS[domain]
            domain_badge(f"{meta['icon']} {domain}", meta["color"])
            selected_subdomains[domain] = st.multiselect(
                f"Subdomains in {domain}",
                options=meta["subdomains"],
                default=selected_subdomains.get(domain, []),
                key=f"sub_{domain}",
                label_visibility="collapsed",
            )

    card_close()

    # ── Learning Style ────────────────────────────────────────────────────────
    card_open("🧠  Learning Style", "How do you learn best? Pick your primary style.")
    learning_style = st.radio(
        "Learning style",
        options=LEARNING_STYLES,
        index=LEARNING_STYLES.index(pref.get("learning_style", LEARNING_STYLES[0])),
        label_visibility="collapsed",
    )
    card_close()

    # ── Goal & Pace ───────────────────────────────────────────────────────────
    card_open("🚀  Goal & Pace", "This helps us recommend the right content density and track your progress.")
    col_g, col_p = st.columns(2)
    with col_g:
        goal = st.selectbox(
            "Primary goal",
            options=GOALS,
            index=GOALS.index(pref.get("goal", GOALS[0])),
        )
    with col_p:
        pace_key = st.selectbox(
            "Weekly learning pace",
            options=list(PACE.keys()),
            index=list(PACE.keys()).index(pref.get("pace_key", "Steady")),
            format_func=lambda k: f"{k}  ·  {PACE[k]}",
        )
    card_close()

    # ── Navigation ────────────────────────────────────────────────────────────
    _, col_next = st.columns([3, 1])
    with col_next:
        if st.button("Next →", use_container_width=True):
            if not name.strip():
                st.error("Please enter your name before continuing.")
            elif not selected_domains:
                st.error("Please select at least one domain.")
            else:
                st.session_state.pref = {
                    "name":           name.strip(),
                    "role":           role.strip(),
                    "domains":        selected_domains,
                    "subdomains":     selected_subdomains,
                    "learning_style": learning_style,
                    "goal":           goal,
                    "pace_key":       pace_key,
                    "pace_hours":     PACE[pace_key],
                }
                go_to(2)
