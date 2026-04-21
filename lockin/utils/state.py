import streamlit as st

# ---------------------------------------------------------------------------
# In-memory scrape cache  (lives for the duration of the Streamlit process)
# Key: (domain, subdomain)
# Value: {"pdf": bytes, "chunks": list, "summary": str|None, "quiz": list|None}
# ---------------------------------------------------------------------------
_SCRAPE_CACHE: dict = {}  # Global cache dictionary that persists across reruns but resets when app restarts

def cache_key(domain: str, subdomain: str) -> tuple:
    """Generate a normalized cache key from domain and subdomain.
    
    Converts both to lowercase and strips whitespace for consistent lookup.
    
    Args:
        domain: Website domain (e.g., "example.com")
        subdomain: Subdomain path (e.g., "/docs/page")
        
    Returns:
        Tuple of (normalized_domain, normalized_subdomain)
    """
    return (domain.strip().lower(), subdomain.strip().lower())


def get_cached(domain: str, subdomain: str) -> dict | None:
    """Retrieve the full cache entry for a given domain/subdomain.
    
    Args:
        domain: Website domain
        subdomain: Subdomain path
        
    Returns:
        Dictionary with keys: "pdf", "chunks", "summary", "quiz"
        Returns None if not found in cache
    """
    return _SCRAPE_CACHE.get(cache_key(domain, subdomain))


def set_cached(
    domain: str,
    subdomain: str,
    pdf_bytes: bytes,
    chunks: list,
    summary: str | None = None,
    quiz: list | None = None,
) -> None:
    """Store scraped data and any pre-computed summary/quiz in cache.
    
    Args:
        domain: Website domain
        subdomain: Subdomain path
        pdf_bytes: Binary PDF data
        chunks: List of text chunks extracted from PDF
        summary: Optional pre-generated summary
        quiz: Optional pre-generated quiz questions
    """
    _SCRAPE_CACHE[cache_key(domain, subdomain)] = {
        "pdf":     pdf_bytes,   # Raw PDF bytes for download/viewing
        "chunks":  chunks,      # Text chunks for display and processing
        "summary": summary,     # Cached summary to avoid regenerating
        "quiz":    quiz,        # Cached quiz to avoid regenerating
    }


def cache_size() -> int:
    """Return the number of entries currently in the cache.
    
    Returns:
        Integer count of cached entries
    """
    return len(_SCRAPE_CACHE)


def clear_cache() -> None:
    """Clear all entries from the in-memory cache."""
    _SCRAPE_CACHE.clear()


# ---------------------------------------------------------------------------
# Session-state initialiser  (call once from app.py)
# ---------------------------------------------------------------------------
def init_app_state() -> None:
    """Initialize all Streamlit session state variables with default values.
    
    This function should be called once at application startup to ensure
    all required session state keys exist. It preserves any existing values.
    
    Session state tracks:
    - Navigation: current page
    - Onboarding: step, preferences, knowledge, completion status
    - Scraper: PDF data, formatted results, completion flag
    - Summarization: last summary, completion flag
    - Chatbot: vector store, processing status, chat history
    - Quiz: questions, answers, submission status, current question index
    """
    defaults = {
        # Navigation
        "current_page":    "dashboard",
        
        # Onboarding
        "step":            1,           # Current onboarding step (1, 2, or 3)
        "pref":            {},          # User's learning preferences
        "knowledge":       {},          # User's knowledge state/topics
        "profile_complete": False,      # Whether user completed onboarding
        
        # Scraper
        "scraped_pdf_bytes": None,      # Raw PDF bytes from scraper
        "scraped_formatted": None,      # Formatted display data
        "scrape_done":       False,     # Whether scraping is complete
        
        # Summarization
        "last_summary": None,           # Most recent summary generated
        "summary_done": False,          # Whether summary has been generated
        
        # Chatbot
        "vector_store":   None,         # FAISS vector store for RAG
        "chat_processed": False,        # Whether PDF has been processed for chat
        "chat_history":   [],           # List of chat messages
        
        # Quiz
        "quiz_data":        None,       # Quiz questions and answers
        "quiz_prefilled":   False,      # Whether quiz has been loaded
        "current_question": 0,          # Index of current quiz question
        "answers":          {},         # User's answers keyed by question index
        "submitted":        False,      # Whether quiz has been submitted
        "quiz_started":     False,      # Whether quiz session is active
        "pdf_content":      None,       # Extracted PDF text content
    }
    
    # Only set default if key doesn't exist (preserves existing values)
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Uncomment for debugging session state
    # st.write("Session State (Initial Load):", st.session_state)