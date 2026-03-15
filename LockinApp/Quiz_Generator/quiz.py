import streamlit as st
import PyPDF2
import json
import re
from langchain_ollama import ChatOllama

# Page config
st.set_page_config(page_title="AI Quiz Generator", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for professional UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: #0f0f1e;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 50px;
        font-size: 16px;
        font-weight: 600;
        transition: all 0.2s;
        border: none;
    }
    
    .quiz-container {
        background: #1a1a2e;
        border-radius: 16px;
        padding: 40px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        border: 1px solid #2a2a3e;
    }
    
    .upload-container {
        background: #1a1a2e;
        border-radius: 16px;
        padding: 50px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        text-align: center;
        border: 1px solid #2a2a3e;
    }
    
    h1 {
        color: #ffffff;
        text-align: center;
        font-size: 2.5em;
        margin-bottom: 40px;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    .quiz-title {
        color: #8b5cf6;
        font-size: 1.8em;
        text-align: center;
        margin-bottom: 35px;
        font-weight: 700;
    }
    
    .question-number {
        color: #a78bfa;
        font-size: 0.95em;
        font-weight: 600;
        margin-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .question-text {
        color: #e5e7eb;
        font-size: 1.25em;
        margin-bottom: 30px;
        font-weight: 500;
        line-height: 1.6;
    }
    
    div[data-testid="stRadio"] > label {
        font-size: 1.05em;
        color: #d1d5db !important;
        font-weight: 500;
    }
    
    div[data-testid="stRadio"] > div {
        background: #2a2a3e;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        border: 2px solid #3a3a4e;
        transition: all 0.2s;
    }
    
    div[data-testid="stRadio"] > div:hover {
        border-color: #8b5cf6;
        background: #2e2e3e;
    }
    
    .summary-box {
        background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
        color: white;
        padding: 40px;
        border-radius: 16px;
        text-align: center;
        font-size: 1.3em;
        margin: 20px 0;
        box-shadow: 0 8px 24px rgba(139, 92, 246, 0.3);
    }
    
    .result-item {
        padding: 20px;
        margin: 12px 0;
        border-radius: 12px;
        font-size: 1.05em;
        background: #2a2a3e;
        border-left: 4px solid;
        color: #e5e7eb;
        line-height: 1.8;
    }
    
    .result-correct {
        border-left-color: #10b981;
        background: rgba(16, 185, 129, 0.1);
    }
    
    .result-wrong {
        border-left-color: #ef4444;
        background: rgba(239, 68, 68, 0.1);
    }
    
    .spinner-container {
        text-align: center;
        padding: 40px;
    }
    
    [data-testid="stMarkdownContainer"] p {
        color: #d1d5db;
    }
    
    .stProgress > div > div {
        background-color: #8b5cf6;
    }
    
    section[data-testid="stSidebar"] {
        background: #1a1a2e;
        border-right: 1px solid #2a2a3e;
    }
    
    section[data-testid="stSidebar"] h3 {
        color: #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = None
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False
if 'pdf_content' not in st.session_state:
    st.session_state.pdf_content = None

def get_llm():
    """Initialize Ollama LLM"""
    return ChatOllama(model="gemma3:1b", temperature=0.7)

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

def generate_quiz_questions(content, num_questions=10):
    """Generate quiz questions using Ollama"""
    try:
        llm = get_llm()
        
        prompt = f"""Based on the following content, generate {num_questions} multiple-choice quiz questions.

Content:
{content[:3000]}

Generate EXACTLY {num_questions} questions in this JSON format:
[
  {{
    "question": "Question text here?",
    "options": {{
      "A": "First option",
      "B": "Second option",
      "C": "Third option",
      "D": "Fourth option"
    }},
    "correct": "A"
  }}
]

IMPORTANT RULES:
1. Return ONLY valid JSON, no extra text
2. Generate exactly {num_questions} questions
3. Each question must have 4 options (A, B, C, D)
4. Mark the correct answer with "correct" field
5. Questions should test understanding of the content
6. Make questions clear and unambiguous

JSON:"""

        response = llm.invoke(prompt)
        response_text = response.content.strip()
        
        # Try to extract JSON from response
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            questions = json.loads(json_str)
            
            # Validate questions
            valid_questions = []
            for q in questions:
                if ('question' in q and 'options' in q and 'correct' in q and
                    len(q['options']) == 4 and q['correct'] in q['options']):
                    valid_questions.append(q)
            
            return valid_questions if len(valid_questions) > 0 else None
        
        return None
        
    except Exception as e:
        st.error(f"Error generating questions: {str(e)}")
        return None

def reset_quiz():
    """Reset quiz state"""
    st.session_state.quiz_data = None
    st.session_state.current_question = 0
    st.session_state.answers = {}
    st.session_state.submitted = False
    st.session_state.quiz_started = False
    st.session_state.pdf_content = None

def show_results():
    """Display quiz results"""
    quiz_data = st.session_state.quiz_data
    answers = st.session_state.answers
    
    correct_count = sum(1 for i, q in enumerate(quiz_data) if answers.get(i) == q['correct'])
    total = len(quiz_data)
    percentage = (correct_count / total) * 100
    
    st.markdown(f"""
    <div class="summary-box">
        <h2>🎉 Quiz Complete!</h2>
        <h1>{correct_count} / {total}</h1>
        <p>Score: {percentage:.1f}%</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("<h3 style='color: #e5e7eb;'>📊 Detailed Results</h3>", unsafe_allow_html=True)
    
    for i, question in enumerate(quiz_data):
        user_answer = answers.get(i)
        correct_answer = question['correct']
        is_correct = user_answer == correct_answer
        
        result_class = "result-correct" if is_correct else "result-wrong"
        icon = "✅" if is_correct else "❌"
        
        user_answer_text = question['options'].get(user_answer, 'Not answered') if user_answer else 'Not answered'
        
        status_icon = "✓" if is_correct else "✗"
        status_text = "CORRECT" if is_correct else "INCORRECT"
        
        st.markdown(f"""
        <div class="result-item {result_class}">
            <strong style="font-size: 1.2em; color: {'#10b981' if is_correct else '#ef4444'};">{status_icon} {status_text}</strong><br><br>
            <strong style="color: #f3f4f6;">Q{i + 1}:</strong> <span style="color: #e5e7eb;">{question['question']}</span><br><br>
            <strong style="color: #d1d5db;">Your answer:</strong> <span style="color: #9ca3af;">{user_answer}) {user_answer_text}</span><br>
            <strong style="color: #d1d5db;">Correct answer:</strong> <span style="color: #10b981;">{correct_answer}) {question['options'][correct_answer]}</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Generate Another Quiz", key="restart"):
            reset_quiz()
            st.rerun()

# Main App
st.markdown("<h1>🤖 AI Quiz Generator</h1>", unsafe_allow_html=True)

if not st.session_state.quiz_started:
    # Upload section
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="upload-container">', unsafe_allow_html=True)
        st.markdown("<h3 style='color: #e5e7eb; margin-bottom: 20px;'>📄 Upload Your PDF</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color: #9ca3af; font-size: 1.05em;'>Upload any PDF document and AI will generate quiz questions from it</p>", unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("", type=['pdf'], label_visibility="collapsed")
        
        num_questions = st.slider("Number of questions to generate:", min_value=5, max_value=20, value=10, step=1)
        
        if uploaded_file:
            if st.button("🚀 Generate Quiz", type="primary"):
                with st.spinner("📖 Reading PDF and generating questions... This may take a minute..."):
                    # Extract text from PDF
                    pdf_text = extract_text_from_pdf(uploaded_file)
                    
                    if pdf_text:
                        st.session_state.pdf_content = pdf_text
                        
                        # Generate questions
                        questions = generate_quiz_questions(pdf_text, num_questions)
                        
                        if questions and len(questions) > 0:
                            st.session_state.quiz_data = questions
                            st.session_state.quiz_started = True
                            st.success(f"✅ Generated {len(questions)} questions!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to generate questions. Please try again or use a different PDF.")
                    else:
                        st.error("❌ Could not extract text from PDF. Please try a different file.")
        
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.submitted:
    # Show results
    show_results()

else:
    # Quiz interface
    quiz_data = st.session_state.quiz_data
    current_q = st.session_state.current_question
    
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown('<div class="quiz-container">', unsafe_allow_html=True)
        
        st.markdown(f'<p class="quiz-title">AI Generated Quiz</p>', unsafe_allow_html=True)
        
        question = quiz_data[current_q]
        
        st.markdown(f'<p class="question-number">Question {current_q + 1} of {len(quiz_data)}:</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="question-text">{question["question"]}</p>', unsafe_allow_html=True)
        
        # Radio options
        options_list = [f"{key}. {value}" for key, value in question['options'].items()]
        
        # Check if question was already answered
        previous_answer = st.session_state.answers.get(current_q)
        default_index = None
        if previous_answer:
            for idx, opt in enumerate(options_list):
                if opt.startswith(previous_answer):
                    default_index = idx
                    break
        
        selected = st.radio(
            "Select your answer:",
            options_list,
            key=f"q_{current_q}",
            index=default_index,
            label_visibility="collapsed"
        )
        
        if selected:
            answer_key = selected.split('.')[0].strip()
            st.session_state.answers[current_q] = answer_key
        
        st.markdown("---")
        
        # Navigation buttons
        col_prev, col_next, col_submit = st.columns([1, 1, 1])
        
        with col_prev:
            if current_q > 0:
                if st.button("⬅️ Previous Question", use_container_width=True):
                    st.session_state.current_question -= 1
                    st.rerun()
        
        with col_next:
            if current_q < len(quiz_data) - 1:
                if st.button("Next Question ➡️", use_container_width=True, type="primary"):
                    st.session_state.current_question += 1
                    st.rerun()
        
        with col_submit:
            if st.button("✅ Submit Quiz", use_container_width=True, type="primary"):
                if len(st.session_state.answers) < len(quiz_data):
                    st.warning(f"⚠️ You've answered {len(st.session_state.answers)} out of {len(quiz_data)} questions.")
                st.session_state.submitted = True
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Progress bar
        progress = (len(st.session_state.answers) / len(quiz_data))
        st.progress(progress)
        st.markdown(f"<p style='text-align: center; color: #a78bfa; margin-top: 15px; font-weight: 600;'>Progress: {len(st.session_state.answers)} / {len(quiz_data)} answered</p>", unsafe_allow_html=True)

# Cancel button in sidebar
with st.sidebar:
    st.markdown("<h3 style='color: #e5e7eb;'>Quiz Controls</h3>", unsafe_allow_html=True)
    if st.button("🚫 Cancel Quiz", use_container_width=True):
        reset_quiz()
        st.rerun()
    
    st.markdown("---")
    st.markdown("<h3 style='color: #e5e7eb;'>ℹ️ About</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #9ca3af;'>This quiz is generated using AI (Ollama) based on your PDF content.</p>", unsafe_allow_html=True)