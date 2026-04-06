import streamlit as st


def render_footer():
    if st.session_state.get("show_about"):
        _render_about()
        return
    if st.session_state.get("show_contact"):
        _render_contact()
        return

    email = ""
    if st.session_state.get("user"):
        email = st.session_state["user"].get("email", "")

    about_href   = f"?lockin_email={email}&page=about"   if email else "?page=about"
    contact_href = f"?lockin_email={email}&page=contact"  if email else "?page=contact"

    st.markdown("<div style='height:3rem'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <style>
    .footer-row {{
        border-top: 1px solid #E9E7E2;
        padding-top: 1.1rem;
        padding-bottom: .75rem;
        display: flex;
        align-items: baseline;
        justify-content: space-between;
    }}
    .footer-row a {{
        color: #A8A29E;
        font-size: .8rem;
        font-family: 'DM Sans', sans-serif;
        text-decoration: underline;
        text-underline-offset: 3px;
        cursor: pointer;
    }}
    .footer-row a:hover {{ color: #18181B; }}
    .footer-sep {{ font-size: .8rem; color: #C8C5BE; margin: 0 .3rem; }}
    </style>
    <div class="footer-row">
        <span style="font-size:.8rem;color:#A8A29E;font-family:'DM Sans',sans-serif;">
            © 2026 Lockin. Your personalised AI learning companion.
        </span>
        <span>
            <a href="{about_href}">About Us</a>
            <span class="footer-sep">·</span>
            <a href="{contact_href}">Contact</a>
        </span>
    </div>
    """, unsafe_allow_html=True)


def _render_about():
    if st.button("← Back", key="about_back"):
        st.session_state["show_about"] = False
        st.rerun()

    st.markdown("""
    <div style="max-width:720px;margin:2rem auto 0;">
        <div style="margin-bottom:2rem;">
            <h1 style="margin-bottom:.25rem;">About Lockin</h1>
            <p style="color:#78716C;font-size:.9375rem;font-weight:300;margin:0;">
                Your personalised AI learning companion.
            </p>
            <div style="height:1px;background:#E9E7E2;margin-top:.9rem;"></div>
        </div>
        <p style="font-size:.9375rem;line-height:1.7;color:#18181B;">
            Lockin is an AI-powered learning platform built to help students and
            professionals take control of their education. We believe learning
            should be personalised, efficient, and actually enjoyable.
        </p>
        <p style="font-size:.9375rem;line-height:1.7;color:#18181B;">
            With Lockin, you can scrape educational content from trusted sources,
            summarise documents with AI, generate quizzes to test your knowledge,
            and chat with your study material — all in one place.
        </p>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem;margin:2rem 0;">
            <div style="background:#FFFFFF;border:1px solid #E9E7E2;border-radius:16px;
                padding:1.25rem 1.5rem;box-shadow:0 1px 3px rgba(0,0,0,.06);">
                <div style="font-size:1.5rem;margin-bottom:.5rem;">🎯</div>
                <div style="font-size:.875rem;font-weight:600;color:#18181B;margin-bottom:.3rem;">
                    Our Mission</div>
                <div style="font-size:.82rem;color:#78716C;line-height:1.5;">
                    Make quality learning accessible and personalised for everyone.
                </div>
            </div>
            <div style="background:#FFFFFF;border:1px solid #E9E7E2;border-radius:16px;
                padding:1.25rem 1.5rem;box-shadow:0 1px 3px rgba(0,0,0,.06);">
                <div style="font-size:1.5rem;margin-bottom:.5rem;">🤖</div>
                <div style="font-size:.875rem;font-weight:600;color:#18181B;margin-bottom:.3rem;">
                    AI-Powered</div>
                <div style="font-size:.82rem;color:#78716C;line-height:1.5;">
                    Built on modern AI to summarise, quiz, and converse with your content.
                </div>
            </div>
            <div style="background:#FFFFFF;border:1px solid #E9E7E2;border-radius:16px;
                padding:1.25rem 1.5rem;box-shadow:0 1px 3px rgba(0,0,0,.06);">
                <div style="font-size:1.5rem;margin-bottom:.5rem;">🔒</div>
                <div style="font-size:.875rem;font-weight:600;color:#18181B;margin-bottom:.3rem;">
                    Your Data</div>
                <div style="font-size:.82rem;color:#78716C;line-height:1.5;">
                    Your profile and preferences stored securely and privately.
                </div>
            </div>
        </div>
        <div style="background:#D1FAE5;border-radius:16px;padding:1.5rem 2rem;">
            <div style="font-size:.875rem;font-weight:600;color:#1C4532;margin-bottom:.3rem;">
                Built as a Final Year Project</div>
            <div style="font-size:.82rem;color:#276749;line-height:1.5;">
                Lockin was developed as a Final Year Project, combining web scraping,
                natural language processing, and personalised learning to create a
                cohesive study companion.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
    _simple_footer()


def _render_contact():
    if st.button("← Back", key="contact_back"):
        st.session_state["show_contact"] = False
        st.rerun()

    st.markdown("""
    <div style="max-width:600px;margin:2rem auto 0;">
        <div style="margin-bottom:2rem;">
            <h1 style="margin-bottom:.25rem;">Contact Us</h1>
            <p style="color:#78716C;font-size:.9375rem;font-weight:300;margin:0;">
                Have a question or feedback? We'd love to hear from you.
            </p>
            <div style="height:1px;background:#E9E7E2;margin-top:.9rem;"></div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:2rem;">
            <div style="background:#FFFFFF;border:1px solid #E9E7E2;border-radius:16px;
                padding:1.25rem 1.5rem;box-shadow:0 1px 3px rgba(0,0,0,.06);">
                <div style="font-size:1.25rem;margin-bottom:.5rem;">📧</div>
                <div style="font-size:.78rem;font-weight:600;color:#78716C;
                    text-transform:uppercase;letter-spacing:.06em;margin-bottom:.3rem;">Email</div>
                <div style="font-size:.875rem;color:#18181B;font-weight:500;">
                    lockin.app@gmail.com</div>
            </div>
            <div style="background:#FFFFFF;border:1px solid #E9E7E2;border-radius:16px;
                padding:1.25rem 1.5rem;box-shadow:0 1px 3px rgba(0,0,0,.06);">
                <div style="font-size:1.25rem;margin-bottom:.5rem;">🐙</div>
                <div style="font-size:.78rem;font-weight:600;color:#78716C;
                    text-transform:uppercase;letter-spacing:.06em;margin-bottom:.3rem;">GitHub</div>
                <div style="font-size:.875rem;color:#18181B;font-weight:500;">
                    github.com/siddhisys/Lockin</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="max-width:600px;margin:0 auto;">
        <div style="background:#FFFFFF;border:1px solid #E9E7E2;border-radius:16px;
            padding:1.5rem 2rem;box-shadow:0 1px 3px rgba(0,0,0,.06);">
            <div style="font-size:.875rem;font-weight:600;color:#18181B;margin-bottom:1rem;">
                Send us a message</div>
    """, unsafe_allow_html=True)

    nc1, nc2 = st.columns(2)
    with nc1:
        name = st.text_input("Your name", placeholder="e.g. Siddhi Mehta", key="contact_name")
    with nc2:
        email = st.text_input("Your email", placeholder="you@example.com", key="contact_email")
    message = st.text_area("Message", placeholder="Tell us what's on your mind…",
                           height=120, key="contact_message")
    if st.button("📨 Send Message", use_container_width=True, key="contact_send"):
        if name and email and message:
            st.success("✅ Message received! We'll get back to you soon.")
        else:
            st.warning("Please fill in all fields.")

    st.markdown("</div></div>", unsafe_allow_html=True)
    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
    _simple_footer()


def _simple_footer():
    st.markdown("""
    <div style="border-top:1px solid #E9E7E2;padding:1rem 0 .5rem;text-align:center;">
        <div style="font-size:.78rem;color:#A8A29E;font-family:'DM Sans',sans-serif;">
            © 2026 Lockin. All rights reserved.
        </div>
    </div>
    """, unsafe_allow_html=True)