import streamlit as st


def apply_global_styles():
    """
    Injects all global CSS into the Streamlit app via a single markdown block.
    This covers fonts, CSS variables (design tokens), layout, and every
    component style (buttons, inputs, selects, alerts, chat, file uploader, etc.).
    Should be called once at the very top of the app entry point.
    """
    st.markdown("""
    <style>
    /* ===== FONTS =====
       DM Sans  — body / UI text (weights 300, 400, 500, 600 + italic 300)
       DM Serif Display — headings (regular + italic)
    */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&family=DM+Serif+Display:ital@0;1&display=swap');


    /* ===== PASSWORD TOGGLE ICON (eye) =====
       Baseweb renders the show/hide icon as an SVG inside the input wrapper.
       Force it to use the muted text colour instead of whatever Baseweb defaults to.
    */
    [data-baseweb="input"] svg,
    [data-baseweb="input"] button svg {
        fill: var(--text-muted) !important;
        color: var(--text-muted) !important;
        opacity: 0.8 !important;
    }

    /* Darken icon on hover for better affordance */
    [data-baseweb="input"] svg:hover,
    [data-baseweb="input"] button svg:hover {
        fill: var(--text) !important;
        color: var(--text) !important;
        opacity: 1 !important;
    }


    /* ===== AUTOFILL BACKGROUND FIX =====
       Browsers override input background and text colour on autofill.
       The inset box-shadow trick replaces the browser's autofill background
       with our surface colour, and -webkit-text-fill-color fixes the text.
       The 9999s transition delay prevents the browser from ever applying
       its own background-color transition.
    */
    input:-webkit-autofill,
    input:-webkit-autofill:hover,
    input:-webkit-autofill:focus,
    textarea:-webkit-autofill,
    textarea:-webkit-autofill:hover,
    textarea:-webkit-autofill:focus {
        -webkit-text-fill-color: var(--text) !important;
        caret-color: var(--text) !important;
        -webkit-box-shadow: 0 0 0px 1000px var(--surface) inset !important;
        box-shadow: 0 0 0px 1000px var(--surface) inset !important;
        transition: background-color 9999s ease-in-out 0s !important;
    }

    /* Extra specificity for Baseweb-wrapped inputs */
    [data-baseweb="input"] input:-webkit-autofill {
        -webkit-text-fill-color: var(--text) !important;
        -webkit-box-shadow: 0 0 0px 1000px var(--surface) inset !important;
    }


    /* ===== DESIGN TOKENS (CSS variables) =====
       Centralised palette and spacing — referenced throughout all rules below.
       Changing a value here propagates everywhere.
    */
    :root {
        /* Backgrounds */
        --bg:           #F8FAFC;   /* page background */
        --surface:      #FFFFFF;   /* card / input background */
        --surface-2:    #F1F5F9;   /* subtle hover / secondary surface */

        /* Borders */
        --border:       #E2E8F0;
        --border-hover: #CBD5E1;

        /* Text */
        --text:         #0F172A;   /* primary text */
        --text-muted:   #64748B;   /* secondary / label text */
        --text-hint:    #94A3B8;   /* placeholder text */

        /* Accent (muted teal-green) */
        --accent:       #7C9A92;
        --accent-mid:   #5F7F77;   /* darker — used on hover */
        --accent-light: #E6F0ED;   /* very light tint — selected state */
        --accent-fg:    #4B6B63;   /* darkest — focus rings, borders */

        /* Semantic */
        --danger:       #EF4444;

        /* Shape */
        --radius:       10px;
        --radius-lg:    16px;

        /* Elevation */
        --shadow-sm:    0 1px 2px rgba(0,0,0,.05);
        --shadow:       0 4px 10px rgba(0,0,0,.06);
        --shadow-lg:    0 10px 25px rgba(0,0,0,.08);
    }


    /* ===== BASE / RESET =====
       Apply background, font, and text colour to every Streamlit root element.
    */
    html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"] {
        background:  var(--bg) !important;
        font-family: 'DM Sans', sans-serif !important;
        color:       var(--text) !important;
    }


    /* ===== HIDE STREAMLIT CHROME =====
       Remove the hamburger menu, footer, toolbar, decoration bar, status widget,
       sidebar, and the sidebar collapse toggle — we use a custom navbar instead.
    */
    #MainMenu, footer, header,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] { display: none !important; }

    [data-testid="stSidebar"]        { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }


    /* ===== SCROLLING =====
       Streamlit sometimes sets overflow:hidden on html/body which breaks
       normal page scrolling. Force scroll back on.
    */
    html, body {
        overflow-y: scroll !important;
        height:     auto   !important;
    }
    [data-testid="stApp"] {
        height:     auto    !important;
        min-height: 100vh   !important;
    }


    /* ===== CONTENT CONTAINER =====
       Cap page width and add consistent padding so content doesn't
       stretch uncomfortably on wide screens.
    */
    .main .block-container {
        padding:        2rem 2.5rem 4rem !important;
        max-width:      1100px !important;
        height:         auto !important;
    }


    /* ===== TYPOGRAPHY =====
       h1 uses the serif display font for contrast with the sans-serif body.
       h2, h3, p, li inherit DM Sans from the root rule above.
    */
    h1 {
        font-family: 'DM Serif Display', serif !important;
        font-size: 1.875rem !important;
        font-weight: 400 !important;
        letter-spacing: -.025em !important;
        color: var(--text) !important;
        line-height: 1.2 !important;
    }

    h2, h3, p, li {
        font-family: 'DM Sans', sans-serif !important;
        color: var(--text) !important;
    }


    /* ===== BUTTONS =====
       Primary style: accent background, white text, subtle lift on hover.
    */
    .stButton > button {
        background: var(--accent) !important;
        color: #fff !important;
        border: none !important;
        border-radius: var(--radius) !important;
        padding: .575rem 1.25rem !important;
        box-shadow: 0 2px 6px rgba(75,107,99,.25) !important;
        transition: all .15s !important;
    }
    .stButton > button:hover {
        background: var(--accent-mid) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 10px rgba(75,107,99,.35) !important;
    }

    /* Download button: outlined variant — white background, accent border */
    [data-testid="stDownloadButton"] > button {
        background: var(--surface) !important;
        color: var(--accent) !important;
        border: 1.5px solid var(--accent) !important;
    }


    /* ===== INPUTS & TEXTAREAS =====
       Style the Baseweb wrapper div (border, background, radius) and
       the inner <input>/<textarea> element (font, colour, caret).
    */
    [data-baseweb="input"] > div,
    [data-baseweb="textarea"] > div {
        background: var(--surface) !important;
        border: 1.5px solid var(--border) !important;
        border-radius: var(--radius) !important;
    }

    /* Focus ring: accent border + soft glow */
    [data-baseweb="input"]:focus-within > div,
    [data-baseweb="textarea"]:focus-within > div {
        border-color: var(--accent-fg) !important;
        box-shadow: 0 0 0 3px rgba(75,107,99,.1) !important;
    }

    /* Inner text — explicit colour needed to override Baseweb's defaults */
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea {
        font-family: 'DM Sans', sans-serif !important;
        font-size: .9rem !important;
        color: var(--text) !important;
        background: var(--surface) !important;
        caret-color: var(--accent-fg) !important;
        /* -webkit-text-fill-color overrides colour in WebKit when autofill is active */
        -webkit-text-fill-color: var(--text) !important;
    }

    /* Placeholder text — slightly dimmer than muted text */
    input::placeholder,
    textarea::placeholder {
        color: var(--text-hint) !important;
        opacity: 1 !important;   /* Firefox reduces opacity by default */
    }


    /* ===== SELECT DROPDOWNS =====
       Style both the trigger div and the floating menu/listbox.
    */
    [data-baseweb="select"] > div {
        background: #fff !important;
        border: 1.5px solid var(--border) !important;
        border-radius: var(--radius) !important;
    }

    /* Hover on menu items */
    [data-baseweb="menu"] li:hover {
        background: var(--surface-2) !important;
    }


    /* ===== ALERT BANNERS =====
       Override Streamlit's default alert colours to match our palette.
    */
    .stSuccess { background: #ECFDF5 !important; color: #065F46 !important; }
    .stInfo    { background: #EFF6FF !important; color: #1E40AF !important; }
    .stWarning { background: #FFFBEB !important; color: #92400E !important; }
    .stError   { background: #FEF2F2 !important; color: #991B1B !important; }


    /* ===== CHAT MESSAGES =====
       Give each message bubble a card-like appearance with a border and shadow.
    */
    [data-testid="stChatMessage"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        padding: 1rem 1.25rem !important;
        box-shadow: var(--shadow-sm) !important;
    }


    /* ===== METRIC CARDS =====
       Style st.metric() tiles to match the card aesthetic.
    */
    [data-testid="stMetric"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        padding: 1.25rem 1.5rem !important;
        box-shadow: var(--shadow-sm) !important;
    }


    /* ===== SCROLLBAR =====
       Thin, rounded scrollbar that blends with the light theme.
    */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-thumb {
        background: var(--border-hover);
        border-radius: 99px;
    }


    /* ===== FILE UPLOADER =====
       The uploader has several sub-elements that each need styling:
       the drop-zone container, the "Browse files" button, helper text, and
       the file name shown after a file is selected.
    */

    /* Root element text colour */
    [data-testid="stFileUploader"] {
        color: var(--text) !important;
    }

    /* Drop-zone container — dashed border signals drag-and-drop affordance */
    [data-testid="stFileUploader"] > div {
        background: var(--surface) !important;
        border: 2px dashed var(--border) !important;
        border-radius: var(--radius-lg) !important;
        padding: 1rem !important;
    }

    /* "Browse files" button — outlined, not filled */
    [data-testid="stFileUploader"] button {
        background: var(--surface) !important;
        color: var(--text) !important;
        border: 1.5px solid var(--border) !important;
        border-radius: var(--radius) !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: .85rem !important;
        font-weight: 500 !important;
        padding: .45rem 1rem !important;
        cursor: pointer !important;
    }

    [data-testid="stFileUploader"] button:hover {
        background: var(--surface-2) !important;
        border-color: var(--border-hover) !important;
    }

    /* "Drag and drop files here" helper text */
    [data-testid="stFileUploader"] small,
    [data-testid="stFileUploader"] span {
        color: var(--text-muted) !important;
    }

    /* File name displayed after a file is chosen */
    [data-testid="stFileUploader"] section {
        color: var(--text) !important;
    }


    /* ===== SELECT DROPDOWN — FLOATING MENU =====
       Styles the popover/listbox that appears when a select is opened.
       Separated from the trigger styles above for clarity.
    */

    /* Popover container and listbox */
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    ul[role="listbox"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        box-shadow: var(--shadow-lg) !important;
    }

    /* Individual option rows */
    [data-baseweb="option"],
    li[role="option"],
    ul[role="listbox"] li {
        background: var(--surface) !important;
        color: var(--text) !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: .9rem !important;
    }

    /* Hover state */
    [data-baseweb="option"]:hover,
    li[role="option"]:hover {
        background: var(--surface-2) !important;
        color: var(--text) !important;
    }

    /* Selected option — light accent tint */
    [aria-selected="true"] {
        background: var(--accent-light) !important;
        color: var(--text) !important;
    }

    /* Ensure all text inside the select trigger uses the correct colour */
    [data-baseweb="select"] * {
        color: var(--text) !important;
    }

    </style>
    """, unsafe_allow_html=True)


def page_header(icon: str, title: str, subtitle: str = ""):
    """
    Renders a consistent page header with an icon, title (h1), optional
    subtitle, and a horizontal rule. Used at the top of every page to
    maintain a uniform look across the app.

    Args:
        icon:     Emoji or character shown to the left of the title.
        title:    Page title rendered in DM Serif Display (h1).
        subtitle: Optional muted description shown below the title.
    """
    # Only render the subtitle paragraph if one was provided
    sub = (f'<p style="color:var(--text-muted);margin:.2rem 0 0;'
           f'font-size:.9375rem;font-weight:300;">{subtitle}</p>' if subtitle else "")

    st.markdown(f"""
    <div style="margin-bottom:1.75rem;">
        <div style="display:flex;align-items:center;gap:.55rem;">
            <span style="font-size:1.5rem;">{icon}</span>
            <h1 style="margin:0!important;">{title}</h1>
        </div>
        {sub}
        <div style="height:1px;background:var(--border);margin-top:.9rem;"></div>
    </div>
    """, unsafe_allow_html=True)


def card(content_html: str, padding: str = "1.25rem 1.5rem", accent_top: bool = False):
    """
    Renders a styled surface card wrapping arbitrary HTML content.
    Useful for grouping related UI sections with a consistent border,
    background, and shadow.

    Args:
        content_html: Raw HTML string to render inside the card.
        padding:      CSS padding shorthand (default: '1.25rem 1.5rem').
        accent_top:   If True, adds a 3px accent-coloured top border
                      to visually emphasise the card.
    """
    # Conditionally add the accent top border rule
    bt = "border-top:3px solid var(--accent-fg);" if accent_top else ""

    st.markdown(f"""
    <div style="background:var(--surface);border:1px solid var(--border);
        border-radius:var(--radius-lg);padding:{padding};
        box-shadow:var(--shadow-sm);margin-bottom:1rem;{bt}">
        {content_html}
    </div>""", unsafe_allow_html=True)