import streamlit as st
from PyPDF2 import PdfReader
from io import BytesIO

@st.cache_resource
def get_llm():
    try:
        from langchain_ollama import ChatOllama
        return ChatOllama(model="gemma2:2b", temperature=0.7, num_ctx=1024, num_predict=256)
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
    st.markdown("# 💬 Chatbot")
    st.markdown("Chat with your PDFs or ask general questions.")
    st.markdown("---")

    col_left, col_right = st.columns([1, 2.5])

    with col_left:
        source = st.radio("Source", ["Upload a PDF", "Use scraped PDF", "General chat (no PDF)"])

        uploaded_file = None
        use_scraped = False

        if source == "Upload a PDF":
            uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")
        elif source == "Use scraped PDF":
            if st.session_state.get("scraped_pdf_bytes"):
                st.success("✅ Scraped PDF ready!")
                use_scraped = True
            else:
                st.info("No scraped PDF yet.")

        if source != "General chat (no PDF)":
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
                        from langchain.text_splitter import RecursiveCharacterTextSplitter # type: ignore
                        from langchain_community.vectorstores import FAISS
                        with st.spinner("Processing..."):
                            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
                            chunks = [c for c in splitter.split_text(pdf_text) if c.strip()]
                            embeddings = get_embeddings()
                            if embeddings and chunks:
                                vs = FAISS.from_texts(texts=chunks, embedding=embeddings)
                                st.session_state.vector_store = vs
                                st.session_state.chat_processed = True
                                st.success(f"✅ Ready! {len(chunks)} chunks processed.")
                            else:
                                st.error("Failed to process document.")
                    else:
                        st.error("No text found in PDF.")
                except Exception as e:
                    st.error(f"Error: {e}")

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.vector_store = None
            st.session_state.chat_processed = False
            st.session_state.chat_history = []
            st.rerun()

        st.markdown("---")
        if st.session_state.get("chat_processed"):
            st.success("📄 Document Mode Active")
        else:
            st.info("💬 General Chat Mode")

    with col_right:
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            else:
                st.chat_message("assistant").write(msg["content"])

        user_question = st.chat_input("Ask a question...")

        if user_question:
            st.session_state.chat_history.append({"role": "user", "content": user_question})
            st.chat_message("user").write(user_question)

            try:
                llm = get_llm()
                if not llm:
                    st.error("Could not connect to Ollama.")
                    return

                with st.spinner("Thinking..."):
                    if st.session_state.get("chat_processed") and st.session_state.get("vector_store"):
                        retriever = st.session_state.vector_store.as_retriever(search_kwargs={"k": 3})
                        docs = retriever.get_relevant_documents(user_question)
                        context = "\n\n".join([d.page_content for d in docs])
                        prompt = f"Context:\n{context}\n\nQuestion: {user_question}\n\nAnswer:"
                        full_response = ""
                        for chunk in llm.stream(prompt):
                            full_response += chunk.content
                    else:
                        full_response = ""
                        for chunk in llm.stream(user_question):
                            full_response += chunk.content

                st.session_state.chat_history.append({"role": "assistant", "content": full_response})
                st.chat_message("assistant").write(full_response)

            except Exception as e:
                st.error(f"Error: {e}")
                st.info("Make sure Ollama is running: ollama serve")