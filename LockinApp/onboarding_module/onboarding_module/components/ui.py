import streamlit as st


def render_progress(current: int, total: int = 3):
    """Render step progress bar with labels."""
    labels = ["Preferences", "Prior Knowledge", "Review"]

    dots_html = '<div class="progress-wrap">'
    for i in range(1, total + 1):
        cls  = "done" if i < current else ("active" if i == current else "")
        icon = "✓" if i < current else str(i)
        dots_html += f'<div class="step-dot {cls}">{icon}</div>'
        if i < total:
            line_cls = "done" if i < current else ""
            dots_html += f'<div class="step-line {line_cls}"></div>'
    dots_html += "</div>"

    labels_html = '<div style="display:flex;justify-content:space-between;margin-top:-1.5rem;margin-bottom:2rem;">'
    for i, lbl in enumerate(labels):
        color  = "#5b8dee" if (i + 1) == current else ("#34d399" if (i + 1) < current else "#6b7280")
        align  = "left" if i == 0 else ("right" if i == len(labels) - 1 else "center")
        labels_html += (
            f'<span style="font-size:0.72rem;color:{color};font-weight:600;'
            f'text-align:{align};flex:1;">{lbl}</span>'
        )
    labels_html += "</div>"

    st.markdown(dots_html + labels_html, unsafe_allow_html=True)


def section_header(title: str, subtitle: str):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{subtitle}</div>', unsafe_allow_html=True)


def card_open(title: str, subtitle: str = ""):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="card-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="card-sub">{subtitle}</div>', unsafe_allow_html=True)


def card_close():
    st.markdown('</div>', unsafe_allow_html=True)


def domain_badge(label: str, color_cls: str):
    st.markdown(
        f'<div class="domain-badge badge-{color_cls}">{label}</div>',
        unsafe_allow_html=True,
    )


def info_chip(text: str):
    st.markdown(f'<div class="info-chip">💡 &nbsp;{text}</div>', unsafe_allow_html=True)


def divider():
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


def review_row(label: str, value: str):
    st.markdown(
        f'<div style="display:flex;justify-content:space-between;padding:6px 0;'
        f'border-bottom:1px solid var(--border);">'
        f'<span style="color:var(--muted);font-size:0.83rem;">{label}</span>'
        f'<span style="color:var(--text);font-size:0.83rem;font-weight:500;'
        f'text-align:right;max-width:60%;">{value}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
