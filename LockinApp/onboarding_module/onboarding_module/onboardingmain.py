import streamlit as st
from config.styles import STYLES
from utils.state import init_state
from pages import step1_preferences, step2_knowledge, step3_review, step4_success

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Onboarding · User Profile",
    page_icon="🧭",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─── Inject CSS ───────────────────────────────────────────────────────────────
st.markdown(STYLES, unsafe_allow_html=True)

# ─── State ────────────────────────────────────────────────────────────────────
init_state()

# ─── Router ───────────────────────────────────────────────────────────────────
STEP_MAP = {
    1: step1_preferences,
    2: step2_knowledge,
    3: step3_review,
    4: step4_success,
}

page = STEP_MAP.get(st.session_state.step)
if page:
    page.render()
