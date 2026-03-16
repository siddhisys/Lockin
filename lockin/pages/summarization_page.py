import streamlit as st
from PyPDF2 import PdfReader
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

def render():
    st.markdown("# 📄 AI Summarizer")
    st.markdown("Upload a PDF and get a concise AI-generated summary.")
    st.markdown("---")

    col_left, col_right = st.columns([1, 2])

    with col_left:
        source = st.radio("Source", ["Upload a PDF", "Use scraped PDF"])

        uploaded_file = None
        use_scraped = False

        if source == "Upload a PDF":
            uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")
        else:
            if st.session_state.get("scraped_pdf_bytes"):
                st.success("✅ Scraped PDF ready!")
                use_scraped = True
            else:
                st.info("No scraped PDF yet. Go to Web Scraper first.")

        gen_btn = st.button("✨ Generate Summary", use_container_width=True)
        st.info("💡 Model: gemma3:1b via Ollama. Make sure Ollama is running.")

    with col_right:
        if gen_btn:
            document_text = ""
            try:
                if use_scraped and st.session_state.get("scraped_pdf_bytes"):
                    reader = PdfReader(BytesIO(st.session_state.scraped_pdf_bytes))
                    for page in reader.pages:
                        document_text += page.extract_text() or ""
                elif uploaded_file:
                    reader = PdfReader(uploaded_file)
                    for page in reader.pages:
                        document_text += page.extract_text() or ""
                else:
                    st.warning("Please upload a PDF or use scraped content.")
                    return

                if not document_text.strip():
                    st.error("Could not extract text from the PDF.")
                    return

                with st.spinner("Generating summary..."):
                    from langchain_ollama import OllamaLLM
                    llm = OllamaLLM(model="gemma3:1b")
                    prompt = f"""Summarize the following document.
Focus on the main topics and key points.
Keep the summary concise and easy to understand.

Document:
{document_text[:4000]}"""
                    summary = llm.invoke(prompt)

                st.session_state.last_summary = summary
                st.markdown("### 📌 Summary")
                st.write(summary)

                buf = BytesIO()
                c = canvas.Canvas(buf, pagesize=A4)
                width, height = A4
                text_obj = c.beginText(40, height - 60)
                text_obj.setFont("Helvetica-Bold", 13)
                text_obj.textLine("AI Generated Summary")
                text_obj.setFont("Helvetica", 10)
                text_obj.textLine(f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}")
                text_obj.textLine("-" * 70)
                text_obj.textLine("")
                text_obj.setFont("Helvetica", 11)
                for line in summary.split("\n"):
                    text_obj.textLine(line)
                c.drawText(text_obj)
                c.showPage()
                c.save()
                buf.seek(0)

                st.download_button(
                    label="📄 Export Summary as PDF",
                    data=buf,
                    file_name="summary.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"Error: {e}")
                st.info("Make sure Ollama is running: ollama serve")
        else:
            st.info("Upload a PDF on the left and click Generate Summary.")