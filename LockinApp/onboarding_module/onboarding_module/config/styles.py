STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg:        #0d0f14;
    --surface:   #161922;
    --border:    #252a35;
    --accent:    #5b8dee;
    --accent2:   #a78bfa;
    --success:   #34d399;
    --text:      #e8eaf0;
    --muted:     #6b7280;
    --tag-bg:    #1e2330;
}

html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 1.5rem 4rem !important; max-width: 780px; }

/* ── Progress bar ── */
.progress-wrap {
    display: flex; align-items: center; gap: 12px;
    margin-bottom: 2.5rem;
}
.step-dot {
    width: 32px; height: 32px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; font-weight: 600; font-family: 'JetBrains Mono', monospace;
    border: 2px solid var(--border);
    background: var(--surface); color: var(--muted);
    transition: all .3s ease;
}
.step-dot.active   { border-color: var(--accent); color: var(--accent); background: rgba(91,141,238,.12); }
.step-dot.done     { border-color: var(--success); color: var(--bg);    background: var(--success); }
.step-line {
    flex: 1; height: 2px; background: var(--border); border-radius: 99px;
}
.step-line.done { background: var(--success); }

/* ── Card ── */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2rem 2.2rem;
    margin-bottom: 1.5rem;
}
.card-title {
    font-size: 1.05rem; font-weight: 600;
    color: var(--text);
    margin-bottom: 0.25rem;
    display: flex; align-items: center; gap: 8px;
}
.card-sub {
    font-size: 0.82rem; color: var(--muted);
    margin-bottom: 1.4rem; line-height: 1.5;
}

/* ── Section header ── */
.section-header {
    font-size: 1.5rem; font-weight: 700; color: var(--text);
    margin-bottom: 0.3rem;
}
.section-sub {
    font-size: 0.88rem; color: var(--muted);
    margin-bottom: 1.8rem; line-height: 1.6;
}

/* ── Domain badge ── */
.domain-badge {
    display: inline-block;
    padding: 3px 10px; border-radius: 99px;
    font-size: 0.72rem; font-weight: 600; letter-spacing: .04em; text-transform: uppercase;
    margin-bottom: 1rem;
}
.badge-ai   { background: rgba(91,141,238,.15);  color: #5b8dee; border: 1px solid rgba(91,141,238,.3); }
.badge-ds   { background: rgba(167,139,250,.15); color: #a78bfa; border: 1px solid rgba(167,139,250,.3); }
.badge-web  { background: rgba(52,211,153,.15);  color: #34d399; border: 1px solid rgba(52,211,153,.3); }

/* ── Streamlit widget overrides ── */
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
}
div[data-baseweb="select"]   { background: var(--surface) !important; }
div[data-baseweb="select"] * { color: var(--text) !important; }

.stRadio > div { gap: 0.5rem !important; }
.stRadio label {
    background: var(--tag-bg) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 0.5rem 1rem !important;
    font-size: 0.85rem !important;
    transition: all .2s !important;
}
.stRadio label:has(input:checked) {
    border-color: var(--accent) !important;
    background: rgba(91,141,238,.12) !important;
    color: var(--accent) !important;
}

/* ── Divider ── */
.divider { height: 1px; background: var(--border); margin: 1.6rem 0; border-radius: 99px; }

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #5b8dee, #a78bfa) !important;
    border: none !important;
    border-radius: 10px !important;
    color: white !important;
    font-weight: 600 !important;
    font-family: 'Sora', sans-serif !important;
    padding: 0.55rem 2rem !important;
    font-size: 0.9rem !important;
    letter-spacing: .02em !important;
    transition: opacity .2s !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

/* ── Success box ── */
.success-wrap {
    text-align: center; padding: 3rem 2rem;
    background: var(--surface); border: 1px solid var(--border); border-radius: 16px;
}
.success-icon  { font-size: 3.5rem; margin-bottom: 1rem; }
.success-title { font-size: 1.6rem; font-weight: 700; color: var(--success); margin-bottom: .5rem; }
.success-sub   { font-size: 0.9rem; color: var(--muted); line-height: 1.6; }

/* ── Info chip ── */
.info-chip {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(91,141,238,.08); border: 1px solid rgba(91,141,238,.2);
    border-radius: 8px; padding: 8px 14px; font-size: 0.8rem; color: #5b8dee;
    margin-bottom: 1.5rem;
}

label, .stMarkdown p { color: var(--text) !important; }
.stTextInput input, .stTextArea textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'Sora', sans-serif !important;
}
</style>
"""
