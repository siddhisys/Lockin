import streamlit as st # type: ignore
import io
from core.router import get_domains, get_subdomains, get_sources
from core.scraper import scrape_sources
from output.formatter import format_results
from output.pdf_generator import generate_pdf

st.set_page_config(
    page_title="Domain Knowledge Scraper",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Domain Knowledge Scraper")
st.markdown(
    "Select a domain and subdomain, scrape credible sources, "
    "view the content, and download it as a PDF."
)

# --- Sidebar selection ---
st.sidebar.header("User Selection")
domains = get_domains()
domain = st.sidebar.selectbox("Select Domain", domains)

subdomain = None
if domain:
    subdomains = get_subdomains(domain)
    subdomain = st.sidebar.selectbox("Select Subdomain", subdomains)

# --- Scrape button ---
if st.sidebar.button("Scrape") and domain and subdomain:
    sources = get_sources(domain, subdomain)

    with st.spinner("🚀 Scraping credible sources... This may take a few moments."):
        results = scrape_sources(sources, domain, subdomain)
        formatted = format_results(results)

    if not formatted:
        st.warning("⚠️ No content could be scraped. Check the URLs or try another subdomain.")
    else:
        st.success("✅ Scraping complete!")

        # --- Display results ---
        for item in formatted:
            st.markdown(f"### {item['title']}")
            st.markdown(f"**Source:** {item['source']}")
            st.markdown(f"**URL:** {item['url']}")
            for chunk in item["content"]:
                st.markdown(f"- {chunk}")
            st.markdown("---")

        # --- PDF Download ---
        pdf_buffer = io.BytesIO()
        pdf_file = generate_pdf(formatted, filename="scraped_content.pdf")
        with open(pdf_file, "rb") as f:
            pdf_buffer.write(f.read())
        pdf_buffer.seek(0)

        st.download_button(
            label="📄 Download PDF",
            data=pdf_buffer,
            file_name="scraped_content.pdf",
            mime="application/pdf",
            help="Click to download the scraped content as a PDF"
        )
