import streamlit as st
import json
import re
from PyPDF2 import PdfReader
from io import BytesIO
from langchain_ollama import ChatOllama


def _nav(page):
    st.session_state["current_page"] = page
    st.rerun()


def reset_quiz():
    for key in ["quiz_data", "current_question", "answers", "submitted", "quiz_started", "use_manual_pdf"]:
        if key in st.session_state:
            del st.session_state[key]


def _get_chunk(pdf_text, question_index, total_questions):
    text_len = len(pdf_text)
    chunk_size = min(800, text_len)
    if text_len <= chunk_size:
        return pdf_text

    if total_questions > 1:
        section_size = text_len // total_questions
        start = min(question_index * section_size, text_len - chunk_size)
    else:
        step = max(1, (text_len - chunk_size) // max(total_questions, 1))
        start = min(question_index * step, text_len - chunk_size)
    
    return pdf_text[start:start + chunk_size]


def generate_one_question(llm, pdf_text, existing_questions, question_index, total_questions):
    chunk = _get_chunk(pdf_text, question_index, total_questions)
    
    prompt = f"""Based on this text, create a multiple choice question with 4 options.
Only one correct answer.

Text: {chunk[:600]}

Output EXACTLY in this format (nothing else):

QUESTION: [your question]
A) [option A]
B) [option B]
C) [option C]
D) [option D]
ANSWER: [A/B/C/D]"""

    for attempt in range(4):
        try:
            response = llm.invoke(prompt)
            text = response.content.strip()
            lines = [line.strip() for line in text.split('\n') if line.strip()]

            question = None
            options = {}
            answer = None

            for line in lines:
                if line.startswith('QUESTION:'):
                    question = line.replace('QUESTION:', '', 1).strip()
                elif line.startswith('A)'):
                    options['A'] = line[2:].strip()
                elif line.startswith('B)'):
                    options['B'] = line[2:].strip()
                elif line.startswith('C)'):
                    options['C'] = line[2:].strip()
                elif line.startswith('D)'):
                    options['D'] = line[2:].strip()
                elif line.startswith('ANSWER:'):
                    ans = line.replace('ANSWER:', '', 1).strip().upper()
                    if ans in ['A', 'B', 'C', 'D']:
                        answer = ans

            if (question and len(options) == 4 and answer and 
                len(question) > 15 and all(len(v) > 3 for v in options.values())):

                # Duplicate check
                for ex in existing_questions:
                    if question.lower() == ex['question'].lower():
                        break
                    overlap = len(set(question.lower().split()) & set(ex['question'].lower().split())) 
                    if overlap / len(set(question.lower().split())) > 0.65:
                        break
                else:
                    # No duplicate found
                    return {
                        "question": question,
                        "options": options,
                        "correct": answer
                    }
        except:
            continue

    # Fallback
    return {
        "question": f"What is the main topic discussed in this section of the document?",
        "options": {
            "A": "Important concept explained",
            "B": "Historical background",
            "C": "Future implications",
            "D": "Technical details"
        },
        "correct": "A"
    }


def render():
    if "use_manual_pdf" not in st.session_state:
        st.session_state.use_manual_pdf = False


    st.markdown("""
    <div style="margin-bottom:1.5rem;">
        <div style="display:flex;align-items:center;gap:.55rem;margin-bottom:.1rem;">
            <span style="font-size:1.5rem;">🧩</span>
            <h1 style="margin:0!important;">Quiz Generator</h1>
        </div>
        <p style="color:var(--text-muted);margin:.2rem 0 0;font-weight:300;">
            Turn any PDF into a multiple-choice quiz. Test what you've learned.
        </p>
        <div style="height:1px;background:var(--border);margin-top:.9rem;"></div>
    </div>
    """, unsafe_allow_html=True)

    # Progress steps
    st.markdown("""
    <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:1.5rem;flex-wrap:wrap;">
        <div style="background:var(--surface-2);color:var(--text-muted);border-radius:20px;padding:.3rem .85rem;font-size:.8rem;font-weight:500;">1 Scrape</div>
        <span style="color:var(--border-hover);">→</span>
        <div style="background:var(--surface-2);color:var(--text-muted);border-radius:20px;padding:.3rem .85rem;font-size:.8rem;font-weight:500;">2 Summarize</div>
        <span style="color:var(--border-hover);">→</span>
        <div style="background:var(--accent);color:#fff;border-radius:20px;padding:.3rem .85rem;font-size:.8rem;font-weight:600;">3 Quiz</div>
        <span style="color:var(--border-hover);">→</span>
        <div style="background:var(--surface-2);color:var(--text-muted);border-radius:20px;padding:.3rem .85rem;font-size:.8rem;font-weight:500;">4 Chat</div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.get("quiz_started"):
        # === SETUP PHASE ===
        has_scraped = bool(st.session_state.get("scraped_pdf_bytes"))
        col_left, col_right = st.columns([1, 2])

        with col_left:
            st.markdown("""<div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);padding:1.25rem 1.25rem 1rem;">""", unsafe_allow_html=True)

            if has_scraped and not st.session_state.use_manual_pdf:
                st.success("✅ Scraped PDF content is ready")
                if st.button("📤 Use a different PDF instead", use_container_width=True):
                    st.session_state.use_manual_pdf = True
                    st.rerun()
                uploaded_file = None
                use_scraped = True
            else:
                if has_scraped:
                    if st.button("← Use scraped PDF", use_container_width=True):
                        st.session_state.use_manual_pdf = False
                        st.rerun()
                uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"], label_visibility="collapsed")
                use_scraped = False

            num_q = st.slider("Number of questions", 3, 10, 5)
            gen_btn = st.button("🚀 Generate Quiz", use_container_width=True, type="primary")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_right:
            if gen_btn:
                # Extract text
                pdf_text = ""
                try:
                    if use_scraped and st.session_state.get("scraped_pdf_bytes"):
                        reader = PdfReader(BytesIO(st.session_state.scraped_pdf_bytes))
                    elif uploaded_file:
                        reader = PdfReader(uploaded_file)
                    else:
                        st.error("Please provide a PDF.")
                        st.stop()

                    for page in reader.pages:
                        pdf_text += page.extract_text() or ""
                    
                    if len(pdf_text.strip()) < 100:
                        st.error("Not enough text extracted from PDF.")
                        st.stop()
                except Exception as e:
                    st.error(f"Error reading PDF: {e}")
                    st.stop()

                llm = ChatOllama(
                    model="qwen2.5:1.5b",
                    temperature=0.3,
                    num_predict=400,
                )

                progress = st.progress(0)
                status = st.empty()
                questions = []

                for i in range(num_q):
                    status.markdown(f"**Generating question {i+1} of {num_q}...**")
                    progress.progress((i + 1) / num_q)
                    
                    q = generate_one_question(llm, pdf_text, questions, i, num_q)
                    if q:
                        questions.append(q)

                progress.empty()
                status.empty()

                if not questions:
                    st.error("Failed to generate questions. Make sure Ollama is running (`ollama serve`).")
                    st.stop()

                st.session_state.quiz_data = questions
                st.session_state.quiz_started = True
                st.session_state.current_question = 0
                st.session_state.answers = {}
                st.session_state.submitted = False
                st.rerun()

            else:
                st.info("Configure options on the left and click **Generate Quiz**")

    elif st.session_state.get("submitted"):
        # === RESULTS PHASE ===
        quiz_data = st.session_state.quiz_data
        answers = st.session_state.answers
        correct_count = sum(1 for i, q in enumerate(quiz_data) if answers.get(i) == q['correct'])
        total = len(quiz_data)
        pct = (correct_count / total) * 100

        color = "#065F46" if pct >= 70 else ("#92400E" if pct >= 40 else "#991B1B")
        bg = "#ECFDF5" if pct >= 70 else ("#FFFBEB" if pct >= 40 else "#FEF2F2")

        st.markdown(f"""
        <div style="background:{bg};border-radius:12px;padding:2rem;text-align:center;margin-bottom:2rem;">
            <div style="font-size:3rem;font-weight:700;color:{color};">{correct_count} / {total}</div>
            <div style="font-size:1.1rem;font-weight:600;color:{color};">{pct:.0f}% — {'Excellent! 🎉' if pct >= 70 else 'Good effort!'}</div>
        </div>
        """, unsafe_allow_html=True)

        for i, q in enumerate(quiz_data):
            user_ans = answers.get(i)
            is_correct = user_ans == q['correct']
            icon = "✅" if is_correct else "❌"
            bg_c = "#ECFDF5" if is_correct else "#FEF2F2"
            
            st.markdown(f"""
            <div style="background:{bg_c};border-radius:10px;padding:1rem;margin-bottom:0.8rem;">
                <strong>{icon} Q{i+1}: {q['question']}</strong><br>
                Your answer: <strong>{user_ans}) {q['options'].get(user_ans, '—')}</strong>
                {' • Correct: ' + q['correct'] + ') ' + q['options'][q['correct']] if not is_correct else ''}
            </div>
            """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔄 Try Again", use_container_width=True):
                reset_quiz()
                st.rerun()
        with c2:
            if st.button("💬 Ask Chatbot", use_container_width=True):
                _nav("chatbot")
        with c3:
            if st.button("🏠 Dashboard", use_container_width=True):
                _nav("dashboard")

    else:
        # === QUIZ IN PROGRESS ===
        quiz_data = st.session_state.quiz_data
        current = st.session_state.current_question
        total = len(quiz_data)

        _, col, _ = st.columns([1, 3, 1])
        with col:
            st.progress((current + 1) / total)
            st.caption(f"Question {current + 1} of {total} • {len(st.session_state.answers)} answered")

            q = quiz_data[current]

            st.markdown(f"""
            <div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);padding:1.6rem 1.4rem;">
                <div style="font-size:0.75rem;letter-spacing:0.5px;text-transform:uppercase;color:var(--text-muted);margin-bottom:0.6rem;">
                    QUESTION {current + 1}
                </div>
                <div style="font-size:1.05rem;line-height:1.55;">{q['question']}</div>
            </div>
            """, unsafe_allow_html=True)

            # Radio options
            options_list = [f"{k}) {v}" for k, v in q['options'].items()]
            
            # Pre-select previous answer
            default_idx = None
            prev = st.session_state.answers.get(current)
            if prev:
                for idx, opt in enumerate(options_list):
                    if opt.startswith(prev + ")"):
                        default_idx = idx
                        break

            selected = st.radio(
                "Select your answer:",
                options_list,
                index=default_idx,
                key=f"radio_q_{current}_{len(st.session_state.answers)}",   # Unique key fix
                label_visibility="collapsed"
            )

            if selected:
                chosen_letter = selected.split(')')[0].strip()
                st.session_state.answers[current] = chosen_letter

            # Navigation
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("← Previous", use_container_width=True, disabled=current == 0):
                    st.session_state.current_question -= 1
                    st.rerun()
            with c2:
                if st.button("Next →", use_container_width=True, disabled=current == total - 1):
                    st.session_state.current_question += 1
                    st.rerun()
            with c3:
                if st.button("✅ Submit Quiz", use_container_width=True, type="primary"):
                    st.session_state.submitted = True
                    st.rerun()

        with st.sidebar:
            if st.button("🚫 Cancel Quiz", use_container_width=True):
                reset_quiz()
                st.rerun()