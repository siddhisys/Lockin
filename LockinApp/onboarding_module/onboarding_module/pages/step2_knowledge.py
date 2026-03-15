import streamlit as st
from config.taxonomy import DOMAINS, LEVELS
from components.ui import render_progress, section_header, card_open, card_close, domain_badge, info_chip, divider
from utils.state import go_to


def render():
    render_progress(current=2)

    pref          = st.session_state.pref
    name          = pref.get("name", "there").split()[0]
    domains       = pref.get("domains", [])
    subdomains_map = pref.get("subdomains", {})

    section_header(
        f"What do you already know, {name}?",
        "Rate your existing knowledge across each subdomain. Be honest — this calibrates your learning path.",
    )
    info_chip("Ratings are private and only used to personalise your content recommendations.")

    knowledge = st.session_state.knowledge.copy()

    for domain in domains:
        meta = DOMAINS[domain]
        subs = subdomains_map.get(domain, meta["subdomains"])

        card_open(
            f"{meta['icon']}  {domain}",
            "Rate your current knowledge level in each selected subdomain.",
        )

        if not subs:
            st.markdown(
                '<span style="color:var(--muted);font-size:0.83rem;">No subdomains selected for this domain.</span>',
                unsafe_allow_html=True,
            )
        else:
            for sub in subs:
                key          = f"{domain}::{sub}"
                current_val  = knowledge.get(key, {})

                domain_badge(sub, meta["color"])

                col_level, col_exp = st.columns([2, 3])
                with col_level:
                    level = st.select_slider(
                        f"Level — {sub}",
                        options=LEVELS,
                        value=current_val.get("level", "Beginner"),
                        key=f"level_{key}",
                        label_visibility="collapsed",
                    )
                with col_exp:
                    months = st.slider(
                        f"Months of experience — {sub}",
                        min_value=0, max_value=60, step=1,
                        value=current_val.get("months_exp", 0),
                        key=f"months_{key}",
                        label_visibility="collapsed",
                        help="Drag to set months of hands-on experience (0 = none)",
                    )
                    st.markdown(
                        f'<div style="font-size:0.75rem;color:var(--muted);margin-top:-8px;">'
                        f'Experience: <b style="color:var(--text)">'
                        f'{months} month{"s" if months != 1 else ""}</b></div>',
                        unsafe_allow_html=True,
                    )

                topics = st.text_input(
                    "Topics you're comfortable with (comma-separated)",
                    value=current_val.get("comfortable_topics", ""),
                    key=f"topics_{key}",
                    placeholder="e.g. linear regression, pandas, REST APIs",
                )

                knowledge[key] = {
                    "domain":             domain,
                    "subdomain":          sub,
                    "level":              level,
                    "months_exp":         months,
                    "comfortable_topics": topics,
                }

                divider()

        card_close()

    # ── Navigation ────────────────────────────────────────────────────────────
    col_back, _, col_next = st.columns([1, 2, 1])
    with col_back:
        if st.button("← Back", use_container_width=True):
            go_to(1)
    with col_next:
        if st.button("Review →", use_container_width=True):
            st.session_state.knowledge = knowledge
            go_to(3)
