import streamlit as st
import requests
import time
import re
import nltk
from bs4 import BeautifulSoup
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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
    "AI": {
        "Machine Learning": {
            "Google AI": ["https://developers.google.com/machine-learning/crash-course/"],
            "OpenAI": ["https://openai.com/research/"]
        },
        "NLP": {
            "Stanford NLP": ["https://nlp.stanford.edu/"]
        }
    },
    "Programming": {
        "Python": {
            "Python Docs": ["https://docs.python.org/3/tutorial/introduction.html"]
        },
        "JavaScript": {
            "MDN": ["https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Introduction"]
        }
    }
}

HEADERS = {"User-Agent": "Mozilla/5.0"}
REQUEST_DELAY = 1.5
SENTENCES_PER_CHUNK = 4
MIN_TEXT_LENGTH = 100

def parse_html(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    texts = [tag.get_text(strip=True) for tag in soup.find_all(["p","li","h1","h2","h3"]) if len(tag.get_text(strip=True)) > 30]
    return " ".join(texts)

def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s.,;:!?()-]", "", text)
    return text.strip()

def chunk_text(text):
    sentences = sent_tokenize(text)
    chunks = []
    for i in range(0, len(sentences), SENTENCES_PER_CHUNK):
        chunk = " ".join(sentences[i:i+SENTENCES_PER_CHUNK])
        if len(chunk) > 40:
            chunks.append(chunk)
    return chunks

def scrape_url(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        raw = parse_html(response.text)
        cleaned = clean_text(raw)
        if len(cleaned) < MIN_TEXT_LENGTH:
            return None
        return chunk_text(cleaned)
    except:
        return None

def render():
    st.markdown("# 🌐 Web Scraper")
    st.markdown("Select a domain and subdomain to scrape content. Download as PDF to use in other tools.")
    st.markdown("---")

    col_left, col_right = st.columns([1, 2.5])

    with col_left:
        domains = list(SCRAPING_SOURCES.keys())
        domain = st.selectbox("Domain", domains)
        subdomains = list(SCRAPING_SOURCES.get(domain, {}).keys())
        subdomain = st.selectbox("Subdomain", subdomains)
        scrape_btn = st.button("🚀 Scrape", use_container_width=True)
        st.info("💡 Download the PDF and upload it to Summarizer, Quiz or Chatbot!")

    with col_right:
        if scrape_btn:
            sources = SCRAPING_SOURCES[domain][subdomain]
            results = []

            with st.spinner("Scraping sources..."):
                for source, urls in sources.items():
                    for url in urls:
                        chunks = scrape_url(url)
                        results.append({
                            "source": source, "url": url,
                            "status": "success" if chunks else "failed",
                            "chunks": chunks or []
                        })
                        time.sleep(REQUEST_DELAY)

            formatted = [r for r in results if r["status"] == "success"]

            if not formatted:
                st.warning("No content could be scraped. Try another subdomain.")
            else:
                st.success(f"✅ Scraped {len(formatted)} source(s)!")

                for item in formatted:
                    st.markdown(f"**{item['source']}**")
                    st.markdown(f"🔗 {item['url']}")
                    for chunk in item["chunks"][:4]:
                        st.markdown(f"- {chunk}")
                    st.markdown("---")

                # Generate PDF
                def safe(t):
                    return str(t).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

                pdf_buffer = BytesIO()
                doc = SimpleDocTemplate(pdf_buffer, pagesize=A4,
                                        rightMargin=20*mm, leftMargin=20*mm,
                                        topMargin=20*mm, bottomMargin=20*mm)
                styles = getSampleStyleSheet()
                h_style = ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=13, spaceAfter=4)
                m_style = ParagraphStyle("M", fontName="Helvetica", fontSize=10, textColor=colors.HexColor("#555555"))
                b_style = ParagraphStyle("B", fontName="Helvetica", fontSize=10, leftIndent=10, spaceAfter=2)
                t_style = ParagraphStyle("T", fontName="Helvetica-Bold", fontSize=16, alignment=1, spaceAfter=12)

                story = [Paragraph("Scraped Content", t_style), Spacer(1, 8*mm)]
                for item in formatted:
                    story.append(Paragraph(safe(f"{domain} > {subdomain}"), h_style))
                    story.append(Paragraph(safe(f"Source: {item['source']}"), m_style))
                    story.append(Paragraph(safe(f"URL: {item['url']}"), m_style))
                    story.append(Spacer(1, 3*mm))
                    for chunk in item["chunks"]:
                        story.append(Paragraph(safe(f"• {chunk}"), b_style))
                        story.append(Spacer(1, 1*mm))
                    story.append(Spacer(1, 5*mm))

                doc.build(story)
                pdf_buffer.seek(0)
                st.session_state.scraped_pdf_bytes = pdf_buffer.getvalue()

                st.download_button(
                    label="📄 Download as PDF",
                    data=st.session_state.scraped_pdf_bytes,
                    file_name="scraped_content.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        else:
            st.info("Choose a domain and subdomain on the left, then click Scrape.")