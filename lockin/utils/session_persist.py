import streamlit as st
import streamlit.components.v1 as components

def inject_session_restore():
    """
    On page load, reads email from localStorage and pushes it into query parameters.
    
    This function is called during app initialization to restore a user's
    previous session. It injects JavaScript that:
    1. Checks localStorage for saved email
    2. If found and not already in URL, adds it as ?lockin_email= parameter
    3. Reloads the page so Streamlit can read the query parameter
    
    The reload is necessary because Streamlit only reads query parameters
    during initial page load, not after they're dynamically added.
    """
    components.html("""
    <script>
        // Try to retrieve saved email from localStorage
        const email = localStorage.getItem('lockin_email');
        
        // If email exists and not already in URL query parameters
        if (email) {
            const url = new URL(window.parent.location.href);
            if (!url.searchParams.get('lockin_email')) {
                // Add email as query parameter
                url.searchParams.set('lockin_email', email);
                // Update URL without triggering navigation
                window.parent.history.replaceState({}, '', url.toString());
                // Reload page so Streamlit can read the new query param
                window.parent.location.reload();
            }
        }
    </script>
    """, height=0)  # height=0 makes the component invisible

def save_session(email: str):
    """
    Save user's email to localStorage for session persistence.
    
    Called after successful login to remember the user across browser sessions.
    The email is stored in localStorage, which persists until explicitly cleared.
    
    Args:
        email: User's email address to store
    """
    components.html(f"""
    <script>
        // Store email in localStorage (persists across browser sessions)
        localStorage.setItem('lockin_email', '{email}');
    </script>
    """, height=0)

def clear_session():
    """
    Remove user's email from localStorage during logout.
    
    Called when user logs out to prevent automatic re-login on next visit.
    This ensures the session is completely terminated.
    """
    components.html("""
    <script>
        // Remove email from localStorage
        localStorage.removeItem('lockin_email');
    </script>
    """, height=0)