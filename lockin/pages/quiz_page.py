import streamlit as st
import json
import re
from PyPDF2 import PdfReader
from io import BytesIO

def reset_quiz():
    st.session_state.quiz_data = None
    st.session_state.current_question = 0
    st.session_state.answers = {}
    st.session_state.submitted = False
    st.session_state.quiz_started = False
    st.session_state.pdf_content = None

def render():
    st.markdown("# 🧩 Quiz Generator")
    st.markdown("Upload a PDF and AI will generate multiple choice questions.")
    st.markdown("---")

    if not st.session_state.get("quiz_started"):
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

            num_q = st.slider("Number of questions", 5, 20, 10)
            gen_btn = st.button("🚀 Generate Quiz", use_container_width=True)

        with col_right:
            if gen_btn:
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
                    else:
                        st.warning("Please upload a PDF or use scraped content.")
                        return

                    if not pdf_text.strip():
                        st.error("Could not extract text from PDF.")
                        return

                    with st.spinner("Generating questions..."):
                        from langchain_ollama import ChatOllama
                        llm = ChatOllama(model="gemma3:1b", temperature=0.7)
                        prompt = f"""Generate {num_q} multiple choice questions from this content.

Content:
{pdf_text[:3000]}

Return ONLY a JSON array like this:
[
  {{
    "question": "Question here?",
    "options": {{"A": "option", "B": "option", "C": "option", "D": "option"}},
    "correct": "A"
  }}
]

JSON:"""
                        response = llm.invoke(prompt)
                        text = response.content.strip()
                        match = re.search(r'\[.*\]', text, re.DOTALL)
                        if match:
                            questions = json.loads(match.group(0))
                            valid = [q for q in questions if 'question' in q and 'options' in q and 'correct' in q and q['correct'] in q['options']]
                            if valid:
                                st.session_state.quiz_data = valid
                                st.session_state.quiz_started = True
                                st.success(f"✅ Generated {len(valid)} questions!")
                                st.rerun()
                            else:
                                st.error("Could not parse questions. Try again.")
                        else:
                            st.error("AI response was not valid JSON. Try again.")
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.info("Make sure Ollama is running: ollama serve")
            else:
                st.info("Configure your quiz on the left and click Generate.")

    elif st.session_state.get("submitted"):
        quiz_data = st.session_state.quiz_data
        answers = st.session_state.answers
        correct = sum(1 for i, q in enumerate(quiz_data) if answers.get(i) == q['correct'])
        total = len(quiz_data)
        pct = (correct / total) * 100

        st.markdown(f"## 🎉 Quiz Complete!")
        st.markdown(f"### Score: {correct} / {total} ({pct:.1f}%)")
        st.markdown("---")

        for i, q in enumerate(quiz_data):
            user_ans = answers.get(i)
            is_correct = user_ans == q['correct']
            icon = "✅" if is_correct else "❌"
            user_text = q['options'].get(user_ans, "Not answered") if user_ans else "Not answered"
            st.markdown(f"{icon} **Q{i+1}:** {q['question']}")
            st.markdown(f"Your answer: {user_ans}) {user_text}")
            if not is_correct:
                st.markdown(f"Correct answer: {q['correct']}) {q['options'][q['correct']]}")
            st.markdown("---")

        if st.button("🔄 New Quiz", use_container_width=True):
            reset_quiz()
            st.rerun()

    else:
        quiz_data = st.session_state.quiz_data
        current_q = st.session_state.current_question
        total = len(quiz_data)
        answered = len(st.session_state.answers)

        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            st.markdown(f"**Question {current_q + 1} of {total}**")
            st.progress(answered / total)
            st.markdown(f"*{answered} / {total} answered*")
            st.markdown("---")

            question = quiz_data[current_q]
            st.markdown(f"### {question['question']}")

            options_list = [f"{k}. {v}" for k, v in question['options'].items()]
            prev_ans = st.session_state.answers.get(current_q)
            default_idx = None
            if prev_ans:
                for idx, opt in enumerate(options_list):
                    if opt.startswith(prev_ans):
                        default_idx = idx
                        break

            selected = st.radio("Select your answer:", options_list,
                                key=f"q_{current_q}", index=default_idx)
            if selected:
                st.session_state.answers[current_q] = selected.split('.')[0].strip()

            st.markdown("---")
            col_prev, col_next, col_submit = st.columns(3)
            with col_prev:
                if current_q > 0:
                    if st.button("← Previous", use_container_width=True):
                        st.session_state.current_question -= 1
                        st.rerun()
            with col_next:
                if current_q < total - 1:
                    if st.button("Next →", use_container_width=True):
                        st.session_state.current_question += 1
                        st.rerun()
            with col_submit:
                if st.button("✅ Submit", use_container_width=True):
                    st.session_state.submitted = True
                    st.rerun()

        with st.sidebar:
            st.markdown("---")
            if st.button("🚫 Cancel Quiz", use_container_width=True):
                reset_quiz()
                st.rerun()