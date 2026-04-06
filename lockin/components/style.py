import streamlit as st

def apply_global_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&family=DM+Serif+Display:ital@0;1&display=swap');

    :root {
        --bg:           #FAFAF8;
        --surface:      #FFFFFF;
        --surface-2:    #F4F3F0;
        --border:       #E9E7E2;
        --border-hover: #C8C5BE;
        --text:         #18181B;
        --text-muted:   #78716C;
        --text-hint:    #A8A29E;
        --accent:       #1C4532;
        --accent-mid:   #276749;
        --accent-light: #D1FAE5;
        --accent-fg:    #059669;
        --danger:       #DC2626;
        --radius:       10px;
        --radius-lg:    16px;
        --shadow-sm:    0 1px 3px rgba(0,0,0,.06);
        --shadow:       0 2px 8px rgba(0,0,0,.07),0 1px 2px rgba(0,0,0,.04);
        --shadow-lg:    0 8px 24px rgba(0,0,0,.09);
    }

    html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"] {
        background:  var(--bg) !important;
        font-family: 'DM Sans', sans-serif !important;
        color:       var(--text) !important;
    }

    /* Hide Streamlit chrome */
    #MainMenu, footer, header,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] { display: none !important; }

    /* Hide sidebar */
    [data-testid="stSidebar"]        { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
                

    /* --------- SCROLL UNLOCK ---------------------------- */
    /* Only unlock scroll on html/body — do NOT set height:auto on stMain     */
    /* or stAppViewContainer as it collapses iframe children to height:0      */
    html, body {
        overflow-y: scroll !important;
        height:     auto   !important;
    }
    [data-testid="stApp"] {
        height:     auto    !important;
        min-height: 100vh   !important;
    }
    .main .block-container {
        padding:        2rem 2.5rem 4rem !important;
        max-width:      1100px           !important;
        height:         auto             !important;
    }
    /* ------------------------------------------------------------ */

    /* -------- TYPOGRAPHY ---------------------------- */
    h1 {
        font-family:    'DM Serif Display', serif !important;
        font-size:      1.875rem !important;
        font-weight:    400      !important;
        letter-spacing: -.025em  !important;
        color:          var(--text) !important;
        line-height:    1.2      !important;
        margin-bottom:  .125rem  !important;
    }
    h2 { font-family: 'DM Sans', sans-serif !important; font-size: 1.125rem  !important; font-weight: 600 !important; color: var(--text) !important; }
    h3 { font-family: 'DM Sans', sans-serif !important; font-size: .9375rem  !important; font-weight: 600 !important; color: var(--text) !important; }
    p, li { font-family: 'DM Sans', sans-serif !important; font-size: .9375rem !important; line-height: 1.65 !important; color: var(--text) !important; }

    /* ------------- BUTTONS ---------------------------- */
    .stButton > button {
        background:    var(--accent) !important;
        color:         #fff !important;
        border:        none !important;
        border-radius: var(--radius) !important;
        font-family:   'DM Sans', sans-serif !important;
        font-size:     .875rem !important;
        font-weight:   500 !important;
        padding:       .575rem 1.25rem !important;
        transition:    background .15s, transform .1s, box-shadow .15s !important;
        box-shadow:    0 1px 3px rgba(28,69,50,.2) !important;
    }
    .stButton > button:hover {
        background:  var(--accent-mid) !important;
        transform:   translateY(-1px)  !important;
        box-shadow:  0 3px 8px rgba(28,69,50,.25) !important;
    }
    .stButton > button:active { transform: none !important; }
    [data-testid="stDownloadButton"] > button {
        background: var(--surface) !important;
        color:      var(--accent)  !important;
        border:     1.5px solid var(--accent) !important;
        box-shadow: none !important;
    }
    [data-testid="stDownloadButton"] > button:hover {
        background: var(--accent-light) !important;
        transform:  translateY(-1px) !important;
    }

    /* ---------- INPUTS ---------------------------- */
    [data-baseweb="input"] > div, [data-baseweb="textarea"] > div {
        background:    var(--surface) !important;
        border:        1.5px solid var(--border) !important;
        border-radius: var(--radius) !important;
    }
    [data-baseweb="input"]:focus-within > div,
    [data-baseweb="textarea"]:focus-within > div {
        border-color: var(--accent-fg) !important;
        box-shadow:   0 0 0 3px rgba(5,150,105,.1) !important;
    }
    [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
        font-family: 'DM Sans', sans-serif !important;
        font-size:   .9rem !important;
        color:       var(--text) !important;
        background:  transparent !important;
    }
    label[data-testid="stWidgetLabel"] > div > p,
    .stTextInput label, .stTextArea label,
    .stSelectbox label, .stMultiSelect label,
    .stRadio label, .stSlider label, .stFileUploader label {
        font-size:      .78rem !important;
        font-weight:    600 !important;
        letter-spacing: .06em !important;
        text-transform: uppercase !important;
        color:          var(--text-muted) !important;
    }

    /* ----------- SELECTBOX ---------------------------- */
    [data-baseweb="select"] > div,
    [data-baseweb="select"] > div > div {
        background:    #fff !important;
        border:        1.5px solid var(--border) !important;
        border-radius: var(--radius) !important;
        color:         var(--text) !important;
        font-family:   'DM Sans', sans-serif !important;
    }
    [data-baseweb="select"] * { color: var(--text) !important; font-family: 'DM Sans', sans-serif !important; }
    [data-baseweb="popover"], [data-baseweb="popover"] > div,
    ul[data-baseweb="menu"], [role="listbox"], [data-baseweb="menu"] {
        background:    #fff !important;
        border:        1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        box-shadow:    var(--shadow-lg) !important;
        color:         var(--text) !important;
    }
    [data-baseweb="menu"] li, [data-baseweb="option"], [role="option"] {
        background:  #fff !important;
        color:       var(--text) !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size:   .875rem !important;
    }
    [data-baseweb="menu"] li:hover, [data-baseweb="option"]:hover,
    [role="option"]:hover, [aria-selected="true"] {
        background: var(--surface-2) !important;
    }
    [data-baseweb="multi-select"] > div, [data-baseweb="multi-select"] > div > div {
        background:    #fff !important;
        border:        1.5px solid var(--border) !important;
        border-radius: var(--radius) !important;
    }
    [data-baseweb="tag"] { background: var(--accent-light) !important; border-radius: 6px !important; border: none !important; }
    [data-baseweb="tag"] span   { color: var(--accent)    !important; font-weight: 600 !important; font-size: .8rem !important; }
    [data-baseweb="tag"] button { color: var(--accent-fg) !important; }

    /* ----------- SLIDER ---------------------------- */
    [data-testid="stSlider"] [role="slider"] {
        background:   var(--accent) !important;
        border-color: var(--accent) !important;
    }

    /* ---------- RADIO ---------------------------- */
    [data-testid="stRadio"] label {
        text-transform: none  !important;
        letter-spacing: 0     !important;
        font-size:      .9rem !important;
        font-weight:    400   !important;
    }

    /* ----------- FILE UPLOADER ---------------------------- */
    [data-testid="stFileUploader"] > div {
        background:    var(--surface) !important;
        border:        2px dashed var(--border) !important;
        border-radius: var(--radius-lg) !important;
        transition:    border-color .15s !important;
    }
    [data-testid="stFileUploader"] > div:hover { border-color: var(--accent-fg) !important; }

    /* -------- ALERTS ---------------------------- */
    [data-testid="stAlert"] {
        border-radius: var(--radius) !important;
        border:        none !important;
        font-family:   'DM Sans', sans-serif !important;
        font-size:     .875rem !important;
    }
    .stSuccess { background: #ECFDF5 !important; color: #065F46 !important; }
    .stInfo    { background: #EFF6FF !important; color: #1E40AF !important; }
    .stWarning { background: #FFFBEB !important; color: #92400E !important; }
    .stError   { background: #FEF2F2 !important; color: #991B1B !important; }

    /* ----------- EXPANDER ---------------------------- */
    .streamlit-expanderHeader {
        background:    var(--surface) !important;
        border:        1.5px solid var(--border) !important;
        border-radius: var(--radius) !important;
        font-weight:   600 !important;
        font-size:     .9rem !important;
        color:         var(--text) !important;
    }
    .streamlit-expanderContent {
        background:    var(--surface) !important;
        border:        1.5px solid var(--border) !important;
        border-top:    none !important;
        border-radius: 0 0 var(--radius) var(--radius) !important;
    }

    /* --------- CHAT ---------------------------- */
    [data-testid="stChatMessage"] {
        background:    var(--surface) !important;
        border:        1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        padding:       1rem 1.25rem !important;
        margin-bottom: .625rem !important;
        box-shadow:    var(--shadow-sm) !important;
    }
    [data-testid="stChatInput"] > div {
        background:    var(--surface) !important;
        border:        1.5px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        box-shadow:    var(--shadow) !important;
    }
    [data-testid="stChatInput"] > div:focus-within {
        border-color: var(--accent-fg) !important;
        box-shadow:   0 0 0 3px rgba(5,150,105,.1) !important;
    }
    [data-testid="stChatInput"] textarea {
        background:  transparent !important;
        font-family: 'DM Sans', sans-serif !important;
        color:       var(--text) !important;
    }

    /* -------- METRICS ---------------------------- */
    [data-testid="stMetric"] {
        background:    var(--surface) !important;
        border:        1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        padding:       1.25rem 1.5rem !important;
        box-shadow:    var(--shadow-sm) !important;
    }
    [data-testid="stMetricValue"] { font-family: 'DM Serif Display', serif !important; color: var(--text) !important; }
    [data-testid="stMetricLabel"] {
        font-size:      .78rem !important;
        color:          var(--text-muted) !important;
        font-weight:    600 !important;
        letter-spacing: .05em !important;
        text-transform: uppercase !important;
    }

    /* ---------- MISC ---------------------------- */
    hr { border: none !important; border-top: 1px solid var(--border) !important; margin: 1.25rem 0 !important; }
    .stSpinner > div { border-top-color: var(--accent-fg) !important; }
    [data-testid="column"] { padding: 0 .4rem !important; }
    ::-webkit-scrollbar       { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border-hover); border-radius: 99px; }

    </style>
    """, unsafe_allow_html=True)


def page_header(icon: str, title: str, subtitle: str = ""):
    sub = (f'<p style="color:var(--text-muted);margin:.2rem 0 0;'
           f'font-size:.9375rem;font-weight:300;">{subtitle}</p>' if subtitle else "")
    st.markdown(f"""
    <div style="margin-bottom:1.75rem;">
        <div style="display:flex;align-items:center;gap:.55rem;margin-bottom:.1rem;">
            <span style="font-size:1.5rem;line-height:1;">{icon}</span>
            <h1 style="margin:0!important;">{title}</h1>
        </div>
        {sub}
        <div style="height:1px;background:var(--border);margin-top:.9rem;"></div>
    </div>
    """, unsafe_allow_html=True)


def card(content_html: str, padding: str = "1.25rem 1.5rem", accent_top: bool = False):
    bt = "border-top:3px solid var(--accent-fg);" if accent_top else ""
    st.markdown(f"""
    <div style="background:var(--surface);border:1px solid var(--border);
        border-radius:var(--radius-lg);padding:{padding};
        box-shadow:var(--shadow-sm);margin-bottom:1rem;{bt}">
        {content_html}
    </div>""", unsafe_allow_html=True)