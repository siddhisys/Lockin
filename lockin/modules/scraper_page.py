import streamlit as st
import requests
import time
import re
import nltk
from bs4 import BeautifulSoup
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download("punkt", quiet=True)
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download("punkt_tab", quiet=True)

from nltk.tokenize import sent_tokenize

SCRAPING_SOURCES = {
    "Artificial Intelligence": {
        "Machine Learning": {
            "Wikipedia – Machine Learning": ["https://en.wikipedia.org/wiki/Machine_learning"],
            "Wikipedia – Supervised Learning": ["https://en.wikipedia.org/wiki/Supervised_learning"],
            "Wikipedia – Unsupervised Learning": ["https://en.wikipedia.org/wiki/Unsupervised_learning"],
        },
        "Natural Language Processing": {
            "Wikipedia – NLP": ["https://en.wikipedia.org/wiki/Natural_language_processing"],
            "Wikipedia – Text Mining": ["https://en.wikipedia.org/wiki/Text_mining"],
            "Wikipedia – Sentiment Analysis": ["https://en.wikipedia.org/wiki/Sentiment_analysis"],
        },
        "Computer Vision": {
            "Wikipedia – Computer Vision": ["https://en.wikipedia.org/wiki/Computer_vision"],
            "Wikipedia – Convolutional Neural Network": ["https://en.wikipedia.org/wiki/Convolutional_neural_network"],
            "Wikipedia – Object Detection": ["https://en.wikipedia.org/wiki/Object_detection"],
        },
        "Deep Learning": {
            "Wikipedia – Deep Learning": ["https://en.wikipedia.org/wiki/Deep_learning"],
            "Wikipedia – Artificial Neural Network": ["https://en.wikipedia.org/wiki/Artificial_neural_network"],
            "Wikipedia – Backpropagation": ["https://en.wikipedia.org/wiki/Backpropagation"],
        },
        "Reinforcement Learning": {
            "Wikipedia – Reinforcement Learning": ["https://en.wikipedia.org/wiki/Reinforcement_learning"],
            "Wikipedia – Markov Decision Process": ["https://en.wikipedia.org/wiki/Markov_decision_process"],
            "Wikipedia – Q-Learning": ["https://en.wikipedia.org/wiki/Q-learning"],
        },
    },
    "Data Science": {
        "Statistical Analysis": {
            "Wikipedia – Statistics": ["https://en.wikipedia.org/wiki/Statistics"],
            "Wikipedia – Regression Analysis": ["https://en.wikipedia.org/wiki/Regression_analysis"],
            "Wikipedia – Hypothesis Testing": ["https://en.wikipedia.org/wiki/Statistical_hypothesis_testing"],
        },
        "Data Visualisation": {
            "Wikipedia – Data Visualisation": ["https://en.wikipedia.org/wiki/Data_and_information_visualization"],
            "Wikipedia – Chart": ["https://en.wikipedia.org/wiki/Chart"],
            "Wikipedia – Histogram": ["https://en.wikipedia.org/wiki/Histogram"],
        },
        "Big Data Engineering": {
            "Wikipedia – Big Data": ["https://en.wikipedia.org/wiki/Big_data"],
            "Wikipedia – Apache Spark": ["https://en.wikipedia.org/wiki/Apache_Spark"],
            "Wikipedia – Data Warehouse": ["https://en.wikipedia.org/wiki/Data_warehouse"],
        },
        "Data Wrangling": {
            "Wikipedia – Data Wrangling": ["https://en.wikipedia.org/wiki/Data_wrangling"],
            "Wikipedia – Data Cleansing": ["https://en.wikipedia.org/wiki/Data_cleansing"],
            "Wikipedia – Feature Engineering": ["https://en.wikipedia.org/wiki/Feature_engineering"],
        },
    },
    "Programming": {
        "Python": {
            "Python Docs – Introduction": ["https://docs.python.org/3/tutorial/introduction.html"],
            "Python Docs – Data Structures": ["https://docs.python.org/3/tutorial/datastructures.html"],
            "Wikipedia – Python": ["https://en.wikipedia.org/wiki/Python_(programming_language)"],
        },
        "JavaScript": {
            "MDN – JS Introduction": ["https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Introduction"],
            "Wikipedia – JavaScript": ["https://en.wikipedia.org/wiki/JavaScript"],
        },
        "Data Structures & Algorithms": {
            "Wikipedia – Data Structures": ["https://en.wikipedia.org/wiki/Data_structure"],
            "Wikipedia – Sorting Algorithms": ["https://en.wikipedia.org/wiki/Sorting_algorithm"],
            "Wikipedia – Big O Notation": ["https://en.wikipedia.org/wiki/Big_O_notation"],
        },
    },
    "Web Development": {
        "Frontend Development": {
            "Wikipedia – HTML": ["https://en.wikipedia.org/wiki/HTML"],
            "Wikipedia – CSS": ["https://en.wikipedia.org/wiki/CSS"],
            "Wikipedia – React": ["https://en.wikipedia.org/wiki/React_(software)"],
        },
        "Backend Development": {
            "Wikipedia – Web Framework": ["https://en.wikipedia.org/wiki/Web_framework"],
            "Wikipedia – REST API": ["https://en.wikipedia.org/wiki/REST"],
            "Wikipedia – Database": ["https://en.wikipedia.org/wiki/Database"],
        },
    },
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
REQUEST_DELAY = 0.5
SENTENCES_PER_CHUNK = 4
MIN_TEXT_LENGTH = 150

_BOILERPLATE_RE = re.compile(
    r"(sign up|log in|subscribe|newsletter|cookie|privacy policy|terms of service|"
    r"all rights reserved|click here|read more|contact us|about us|follow us|copyright|©|"
    r"advertisement|from wikipedia|retrieved from|wikimedia foundation|edit this page|"
    r"cite this page|this article|main page)", re.IGNORECASE)

def _is_boilerplate(text):
    return len(text.strip()) < 40 or bool(_BOILERPLATE_RE.search(text))

def _parse_wikipedia(soup):
    content = soup.find("div", {"class": "mw-parser-output"})
    if not content:
        return ""
    texts, total = [], 0
    for tag in content.find_all(["p", "h2", "h3"]):
        for u in tag.find_all(["sup", "span", "table"]):
            u.decompose()
        t = tag.get_text(separator=" ", strip=True)
        if not _is_boilerplate(t):
            texts.append(t)
            total += len(t)
        if total > 8000:
            break
    return " ".join(texts)

def _parse_generic(soup):
    for tag in soup(["script","style","nav","footer","header","aside","form","button","noscript","iframe","svg"]):
        tag.decompose()
    return " ".join(t for tag in soup.find_all(["p","h2","h3","li"])
                    if not _is_boilerplate(t := tag.get_text(separator=" ", strip=True)))

def parse_html(html, url):
    soup = BeautifulSoup(html, "html.parser")
    return _parse_wikipedia(soup) if "wikipedia.org" in url else _parse_generic(soup)

def clean_text(text):
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\s+", " ", text)
    return re.sub(r"[^\w\s.,;:!?()\-\']", "", text).strip()

def chunk_text(text):
    sentences = [s.strip() for s in sent_tokenize(text) if len(s.strip()) > 40]
    return [c for i in range(0, len(sentences), SENTENCES_PER_CHUNK)
            if len(c := " ".join(sentences[i:i+SENTENCES_PER_CHUNK])) > 60]

def scrape_url(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        chunks = chunk_text(clean_text(parse_html(resp.text, url)))
        return chunks or None
    except Exception:
        return None

def build_pdf(domain, subdomain, formatted):
    def safe(t):
        return str(t).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    pdf_buf = BytesIO()
    doc = SimpleDocTemplate(pdf_buf, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    t_sty = ParagraphStyle("T", fontName="Helvetica-Bold", fontSize=16, alignment=1, spaceAfter=12)
    h_sty = ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=13, spaceAfter=4)
    m_sty = ParagraphStyle("M", fontName="Helvetica", fontSize=10, textColor=colors.HexColor("#555555"))
    b_sty = ParagraphStyle("B", fontName="Helvetica", fontSize=10, leftIndent=10, spaceAfter=2)
    story = [Paragraph("Scraped Content", t_sty), Spacer(1, 8*mm)]
    for item in formatted:
        story += [
            Paragraph(safe(f"{domain} › {subdomain}"), h_sty),
            Paragraph(safe(f"Source: {item['source']}"), m_sty),
            Paragraph(safe(f"URL: {item['url']}"), m_sty),
            Spacer(1, 3*mm),
        ]
        for chunk in item["chunks"]:
            story += [Paragraph(safe(f"• {chunk}"), b_sty), Spacer(1, 1*mm)]
        story.append(Spacer(1, 5*mm))
    doc.build(story)
    pdf_buf.seek(0)
    return pdf_buf.getvalue()

def _nav(page):
    st.session_state["current_page"] = page
    st.rerun()

def _render_expanders(display_results):
    """Render source expanders — used by both cache and fresh scrape paths."""
    for item in display_results:
        with st.expander(f"📄 {item['source']}", expanded=False):
            st.markdown(f"🔗 `{item['url']}`")
            for chunk in item["chunks"][:4]:
                st.markdown(f"- {chunk}")

def render():
    from utils.db import (
        get_cached_scrape, save_scrape_cache,
        get_cached_display, save_display_cache,
    )

    # ------- Header ----------------------------
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

    # -------- Step indicator ----------------------------
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

    with col_left:
        st.markdown("""<div style="background:var(--surface);border:1px solid var(--border);
            border-radius:var(--radius-lg);padding:1.25rem 1.25rem .75rem;">
        """, unsafe_allow_html=True)

        domains    = list(SCRAPING_SOURCES.keys())
        domain     = st.selectbox("Domain", domains)
        subdomains = list(SCRAPING_SOURCES[domain].keys())
        subdomain  = st.selectbox("Subdomain", subdomains)

        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        scrape_btn = st.button("🚀 Scrape Content", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.get("scraped_pdf_bytes"):
            st.markdown("""
            <div style="margin-top:.75rem;background:#ECFDF5;border:1px solid #A7F3D0;
                border-radius:var(--radius);padding:.75rem 1rem;
                font-size:.85rem;font-weight:500;color:#065F46;">
                ✅ PDF ready — use it in other tools below
            </div>
            """, unsafe_allow_html=True)

    with col_right:
        if scrape_btn:
            # ------- Check DB cache first ----------------------------
            cached_pdf    = get_cached_scrape(domain, subdomain)
            cached_chunks = get_cached_display(domain, subdomain)

            if cached_pdf and cached_chunks:
                # -------- Instant load — zero HTTP calls ----------------------------
                st.session_state.scraped_pdf_bytes = cached_pdf
                st.session_state["scrape_done"] = True
                st.success("⚡ Loaded from cache instantly!")
                _render_expanders(cached_chunks)

            else:
                # ---------- Fresh scrape ----------------------------
                sources   = SCRAPING_SOURCES[domain][subdomain]
                all_urls  = [(source, url)
                             for source, urls in sources.items()
                             for url in urls]
                total_urls = len(all_urls)

                status_text  = st.empty()
                progress_bar = st.progress(0)
                results      = []

                for i, (source, url) in enumerate(all_urls):
                    status_text.markdown(f"""
                    <div style="font-size:.85rem;color:var(--text-muted);margin-bottom:.5rem;">
                        🔍 Scraping <strong>{source}</strong>... ({i+1}/{total_urls})
                    </div>
                    """, unsafe_allow_html=True)
                    progress_bar.progress((i + 1) / total_urls)

                    chunks = scrape_url(url)
                    results.append({
                        "source": source, "url": url,
                        "status": "success" if chunks else "failed",
                        "chunks": chunks or [],
                    })
                    time.sleep(REQUEST_DELAY)

                progress_bar.progress(1.0)
                status_text.empty()
                progress_bar.empty()

                formatted = [r for r in results if r["status"] == "success"]

                if not formatted:
                    st.warning("⚠️ No content could be scraped. Try another subdomain.")
                else:
                    with st.spinner("📄 Building PDF…"):
                        pdf_bytes = build_pdf(domain, subdomain, formatted)

                    st.session_state.scraped_pdf_bytes = pdf_bytes
                    st.session_state["scrape_done"] = True

                    # Save both PDF and chunks to DB
                    save_scrape_cache(domain, subdomain, pdf_bytes)
                    save_display_cache(domain, subdomain, formatted)

                    st.success(f"✅ Scraped {len(formatted)} source(s) and saved to cache!")
                    _render_expanders(formatted)

        elif st.session_state.get("scraped_pdf_bytes"):
            st.markdown("""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:1.5rem;margin-bottom:1rem;">
                <div style="font-size:.875rem;font-weight:600;color:var(--text);margin-bottom:.5rem;">
                    📋 You have scraped content ready
                </div>
                <div style="font-size:.85rem;color:var(--text-muted);">
                    Use the tools below or scrape new content on the left.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:2rem 1.5rem;text-align:center;
                color:var(--text-muted);">
                <div style="font-size:2rem;margin-bottom:.75rem;">🌐</div>
                <div style="font-size:.9rem;font-weight:500;margin-bottom:.35rem;">
                    No content scraped yet</div>
                <div style="font-size:.82rem;">
                    Choose a domain and subdomain on the left, then click Scrape Content.
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ------- Download + What's next (always visible when PDF exists) ----------------------------
    if st.session_state.get("scraped_pdf_bytes"):
        st.markdown("<div style='height:1px;background:var(--border);margin:1.5rem 0;'></div>",
                    unsafe_allow_html=True)

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
        </div>
        """, unsafe_allow_html=True)

        nc1, nc2, nc3 = st.columns(3)
        with nc1:
            st.markdown("""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:1rem;text-align:center;margin-bottom:.5rem;">
                <div style="font-size:1.4rem;margin-bottom:.4rem;">📄</div>
                <div style="font-size:.82rem;font-weight:600;color:var(--text);margin-bottom:.2rem;">
                    Summarize it</div>
                <div style="font-size:.75rem;color:var(--text-muted);">Get a concise overview</div>
            </div>""", unsafe_allow_html=True)
            if st.button("Open Summarizer", key="next_sum", use_container_width=True):
                _nav("summarization")
        with nc2:
            st.markdown("""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:1rem;text-align:center;margin-bottom:.5rem;">
                <div style="font-size:1.4rem;margin-bottom:.4rem;">🧩</div>
                <div style="font-size:.82rem;font-weight:600;color:var(--text);margin-bottom:.2rem;">
                    Test yourself</div>
                <div style="font-size:.75rem;color:var(--text-muted);">Generate a quiz</div>
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