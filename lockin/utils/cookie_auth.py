import streamlit as st
import streamlit.components.v1 as components

def set_auth_cookie(email: str):
    """Set an authentication cookie in the browser to persist login session."""
    components.html(f"""
    <script>
        // Set cookie with email, expires in 30 days (2592000 seconds)
        document.cookie = "lockin_email={email}; path=/; max-age=2592000; SameSite=Lax";
    </script>
    """, height=0)  # height=0 makes the component invisible

def clear_auth_cookie():
    """Remove the authentication cookie during logout."""
    components.html("""
    <script>
        // Delete cookie by setting max-age=0 (immediate expiration)
        document.cookie = "lockin_email=; path=/; max-age=0; SameSite=Lax";
    </script>
    """, height=0)

def get_auth_cookie() -> str | None:
    """
    Read cookie via query param trick — inject JS that appends cookie to URL.
    
    Python can't directly read browser cookies, so JavaScript reads the cookie
    and adds it as a query parameter. Streamlit's st.query_params can then access it.
    """
    components.html("""
    <script>
        // Helper function to extract cookie value by name
        function getCookie(name) {
            const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
            return match ? match[2] : null;
        }
        
        // Read the lockin_email cookie
        const email = getCookie('lockin_email');
        
        // If cookie exists and not already in URL, add it as a query parameter
        if (email) {
            const url = new URL(window.parent.location.href);
            if (!url.searchParams.get('lockin_email')) {
                url.searchParams.set('lockin_email', email);
                window.parent.history.replaceState({}, '', url);
            }
        }
    </script>
    """, height=0)