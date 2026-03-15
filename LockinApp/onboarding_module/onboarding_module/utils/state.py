import streamlit as st
from datetime import datetime


def init_state():
    """Initialise all session state keys with defaults."""
    defaults = {
        "step":             1,
        "pref":             {},
        "knowledge":        {},
        "profile_complete": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def go_to(step: int):
    st.session_state.step = step
    st.rerun()


def reset():
    for key in ["step", "pref", "knowledge", "profile_complete"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


def build_profile() -> dict:
    """
    Assemble the final profile dict ready to persist.
    Replace the placeholder comment below with your DB write once connected.
    """
    return {
        "user_id":    None,               # ← populate from auth / DB on save
        "created_at": datetime.now().isoformat(),
        "preferences": st.session_state.pref,
        "knowledge":   st.session_state.knowledge,
        "status":      "pending_db",      # ← update to "saved" after DB write
    }


def save_profile(profile: dict):
    """
    Placeholder — swap this body for your actual DB call.

    Example (MongoDB):
        from db import get_collection
        col = get_collection("user_profiles")
        result = col.insert_one(profile)
        return str(result.inserted_id)

    Example (Supabase):
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        client.table("user_profiles").insert(profile).execute()
    """
    # For now, just flag success in session state
    st.session_state.profile_complete = True
