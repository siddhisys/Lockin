import streamlit as st
from PyPDF2 import PdfReader
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
from textwrap import wrap

from utils.state import get_cached

# ---------------------------------------------------------------------------
# In-memory summary cache  key: hash of first 3000 chars of document text
# ---------------------------------------------------------------------------
_SUMMARY_CACHE: dict[int, str] = {}  # Global cache dictionary to store summaries by hash

def _summary_cache_key(text: str) -> int:
    """Generate a hash key from the first 3000 characters of the document text.
    
    Args:
        text: The document text to hash
        
    Returns:
        Integer hash value used as cache key
    """
    return hash(text[:3000])

def _get_cached_summary(text: str) -> str | None:
    """Retrieve a cached summary for the given text if it exists.
    
    Args:
        text: The document text to look up
        
    Returns:
        Cached summary string or None if not found
    """
    return _SUMMARY_CACHE.get(_summary_cache_key(text))

def _set_cached_summary(text: str, summary: str) -> None:
    """Store a summary in the cache for future use.
    
    Args:
        text: The original document text
        summary: The generated summary to cache
    """
    _SUMMARY_CACHE[_summary_cache_key(text)] = summary


# ---------------------------------------------------------------------------
# Prompt builder — keeps it tight but complete
# ---------------------------------------------------------------------------
_SUMMARY_PROMPT = """\
Summarize the document below in 5-8 bullet points.
Cover: main topic, key concepts, important details, and conclusion.
Be concise. No preamble.

---
{text}
---"""

MAX_PROMPT_CHARS = 2500   # Limit for gemma3:1b model's optimal input size


def _build_prompt(raw_text: str) -> str:
    """Construct an optimized prompt for the LLM by trimming long texts.
    
    For documents exceeding MAX_PROMPT_CHARS, extracts the beginning, middle,
    and end sections to provide context while staying within token limits.
    
    Args:
        raw_text: The extracted document text
        
    Returns:
        Formatted prompt string ready for LLM input
    """
    text = raw_text.strip()
    if len(text) > MAX_PROMPT_CHARS:
        # Extract beginning (first 800 chars)
        start  = text[:800]
        # Extract middle section (900 chars from the center)
        middle = text[len(text)//2 - 450 : len(text)//2 + 450]
        # Extract end (last 500 chars)
        end    = text[-500:]
        # Combine sections with ellipsis markers
        text   = f"{start}\n\n[…]\n\n{middle}\n\n[…]\n\n{end}"
    return _SUMMARY_PROMPT.format(text=text)


# ---------------------------------------------------------------------------
def _nav(page):
    """Helper function to navigate between pages in the Streamlit app.
    
    Args:
        page: The target page name to navigate to
    """
    st.session_state["current_page"] = page
    st.rerun()  # Force Streamlit to rerun the app with the new page


def render():
    """Main render function for the AI Summarizer page.
    
    This function handles the entire UI for document summarization including:
    - File upload (either from web scraper or manual upload)
    - Summary generation using Ollama LLM
    - Caching of summaries
    - PDF export functionality
    - Navigation to quiz and chatbot features
    """
    
    # Top navigation bar with dashboard button
    top_col1, top_col2 = st.columns([6, 1])
    with top_col2:
        if st.button("🏠 Dashboard", key="sum_dashboard", use_container_width=True):
            _nav("dashboard")

    # Page header with title and description
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

    # Progress indicator showing the 4-step workflow
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

    # Check if we have scraped content from previous step
    has_scraped = bool(st.session_state.get("scraped_pdf_bytes"))
    # Track whether user wants to manually upload instead of using scraped content
    if "sum_use_manual" not in st.session_state:
        st.session_state.sum_use_manual = False

    # Split layout into left (controls) and right (output) columns
    col_left, col_right = st.columns([1, 2])

    with col_left:
        # Left panel with file upload controls
        st.markdown("""<div style="background:var(--surface);border:1px solid var(--border);
            border-radius:var(--radius-lg);padding:1.25rem 1.25rem .75rem;">
        """, unsafe_allow_html=True)

        # Handle file source selection (scraped vs manual upload)
        if has_scraped and not st.session_state.sum_use_manual:
            # Show scraped content status with green success indicator
            st.markdown("""
            <div style="background:#ECFDF5;border:1px solid #A7F3D0;border-radius:10px;
                padding:.75rem 1rem;margin-bottom:.75rem;">
                <div style="font-size:.82rem;font-weight:600;color:#065F46;margin-bottom:.2rem;">
                    ✅ Scraped content loaded</div>
                <div style="font-size:.75rem;color:#059669;">Ready to summarize automatically</div>
            </div>""", unsafe_allow_html=True)
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
                # Show message and link to web scraper if no content available
                st.markdown("""
                <div style="font-size:.8rem;color:var(--text-muted);margin:.5rem 0;">
                    No scraped content yet.</div>""", unsafe_allow_html=True)
                if st.button("← Go to Web Scraper", key="sum_to_scraper",
                             use_container_width=True):
                    _nav("scraper")

        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        # Main generate button
        gen_btn = st.button("✨ Generate Summary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Information about Ollama requirement
        st.markdown("""
        <div style="margin-top:.75rem;background:#FFFBEB;border:1px solid #FDE68A;
            border-radius:var(--radius);padding:.7rem 1rem;font-size:.8rem;color:#92400E;">
            💡 Requires Ollama running locally with <strong>gemma3:1b</strong>
        </div>""", unsafe_allow_html=True)

    with col_right:
        # Right panel - summary generation and display
        if gen_btn:
            document_text = ""
            try:
                # Extract text from either scraped PDF or uploaded file
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

                # Check cache first to avoid redundant LLM calls
                cached_summary = _get_cached_summary(document_text)
                if cached_summary:
                    # Use cached summary for instant response
                    st.session_state["last_summary"] = cached_summary
                    st.session_state["summary_done"] = True
                    st.success("⚡ Loaded from cache instantly!")
                else:
                    # Generate new summary using LLM
                    # The spinner shows during the blocking LLM call
                    with st.spinner("🤖 Generating summary…"):
                        from langchain_ollama import OllamaLLM
                        llm    = OllamaLLM(model="gemma3:1b")
                        prompt = _build_prompt(document_text)
                        summary = llm.invoke(prompt)

                    # Store the generated summary
                    st.session_state["last_summary"] = summary
                    st.session_state["summary_done"] = True
                    # Cache for future use
                    _set_cached_summary(document_text, summary)

            except Exception as e:
                st.error(f"Error: {e}")
                st.info("Make sure Ollama is running: `ollama serve`")
                return

        # ---- Display the summary if it exists ----
        if st.session_state.get("last_summary"):
            # Render summary in a styled card
            st.markdown("""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-top:3px solid var(--accent-fg);
                border-radius:var(--radius-lg);padding:1.5rem;margin-bottom:1rem;">
                <div style="font-size:.72rem;font-weight:600;letter-spacing:.07em;
                    text-transform:uppercase;color:var(--text-muted);margin-bottom:.75rem;">
                    📌 Summary</div>
            """, unsafe_allow_html=True)
            st.write(st.session_state["last_summary"])
            st.markdown("</div>", unsafe_allow_html=True)

            # PDF export functionality using ReportLab
            buf = BytesIO()
            c = canvas.Canvas(buf, pagesize=A4)

            # Page dimensions
            page_width, page_height = A4

            # Create text object for the PDF
            obj = c.beginText(40, page_height - 60)

            # Add title to PDF
            obj.setFont("Helvetica-Bold", 13)
            obj.textLine("AI Generated Summary")

            # Add metadata (timestamp)
            obj.setFont("Helvetica", 10)
            obj.textLine(f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}")
            obj.textLine("-" * 70)
            obj.textLine("")

            # Body text with word wrapping
            obj.setFont("Helvetica", 11)

            max_chars_per_line = 90
            line_height = 14
            y_position = page_height - 120  # Start position below header

            # Process each line of the summary
            for line in st.session_state["last_summary"].split("\n"):
                wrapped_lines = wrap(line, max_chars_per_line)

                for wline in wrapped_lines:
                    # Check if we need a new page
                    if y_position <= 40:  # Bottom margin reached
                        c.drawText(obj)
                        c.showPage()
                        # Reset for new page
                        obj = c.beginText(40, page_height - 60)
                        obj.setFont("Helvetica", 11)
                        y_position = page_height - 60

                    obj.setTextOrigin(40, y_position)
                    obj.textLine(wline)
                    y_position -= line_height

            # Finalize the PDF
            c.drawText(obj)
            c.showPage()
            c.save()
            buf.seek(0)

            # Provide download button for the exported PDF
            st.download_button(
                label="📄 Export Summary as PDF",
                data=buf,
                file_name="summary.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            # Show placeholder when no summary exists
            st.markdown("""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:2rem 1.5rem;text-align:center;
                color:var(--text-muted);">
                <div style="font-size:2rem;margin-bottom:.75rem;">📄</div>
                <div style="font-size:.9rem;font-weight:500;margin-bottom:.35rem;">
                    No summary yet</div>
                <div style="font-size:.82rem;">Click Generate Summary to get started.</div>
            </div>""", unsafe_allow_html=True)

    # ---- Next steps navigation ----
    # Show options to continue to quiz or chatbot after summary is generated
    if st.session_state.get("summary_done"):
        st.markdown("""
        <div style="height:1px;background:var(--border);margin:1.5rem 0;"></div>
        <div style="font-size:.72rem;font-weight:600;letter-spacing:.08em;
            text-transform:uppercase;color:var(--text-muted);margin-bottom:.75rem;">
            What would you like to do next?</div>""", unsafe_allow_html=True)

        # Two-column layout for navigation cards
        nc1, nc2 = st.columns(2)
        with nc1:
            # Quiz generator card
            st.markdown("""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:1rem;text-align:center;margin-bottom:.5rem;">
                <div style="font-size:1.4rem;margin-bottom:.4rem;">🧩</div>
                <div style="font-size:.82rem;font-weight:600;color:var(--text);margin-bottom:.2rem;">
                    Test your knowledge</div>
                <div style="font-size:.75rem;color:var(--text-muted);">Generate a quiz from this content</div>
            </div>""", unsafe_allow_html=True)
            if st.button("Open Quiz Generator", key="sum_quiz", use_container_width=True):
                _nav("quiz")
        with nc2:
            # Chatbot card
            st.markdown("""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:1rem;text-align:center;margin-bottom:.5rem;">
                <div style="font-size:1.4rem;margin-bottom:.4rem;">💬</div>
                <div style="font-size:.82rem;font-weight:600;color:var(--text);margin-bottom:.2rem;">
                    Dig deeper</div>
                <div style="font-size:.75rem;color:var(--text-muted);">Ask the chatbot questions</div>
            </div>""", unsafe_allow_html=True)
            if st.button("Open Chatbot", key="sum_chat", use_container_width=True):
                _nav("chatbot")