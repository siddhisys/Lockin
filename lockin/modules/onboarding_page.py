import streamlit as st
from utils.db import save_user_profile

# ----- Matches from scraper_page.py SCRAPING_SOURCES ---------------
DOMAINS = {
    "Artificial Intelligence": {
        "icon": "🤖",
        "subdomains": [
            "Machine Learning",
            "Natural Language Processing",
            "Computer Vision",
            "Deep Learning",
            "Reinforcement Learning",
        ],
    },
    "Data Science": {
        "icon": "📊",
        "subdomains": [
            "Statistical Analysis",
            "Data Visualisation",
            "Big Data Engineering",
            "Data Wrangling",
        ],
    },
    "Programming": {
        "icon": "💻",
        "subdomains": [
            "Python",
            "JavaScript",
            "Data Structures & Algorithms",
        ],
    },
    "Web Development": {
        "icon": "🌐",
        "subdomains": [
            "Frontend Development",
            "Backend Development",
        ],
    },
}

LEVELS = ["Beginner", "Intermediate", "Advanced", "Expert"]
LEARNING_STYLES = [
    "📖  Reading articles & documentation",
    "🎥  Watching video tutorials",
    "🛠️  Hands-on projects & coding",
    "🧩  Solving quizzes & challenges",
    "👥  Peer discussion & mentoring",
]
GOALS = [
    "Get a job / switch careers",
    "Upskill for my current role",
    "Build a personal project",
    "Academic research",
    "General curiosity & exploration",
]
PACE = {
    "Casual": "~1–2 hrs / week",
    "Steady": "~3–5 hrs / week",
    "Intensive": "~6–10 hrs / week",
    "Full-time": "10+ hrs / week",
}


def render():
    if "step" not in st.session_state:
        st.session_state.step = 1

    col1, col2, col3 = st.columns([1, 2.5, 1])
    with col2:
        step = st.session_state.step
        if step == 1:
            render_step1()
        elif step == 2:
            render_step2()
        elif step == 3:
            render_step3()
        elif step == 4:
            render_step4()


def render_step1():
    st.markdown("## 🧭 Step 1 — Tell us about yourself")
    st.markdown("Help us personalise your learning journey.")
    st.markdown("---")

    if "pref" not in st.session_state:
        st.session_state.pref = {}
    pref = st.session_state.pref

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full name", value=pref.get("name", ""), placeholder="e.g. Siddhi Mehta")
    with col2:
        role = st.text_input("Current role", value=pref.get("role", ""), placeholder="e.g. CS Student")

    st.markdown("#### 🎯 Domains of Interest")
    selected_domains = st.multiselect(
        "Choose domains",
        options=list(DOMAINS.keys()),
        default=pref.get("domains", []),
    )

    selected_subdomains = pref.get("subdomains", {})
    if selected_domains:
        for domain in selected_domains:
            meta = DOMAINS[domain]
            st.markdown(f"**{meta['icon']} {domain}**")
            selected_subdomains[domain] = st.multiselect(
                "Subdomains",
                options=meta["subdomains"],
                default=selected_subdomains.get(domain, []),
                key=f"sub_{domain}",
            )

    st.markdown("#### 🧠 Learning Style")
    learning_style = st.radio(
        "How do you learn best?",
        options=LEARNING_STYLES,
        index=LEARNING_STYLES.index(pref.get("learning_style", LEARNING_STYLES[0])),
    )

    st.markdown("#### 🚀 Goal & Pace")
    col_g, col_p = st.columns(2)
    with col_g:
        goal = st.selectbox(
            "Primary goal",
            options=GOALS,
            index=GOALS.index(pref.get("goal", GOALS[0])),
        )
    with col_p:
        pace_key = st.selectbox(
            "Weekly pace",
            options=list(PACE.keys()),
            index=list(PACE.keys()).index(pref.get("pace_key", "Steady")),
            format_func=lambda k: f"{k} · {PACE[k]}",
        )

    st.markdown("---")
    _, col_next = st.columns([3, 1])
    with col_next:
        if st.button("Next →", use_container_width=True):
            if not name.strip():
                st.error("Please enter your name.")
            elif not selected_domains:
                st.error("Please select at least one domain.")
            else:
                st.session_state.pref = {
                    "name": name.strip(),
                    "role": role.strip(),
                    "domains": selected_domains,
                    "subdomains": selected_subdomains,
                    "learning_style": learning_style,
                    "goal": goal,
                    "pace_key": pace_key,
                    "pace_hours": PACE[pace_key],
                }
                st.session_state.step = 2
                st.rerun()


def render_step2():
    st.markdown("## 🧠 Step 2 — Prior Knowledge")
    st.markdown("Rate your existing knowledge in each subdomain.")
    st.markdown("---")

    pref = st.session_state.pref
    domains = pref.get("domains", [])
    subdomains_map = pref.get("subdomains", {})

    if "knowledge" not in st.session_state:
        st.session_state.knowledge = {}
    knowledge = st.session_state.knowledge.copy()

    for domain in domains:
        meta = DOMAINS[domain]
        subs = subdomains_map.get(domain, meta["subdomains"])
        st.markdown(f"### {meta['icon']} {domain}")
        for sub in subs:
            key = f"{domain}::{sub}"
            current_val = knowledge.get(key, {})
            st.markdown(f"**{sub}**")
            col_level, col_exp = st.columns([2, 3])
            with col_level:
                level = st.select_slider(
                    "Level",
                    options=LEVELS,
                    value=current_val.get("level", "Beginner"),
                    key=f"level_{key}",
                )
            with col_exp:
                months = st.slider(
                    "Months of experience",
                    0, 60,
                    current_val.get("months_exp", 0),
                    key=f"months_{key}",
                )
            topics = st.text_input(
                "Topics you know (comma-separated)",
                value=current_val.get("comfortable_topics", ""),
                key=f"topics_{key}",
                placeholder="e.g. linear regression, pandas",
            )
            knowledge[key] = {
                "domain": domain,
                "subdomain": sub,
                "level": level,
                "months_exp": months,
                "comfortable_topics": topics,
            }
            st.markdown("---")

    col_back, _, col_next = st.columns([1, 2, 1])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col_next:
        if st.button("Review →", use_container_width=True):
            st.session_state.knowledge = knowledge
            st.session_state.step = 3
            st.rerun()


def render_step3():
    st.markdown("## ✅ Step 3 — Review Your Profile")
    st.markdown("Everything look good?")
    st.markdown("---")

    pref = st.session_state.pref
    knowledge = st.session_state.knowledge

    st.markdown("### 🎯 Preferences")
    st.write(f"**Name:** {pref.get('name')}")
    st.write(f"**Role:** {pref.get('role') or '—'}")
    st.write(f"**Domains:** {', '.join(pref.get('domains', []))}")
    st.write(f"**Learning Style:** {pref.get('learning_style')}")
    st.write(f"**Goal:** {pref.get('goal')}")
    st.write(f"**Pace:** {pref.get('pace_key')} · {pref.get('pace_hours')}")

    if knowledge:
        st.markdown("### 🧠 Prior Knowledge")
        for data in knowledge.values():
            st.write(f"• **{data['subdomain']}** — {data['level']} ({data['months_exp']} months)")

    st.markdown("---")
    col_back, _, col_submit = st.columns([1, 2, 1])
    with col_back:
        if st.button("← Edit", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with col_submit:
        if st.button("✅ Submit Profile", use_container_width=True):
            user_id = st.session_state.user["id"]
            ok = save_user_profile(user_id, st.session_state.pref, st.session_state.knowledge)
            if ok:
                st.session_state.onboarding_complete = True
                st.session_state.step = 4
                st.rerun()
            else:
                st.error("Failed to save. Check your database connection.")


def render_step4():
    pref = st.session_state.pref
    name = pref.get("name", "there").split()[0]
    st.markdown(f"## 🎉 You're all set, {name}!")
    st.success("Your profile has been saved successfully.")
    st.write(f"**Domains:** {', '.join(pref.get('domains', []))}")
    st.write(f"**Pace:** {pref.get('pace_key')} · {pref.get('pace_hours')}")
    st.markdown("---")
    _, col_btn, _ = st.columns([1, 2, 1])
    with col_btn:
        if st.button("🚀 Go to Dashboard", use_container_width=True):
            st.session_state.current_page = "dashboard"
            st.rerun()