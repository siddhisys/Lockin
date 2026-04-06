import streamlit as st
from PyPDF2 import PdfReader
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

def _nav(page):
    st.session_state["current_page"] = page
    st.rerun()

def render():
    # ------- Top bar: back to dashboard ----------------------------
    top_col1, top_col2 = st.columns([6, 1])
    with top_col2:
        if st.button("🏠 Dashboard", key="sum_dashboard", use_container_width=True):
            _nav("dashboard")

    st.markdown("""
    <div style="margin-bottom:1.75rem;">
        <div style="display:flex;align-items:center;gap:.55rem;margin-bottom:.1rem;">
            <span style="font-size:1.5rem;">📄</span>
            <h1 style="margin:0!important;">AI Summarizer</h1>
        </div>
        <p style="color:var(--text-muted);margin:.2rem 0 0;font-weight:300;">
            Upload a PDF and get a concise, AI-generated summary in seconds.
        </p>
        <div style="height:1px;background:var(--border);margin-top:.9rem;"></div>
    </div>
    """, unsafe_allow_html=True)

    # -------- Step indicator ----------------------------
    st.markdown("""
    <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:1.5rem;flex-wrap:wrap;">
        <div style="background:var(--surface-2);color:var(--text-muted);border-radius:20px;
            padding:.3rem .85rem;font-size:.8rem;font-weight:500;">1 Scrape</div>
        <span style="color:var(--border-hover);">→</span>
        <div style="background:var(--accent);color:#fff;border-radius:20px;
            padding:.3rem .85rem;font-size:.8rem;font-weight:600;">2 Summarize</div>
        <span style="color:var(--border-hover);">→</span>
        <div style="background:var(--surface-2);color:var(--text-muted);border-radius:20px;
            padding:.3rem .85rem;font-size:.8rem;font-weight:500;">3 Quiz</div>
        <span style="color:var(--border-hover);">→</span>
        <div style="background:var(--surface-2);color:var(--text-muted);border-radius:20px;
            padding:.3rem .85rem;font-size:.8rem;font-weight:500;">4 Chat</div>
    </div>
    """, unsafe_allow_html=True)

    # ------- Determine PDF source automatically ----------------------------
    has_scraped = bool(st.session_state.get("scraped_pdf_bytes"))

    if "sum_use_manual" not in st.session_state:
        st.session_state.sum_use_manual = False

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("""<div style="background:var(--surface);border:1px solid var(--border);
            border-radius:var(--radius-lg);padding:1.25rem 1.25rem .75rem;">
        """, unsafe_allow_html=True)

        # Auto-loaded scraped PDF
        if has_scraped and not st.session_state.sum_use_manual:
            st.markdown("""
            <div style="background:#ECFDF5;border:1px solid #A7F3D0;border-radius:10px;
                padding:.75rem 1rem;margin-bottom:.75rem;">
                <div style="font-size:.82rem;font-weight:600;color:#065F46;margin-bottom:.2rem;">
                    ✅ Scraped content loaded
                </div>
                <div style="font-size:.75rem;color:#059669;">
                    Ready to summarize automatically
                </div>
            </div>
            """, unsafe_allow_html=True)
            uploaded_file = None
            use_scraped   = True
            if st.button("📤 Use a different PDF instead", use_container_width=True):
                st.session_state.sum_use_manual = True
                st.rerun()

        else:
            # Manual upload mode
            if has_scraped:
                if st.button("← Use scraped PDF", use_container_width=True):
                    st.session_state.sum_use_manual = False
                    st.rerun()
            uploaded_file = st.file_uploader("Upload PDF", type=["pdf"],
                                              label_visibility="collapsed")
            use_scraped = False
            if not uploaded_file and not has_scraped:
                st.markdown("""
                <div style="font-size:.8rem;color:var(--text-muted);margin:.5rem 0;">
                    No scraped content yet.
                </div>""", unsafe_allow_html=True)
                if st.button("← Go to Web Scraper", key="sum_to_scraper",
                             use_container_width=True):
                    _nav("scraper")

        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        gen_btn = st.button("✨ Generate Summary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
        <div style="margin-top:.75rem;background:#FFFBEB;border:1px solid #FDE68A;
            border-radius:var(--radius);padding:.7rem 1rem;font-size:.8rem;color:#92400E;">
            💡 Requires Ollama running locally with <strong>gemma3:1b</strong>
        </div>""", unsafe_allow_html=True)

    with col_right:
        if gen_btn:
            document_text = ""
            try:
                if use_scraped and st.session_state.get("scraped_pdf_bytes"):
                    reader = PdfReader(BytesIO(st.session_state.scraped_pdf_bytes))
                    for p in reader.pages:
                        document_text += p.extract_text() or ""
                elif uploaded_file:
                    reader = PdfReader(uploaded_file)
                    for p in reader.pages:
                        document_text += p.extract_text() or ""
                else:
                    st.warning("Please upload a PDF or scrape content first.")
                    return

                if not document_text.strip():
                    st.error("Could not extract text from the PDF.")
                    return

                progress = st.progress(0)
                status   = st.empty()

                status.markdown("*📖 Reading document…*")
                progress.progress(25)
                import time; time.sleep(0.3)

                status.markdown("*🤖 Sending to AI…*")
                progress.progress(50)

                from langchain_ollama import OllamaLLM
                llm = OllamaLLM(model="gemma3:1b")
                summary = llm.invoke(f"""Summarize the following document.
Focus on the main topics and key points. Keep it concise and easy to understand.

Document:
{document_text[:4000]}""")

                status.markdown("*✍️ Formatting summary…*")
                progress.progress(90)
                time.sleep(0.2)

                progress.progress(100)
                status.empty()
                progress.empty()

                st.session_state["last_summary"] = summary
                st.session_state["summary_done"] = True

            except Exception as e:
                st.error(f"Error: {e}")
                st.info("Make sure Ollama is running: `ollama serve`")
                return

        # --------- Show summary ----------------------------
        if st.session_state.get("last_summary"):
            st.markdown("""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-top:3px solid var(--accent-fg);
                border-radius:var(--radius-lg);padding:1.5rem;margin-bottom:1rem;">
                <div style="font-size:.72rem;font-weight:600;letter-spacing:.07em;
                    text-transform:uppercase;color:var(--text-muted);margin-bottom:.75rem;">
                    📌 Summary
                </div>
            """, unsafe_allow_html=True)
            st.write(st.session_state["last_summary"])
            st.markdown("</div>", unsafe_allow_html=True)

            buf = BytesIO()
            c   = canvas.Canvas(buf, pagesize=A4)
            _, h = A4
            obj = c.beginText(40, h - 60)
            obj.setFont("Helvetica-Bold", 13)
            obj.textLine("AI Generated Summary")
            obj.setFont("Helvetica", 10)
            obj.textLine(f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}")
            obj.textLine("-" * 70)
            obj.textLine("")
            obj.setFont("Helvetica", 11)
            for line in st.session_state["last_summary"].split("\n"):
                obj.textLine(line)
            c.drawText(obj)
            c.showPage()
            c.save()
            buf.seek(0)

            st.download_button(
                label="📄 Export Summary as PDF",
                data=buf,
                file_name="summary.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.markdown("""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:2rem 1.5rem;text-align:center;
                color:var(--text-muted);">
                <div style="font-size:2rem;margin-bottom:.75rem;">📄</div>
                <div style="font-size:.9rem;font-weight:500;margin-bottom:.35rem;">
                    No summary yet</div>
                <div style="font-size:.82rem;">
                    Click Generate Summary to get started.
                </div>
            </div>""", unsafe_allow_html=True)

    # --------- What's next ----------------------------
    if st.session_state.get("summary_done"):
        st.markdown("""
        <div style="height:1px;background:var(--border);margin:1.5rem 0;"></div>
        <div style="font-size:.72rem;font-weight:600;letter-spacing:.08em;
            text-transform:uppercase;color:var(--text-muted);margin-bottom:.75rem;">
            What would you like to do next?
        </div>""", unsafe_allow_html=True)

        nc1, nc2 = st.columns(2)
        with nc1:
            st.markdown("""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:1rem;text-align:center;margin-bottom:.5rem;">
                <div style="font-size:1.4rem;margin-bottom:.4rem;">🧩</div>
                <div style="font-size:.82rem;font-weight:600;color:var(--text);margin-bottom:.2rem;">
                    Test your knowledge</div>
                <div style="font-size:.75rem;color:var(--text-muted);">
                    Generate a quiz from this content</div>
            </div>""", unsafe_allow_html=True)
            if st.button("Open Quiz Generator", key="sum_quiz", use_container_width=True):
                _nav("quiz")
        with nc2:
            st.markdown("""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:1rem;text-align:center;margin-bottom:.5rem;">
                <div style="font-size:1.4rem;margin-bottom:.4rem;">💬</div>
                <div style="font-size:.82rem;font-weight:600;color:var(--text);margin-bottom:.2rem;">
                    Dig deeper</div>
                <div style="font-size:.75rem;color:var(--text-muted);">
                    Ask the chatbot questions</div>
            </div>""", unsafe_allow_html=True)
            if st.button("Open Chatbot", key="sum_chat", use_container_width=True):
                _nav("chatbot")