import streamlit as st
from utils.db import save_user_profile

# ----------------------------------------------------------------
# DOMAIN CATALOGUE
# Must stay in sync with SCRAPING_SOURCES in scraper_page.py so
# that subdomain names match the topics the scraper can fetch.
# Structure: { domain_name: { "icon": str, "subdomains": [str] } }
# ----------------------------------------------------------------
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

# Proficiency levels used in the prior-knowledge step slider
LEVELS = ["Beginner", "Intermediate", "Advanced", "Expert"]

# Learning style options shown as a radio group
LEARNING_STYLES = [
    "📖  Reading articles & documentation",
    "🎥  Watching video tutorials",
    "🛠️  Hands-on projects & coding",
    "🧩  Solving quizzes & challenges",
    "👥  Peer discussion & mentoring",
]

# Primary goal options shown in a selectbox
GOALS = [
    "Get a job / switch careers",
    "Upskill for my current role",
    "Build a personal project",
    "Academic research",
    "General curiosity & exploration",
]

# Pace options: key = display label, value = human-readable time estimate
PACE = {
    "Casual":    "~1–2 hrs / week",
    "Steady":    "~3–5 hrs / week",
    "Intensive": "~6–10 hrs / week",
    "Full-time": "10+ hrs / week",
}


def render():
    """
    Entry point for the onboarding flow. Routes to the correct step
    based on st.session_state.step (1–4). The form is centred in a
    narrow middle column for a focused, distraction-free experience.

    Steps:
      1 — Personal info, domain selection, learning style, goal & pace
      2 — Prior knowledge rating per subdomain
      3 — Review summary before submitting
      4 — Success / completion screen
    """

    # Default to step 1 if the user hasn't started onboarding yet
    if "step" not in st.session_state:
        st.session_state.step = 1

    # Centre content: outer columns act as blank gutters
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


# ----------------------------------------------------------------
# STEP 1 — Personal info, interests, learning style, goal & pace
# ----------------------------------------------------------------
def render_step1():
    """
    Collects the user's name, role, domain/subdomain interests,
    preferred learning style, primary goal, and weekly pace.
    Validates that name and at least one domain are filled before
    advancing to step 2. Persists all values in st.session_state.pref.
    """
    st.markdown("## 🧭 Step 1 — Tell us about yourself")
    st.markdown("Help us personalise your learning journey.")
    st.markdown("---")

    # Initialise preferences dict if this is the first visit to step 1
    if "pref" not in st.session_state:
        st.session_state.pref = {}
    pref = st.session_state.pref

    # Basic identity fields side by side
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full name",     value=pref.get("name", ""), placeholder="e.g. Siddhi Mehta")
    with col2:
        role = st.text_input("Current role",  value=pref.get("role", ""), placeholder="e.g. CS Student")

    # Domain multi-select — top-level subjects the user is interested in
    st.markdown("#### 🎯 Domains of Interest")
    selected_domains = st.multiselect(
        "Choose domains",
        options=list(DOMAINS.keys()),
        default=pref.get("domains", []),
    )

    # Dynamically render a subdomain picker for each selected domain
    selected_subdomains = pref.get("subdomains", {})
    if selected_domains:
        for domain in selected_domains:
            meta = DOMAINS[domain]
            st.markdown(f"**{meta['icon']} {domain}**")
            selected_subdomains[domain] = st.multiselect(
                "Subdomains",
                options=meta["subdomains"],
                default=selected_subdomains.get(domain, []),
                key=f"sub_{domain}",   # unique key per domain to avoid widget conflicts
            )

    # Learning style — single-select radio
    st.markdown("#### 🧠 Learning Style")
    learning_style = st.radio(
        "How do you learn best?",
        options=LEARNING_STYLES,
        index=LEARNING_STYLES.index(pref.get("learning_style", LEARNING_STYLES[0])),
    )

    # Goal and pace side by side
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
            format_func=lambda k: f"{k} · {PACE[k]}",  # show time estimate in the dropdown
        )

    st.markdown("---")

    # Next button floated to the right via a 3:1 column split
    _, col_next = st.columns([3, 1])
    with col_next:
        if st.button("Next →", use_container_width=True):
            # Validate required fields before advancing
            if not name.strip():
                st.error("Please enter your name.")
            elif not selected_domains:
                st.error("Please select at least one domain.")
            else:
                # Persist all step-1 values to session state
                st.session_state.pref = {
                    "name":           name.strip(),
                    "role":           role.strip(),
                    "domains":        selected_domains,
                    "subdomains":     selected_subdomains,
                    "learning_style": learning_style,
                    "goal":           goal,
                    "pace_key":       pace_key,
                    "pace_hours":     PACE[pace_key],  # resolved human-readable string
                }
                st.session_state.step = 2
                st.rerun()


# ----------------------------------------------------------------
# STEP 2 — Prior knowledge rating per subdomain
# ----------------------------------------------------------------
def render_step2():
    """
    For each subdomain the user selected in step 1, renders:
      - A level slider (Beginner → Expert)
      - A months-of-experience slider (0–60)
      - A free-text field for comfortable topics

    All ratings are accumulated in st.session_state.knowledge using
    composite keys of the form "Domain::Subdomain".
    """
    st.markdown("## 🧠 Step 2 — Prior Knowledge")
    st.markdown("Rate your existing knowledge in each subdomain.")
    st.markdown("---")

    pref           = st.session_state.pref
    domains        = pref.get("domains", [])
    subdomains_map = pref.get("subdomains", {})

    # Initialise knowledge dict on first visit; work on a copy to avoid
    # mutating session state until the user clicks Next
    if "knowledge" not in st.session_state:
        st.session_state.knowledge = {}
    knowledge = st.session_state.knowledge.copy()

    for domain in domains:
        meta = DOMAINS[domain]
        # Fall back to all subdomains for the domain if the user picked none
        subs = subdomains_map.get(domain, meta["subdomains"])
        st.markdown(f"### {meta['icon']} {domain}")

        for sub in subs:
            key         = f"{domain}::{sub}"   # composite key — unique per domain+subdomain
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

            # Store the rating for this subdomain under the composite key
            knowledge[key] = {
                "domain":              domain,
                "subdomain":           sub,
                "level":               level,
                "months_exp":          months,
                "comfortable_topics":  topics,
            }
            st.markdown("---")

    # Back / Next navigation buttons at the bottom
    col_back, _, col_next = st.columns([1, 2, 1])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col_next:
        if st.button("Review →", use_container_width=True):
            # Persist the completed knowledge ratings before advancing
            st.session_state.knowledge = knowledge
            st.session_state.step = 3
            st.rerun()


# ----------------------------------------------------------------
# STEP 3 — Review summary before submitting
# ----------------------------------------------------------------
def render_step3():
    """
    Displays a read-only summary of all data collected in steps 1 and 2.
    The user can go back to edit or submit their profile to the database.
    On successful save, sets onboarding_complete = True and advances to
    the success screen (step 4).
    """
    st.markdown("## ✅ Step 3 — Review Your Profile")
    st.markdown("Everything look good?")
    st.markdown("---")

    pref      = st.session_state.pref
    knowledge = st.session_state.knowledge

    # Preferences summary
    st.markdown("### 🎯 Preferences")
    st.write(f"**Name:** {pref.get('name')}")
    st.write(f"**Role:** {pref.get('role') or '—'}")
    st.write(f"**Domains:** {', '.join(pref.get('domains', []))}")
    st.write(f"**Learning Style:** {pref.get('learning_style')}")
    st.write(f"**Goal:** {pref.get('goal')}")
    st.write(f"**Pace:** {pref.get('pace_key')} · {pref.get('pace_hours')}")

    # Prior knowledge summary — only shown if the user rated any subdomains
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

            # Persist to the database; save_user_profile returns True on success
            ok = save_user_profile(user_id, st.session_state.pref, st.session_state.knowledge)
            if ok:
                st.session_state.onboarding_complete = True  # unlocks the main app
                st.session_state.step = 4
                st.rerun()
            else:
                st.error("Failed to save. Check your database connection.")


# ----------------------------------------------------------------
# STEP 4 — Success / completion screen
# ----------------------------------------------------------------
def render_step4():
    """
    Confirms that the profile was saved and shows a summary of the
    key selections. Provides a single CTA button to enter the app.
    """
    pref = st.session_state.pref
    name = pref.get("name", "there").split()[0]  # first name only

    st.markdown(f"## 🎉 You're all set, {name}!")
    st.success("Your profile has been saved successfully.")

    # Brief recap so the user can confirm what was saved
    st.write(f"**Domains:** {', '.join(pref.get('domains', []))}")
    st.write(f"**Pace:** {pref.get('pace_key')} · {pref.get('pace_hours')}")

    st.markdown("---")

    # CTA centred with outer gutters
    _, col_btn, _ = st.columns([1, 2, 1])
    with col_btn:
        if st.button("🚀 Go to Dashboard", use_container_width=True):
            st.session_state.current_page = "dashboard"
            st.rerun()