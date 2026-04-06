import streamlit as st

def init_app_state():
    defaults = {
        "current_page": "dashboard",
        "step": 1,
        "pref": {},
        "knowledge": {},
        "profile_complete": False,
        # Scraper
        "scraped_pdf_bytes": None,
        "scraped_formatted": None,
        "scrape_done": False,
        # Summarization
        "last_summary": None,
        "summary_done": False,
        # Chatbot
        "vector_store": None,
        "chat_processed": False,
        "chat_history": [],
        # Quiz
        "quiz_data": None,
        "current_question": 0,
        "answers": {},
        "submitted": False,
        "quiz_started": False,
        "pdf_content": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v