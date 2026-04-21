import streamlit as st
import json
import re
from PyPDF2 import PdfReader
from io import BytesIO
from langchain_ollama import ChatOllama


def _nav(page):
    """Navigate to a different page by updating session state and rerunning."""
    st.session_state["current_page"] = page
    st.rerun()


def reset_quiz():
    """
    Clears all quiz-related session state so the user can start fresh.
    Called when the user cancels a quiz or clicks Try Again on the results screen.
    """
    st.session_state.quiz_data        = None
    st.session_state.current_question = 0
    st.session_state.answers          = {}
    st.session_state.submitted        = False
    st.session_state.quiz_started     = False
    st.session_state.use_manual_pdf   = False


def _get_chunk(pdf_text, question_index):
    """
    Returns an 800-character window of the PDF text, offset by question_index.
    Sliding the window ensures each question is generated from a different
    part of the document, producing more varied and non-repetitive questions.

    Args:
        pdf_text:       Full extracted text from the PDF.
        question_index: 0-based index of the question being generated.
    """
    chunk_size = 800
    text_len   = len(pdf_text)

    # If the whole document fits in one chunk, just return everything
    if text_len <= chunk_size:
        return pdf_text

    # Distribute starting offsets evenly across 10 positions in the document
    step  = max(1, (text_len - chunk_size) // 10)
    start = (question_index * step) % (text_len - chunk_size)
    return pdf_text[start : start + chunk_size]


def generate_one_question(llm, pdf_text, existing_questions, question_index):
    """
    Generates a single MCQ from a sliding window of the PDF text.
    Passes already-generated questions back to the model so it avoids
    repeating them. Retries up to 3 times if the response is malformed.

    Args:
        llm:                Initialised ChatOllama instance.
        pdf_text:           Full extracted PDF text.
        existing_questions: List of already-generated question dicts — used
                            to build the "do not repeat" instruction.
        question_index:     0-based index used to select the text window.

    Returns:
        A validated question dict, or None if all 3 attempts fail.
    """
    # Build a "do not repeat" block if we already have questions
    already = ""
    if existing_questions:
        already = "Do NOT repeat these questions:\n" + "\n".join(
            f"- {q['question']}" for q in existing_questions
        ) + "\n\n"

    # Each question sees a different slice of the document
    chunk = _get_chunk(pdf_text, question_index)

    prompt = f"""{already}Using the text below, write ONE multiple-choice question.
Return ONLY this JSON object, nothing else:
{{"question":"string","options":{{"A":"string","B":"string","C":"string","D":"string"}},"correct":"A"}}

Text:
{chunk}"""

    for attempt in range(3):
        try:
            response = llm.invoke(prompt)
            text     = response.content.strip()

            # Strip any markdown code fences the model may have added
            text = re.sub(r"```json|```", "", text).strip()

            # Extract the first JSON object from the response
            match = re.search(r'\{[\s\S]*\}', text)
            if not match:
                continue

            json_str = match.group(0)
            # Fix trailing commas which are valid in JS but not in Python's json module
            json_str = re.sub(r',\s*([}\]])', r'\1', json_str)

            q = json.loads(json_str)

            # Validate the structure before accepting the question
            if (isinstance(q, dict)
                    and 'question' in q
                    and 'options'  in q
                    and 'correct'  in q
                    and isinstance(q['options'], dict)
                    and len(q['options']) == 4
                    and q['correct'] in q['options']):
                return q

        except Exception:
            continue   # malformed JSON or unexpected response — try again

    return None  # all 3 attempts failed


def render():
    """
    Renders the Quiz Generator page across three states:
      1. Setup screen — PDF source selection and quiz configuration
      2. Quiz in progress — one question at a time with Previous/Next navigation
      3. Results screen — score summary and per-question breakdown

    Generation uses a per-question retry loop to guarantee the requested
    number of questions is produced (or report how many were achieved).
    """

    # Initialise the manual-upload flag if not already set
    if "use_manual_pdf" not in st.session_state:
        st.session_state.use_manual_pdf = False

    # Dashboard shortcut pinned to the top-right
    t1, t2 = st.columns([6, 1])
    with t2:
        if st.button("🏠 Dashboard", key="quiz_dash"):
            _nav("dashboard")

    # Page header
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

    # Workflow progress breadcrumb — step 3 (Quiz) is highlighted
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

    # ----------------------------------------------------------------
    # STATE 1: SETUP SCREEN
    # ----------------------------------------------------------------
    if not st.session_state.get("quiz_started"):
        has_scraped = bool(st.session_state.get("scraped_pdf_bytes"))
        col_left, col_right = st.columns([1, 2])

        with col_left:
            st.markdown("""<div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:1.25rem 1.25rem 1rem;">
            """, unsafe_allow_html=True)

            # ---- PDF source selection ----
            if has_scraped and not st.session_state.use_manual_pdf:
                # Scraped PDF available and not overridden — use it automatically
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
                # Manual upload mode — show a back button if scraped content exists
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

            num_q   = st.slider("Number of questions", 3, 10, 8)
            gen_btn = st.button("🚀 Generate Quiz", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Hint explaining the per-question generation approach
            st.markdown("""
            <div style="margin-top:.75rem;background:#FFFBEB;border:1px solid #FDE68A;
                border-radius:var(--radius);padding:.7rem 1rem;font-size:.78rem;color:#92400E;">
                ⏱️ Generates one question at a time — guarantees exact count.
            </div>""", unsafe_allow_html=True)

        with col_right:
            if gen_btn:
                pdf_text = ""
                try:
                    # Determine which PDF source to read from
                    if use_scraped and st.session_state.get("scraped_pdf_bytes"):
                        reader = PdfReader(BytesIO(st.session_state.scraped_pdf_bytes))
                    elif uploaded_file:
                        reader = PdfReader(uploaded_file)
                    else:
                        st.warning("Please provide a PDF first.")
                        st.stop()

                    for page in reader.pages:
                        pdf_text += page.extract_text() or ""

                    if not pdf_text.strip():
                        st.error("Could not extract text from the PDF.")
                        st.stop()

                except Exception as e:
                    st.error(f"Error reading PDF: {e}")
                    st.stop()

                # temperature=0.7 provides enough variety so consecutive
                # questions don't feel repetitive (was 0.2 previously)
                llm = ChatOllama(
                    model="qwen2.5:1.5b",
                    temperature=0.7,
                    num_predict=512,
                )

                progress  = st.progress(0)
                status    = st.empty()
                questions = []

                # Retry loop — keeps generating until we have exactly num_q
                # questions or we hit the hard attempt ceiling.
                # max_attempts = num_q * 5 prevents an infinite loop if the
                # model consistently fails to produce valid JSON.
                max_attempts = num_q * 5
                attempts     = 0

                while len(questions) < num_q and attempts < max_attempts:
                    i = len(questions)
                    status.markdown(f"*🧠 Generating question {i + 1} of {num_q}…*")
                    progress.progress(i / num_q)

                    q = generate_one_question(llm, pdf_text, questions, i)
                    attempts += 1

                    if q:
                        questions.append(q)
                    # If q is None the attempt failed — loop retries automatically

                # Clean up the progress UI before showing results
                progress.progress(1.0)
                status.empty()
                progress.empty()

                if not questions:
                    st.error("Could not generate any questions. "
                             "Make sure Ollama is running: `ollama serve`")
                    st.stop()

                # Warn if we couldn't reach the requested count after all attempts
                if len(questions) < num_q:
                    st.warning(f"⚠️ Could only generate {len(questions)} of "
                               f"{num_q} questions after {max_attempts} attempts.")

                # Persist quiz to session state and trigger the quiz-in-progress view
                st.session_state.quiz_data        = questions
                st.session_state.quiz_started     = True
                st.session_state.current_question = 0
                st.session_state.answers          = {}
                st.session_state.submitted        = False
                st.rerun()

            else:
                # Empty state placeholder shown before generation starts
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

    # ----------------------------------------------------------------
    # STATE 2: RESULTS SCREEN
    # ----------------------------------------------------------------
    elif st.session_state.get("submitted"):
        quiz_data = st.session_state.quiz_data
        answers   = st.session_state.answers

        # Calculate score
        correct = sum(
            1 for i, q in enumerate(quiz_data)
            if answers.get(i) == q['correct']
        )
        total = len(quiz_data)
        pct   = (correct / total) * 100

        # Choose colour scheme based on percentage band
        color = "#065F46" if pct >= 70 else ("#92400E" if pct >= 40 else "#991B1B")
        bg    = "#ECFDF5" if pct >= 70 else ("#FFFBEB" if pct >= 40 else "#FEF2F2")

        # Score banner
        st.markdown(f"""
        <div style="background:{bg};border-radius:12px;padding:1.75rem 2rem;
            text-align:center;margin-bottom:1.5rem;">
            <div style="font-size:2.5rem;font-weight:700;color:{color};
                margin-bottom:.25rem;">{correct} / {total}</div>
            <div style="font-size:1rem;font-weight:600;color:{color};">
                {pct:.0f}% — {'Great job! 🎉' if pct >= 70 else ('Good effort! 💪' if pct >= 40 else 'Keep studying! 📚')}
            </div>
        </div>""", unsafe_allow_html=True)

        # Per-question breakdown — green for correct, red for incorrect
        for i, q in enumerate(quiz_data):
            user_ans   = answers.get(i)
            is_correct = user_ans == q['correct']
            icon       = "✅" if is_correct else "❌"
            bg_c       = "#ECFDF5" if is_correct else "#FEF2F2"
            user_text  = (q['options'].get(user_ans, "Not answered")
                          if user_ans else "Not answered")
            # Only show the correct answer hint if the user got it wrong
            correct_t  = (
                f' · Correct: <strong>{q["correct"]}) '
                f'{q["options"][q["correct"]]}</strong>'
                if not is_correct else ''
            )
            st.markdown(f"""
            <div style="background:{bg_c};border-radius:10px;
                padding:.9rem 1.1rem;margin-bottom:.5rem;">
                <div style="font-size:.875rem;font-weight:600;margin-bottom:.3rem;">
                    {icon} Q{i+1}: {q['question']}</div>
                <div style="font-size:.82rem;color:var(--text-muted);">
                    Your answer: <strong>{user_ans}) {user_text}</strong>{correct_t}
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        # Action buttons: retry, chat about material, or go home
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

    # ----------------------------------------------------------------
    # STATE 3: QUIZ IN PROGRESS
    # ----------------------------------------------------------------
    else:
        quiz_data = st.session_state.quiz_data
        current_q = st.session_state.current_question
        total     = len(quiz_data)
        answered  = len(st.session_state.answers)

        # Centre the question card using outer gutters
        _, col2, _ = st.columns([1, 3, 1])
        with col2:
            # Progress indicators: "Question X of Y" and answered count
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;
                font-size:.8rem;color:var(--text-muted);margin-bottom:.4rem;">
                <span>Question {current_q + 1} of {total}</span>
                <span>{answered} answered</span>
            </div>""", unsafe_allow_html=True)
            st.progress(answered / total)
            st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)

            # Question card
            question = quiz_data[current_q]
            st.markdown(f"""
            <div style="background:var(--surface);border:1px solid var(--border);
                border-radius:var(--radius-lg);padding:1.5rem;margin-bottom:1rem;">
                <div style="font-size:.72rem;font-weight:600;letter-spacing:.07em;
                    text-transform:uppercase;color:var(--text-muted);
                    margin-bottom:.6rem;">Question {current_q + 1}</div>
                <div style="font-size:1rem;font-weight:500;color:var(--text);
                    line-height:1.5;">{question['question']}</div>
            </div>""", unsafe_allow_html=True)

            # Build option labels and restore any previously selected answer
            options_list = [f"{k}. {v}" for k, v in question['options'].items()]
            prev_ans     = st.session_state.answers.get(current_q)
            default_idx  = None
            if prev_ans:
                # Find which index in options_list corresponds to the saved answer
                for idx, opt in enumerate(options_list):
                    if opt.startswith(prev_ans):
                        default_idx = idx
                        break

            selected = st.radio("Choose your answer:", options_list,
                                key=f"q_{current_q}", index=default_idx)
            if selected:
                # Store only the letter key (e.g. "A"), not the full option string
                st.session_state.answers[current_q] = selected.split('.')[0].strip()

            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

            # Navigation: Previous / Next / Submit
            # Previous and Next are disabled at the boundary questions
            cp, cn, cs = st.columns(3)
            with cp:
                if st.button("← Previous", use_container_width=True,
                             disabled=current_q == 0, key="quiz_prev"):
                    st.session_state.current_question -= 1
                    st.rerun()
            with cn:
                if st.button("Next →", use_container_width=True,
                             disabled=current_q >= total - 1, key="quiz_next"):
                    st.session_state.current_question += 1
                    st.rerun()
            with cs:
                if st.button("✅ Submit Quiz", use_container_width=True,
                             key="quiz_submit"):
                    st.session_state.submitted = True
                    st.rerun()

        # Cancel button in the sidebar — resets everything and returns to setup
        with st.sidebar:
            st.markdown("---")
            if st.button("🚫 Cancel Quiz", use_container_width=True):
                reset_quiz()
                st.rerun()