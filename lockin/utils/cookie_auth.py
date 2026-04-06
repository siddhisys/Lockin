import streamlit as st
import streamlit.components.v1 as components

def set_auth_cookie(email: str):
    components.html(f"""
    <script>
        document.cookie = "lockin_email={email}; path=/; max-age=2592000; SameSite=Lax";
    </script>
    """, height=0)

def clear_auth_cookie():
    components.html("""
    <script>
        document.cookie = "lockin_email=; path=/; max-age=0; SameSite=Lax";
    </script>
    """, height=0)

def get_auth_cookie() -> str | None:
    """Read cookie via query param trick — inject JS that appends cookie to URL."""
    # We can't read cookies directly from Python; we use st.query_params instead.
    # JS writes the cookie value into ?lockin_email=... on first load.
    components.html("""
    <script>
        function getCookie(name) {
            const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
            return match ? match[2] : null;
        }
        const email = getCookie('lockin_email');
        if (email) {
            const url = new URL(window.parent.location.href);
            if (!url.searchParams.get('lockin_email')) {
                url.searchParams.set('lockin_email', email);
                window.parent.history.replaceState({}, '', url);
            }
        }
    </script>
    """, height=0)