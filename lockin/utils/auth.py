import streamlit as st
import hashlib
import re
from utils.db import create_user, get_user_by_email, get_user_profile

def hash_password(password):
    """
    Hash a plaintext password using SHA-256.
    
    Note: In production, use a stronger hashing algorithm like bcrypt or Argon2
    with salting. This is simplified for demonstration purposes.
    
    Args:
        password: Plaintext password string
        
    Returns:
        Hexadecimal hash string of the password
    """
    return hashlib.sha256(password.encode()).hexdigest()

def init_auth():
    """
    Initialize authentication state and restore session from query parameters.
    
    This function:
    1. Sets default values for authentication-related session state variables
    2. Attempts to restore a previous login session from URL query parameters
    3. Fetches user profile data if available
    
    The query parameter method allows session persistence across page reloads
    and browser restarts via localStorage (set by frontend JavaScript).
    """
    # Define default values for authentication state
    defaults = {
        "authenticated": False,      # Whether user is logged in
        "user": None,                # User object with id, email, full_name
        "onboarding_complete": False, # Whether user completed initial setup
    }
    
    # Initialize any missing session state keys with their defaults
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Attempt to restore session from query parameter
    # This allows "Remember Me" functionality across browser sessions
    if not st.session_state["authenticated"]:
        email = st.query_params.get("lockin_email")
        if email:
            user = get_user_by_email(email)
            if user:
                # Restore authentication state
                st.session_state.authenticated = True
                st.session_state.user = {
                    "id": user["id"],
                    "email": user["email"],
                    "full_name": user["full_name"],
                }
                
                # Fetch user profile to restore preferences and knowledge state
                profile = get_user_profile(user["id"])
                if profile and profile.get("preferences"):
                    # User has completed onboarding previously
                    st.session_state.onboarding_complete = True
                    st.session_state.pref = profile["preferences"]  # User's learning preferences
                    st.session_state.knowledge = profile["knowledge"] or {}  # User's knowledge state
                else:
                    # New user or missing profile - needs onboarding
                    st.session_state.onboarding_complete = False

def login_user(email, password):
    """
    Authenticate a user with email and password.
    
    Args:
        email: User's email address (case-insensitive)
        password: Plaintext password to verify
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Normalize email to lowercase for consistent lookup
    user = get_user_by_email(email.strip().lower())
    
    # Check if user exists
    if not user:
        return False, "No account found with that email."
    
    # Verify password by comparing hashes
    if user["password_hash"] != hash_password(password):
        return False, "Incorrect password."

    # Set authentication state in session
    st.session_state.authenticated = True
    st.session_state.user = {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
    }

    # Persist login by storing email in query parameter
    # This will be picked up by init_auth() on next load
    st.query_params["lockin_email"] = user["email"]

    # Check if user has completed onboarding and load their preferences
    profile = get_user_profile(user["id"])
    if profile and profile.get("preferences"):
        # Returning user - restore their settings
        st.session_state.onboarding_complete = True
        st.session_state.pref = profile["preferences"]
        st.session_state.knowledge = profile["knowledge"] or {}
    else:
        # New user or missing profile - needs onboarding
        st.session_state.onboarding_complete = False

    return True, "Login successful!"

def signup_user(full_name, email, password):
    """
    Create a new user account.
    
    Args:
        full_name: User's full name
        email: User's email address (must be unique)
        password: Plaintext password (minimum 6 characters)
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Normalize inputs
    email = email.strip().lower()
    
    # Input validation
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False, "Please enter a valid email address."
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    
    if not full_name.strip():
        return False, "Please enter your full name."

    # Attempt to create user in database
    result = create_user(email, hash_password(password), full_name.strip())
    
    # Handle duplicate email case
    if result == "duplicate":
        return False, "An account with this email already exists."
    
    # Check for other database errors
    if not result:
        return False, "Signup failed. Please try again."

    # Auto-login after successful signup
    st.session_state.authenticated = True
    st.session_state.user = result  # User dict from database
    st.session_state.onboarding_complete = False  # New user needs onboarding

    # Persist session via query parameter
    st.query_params["lockin_email"] = result["email"]

    return True, "Account created!"

def logout_user():
    """
    Log out the current user and clear all session data.
    
    This function:
    1. Clears the query parameters (removes persistent login)
    2. Removes all authentication-related session state variables
    """
    # Clear query parameters to prevent auto-login on next visit
    st.query_params.clear()
    
    # List of all authentication-related session keys to remove
    auth_keys = [
        "authenticated",      # Login status
        "user",              # User object
        "onboarding_complete", # Onboarding status
        "pref",              # User preferences
        "knowledge",         # Knowledge state
        "step",              # Current onboarding step
        "profile_complete",  # Profile completion flag
        "current_page"       # Current page in the app
    ]
    
    # Remove each key if it exists in session state
    for key in auth_keys:
        if key in st.session_state:
            del st.session_state[key]