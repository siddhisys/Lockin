import streamlit as st

def render():
    pref = st.session_state.get("pref", {})
    name = pref.get("name", "there").split()[0]
    domains = pref.get("domains", [])
    pace = pref.get("pace_key", "Steady")
    goal = pref.get("goal", "—")

    st.markdown(f"# Welcome back, {name} 👋")
    st.markdown("Here's your learning hub. Where would you like to start?")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"🎯 **Goal**\n\n{goal}")
    with col2:
        st.info(f"⏱️ **Pace**\n\n{pace}")
    with col3:
        st.info(f"📚 **Domains**\n\n{', '.join(domains) if domains else '—'}")

    st.markdown("---")
    st.markdown("### 🚀 Your Tools")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### 🌐 Web Scraper")
        st.markdown("Scrape credible sources by topic and download as PDF.")
        if st.button("Open Scraper", use_container_width=True, key="dash_scraper"):
            st.session_state.current_page = "scraper"
            st.rerun()

        st.markdown("---")

        st.markdown("#### 🧩 Quiz Generator")
        st.markdown("Upload a PDF and generate MCQ questions to test yourself.")
        if st.button("Open Quiz", use_container_width=True, key="dash_quiz"):
            st.session_state.current_page = "quiz"
            st.rerun()

    with col_b:
        st.markdown("#### 📄 AI Summarizer")
        st.markdown("Upload a PDF and get a concise AI summary. Export as PDF.")
        if st.button("Open Summarizer", use_container_width=True, key="dash_summarizer"):
            st.session_state.current_page = "summarization"
            st.rerun()

        st.markdown("---")

        st.markdown("#### 💬 Chatbot")
        st.markdown("Chat with your PDFs or ask the AI general questions.")
        if st.button("Open Chatbot", use_container_width=True, key="dash_chatbot"):
            st.session_state.current_page = "chatbot"
            st.rerun()

    st.markdown("---")
    st.markdown("""
    💡 **Suggested Flow:**
    1. **Web Scraper** → gather content → download PDF
    2. **Summarizer** → upload PDF → get overview
    3. **Quiz** → test your understanding
    4. **Chatbot** → ask deep questions
    """)