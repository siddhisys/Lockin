import streamlit as st
import requests
import re
import nltk
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from io import BytesIO
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

# Download NLTK tokeniser data on first run if not already present.
# punkt and punkt_tab are both required by sent_tokenize.
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download("punkt", quiet=True)
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download("punkt_tab", quiet=True)

from nltk.tokenize import sent_tokenize
from utils.state import get_cached, set_cached

# ---------------------------------------------------------------------------
# SOURCE CATALOGUE
# Must stay in sync with DOMAINS in onboarding.py and profile_edit.py so
# that subdomain names match what the user selected during onboarding.
# Structure: { domain: { subdomain: { source_label: [url, ...] } } }
# ---------------------------------------------------------------------------
SCRAPING_SOURCES = {
    "Artificial Intelligence": {
        "Machine Learning": {
            "Wikipedia – Machine Learning":     ["https://en.wikipedia.org/wiki/Machine_learning"],
            "Wikipedia – Supervised Learning":  ["https://en.wikipedia.org/wiki/Supervised_learning"],
            "Wikipedia – Unsupervised Learning":["https://en.wikipedia.org/wiki/Unsupervised_learning"],
        },
        "Natural Language Processing": {
            "Wikipedia – NLP":               ["https://en.wikipedia.org/wiki/Natural_language_processing"],
            "Wikipedia – Text Mining":       ["https://en.wikipedia.org/wiki/Text_mining"],
            "Wikipedia – Sentiment Analysis":["https://en.wikipedia.org/wiki/Sentiment_analysis"],
        },
        "Computer Vision": {
            "Wikipedia – Computer Vision":              ["https://en.wikipedia.org/wiki/Computer_vision"],
            "Wikipedia – Convolutional Neural Network": ["https://en.wikipedia.org/wiki/Convolutional_neural_network"],
            "Wikipedia – Object Detection":             ["https://en.wikipedia.org/wiki/Object_detection"],
        },
        "Deep Learning": {
            "Wikipedia – Deep Learning":             ["https://en.wikipedia.org/wiki/Deep_learning"],
            "Wikipedia – Artificial Neural Network": ["https://en.wikipedia.org/wiki/Artificial_neural_network"],
            "Wikipedia – Backpropagation":           ["https://en.wikipedia.org/wiki/Backpropagation"],
        },
        "Reinforcement Learning": {
            "Wikipedia – Reinforcement Learning":  ["https://en.wikipedia.org/wiki/Reinforcement_learning"],
            "Wikipedia – Markov Decision Process": ["https://en.wikipedia.org/wiki/Markov_decision_process"],
            "Wikipedia – Q-Learning":              ["https://en.wikipedia.org/wiki/Q-learning"],
        },
    },
    "Data Science": {
        "Statistical Analysis": {
            "Wikipedia – Statistics":          ["https://en.wikipedia.org/wiki/Statistics"],
            "Wikipedia – Regression Analysis": ["https://en.wikipedia.org/wiki/Regression_analysis"],
            "Wikipedia – Hypothesis Testing":  ["https://en.wikipedia.org/wiki/Statistical_hypothesis_testing"],
        },
        "Data Visualisation": {
            "Wikipedia – Data Visualisation": ["https://en.wikipedia.org/wiki/Data_and_information_visualization"],
            "Wikipedia – Chart":              ["https://en.wikipedia.org/wiki/Chart"],
            "Wikipedia – Histogram":          ["https://en.wikipedia.org/wiki/Histogram"],
        },
        "Big Data Engineering": {
            "Wikipedia – Big Data":       ["https://en.wikipedia.org/wiki/Big_data"],
            "Wikipedia – Apache Spark":   ["https://en.wikipedia.org/wiki/Apache_Spark"],
            "Wikipedia – Data Warehouse": ["https://en.wikipedia.org/wiki/Data_warehouse"],
        },
        "Data Wrangling": {
            "Wikipedia – Data Wrangling":      ["https://en.wikipedia.org/wiki/Data_wrangling"],
            "Wikipedia – Data Cleansing":      ["https://en.wikipedia.org/wiki/Data_cleansing"],
            "Wikipedia – Feature Engineering": ["https://en.wikipedia.org/wiki/Feature_engineering"],
        },
    },
    "Programming": {
        "Python": {
            "Python Docs – Introduction":    ["https://docs.python.org/3/tutorial/introduction.html"],
            "Python Docs – Data Structures": ["https://docs.python.org/3/tutorial/datastructures.html"],
            "Wikipedia – Python":            ["https://en.wikipedia.org/wiki/Python_(programming_language)"],
        },
        "JavaScript": {
            "MDN – JS Introduction": ["https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Introduction"],
            "Wikipedia – JavaScript":["https://en.wikipedia.org/wiki/JavaScript"],
        },
        "Data Structures & Algorithms": {
            "Wikipedia – Data Structures":    ["https://en.wikipedia.org/wiki/Data_structure"],
            "Wikipedia – Sorting Algorithms": ["https://en.wikipedia.org/wiki/Sorting_algorithm"],
            "Wikipedia – Big O Notation":     ["https://en.wikipedia.org/wiki/Big_O_notation"],
        },
    },
    "Web Development": {
        "Frontend Development": {
            "Wikipedia – HTML":  ["https://en.wikipedia.org/wiki/HTML"],
            "Wikipedia – CSS":   ["https://en.wikipedia.org/wiki/CSS"],
            "Wikipedia – React": ["https://en.wikipedia.org/wiki/React_(software)"],
        },
        "Backend Development": {
            "Wikipedia – Web Framework": ["https://en.wikipedia.org/wiki/Web_framework"],
            "Wikipedia – REST API":      ["https://en.wikipedia.org/wiki/REST"],
            "Wikipedia – Database":      ["https://en.wikipedia.org/wiki/Database"],
        },
    },
}

# Mimic a real browser so Wikipedia and MDN don't block the request
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}

MAX_WORKERS         = 5   # max concurrent HTTP requests in the thread pool
SENTENCES_PER_CHUNK = 4   # how many sentences are grouped into one text chunk

# Regex that matches common boilerplate phrases found on web pages.
# Any paragraph containing these phrases is discarded during parsing.
_BOILERPLATE_RE = re.compile(
    r"(sign up|log in|subscribe|newsletter|cookie|privacy policy|terms of service|"
    r"all rights reserved|click here|read more|contact us|about us|follow us|copyright|©|"
    r"advertisement|from wikipedia|retrieved from|wikimedia foundation|edit this page|"
    r"cite this page|this article|main page)", re.IGNORECASE)


# ---------------------------------------------------------------------------
# SCRAPING HELPERS
# ---------------------------------------------------------------------------

def _is_boilerplate(text: str) -> bool:
    """Returns True if the text is too short or matches a boilerplate pattern."""
    return len(text.strip()) < 40 or bool(_BOILERPLATE_RE.search(text))


def _parse_wikipedia(soup: BeautifulSoup) -> str:
    """
    Extracts body text from a Wikipedia page by targeting the main content
    div and iterating over paragraph and heading tags. Citation superscripts,
    spans, and tables are stripped before text extraction. Stops after 8000
    characters to keep the content manageable.
    """
    content = soup.find("div", {"class": "mw-parser-output"})
    if not content:
        return ""
    texts, total = [], 0
    for tag in content.find_all(["p", "h2", "h3"]):
        # Remove inline elements that add noise (footnote numbers, tables, etc.)
        for u in tag.find_all(["sup", "span", "table"]):
            u.decompose()
        t = tag.get_text(separator=" ", strip=True)
        if not _is_boilerplate(t):
            texts.append(t)
            total += len(t)
        if total > 8000:
            break
    return " ".join(texts)


def _parse_generic(soup: BeautifulSoup) -> str:
    """
    Extracts body text from a non-Wikipedia page. Removes noisy structural
    elements (nav, footer, scripts, etc.) before collecting paragraph and
    list-item text. Boilerplate sentences are filtered out.
    """
    # Decompose all non-content tags in-place before extracting text
    for tag in soup(["script", "style", "nav", "footer", "header", "aside",
                     "form", "button", "noscript", "iframe", "svg"]):
        tag.decompose()
    return " ".join(
        t for tag in soup.find_all(["p", "h2", "h3", "li"])
        if not _is_boilerplate(t := tag.get_text(separator=" ", strip=True))
    )


def _parse_html(html: str, url: str) -> str:
    """
    Routes to the correct parser depending on whether the URL is from Wikipedia
    or a generic site, then returns the extracted plain text.
    """
    soup = BeautifulSoup(html, "html.parser")
    return _parse_wikipedia(soup) if "wikipedia.org" in url else _parse_generic(soup)


def _clean(text: str) -> str:
    """
    Removes Wikipedia citation brackets (e.g. [1], [42]), collapses whitespace,
    and strips non-printable / non-standard characters from the text.
    """
    text = re.sub(r"\[\d+\]", "", text)          # strip citation markers
    text = re.sub(r"\s+", " ", text)              # collapse whitespace
    return re.sub(r"[^\w\s.,;:!?()\-\']", "", text).strip()


def _chunk(text: str) -> list[str]:
    """
    Tokenises text into sentences with NLTK, filters out very short ones
    (< 40 chars), then groups them into chunks of SENTENCES_PER_CHUNK.
    Chunks shorter than 60 characters are discarded as too thin.
    """
    sentences = [s.strip() for s in sent_tokenize(text) if len(s.strip()) > 40]
    return [
        c for i in range(0, len(sentences), SENTENCES_PER_CHUNK)
        if len(c := " ".join(sentences[i:i + SENTENCES_PER_CHUNK])) > 60
    ]


def _scrape_one(source: str, url: str) -> dict:
    """
    Fetches a single URL, parses and cleans the HTML, and chunks the text.
    Returns a result dict regardless of success or failure so the caller
    can always collect a result (failed ones are filtered later).
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        chunks = _chunk(_clean(_parse_html(resp.text, url)))
        return {
            "source": source,
            "url":    url,
            "status": "success" if chunks else "failed",
            "chunks": chunks or [],
        }
    except Exception:
        return {"source": source, "url": url, "status": "failed", "chunks": []}


def _scrape_all(sources: dict, status_ph, progress_bar) -> list[dict]:
    """
    Scrapes all URLs in `sources` concurrently using a thread pool.
    Updates the status placeholder and progress bar as each future completes.
    Results are returned in their original order (not completion order)
    and filtered to only include successful scrapes.

    Args:
        sources:      Dict of { source_label: [url, ...] } for a single subdomain.
        status_ph:    Streamlit empty() placeholder for status text updates.
        progress_bar: Streamlit progress bar widget.
    """
    # Flatten the sources dict into an ordered list of (source_label, url) pairs
    all_urls = [(src, url) for src, urls in sources.items() for url in urls]
    total    = len(all_urls)
    results  = [None] * total   # pre-sized so we can write by index and preserve order

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        # Map each future to its original index so we can write results in order
        future_map = {
            pool.submit(_scrape_one, src, url): idx
            for idx, (src, url) in enumerate(all_urls)
        }
        done = 0
        for future in as_completed(future_map):
            idx          = future_map[future]
            results[idx] = future.result()
            done        += 1
            src, _       = all_urls[idx]
            status_ph.markdown(
                f'<div style="font-size:.85rem;color:var(--text-muted);">'
                f'✅ <strong>{src}</strong> ({done}/{total})</div>',
                unsafe_allow_html=True)
            progress_bar.progress(done / total)

    # Filter out failed scrapes before returning
    return [r for r in results if r and r["status"] == "success"]


# ---------------------------------------------------------------------------
# PDF HELPERS
# ---------------------------------------------------------------------------

def _build_pdf(domain: str, subdomain: str, formatted: list[dict]) -> bytes:
    """
    Builds a ReportLab PDF from the scraped chunks and returns it as bytes.
    Each source gets a section header, metadata lines, and bulleted chunks.
    HTML-escapes all text to prevent ReportLab's XML parser from choking
    on special characters.
    """
    def safe(t):
        """Escape characters that would break ReportLab's XML-based renderer."""
        return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=20*mm, leftMargin=20*mm,
                            topMargin=20*mm,   bottomMargin=20*mm)

    # Paragraph styles
    t_s = ParagraphStyle("T", fontName="Helvetica-Bold", fontSize=16, alignment=1, spaceAfter=12)  # title
    h_s = ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=13, spaceAfter=4)                # source heading
    m_s = ParagraphStyle("M", fontName="Helvetica",      fontSize=10, textColor=colors.HexColor("#555555"))  # metadata
    b_s = ParagraphStyle("B", fontName="Helvetica",      fontSize=10, leftIndent=10, spaceAfter=2)  # bullet body

    story = [Paragraph("Scraped Content", t_s), Spacer(1, 8*mm)]

    for item in formatted:
        story += [
            Paragraph(safe(f"{domain} › {subdomain}"), h_s),
            Paragraph(safe(f"Source: {item['source']}"), m_s),
            Paragraph(safe(f"URL: {item['url']}"),       m_s),
            Spacer(1, 3*mm),
        ]
        for chunk in item["chunks"]:
            story += [Paragraph(safe(f"• {chunk}"), b_s), Spacer(1, 1*mm)]
        story.append(Spacer(1, 5*mm))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


def _extract_text(pdf_bytes: bytes) -> str:
    """Extracts and concatenates all text pages from a PDF byte string."""
    reader = PdfReader(BytesIO(pdf_bytes))
    return "".join(p.extract_text() or "" for p in reader.pages)


# ---------------------------------------------------------------------------
# PRE-COMPUTATION — summary + quiz generated silently after scrape
# ---------------------------------------------------------------------------

# Template for the summary prompt. Text is injected at {text}.
_SUMMARY_PROMPT = """\
Summarize the document below in 5-8 bullet points.
Cover: main topic, key concepts, important details, and conclusion.
Be concise. No preamble.

---
{text}
---"""

# Max characters sent to the LLM — kept small for speed with a 1b model.
# Excess text is sampled from the start, middle, and end.
MAX_PROMPT_CHARS = 2500


def _build_summary_prompt(raw: str) -> str:
    """
    Builds the summary prompt, truncating long documents by sampling
    800 chars from the start, 900 from the middle, and 500 from the end.
    This keeps the prompt within MAX_PROMPT_CHARS while preserving coverage.
    """
    text = raw.strip()
    if len(text) > MAX_PROMPT_CHARS:
        start  = text[:800]
        middle = text[len(text)//2 - 450 : len(text)//2 + 450]
        end    = text[-500:]
        text   = f"{start}\n\n[…]\n\n{middle}\n\n[…]\n\n{end}"
    return _SUMMARY_PROMPT.format(text=text)


@st.cache_resource
def _get_summary_llm():
    """
    Returns a cached OllamaLLM instance for summarisation.
    gemma3:1b is used — fast enough for a background pre-computation step.
    """
    from langchain_ollama import OllamaLLM
    return OllamaLLM(model="gemma3:1b")


@st.cache_resource
def _get_quiz_llm():
    """
    Returns a cached ChatOllama instance for quiz generation.
    temperature=0 ensures deterministic, well-structured JSON output.
    """
    from langchain_ollama import ChatOllama
    return ChatOllama(model="qwen2.5:1.5b", temperature=0, num_predict=512)


def _precompute_all(pdf_bytes: bytes) -> None:
    """
    Silently pre-generates a summary and 5 seed quiz questions right after
    a scrape succeeds. Both steps are no-ops if content already exists in
    session state, so calling this on a cache hit is safe.

    This means the Summarize and Quiz pages load instantly — no waiting.
    Errors are caught silently so a model failure never blocks the scraper.
    """
    text = _extract_text(pdf_bytes)
    if not text.strip():
        return

    # ---- Step 1: Auto-summary ----
    if not st.session_state.get("last_summary"):
        try:
            llm     = _get_summary_llm()
            summary = llm.invoke(_build_summary_prompt(text))
            st.session_state["last_summary"] = summary
            st.session_state["summary_done"] = True
            st.session_state["summary_auto"] = True   # triggers the "⚡ Summary auto-ready" badge
        except Exception:
            pass   # silent failure — user can still generate manually on the Summarize page

    # ---- Step 2: Auto-quiz (5 seed questions) ----
    if not st.session_state.get("quiz_data"):
        try:
            from modules.quiz_page import generate_single_question
            llm       = _get_quiz_llm()
            questions = []
            for _ in range(5):
                q = generate_single_question(llm, text, questions)
                if q:
                    questions.append(q)
            if questions:
                st.session_state["quiz_data"]      = questions
                st.session_state["quiz_prefilled"] = True   # triggers the "⚡ Quiz auto-ready" badge
        except Exception:
            pass   # silent failure — user can still generate manually on the Quiz page


# ---------------------------------------------------------------------------
# UI HELPERS
# ---------------------------------------------------------------------------

def _nav(page: str) -> None:
    """Navigate to a different page by updating session state and rerunning."""
    st.session_state["current_page"] = page
    st.rerun()


def _render_expanders(items: list[dict]) -> None:
    """
    Renders a collapsible expander for each scraped source, showing the URL
    and a preview of the first 4 chunks. Used in both the fresh-scrape and
    cache-hit paths to display what was collected.
    """
    for item in items:
        with st.expander(f"📄 {item['source']}", expanded=False):
            st.markdown(f"🔗 `{item['url']}`")
            for chunk in item["chunks"][:4]:   # preview only — full content is in the PDF
                st.markdown(f"- {chunk}")


# ---------------------------------------------------------------------------
# MAIN RENDER
# ---------------------------------------------------------------------------

def render():
    """
    Renders the Web Scraper page. Handles three right-column states:
      1. Scrape button clicked — runs a fresh threaded scrape or loads from cache
      2. Content already in session state — shows a "content ready" prompt
      3. Nothing scraped yet — shows an empty state card

    After a successful scrape, _precompute_all() is called to silently
    pre-generate a summary and quiz so downstream pages load instantly.
    """

    # ---- Page header ----
    st.markdown("""
    <div style="margin-bottom:1.75rem;">
        <div style="display:flex;align-items:center;gap:.55rem;margin-bottom:.1rem;">
            <span style="font-size:1.5rem;">🌐</span>
            <h1 style="margin:0!important;">Web Scraper</h1>
        </div>
        <p style="color:var(--text-muted);margin:.2rem 0 0;font-weight:300;">
            Select a domain and subdomain to scrape educational content.
        </p>
        <div style="height:1px;background:var(--border);margin-top:.9rem;"></div>
    </div>
    """, unsafe_allow_html=True)

    # Workflow progress breadcrumb — step 1 (Scrape) is highlighted
    st.markdown("""
    <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:1.5rem;flex-wrap:wrap;">
        <div style="background:var(--accent);color:#fff;border-radius:20px;
            padding:.3rem .85rem;font-size:.8rem;font-weight:600;">1 Scrape</div>
        <span style="color:var(--border-hover);">→</span>
        <div style="background:var(--surface-2);color:var(--text-muted);border-radius:20px;
            padding:.3rem .85rem;font-size:.8rem;font-weight:500;">2 Summarize</div>
        <span style="color:var(--border-hover);">→</span>
        <div style="background:var(--surface-2);color:var(--text-muted);border-radius:20px;
            padding:.3rem .85rem;font-size:.8rem;font-weight:500;">3 Quiz</div>
        <span style="color:var(--border-hover);">→</span>
        <div style="background:var(--surface-2);color:var(--text-muted);border-radius:20px;
            padding:.3rem .85rem;font-size:.8rem;font-weight:500;">4 Chat</div>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 2.2])

    # ----------------------------------------------------------------
    # LEFT COLUMN — domain/subdomain selectors and status badges
    # ----------------------------------------------------------------
    with col_left:
        st.markdown("""<div style="background:var(--surface);border:1px solid var(--border);
            border-radius:var(--radius-lg);padding:1.25rem 1.25rem .75rem;">
        """, unsafe_allow_html=True)

        domains   = list(SCRAPING_SOURCES.keys())
        domain    = st.selectbox("Domain",    domains)
        subdomain = st.selectbox("Subdomain", list(SCRAPING_SOURCES[domain].keys()))

        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        scrape_btn = st.button("🚀 Scrape Content", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Status badges — shown below the controls card once content exists
        if st.session_state.get("scraped_pdf_bytes"):
            st.markdown("""
            <div style="margin-top:.75rem;background:#ECFDF5;border:1px solid #A7F3D0;
                border-radius:var(--radius);padding:.6rem 1rem;
                font-size:.8rem;font-weight:500;color:#065F46;">
                ✅ PDF ready
            </div>""", unsafe_allow_html=True)

        # These badges are set by _precompute_all() after a successful scrape
        if st.session_state.get("summary_auto"):
            st.markdown("""
            <div style="margin-top:.5rem;background:#EFF6FF;border:1px solid #BFDBFE;
                border-radius:var(--radius);padding:.6rem 1rem;
                font-size:.8rem;font-weight:500;color:#1E40AF;">
                ⚡ Summary auto-ready
            </div>""", unsafe_allow_html=True)

        if st.session_state.get("quiz_prefilled"):
            st.markdown("""
            <div style="margin-top:.5rem;background:#F5F3FF;border:1px solid #DDD6FE;
                border-radius:var(--radius);padding:.6rem 1rem;
                font-size:.8rem;font-weight:500;color:#5B21B6;">
                ⚡ Quiz auto-ready
            </div>""", unsafe_allow_html=True)

    # ----------------------------------------------------------------
    # RIGHT COLUMN — scrape output / status / empty state
    # ----------------------------------------------------------------
    with col_right:
        if scrape_btn:
            # Check if this domain+subdomain combination is already in the memory cache
            cached = get_cached(domain, subdomain)

            if cached:
                # ---- Cache hit: load instantly, skip HTTP requests ----
                st.session_state.scraped_pdf_bytes = cached["pdf"]
                st.session_state["scrape_done"]    = True
                st.success("⚡ Loaded from cache instantly!")
                _render_expanders(cached["chunks"])

                # Pre-compute only if the downstream session state is missing
                if not st.session_state.get("last_summary") or \
                   not st.session_state.get("quiz_data"):
                    with st.spinner("⚡ Preparing summary and quiz…"):
                        _precompute_all(cached["pdf"])

            else:
                # ---- Cache miss: run a fresh parallel scrape ----
                sources      = SCRAPING_SOURCES[domain][subdomain]
                status_text  = st.empty()
                progress_bar = st.progress(0)

                status_text.markdown(
                    '<div style="font-size:.85rem;color:var(--text-muted);">'
                    '🔍 Scraping in parallel…</div>',
                    unsafe_allow_html=True)

                formatted = _scrape_all(sources, status_text, progress_bar)

                progress_bar.progress(1.0)
                status_text.empty()
                progress_bar.empty()

                if not formatted:
                    st.warning("⚠️ No content could be scraped. Try another subdomain.")
                else:
                    with st.spinner("📄 Building PDF…"):
                        pdf_bytes = _build_pdf(domain, subdomain, formatted)

                    # Store the PDF in session state and the memory cache
                    st.session_state.scraped_pdf_bytes = pdf_bytes
                    st.session_state["scrape_done"]    = True
                    set_cached(domain, subdomain, pdf_bytes, formatted)

                    st.success(f"✅ Scraped {len(formatted)} source(s) successfully!")
                    _render_expanders(formatted)

                    # Silently pre-generate summary and quiz in the background
                    with st.spinner("⚡ Auto-preparing summary and quiz in the background…"):
                        _precompute_all(pdf_bytes)

                    st.success("✅ Summary and quiz are ready — navigate there anytime!")

        elif st.session_state.get("scraped_pdf_bytes"):
            # Content exists from a previous scrape — prompt the user to act on it
            st.markdown("""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:1.5rem;margin-bottom:1rem;">
                <div style="font-size:.875rem;font-weight:600;color:var(--text);margin-bottom:.5rem;">
                    📋 You have scraped content ready</div>
                <div style="font-size:.85rem;color:var(--text-muted);">
                    Use the tools below or scrape new content on the left.</div>
            </div>""", unsafe_allow_html=True)
        else:
            # Nothing scraped yet — show the empty state card
            st.markdown("""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:2rem 1.5rem;text-align:center;
                color:var(--text-muted);">
                <div style="font-size:2rem;margin-bottom:.75rem;">🌐</div>
                <div style="font-size:.9rem;font-weight:500;margin-bottom:.35rem;">
                    No content scraped yet</div>
                <div style="font-size:.82rem;">
                    Choose a domain and subdomain on the left, then click Scrape Content.</div>
            </div>""", unsafe_allow_html=True)

    # ----------------------------------------------------------------
    # BOTTOM SECTION — download button + "What's next?" tool cards
    # Only rendered once content has been scraped
    # ----------------------------------------------------------------
    if st.session_state.get("scraped_pdf_bytes"):
        st.markdown("<div style='height:1px;background:var(--border);margin:1.5rem 0;'></div>",
                    unsafe_allow_html=True)

        # Download button floated to the left in a narrow column
        dl_col, _ = st.columns([1, 2])
        with dl_col:
            st.download_button(
                label="📄 Download PDF",
                data=st.session_state.scraped_pdf_bytes,
                file_name=f"scraped_{domain}_{subdomain}.pdf".replace(" ", "_"),
                mime="application/pdf",
                use_container_width=True,
            )

        st.markdown("""
        <div style="font-size:.72rem;font-weight:600;letter-spacing:.08em;
            text-transform:uppercase;color:var(--text-muted);
            margin:1.25rem 0 .75rem;">
            What would you like to do next?
        </div>""", unsafe_allow_html=True)

        # Three "next step" cards — Summarize, Quiz, Chat
        nc1, nc2, nc3 = st.columns(3)

        with nc1:
            ready = st.session_state.get("summary_auto")
            # Show "⚡ Already ready!" hint if summary was pre-computed
            st.markdown(f"""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:1rem;text-align:center;margin-bottom:.5rem;">
                <div style="font-size:1.4rem;margin-bottom:.4rem;">📄</div>
                <div style="font-size:.82rem;font-weight:600;color:var(--text);margin-bottom:.2rem;">
                    Summarize it</div>
                <div style="font-size:.75rem;color:{'#059669' if ready else 'var(--text-muted)'};">
                    {"⚡ Already ready!" if ready else "Get a concise overview"}
                </div>
            </div>""", unsafe_allow_html=True)
            if st.button("Open Summarizer", key="next_sum", use_container_width=True):
                _nav("summarization")

        with nc2:
            ready = st.session_state.get("quiz_prefilled")
            # Show "⚡ Already ready!" hint if quiz was pre-computed
            st.markdown(f"""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:1rem;text-align:center;margin-bottom:.5rem;">
                <div style="font-size:1.4rem;margin-bottom:.4rem;">🧩</div>
                <div style="font-size:.82rem;font-weight:600;color:var(--text);margin-bottom:.2rem;">
                    Test yourself</div>
                <div style="font-size:.75rem;color:{'#059669' if ready else 'var(--text-muted)'};">
                    {"⚡ Already ready!" if ready else "Generate a quiz"}
                </div>
            </div>""", unsafe_allow_html=True)
            if st.button("Open Quiz", key="next_quiz", use_container_width=True):
                _nav("quiz")

        with nc3:
            st.markdown("""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:1rem;text-align:center;margin-bottom:.5rem;">
                <div style="font-size:1.4rem;margin-bottom:.4rem;">💬</div>
                <div style="font-size:.82rem;font-weight:600;color:var(--text);margin-bottom:.2rem;">
                    Ask questions</div>
                <div style="font-size:.75rem;color:var(--text-muted);">Chat with content</div>
            </div>""", unsafe_allow_html=True)
            if st.button("Open Chatbot", key="next_chat", use_container_width=True):
                _nav("chatbot")