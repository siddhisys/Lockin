import streamlit as st
import json
import re
from PyPDF2 import PdfReader
from io import BytesIO

def _nav(page):
    st.session_state["current_page"] = page
    st.rerun()

def reset_quiz():
    for k, v in [("quiz_data", None), ("current_question", 0),
                 ("answers", {}), ("submitted", False),
                 ("quiz_started", False), ("pdf_content", None),
                 ("use_manual_pdf", False)]:
        st.session_state[k] = v

def generate_single_question(llm, pdf_text, existing_questions):
    """Ask model for exactly ONE question at a time."""
    # Tell it what questions already exist so it doesn't repeat
    existing = ""
    if existing_questions:
        existing = "Already asked:\n" + "\n".join(
            f"- {q['question']}" for q in existing_questions
        )

    prompt = f"""Generate ONE multiple choice question from the content below.

{existing}

Content: {pdf_text[:600]}

Return ONLY this JSON (one object, not an array):
{{"question":"string","options":{{"A":"string","B":"string","C":"string","D":"string"}},"correct":"A"}}

JSON:"""

    for attempt in range(3):  # up to 3 retries per question
        try:
            response = llm.invoke(prompt)
            text = response.content.strip()

            # Strip markdown fences
            text = re.sub(r"```json|```", "", text).strip()

            # Find JSON object
            match = re.search(r'\{[\s\S]*\}', text)
            if not match:
                continue

            json_str = match.group(0)
            # Fix trailing commas
            json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
            # Fix single quotes
            json_str = re.sub(r"'", '"', json_str)

            q = json.loads(json_str)

            # Validate structure
            if (isinstance(q, dict)
                    and 'question' in q
                    and 'options' in q
                    and 'correct' in q
                    and isinstance(q['options'], dict)
                    and str(q['correct']) in q['options']
                    and len(q['options']) == 4):
                return q
        except Exception:
            continue

    return None  # failed after 3 attempts

def render():
    if "use_manual_pdf" not in st.session_state:
        st.session_state.use_manual_pdf = False

    # ------- Top bar ----------------------------
    top1, top2 = st.columns([6, 1])
    with top2:
        if st.button("🏠 Dashboard", key="quiz_dashboard", use_container_width=True):
            _nav("dashboard")

    st.markdown("""
    <div style="margin-bottom:1.75rem;">
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

    st.markdown("""
    <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:1.5rem;flex-wrap:wrap;">
        <div style="background:var(--surface-2);color:var(--text-muted);border-radius:20px;
            padding:.3rem .85rem;font-size:.8rem;font-weight:500;">1 Scrape</div>
        <span style="color:var(--border-hover);">→</span>
        <div style="background:var(--surface-2);color:var(--text-muted);border-radius:20px;
            padding:.3rem .85rem;font-size:.8rem;font-weight:500;">2 Summarize</div>
        <span style="color:var(--border-hover);">→</span>
        <div style="background:var(--accent);color:#fff;border-radius:20px;
            padding:.3rem .85rem;font-size:.8rem;font-weight:600;">3 Quiz</div>
        <span style="color:var(--border-hover);">→</span>
        <div style="background:var(--surface-2);color:var(--text-muted);border-radius:20px;
            padding:.3rem .85rem;font-size:.8rem;font-weight:500;">4 Chat</div>
    </div>
    """, unsafe_allow_html=True)

    # -------- Setup screen ----------------------------
    if not st.session_state.get("quiz_started"):
        has_scraped = bool(st.session_state.get("scraped_pdf_bytes"))

        col_left, col_right = st.columns([1, 2])
        with col_left:
            st.markdown("""<div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:1.25rem 1.25rem 1rem;">
            """, unsafe_allow_html=True)

            if has_scraped and not st.session_state.use_manual_pdf:
                st.markdown("""
                <div style="background:#ECFDF5;border:1px solid #A7F3D0;border-radius:10px;
                    padding:.75rem 1rem;margin-bottom:.75rem;">
                    <div style="font-size:.82rem;font-weight:600;color:#065F46;margin-bottom:.2rem;">
                        ✅ Scraped content loaded</div>
                    <div style="font-size:.75rem;color:#059669;">
                        Ready to generate quiz automatically</div>
                </div>""", unsafe_allow_html=True)
                uploaded_file = None
                use_scraped   = True
                if st.button("📤 Use a different PDF instead", use_container_width=True):
                    st.session_state.use_manual_pdf = True
                    st.rerun()
            else:
                if has_scraped:
                    if st.button("← Use scraped PDF", use_container_width=True):
                        st.session_state.use_manual_pdf = False
                        st.rerun()
                uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"],
                                                  label_visibility="collapsed")
                use_scraped = False
                if not uploaded_file and not has_scraped:
                    st.markdown("""<div style="font-size:.8rem;color:var(--text-muted);
                        margin:.5rem 0;">No scraped content yet.</div>""",
                        unsafe_allow_html=True)
                    if st.button("← Go to Web Scraper", use_container_width=True):
                        _nav("scraper")

            num_q = st.slider("Number of questions", 5, 20, 10)
            st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
            gen_btn = st.button("🚀 Generate Quiz", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("""
            <div style="margin-top:.75rem;background:#FFFBEB;border:1px solid #FDE68A;
                border-radius:var(--radius);padding:.7rem 1rem;font-size:.78rem;color:#92400E;">
                ⏱️ Generating one question at a time — guarantees exact count.
            </div>""", unsafe_allow_html=True)

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
                        st.warning("No PDF content available.")
                        return

                    if not pdf_text.strip():
                        st.error("Could not extract text from PDF.")
                        return

                    from langchain_ollama import ChatOllama
                    llm = ChatOllama(model="qwen2.5:1.5b", temperature=0, num_predict=512)

                    # -------- Generate one question at a time ----------------------------
                    progress     = st.progress(0)
                    status       = st.empty()
                    questions    = []
                    failed_count = 0

                    for i in range(num_q):
                        status.markdown(
                            f"*🧠 Generating question {i+1} of {num_q}…*")
                        progress.progress((i) / num_q)

                        q = generate_single_question(llm, pdf_text, questions)

                        if q:
                            questions.append(q)
                        else:
                            failed_count += 1
                            status.markdown(
                                f"*⚠️ Question {i+1} failed, skipping…*")

                    progress.progress(1.0)
                    status.empty()
                    progress.empty()

                    if not questions:
                        st.error("Could not generate any questions. Make sure Ollama is running.")
                        return

                    if failed_count > 0:
                        st.warning(f"⚠️ {failed_count} question(s) could not be generated. "
                                   f"Got {len(questions)} of {num_q} requested.")

                    st.session_state.quiz_data        = questions
                    st.session_state.quiz_started     = True
                    st.session_state.current_question = 0
                    st.session_state.answers          = {}
                    st.session_state.submitted        = False
                    st.rerun()

                except Exception as e:
                    if 'progress' in locals(): progress.empty()
                    if 'status'   in locals(): status.empty()
                    st.error(f"Error: {e}")
                    st.info("Make sure Ollama is running: `ollama serve`")
            else:
                st.markdown("""
                <div style="background:var(--surface);border:1px solid var(--border);
                    border-radius:var(--radius-lg);padding:2rem 1.5rem;text-align:center;
                    color:var(--text-muted);">
                    <div style="font-size:2rem;margin-bottom:.75rem;">🧩</div>
                    <div style="font-size:.9rem;font-weight:500;margin-bottom:.35rem;">
                        Ready to test yourself?</div>
                    <div style="font-size:.82rem;">
                        Configure your quiz on the left and click Generate.
                    </div>
                </div>""", unsafe_allow_html=True)

    # --------- Results screen ----------------------------
    elif st.session_state.get("submitted"):
        quiz_data = st.session_state.quiz_data
        answers   = st.session_state.answers
        correct   = sum(1 for i, q in enumerate(quiz_data) if answers.get(i) == q['correct'])
        total     = len(quiz_data)
        pct       = (correct / total) * 100
        color     = "#065F46" if pct >= 70 else ("#92400E" if pct >= 40 else "#991B1B")
        bg        = "#ECFDF5" if pct >= 70 else ("#FFFBEB" if pct >= 40 else "#FEF2F2")

        st.markdown(f"""
        <div style="background:{bg};border-radius:12px;padding:1.75rem 2rem;
            text-align:center;margin-bottom:1.5rem;">
            <div style="font-size:2.5rem;font-weight:700;color:{color};
                margin-bottom:.25rem;">{correct} / {total}</div>
            <div style="font-size:1rem;font-weight:600;color:{color};">
                {pct:.0f}% — {'Great job! 🎉' if pct >= 70 else ('Good effort! 💪' if pct >= 40 else 'Keep studying! 📚')}
            </div>
        </div>""", unsafe_allow_html=True)

        for i, q in enumerate(quiz_data):
            user_ans   = answers.get(i)
            is_correct = user_ans == q['correct']
            icon       = "✅" if is_correct else "❌"
            bg_c       = "#ECFDF5" if is_correct else "#FEF2F2"
            user_text  = q['options'].get(user_ans, "Not answered") if user_ans else "Not answered"
            correct_t  = (f' · Correct: <strong>{q["correct"]}) {q["options"][q["correct"]]}</strong>'
                          if not is_correct else '')
            st.markdown(f"""
            <div style="background:{bg_c};border-radius:10px;padding:.9rem 1.1rem;margin-bottom:.5rem;">
                <div style="font-size:.875rem;font-weight:600;margin-bottom:.3rem;">
                    {icon} Q{i+1}: {q['question']}</div>
                <div style="font-size:.82rem;color:var(--text-muted);">
                    Your answer: <strong>{user_ans}) {user_text}</strong>{correct_t}
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            if st.button("🔄 Try Again", use_container_width=True):
                reset_quiz()
                st.rerun()
        with rc2:
            if st.button("💬 Ask the Chatbot", use_container_width=True):
                _nav("chatbot")
        with rc3:
            if st.button("🏠 Dashboard", key="quiz_done_dash", use_container_width=True):
                _nav("dashboard")

    # ------ Quiz in progress ----------------------------
    else:
        quiz_data = st.session_state.quiz_data
        current_q = st.session_state.current_question
        total     = len(quiz_data)
        answered  = len(st.session_state.answers)

        _, col2, _ = st.columns([1, 3, 1])
        with col2:
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;
                font-size:.8rem;color:var(--text-muted);margin-bottom:.4rem;">
                <span>Question {current_q + 1} of {total}</span>
                <span>{answered} answered</span>
            </div>""", unsafe_allow_html=True)
            st.progress(answered / total)
            st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)

            question = quiz_data[current_q]
            st.markdown(f"""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:1.5rem;margin-bottom:1rem;">
                <div style="font-size:.72rem;font-weight:600;letter-spacing:.07em;
                    text-transform:uppercase;color:var(--text-muted);margin-bottom:.6rem;">
                    Question {current_q + 1}</div>
                <div style="font-size:1rem;font-weight:500;color:var(--text);line-height:1.5;">
                    {question['question']}</div>
            </div>""", unsafe_allow_html=True)

            options_list = [f"{k}. {v}" for k, v in question['options'].items()]
            prev_ans     = st.session_state.answers.get(current_q)
            default_idx  = None
            if prev_ans:
                for idx, opt in enumerate(options_list):
                    if opt.startswith(prev_ans):
                        default_idx = idx
                        break

            selected = st.radio("Choose your answer:", options_list,
                                key=f"q_{current_q}", index=default_idx)
            if selected:
                st.session_state.answers[current_q] = selected.split('.')[0].strip()

            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
            cp, cn, cs = st.columns(3)
            with cp:
                if current_q > 0:
                    if st.button("← Previous", use_container_width=True):
                        st.session_state.current_question -= 1
                        st.rerun()
            with cn:
                if current_q < total - 1:
                    if st.button("Next →", use_container_width=True):
                        st.session_state.current_question += 1
                        st.rerun()
            with cs:
                if st.button("✅ Submit Quiz", use_container_width=True):
                    st.session_state.submitted = True
                    st.rerun()

        with st.sidebar:
            st.markdown("---")
            if st.button("🚫 Cancel Quiz", use_container_width=True):
                reset_quiz()
                st.rerun()