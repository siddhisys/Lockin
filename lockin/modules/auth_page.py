import streamlit as st
from utils.auth import login_user, signup_user


def render():
    """
    Renders the authentication page with two tabs: Sign In and Create Account.
    Centres the form in a narrow middle column to keep it compact and focused.
    On success, calls st.rerun() so the app re-evaluates session state and
    redirects the user to the main app without an explicit page navigation call.
    """

    # Three-column layout — content lives in the middle column only,
    # leaving the outer columns as blank gutters for visual centering
    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        # App branding
        st.markdown("# 🔒 Lockin")
        st.markdown("##### Your personalised AI learning companion")
        st.markdown("---")

        # Two tabs: existing users sign in on the left, new users sign up on the right
        tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])

        # ----------------------------------------------------------------
        # SIGN IN TAB
        # ----------------------------------------------------------------
        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)

            email    = st.text_input("Email",    key="login_email", placeholder="you@example.com")
            password = st.text_input("Password", type="password",   key="login_pass")

            if st.button("Sign In", use_container_width=True, key="login_btn"):
                # Client-side guard: ensure both fields are filled before hitting the backend
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    with st.spinner("Signing in..."):
                        ok, msg = login_user(email, password)  # returns (success: bool, message: str)

                    if ok:
                        st.success(msg)
                        st.rerun()   # re-run triggers the session-state check that redirects to the app
                    else:
                        st.error(msg)

        # ----------------------------------------------------------------
        # CREATE ACCOUNT TAB
        # ----------------------------------------------------------------
        with tab_signup:
            st.markdown("<br>", unsafe_allow_html=True)

            full_name  = st.text_input("Full Name",        key="signup_name",  placeholder="e.g. Siddhi Mehta")
            email_s    = st.text_input("Email",            key="signup_email", placeholder="you@example.com")
            password_s = st.text_input("Password",         type="password",    key="signup_pass",  placeholder="Min. 6 characters")
            password_c = st.text_input("Confirm Password", type="password",    key="signup_pass2")

            if st.button("Create Account", use_container_width=True, key="signup_btn"):
                # Client-side validation before calling the backend
                if not all([full_name, email_s, password_s, password_c]):
                    st.error("Please fill in all fields.")
                elif password_s != password_c:
                    # Catch mismatched passwords early — no need to hit the server
                    st.error("Passwords do not match.")
                else:
                    with st.spinner("Creating account..."):
                        ok, msg = signup_user(full_name, email_s, password_s)  # returns (success: bool, message: str)

                    if ok:
                        st.success(msg)
                        st.rerun()   # re-run triggers the session-state check that redirects to the app
                    else:
                        st.error(msg)