import json
import streamlit as st
from config.taxonomy import DOMAINS, PACE, LEVEL_COLORS
from components.ui import render_progress, section_header, card_open, card_close, domain_badge, review_row
from utils.state import go_to, build_profile, save_profile


def render():
    render_progress(current=3)
    section_header(
        "Review your profile",
        "Everything look good? You can go back to edit anything before submitting.",
    )

    pref      = st.session_state.pref
    knowledge = st.session_state.knowledge

    # ── Preferences summary ───────────────────────────────────────────────────
    card_open("🎯  Preferences")
    rows = [
        ("Name",           pref.get("name",  "—")),
        ("Role",           pref.get("role",  "—") or "—"),
        ("Domains",        ", ".join(pref.get("domains", []))),
        ("Learning Style", pref.get("learning_style", "—")),
        ("Goal",           pref.get("goal",  "—")),
        ("Pace",           f"{pref.get('pace_key', '')}  ·  {pref.get('pace_hours', '')}"),
    ]
    for label, value in rows:
        review_row(label, value)
    card_close()

    # ── Knowledge summary ─────────────────────────────────────────────────────
    if knowledge:
        card_open("🧠  Prior Knowledge")
        for data in knowledge.values():
            badge_cls = f"badge-{DOMAINS[data['domain']]['color']}"
            lc        = LEVEL_COLORS.get(data["level"], "#6b7280")
            topics    = data["comfortable_topics"] or "None specified"
            st.markdown(
                f'<div style="padding:10px 0;border-bottom:1px solid var(--border);">'
                f'  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
                f'    <span class="domain-badge {badge_cls}" style="margin-bottom:0;">{data["subdomain"]}</span>'
                f'    <span style="font-size:0.8rem;font-weight:600;color:{lc};">{data["level"]}</span>'
                f'  </div>'
                f'  <div style="font-size:0.76rem;color:var(--muted);">'
                f'    {data["months_exp"]} month{"s" if data["months_exp"] != 1 else ""} exp'
                f'    &nbsp;·&nbsp; Topics: {topics}'
                f'  </div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        card_close()

    # ── Raw JSON preview ──────────────────────────────────────────────────────
    with st.expander("🔍  View raw profile data (JSON)", expanded=False):
        st.code(json.dumps(build_profile(), indent=2, ensure_ascii=False), language="json")

    # ── Navigation ────────────────────────────────────────────────────────────
    col_back, _, col_submit = st.columns([1, 2, 1])
    with col_back:
        if st.button("← Edit", use_container_width=True):
            go_to(2)
    with col_submit:
        if st.button("✓  Submit Profile", use_container_width=True):
            profile = build_profile()
            save_profile(profile)       # ← swap internals for real DB when ready
            go_to(4)
