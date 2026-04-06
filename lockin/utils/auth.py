import streamlit as st
import hashlib
import re
from utils.db import create_user, get_user_by_email, get_user_profile

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_auth():
    defaults = {
        "authenticated": False,
        "user": None,
        "onboarding_complete": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Restore from query param written by localStorage JS
    if not st.session_state["authenticated"]:
        email = st.query_params.get("lockin_email")
        if email:
            user = get_user_by_email(email)
            if user:
                st.session_state.authenticated = True
                st.session_state.user = {
                    "id": user["id"],
                    "email": user["email"],
                    "full_name": user["full_name"],
                }
                profile = get_user_profile(user["id"])
                if profile and profile.get("preferences"):
                    st.session_state.onboarding_complete = True
                    st.session_state.pref = profile["preferences"]
                    st.session_state.knowledge = profile["knowledge"] or {}
                else:
                    st.session_state.onboarding_complete = False

def login_user(email, password):
    user = get_user_by_email(email.strip().lower())
    if not user:
        return False, "No account found with that email."
    if user["password_hash"] != hash_password(password):
        return False, "Incorrect password."

    st.session_state.authenticated = True
    st.session_state.user = {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
    }

    # Save to localStorage via query param
    st.query_params["lockin_email"] = user["email"]

    profile = get_user_profile(user["id"])
    if profile and profile.get("preferences"):
        st.session_state.onboarding_complete = True
        st.session_state.pref = profile["preferences"]
        st.session_state.knowledge = profile["knowledge"] or {}
    else:
        st.session_state.onboarding_complete = False

    return True, "Login successful!"

def signup_user(full_name, email, password):
    email = email.strip().lower()
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False, "Please enter a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if not full_name.strip():
        return False, "Please enter your full name."

    result = create_user(email, hash_password(password), full_name.strip())
    if result == "duplicate":
        return False, "An account with this email already exists."
    if not result:
        return False, "Signup failed. Please try again."

    st.session_state.authenticated = True
    st.session_state.user = result
    st.session_state.onboarding_complete = False

    st.query_params["lockin_email"] = result["email"]

    return True, "Account created!"

def logout_user():
    st.query_params.clear()
    for key in ["authenticated", "user", "onboarding_complete", "pref",
                "knowledge", "step", "profile_complete", "current_page"]:
        if key in st.session_state:
            del st.session_state[key]