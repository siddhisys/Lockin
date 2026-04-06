import streamlit as st
from PyPDF2 import PdfReader
from io import BytesIO

def _nav(page):
    st.session_state["current_page"] = page
    st.rerun()

@st.cache_resource
def get_llm():
    try:
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model="gemma2:2b",
            temperature=0.7,
            num_ctx=512,
            num_predict=128,
            num_thread=4,
        )
    except:
        return None

@st.cache_resource
def get_embeddings():
    try:
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(model="nomic-embed-text")
    except:
        return None

def render():
    if "chat_use_manual" not in st.session_state:
        st.session_state.chat_use_manual = False

    # --------- Top bar ----------------------------
    top1, top2 = st.columns([6, 1])
    with top2:
        if st.button("🏠 Dashboard", key="chat_dashboard", use_container_width=True):
            _nav("dashboard")

    st.markdown("""
    <div style="margin-bottom:1.75rem;">
        <div style="display:flex;align-items:center;gap:.55rem;margin-bottom:.1rem;">
            <span style="font-size:1.5rem;">💬</span>
            <h1 style="margin:0!important;">Chatbot</h1>
        </div>
        <p style="color:var(--text-muted);margin:.2rem 0 0;font-weight:300;">
            Chat with your PDF documents or ask the AI any question.
        </p>
        <div style="height:1px;background:var(--border);margin-top:.9rem;"></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:1.5rem;flex-wrap:wrap;">
        <div style="background:var(--surface-2);color:var(--text-muted);border-radius:20px;
            padding:.3rem .85rem;font-size:.8rem;font-weight:500;">1 Scrape</div>
        <span style="color:var(--border-hover);">→</span>
        <div style="background:var(--surface-2);color:var(--text-muted);border-radius:20px;
            padding:.3rem .85rem;font-size:.8rem;font-weight:500;">2 Summarize</div>
        <span style="color:var(--border-hover);">→</span>
        <div style="background:var(--surface-2);color:var(--text-muted);border-radius:20px;
            padding:.3rem .85rem;font-size:.8rem;font-weight:500;">3 Quiz</div>
        <span style="color:var(--border-hover);">→</span>
        <div style="background:var(--accent);color:#fff;border-radius:20px;
            padding:.3rem .85rem;font-size:.8rem;font-weight:600;">4 Chat</div>
    </div>
    """, unsafe_allow_html=True)

    has_scraped = bool(st.session_state.get("scraped_pdf_bytes"))

    col_left, col_right = st.columns([1, 2.5])

    with col_left:
        st.markdown("""<div style="background:var(--surface);border:1px solid var(--border);
            border-radius:var(--radius-lg);padding:1.25rem 1.25rem .75rem;">
        """, unsafe_allow_html=True)

        # ---------- Source selection ----------------------------
        if has_scraped and not st.session_state.chat_use_manual:
            # Auto-loaded scraped PDF
            st.markdown("""
            <div style="background:#ECFDF5;border:1px solid #A7F3D0;border-radius:10px;
                padding:.75rem 1rem;margin-bottom:.75rem;">
                <div style="font-size:.82rem;font-weight:600;color:#065F46;margin-bottom:.2rem;">
                    ✅ Scraped content loaded
                </div>
                <div style="font-size:.75rem;color:#059669;">
                    Process it below to start chatting
                </div>
            </div>""", unsafe_allow_html=True)
            uploaded_file = None
            use_scraped   = True

            c1, c2 = st.columns(2)
            with c1:
                if st.button("📤 Use different PDF", use_container_width=True):
                    st.session_state.chat_use_manual = True
                    st.rerun()
            with c2:
                if st.button("💬 General chat", use_container_width=True):
                    st.session_state.chat_use_manual = "general"
                    st.rerun()

        elif st.session_state.chat_use_manual == "general":
            st.info("💬 General chat mode — no document needed.")
            uploaded_file = None
            use_scraped   = False
            if has_scraped:
                if st.button("← Use scraped PDF", use_container_width=True):
                    st.session_state.chat_use_manual = False
                    st.rerun()

        else:
            # Manual upload
            if has_scraped:
                if st.button("← Use scraped PDF", use_container_width=True):
                    st.session_state.chat_use_manual = False
                    st.rerun()
            uploaded_file = st.file_uploader("Upload PDF", type=["pdf"],
                                              label_visibility="collapsed")
            use_scraped = False
            if not uploaded_file and not has_scraped:
                st.markdown("""<div style="font-size:.8rem;color:var(--text-muted);
                    margin:.5rem 0;">No scraped content yet.</div>""",
                    unsafe_allow_html=True)
                if st.button("← Go to Web Scraper", key="chat_to_scraper",
                             use_container_width=True):
                    _nav("scraper")

        # -------- Process button (only for PDF modes) ----------------------------
        is_general = st.session_state.chat_use_manual == "general"
        if not is_general:
            if st.button("⚙️ Process Document", use_container_width=True):
                pdf_text = ""
                try:
                    if use_scraped and st.session_state.get("scraped_pdf_bytes"):
                        reader = PdfReader(BytesIO(st.session_state.scraped_pdf_bytes))
                        for page in reader.pages:
                            pdf_text += page.extract_text() or ""
                    elif uploaded_file:
                        reader = PdfReader(uploaded_file)
                        for page in reader.pages:
                            pdf_text += page.extract_text() or ""

                    if pdf_text.strip():
                        progress = st.progress(0)
                        status   = st.empty()
                        status.markdown("*✂️ Splitting text…*")
                        progress.progress(30)

                        from langchain.text_splitter import RecursiveCharacterTextSplitter
                        from langchain_community.vectorstores import FAISS

                        splitter = RecursiveCharacterTextSplitter(
                            chunk_size=500, chunk_overlap=100)
                        chunks = [c for c in splitter.split_text(pdf_text) if c.strip()]

                        status.markdown("*🔢 Building vector index…*")
                        progress.progress(65)

                        embeddings = get_embeddings()
                        if embeddings and chunks:
                            vs = FAISS.from_texts(texts=chunks, embedding=embeddings)
                            st.session_state.vector_store   = vs
                            st.session_state.chat_processed = True
                            progress.progress(100)
                            status.empty()
                            progress.empty()
                            st.success(f"✅ Ready! {len(chunks)} chunks indexed.")
                        else:
                            progress.empty(); status.empty()
                            st.error("Failed to process document.")
                    else:
                        st.error("No text found in PDF.")
                except Exception as e:
                    st.error(f"Error: {e}")

        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.vector_store   = None
            st.session_state.chat_processed = False
            st.session_state.chat_history   = []
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        # Mode badge
        if is_general:
            st.markdown("""
            <div style="margin-top:.75rem;background:#EFF6FF;border:1px solid #BFDBFE;
                border-radius:var(--radius);padding:.7rem 1rem;
                font-size:.82rem;font-weight:500;color:#1E40AF;">
                💬 General chat mode</div>""", unsafe_allow_html=True)
        elif st.session_state.get("chat_processed"):
            st.markdown("""
            <div style="margin-top:.75rem;background:#ECFDF5;border:1px solid #A7F3D0;
                border-radius:var(--radius);padding:.7rem 1rem;
                font-size:.82rem;font-weight:500;color:#065F46;">
                📄 Document mode active</div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="margin-top:.75rem;background:#FFFBEB;border:1px solid #FDE68A;
                border-radius:var(--radius);padding:.7rem 1rem;
                font-size:.82rem;font-weight:500;color:#92400E;">
                ⚠️ Process a document to enable document mode</div>""",
                unsafe_allow_html=True)

        # Other tools
        st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
        st.markdown("""<div style="font-size:.72rem;font-weight:600;letter-spacing:.07em;
            text-transform:uppercase;color:var(--text-muted);margin-bottom:.4rem;">
            Other Tools</div>""", unsafe_allow_html=True)
        if st.button("📄 Summarizer", key="chat_sum", use_container_width=True):
            _nav("summarization")
        if st.button("🧩 Quiz Generator", key="chat_quiz", use_container_width=True):
            _nav("quiz")

    with col_right:
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        if not st.session_state.chat_history:
            st.markdown("""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:2rem 1.5rem;text-align:center;
                color:var(--text-muted);margin-bottom:1rem;">
                <div style="font-size:2rem;margin-bottom:.75rem;">💬</div>
                <div style="font-size:.9rem;font-weight:500;margin-bottom:.35rem;">
                    Start a conversation</div>
                <div style="font-size:.82rem;">
                    {'Process your document first, then ask questions.' if not is_general else 'Ask the AI anything!'}
                </div>
            </div>""", unsafe_allow_html=True)

        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

        user_question = st.chat_input("Ask a question…")

        if user_question:
            st.session_state.chat_history.append(
                {"role": "user", "content": user_question})
            st.chat_message("user").write(user_question)

            try:
                llm = get_llm()
                if not llm:
                    st.error("Could not connect to Ollama.")
                    return

                if (st.session_state.get("chat_processed")
                        and st.session_state.get("vector_store")):
                    retriever = st.session_state.vector_store.as_retriever(
                        search_kwargs={"k": 2})
                    docs    = retriever.get_relevant_documents(user_question)
                    context = "\n\n".join([d.page_content for d in docs])
                    prompt  = (f"Answer briefly using only this context.\n\n"
                               f"Context:\n{context}\n\n"
                               f"Question: {user_question}\nAnswer:")
                else:
                    prompt = user_question

                with st.chat_message("assistant"):
                    placeholder   = st.empty()
                    full_response = ""
                    for chunk in llm.stream(prompt):
                        full_response += chunk.content
                        placeholder.markdown(full_response + "▌")
                    placeholder.markdown(full_response)

                st.session_state.chat_history.append(
                    {"role": "assistant", "content": full_response})

            except Exception as e:
                st.error(f"Error: {e}")
                st.info("Make sure Ollama is running: `ollama serve`")