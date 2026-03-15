import streamlit as st
from config.taxonomy import PACE
from utils.state import reset


def render():
    pref    = st.session_state.pref
    name    = pref.get("name", "there").split()[0]
    domains = pref.get("domains", [])
    pace_k  = pref.get("pace_key", "Steady")

    st.markdown(
        f"""
        <div class="success-wrap">
            <div class="success-icon">🎉</div>
            <div class="success-title">You're all set, {name}!</div>
            <div class="success-sub">
                Your profile has been saved and your personalised learning path is being prepared.<br><br>
                <strong style="color:var(--text);">Domains:</strong> {", ".join(domains)}<br>
                <strong style="color:var(--text);">Pace:</strong> {pace_k} · {PACE.get(pace_k, "")}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    _, col_btn, _ = st.columns([1, 2, 1])
    with col_btn:
        if st.button("🔄  Restart Onboarding", use_container_width=True):
            reset()
