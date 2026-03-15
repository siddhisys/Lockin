import streamlit as st # type: ignore
from PyPDF2 import PdfReader # type: ignore
from langchain_ollama import OllamaLLM # type: ignore
from io import BytesIO
from reportlab.lib.pagesizes import A4 # type: ignore
from reportlab.pdfgen import canvas # type: ignore
from datetime import datetime


# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="AI Document Summarizer",
    page_icon="📄",
    layout="centered"
)

# -----------------------------
# PDF Generator Function
# -----------------------------
def generate_pdf(summary_text):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    text_object = c.beginText(40, height - 60)
    text_object.setFont("Helvetica", 11)

    title = "AI Generated Document Summary"
    date = datetime.now().strftime("%d %B %Y, %H:%M")

    text_object.textLine(title)
    text_object.textLine(f"Generated on: {date}")
    text_object.textLine("-" * 60)
    text_object.textLine("")

    for line in summary_text.split("\n"):
        text_object.textLine(line)

    c.drawText(text_object)
    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer


# -----------------------------
# UI - Header
# -----------------------------
st.title("📄 AI Document Summarizer")
st.write(
    "Upload a document and get a concise AI-generated summary of the main topics. "
    "You can also export the summary as a PDF."
)

st.divider()

# -----------------------------
# File Upload
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload a PDF document",
    type=["pdf"],
    help="Only PDF files are supported"
)

# -----------------------------
# Initialize LLM
# -----------------------------
llm = OllamaLLM(model="gemma3:1b")

# -----------------------------
# Main Logic
# -----------------------------
if uploaded_file is not None:
    try:
        reader = PdfReader(uploaded_file)
        document_text = ""

        for page in reader.pages:
            document_text += page.extract_text()

        st.success("Document successfully loaded.")

        if st.button("✨ Generate Summary"):
            with st.spinner("Generating summary... Please wait"):
                prompt = f"""
                Summarize the following document.
                Focus on the main topics and key points.
                Keep the summary concise and easy to understand.

                Document:
                {document_text}
                """

                summary = llm.invoke(prompt)

            st.subheader("📌 Summary")
            st.write(summary)

            pdf_file = generate_pdf(summary)

            st.download_button(
                label="📄 Export Summary as PDF",
                data=pdf_file,
                file_name="document_summary.pdf",
                mime="application/pdf"
            )

    except Exception as e:
        st.error(f"An error occurred: {e}")

else:
    st.info("Please upload a PDF file to begin.")
