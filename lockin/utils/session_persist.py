import streamlit as st
import streamlit.components.v1 as components

def inject_session_restore():
    """On page load, reads localStorage and pushes email into query param."""
    components.html("""
    <script>
        const email = localStorage.getItem('lockin_email');
        if (email) {
            const url = new URL(window.parent.location.href);
            if (!url.searchParams.get('lockin_email')) {
                url.searchParams.set('lockin_email', email);
                window.parent.history.replaceState({}, '', url.toString());
                window.parent.location.reload();
            }
        }
    </script>
    """, height=0)

def save_session(email: str):
    components.html(f"""
    <script>
        localStorage.setItem('lockin_email', '{email}');
    </script>
    """, height=0)

def clear_session():
    components.html("""
    <script>
        localStorage.removeItem('lockin_email');
    </script>
    """, height=0)