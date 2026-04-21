import streamlit as st
from PyPDF2 import PdfReader
from io import BytesIO


def _nav(page):
    """Navigate to a different page by updating session state and rerunning."""
    st.session_state["current_page"] = page
    st.rerun()


@st.cache_resource
def get_llm():
    """
    Initialises and caches the Ollama LLM instance for the app's lifetime.
    Uses gemma2:2b — a small model that balances speed and quality for chat.
    Cached with @st.cache_resource so the model is only loaded once, not on
    every Streamlit rerun. Returns None if Ollama is unavailable.
    """
    try:
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model="gemma2:2b",
            temperature=0.7,    # moderate creativity for conversational replies
            num_ctx=512,        # context window (tokens) — kept small for speed
            num_predict=128,    # max tokens to generate per response
            num_thread=4,       # CPU threads to use for inference
        )
    except:
        return None


@st.cache_resource
def get_embeddings():
    """
    Initialises and caches the Ollama embedding model for the app's lifetime.
    nomic-embed-text is a lightweight embedding model well-suited for
    semantic search over document chunks. Cached so it's only loaded once.
    Returns None if Ollama is unavailable.
    """
    try:
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(model="nomic-embed-text")
    except:
        return None


def render():
    """
    Renders the Chatbot page. Supports three modes:
      1. Document mode (scraped PDF) — auto-loaded from session state
      2. Document mode (manual upload) — user uploads their own PDF
      3. General chat mode — no document, plain LLM conversation

    In document modes, the PDF is chunked and indexed into a FAISS vector
    store. At query time, the top-k relevant chunks are retrieved and
    injected into the prompt as context (RAG pattern).
    In general mode, the user's message is sent directly to the LLM.
    """

    # Initialise the source-selection flag if this is the first render
    if "chat_use_manual" not in st.session_state:
        st.session_state.chat_use_manual = False

    # ----------------------------------------------------------------
    # Top bar — dashboard shortcut on the far right
    # ----------------------------------------------------------------
    top1, top2 = st.columns([6, 1])
    with top2:
        if st.button("🏠 Dashboard", key="chat_dashboard", use_container_width=True):
            _nav("dashboard")

    # Page header
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

    # Workflow progress breadcrumb — step 4 (Chat) is highlighted
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

    # Check whether a scraped PDF is available from a previous step
    has_scraped = bool(st.session_state.get("scraped_pdf_bytes"))

    # Two-column layout: controls on the left, chat interface on the right
    col_left, col_right = st.columns([1, 2.5])

    # ----------------------------------------------------------------
    # LEFT COLUMN — source selection, process button, mode badge, tools
    # ----------------------------------------------------------------
    with col_left:
        st.markdown("""<div style="background:var(--surface);border:1px solid var(--border);
            border-radius:var(--radius-lg);padding:1.25rem 1.25rem .75rem;">
        """, unsafe_allow_html=True)

        # ---- Source selection: three possible states ----

        if has_scraped and not st.session_state.chat_use_manual:
            # State 1: scraped PDF is available and the user hasn't opted out of it
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

            # Give the user an escape hatch to either upload their own PDF or go fully general
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
            # State 2: general chat — no document context, plain LLM conversation
            st.info("💬 General chat mode — no document needed.")
            uploaded_file = None
            use_scraped   = False

            # Allow reverting to the scraped PDF if one is available
            if has_scraped:
                if st.button("← Use scraped PDF", use_container_width=True):
                    st.session_state.chat_use_manual = False
                    st.rerun()

        else:
            # State 3: manual PDF upload mode
            if has_scraped:
                # Offer a quick way back to the auto-loaded scraped PDF
                if st.button("← Use scraped PDF", use_container_width=True):
                    st.session_state.chat_use_manual = False
                    st.rerun()

            uploaded_file = st.file_uploader("Upload PDF", type=["pdf"],
                                              label_visibility="collapsed")
            use_scraped = False

            # If there's no scraped content and nothing uploaded yet, prompt the user
            if not uploaded_file and not has_scraped:
                st.markdown("""<div style="font-size:.8rem;color:var(--text-muted);
                    margin:.5rem 0;">No scraped content yet.</div>""",
                    unsafe_allow_html=True)
                if st.button("← Go to Web Scraper", key="chat_to_scraper",
                             use_container_width=True):
                    _nav("scraper")

        # ---- Process Document button (hidden in general chat mode) ----
        is_general = st.session_state.chat_use_manual == "general"

        if not is_general:
            if st.button("⚙️ Process Document", use_container_width=True):
                pdf_text = ""
                try:
                    # Extract raw text from whichever PDF source is active
                    if use_scraped and st.session_state.get("scraped_pdf_bytes"):
                        reader = PdfReader(BytesIO(st.session_state.scraped_pdf_bytes))
                        for page in reader.pages:
                            pdf_text += page.extract_text() or ""
                    elif uploaded_file:
                        reader = PdfReader(uploaded_file)
                        for page in reader.pages:
                            pdf_text += page.extract_text() or ""

                    if pdf_text.strip():
                        # Show incremental progress to the user during indexing
                        progress = st.progress(0)
                        status   = st.empty()

                        # Step 1: split the raw text into overlapping chunks
                        # chunk_overlap=100 ensures sentences aren't cut off at boundaries
                        status.markdown("*✂️ Splitting text…*")
                        progress.progress(30)

                        from langchain.text_splitter import RecursiveCharacterTextSplitter
                        from langchain_community.vectorstores import FAISS

                        splitter = RecursiveCharacterTextSplitter(
                            chunk_size=500, chunk_overlap=100)
                        chunks = [c for c in splitter.split_text(pdf_text) if c.strip()]

                        # Step 2: embed each chunk and store in a FAISS index for fast retrieval
                        status.markdown("*🔢 Building vector index…*")
                        progress.progress(65)

                        embeddings = get_embeddings()
                        if embeddings and chunks:
                            vs = FAISS.from_texts(texts=chunks, embedding=embeddings)

                            # Persist the vector store and a processed flag in session state
                            st.session_state.vector_store   = vs
                            st.session_state.chat_processed = True

                            progress.progress(100)
                            status.empty()
                            progress.empty()
                            st.success(f"✅ Ready! {len(chunks)} chunks indexed.")
                        else:
                            progress.empty()
                            status.empty()
                            st.error("Failed to process document.")
                    else:
                        st.error("No text found in PDF.")

                except Exception as e:
                    st.error(f"Error: {e}")

        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        # Clear chat resets the vector store, processed flag, and message history
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.vector_store   = None
            st.session_state.chat_processed = False
            st.session_state.chat_history   = []
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        # ---- Mode status badge below the controls card ----
        if is_general:
            st.markdown("""
            <div style="margin-top:.75rem;background:#EFF6FF;border:1px solid #BFDBFE;
                border-radius:var(--radius);padding:.7rem 1rem;
                font-size:.82rem;font-weight:500;color:#1E40AF;">
                💬 General chat mode</div>""", unsafe_allow_html=True)
        elif st.session_state.get("chat_processed"):
            # Document has been chunked and indexed — RAG is active
            st.markdown("""
            <div style="margin-top:.75rem;background:#ECFDF5;border:1px solid #A7F3D0;
                border-radius:var(--radius);padding:.7rem 1rem;
                font-size:.82rem;font-weight:500;color:#065F46;">
                📄 Document mode active</div>""", unsafe_allow_html=True)
        else:
            # PDF selected but not yet processed — prompt the user to click Process
            st.markdown("""
            <div style="margin-top:.75rem;background:#FFFBEB;border:1px solid #FDE68A;
                border-radius:var(--radius);padding:.7rem 1rem;
                font-size:.82rem;font-weight:500;color:#92400E;">
                ⚠️ Process a document to enable document mode</div>""",
                unsafe_allow_html=True)

        # ---- Quick-nav shortcuts to related tools ----
        st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
        st.markdown("""<div style="font-size:.72rem;font-weight:600;letter-spacing:.07em;
            text-transform:uppercase;color:var(--text-muted);margin-bottom:.4rem;">
            Other Tools</div>""", unsafe_allow_html=True)
        if st.button("📄 Summarizer", key="chat_sum", use_container_width=True):
            _nav("summarization")
        if st.button("🧩 Quiz Generator", key="chat_quiz", use_container_width=True):
            _nav("quiz")

    # ----------------------------------------------------------------
    # RIGHT COLUMN — chat history and message input
    # ----------------------------------------------------------------
    with col_right:
        # Initialise chat history list on first render
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # Empty state placeholder shown before the first message is sent
        if not st.session_state.chat_history:
            st.markdown("""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:2rem 1.5rem;text-align:center;
                color:var(--text-muted);margin-bottom:1rem;">
                <div style="font-size:2rem;margin-bottom:.75rem;">💬</div>
                <div style="font-size:.9rem;font-weight:500;margin-bottom:.35rem;">
                    Start a conversation</div>
                <div style="font-size:.82rem;">
                    {'Ask the AI anything!'}
                </div>
            </div>""", unsafe_allow_html=True)

        # Replay the full conversation history so the UI is consistent on rerun
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

        # Chat input widget — always rendered at the bottom of the column
        user_question = st.chat_input("Ask a question…")

        if user_question:
            # Append user message to history and display it immediately
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
                    # ---- RAG mode: retrieve relevant chunks then answer ----
                    # k=2 keeps the context small so it fits in num_ctx=512
                    retriever = st.session_state.vector_store.as_retriever(
                        search_kwargs={"k": 2})
                    docs    = retriever.get_relevant_documents(user_question)
                    context = "\n\n".join([d.page_content for d in docs])

                    # Instruct the model to answer only from the retrieved context
                    prompt  = (f"Answer briefly using only this context.\n\n"
                               f"Context:\n{context}\n\n"
                               f"Question: {user_question}\nAnswer:")
                else:
                    # ---- General mode: send the question directly ----
                    prompt = user_question

                # Stream the response token-by-token with a typing cursor (▌)
                with st.chat_message("assistant"):
                    placeholder   = st.empty()
                    full_response = ""
                    for chunk in llm.stream(prompt):
                        full_response += chunk.content
                        placeholder.markdown(full_response + "▌")  # live cursor effect
                    placeholder.markdown(full_response)  # final render without cursor

                # Persist the completed assistant reply in history
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": full_response})

            except Exception as e:
                st.error(f"Error: {e}")
                st.info("Make sure Ollama is running: `ollama serve`")