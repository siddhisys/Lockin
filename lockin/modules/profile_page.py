import streamlit as st
from utils.db import save_user_profile

# ----------------------------------------------------------------
# DOMAIN CATALOGUE
# Must stay in sync with onboarding.py and scraper_page.py so that
# subdomain names are consistent across the whole app.
# ----------------------------------------------------------------
DOMAINS = {
    "Artificial Intelligence": {
        "icon": "🤖",
        "subdomains": ["Machine Learning", "Natural Language Processing", "Computer Vision", "Deep Learning", "Reinforcement Learning"],
    },
    "Data Science": {
        "icon": "📊",
        "subdomains": ["Statistical Analysis", "Data Visualisation", "Big Data Engineering", "Data Wrangling"],
    },
    "Programming": {
        "icon": "💻",
        "subdomains": ["Python", "JavaScript", "Data Structures & Algorithms"],
    },
    "Web Development": {
        "icon": "🌐",
        "subdomains": ["Frontend Development", "Backend Development"],
    },
}

# Proficiency levels used in the prior-knowledge sliders
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
GOALS = ["Get a job / switch careers", "Upskill for my current role",
         "Build a personal project", "Academic research", "General curiosity & exploration"]

# Pace options: key = display label, value = human-readable time estimate
PACE = {"Casual": "~1–2 hrs / week", "Steady": "~3–5 hrs / week",
        "Intensive": "~6–10 hrs / week", "Full-time": "10+ hrs / week"}


def render():
    """
    Renders the Edit Profile page — a single-page form that lets the user
    update any preference or knowledge rating set during onboarding.

    On save, validates required fields, then calls save_user_profile() to
    persist changes to the database and updates session state in-place so
    the rest of the app (e.g. the dashboard) reflects the new values
    immediately without a full re-login.
    """
    st.markdown("# ✏️ Edit Profile")
    st.markdown("Update your learning preferences. Changes are saved to the database.")
    st.markdown("---")

    # Read current values from session state — fall back to empty dicts
    # if the user somehow lands here without a completed profile
    pref      = st.session_state.get("pref", {})
    knowledge = st.session_state.get("knowledge", {})

    # Centre the form: outer columns act as blank gutters
    col1, col2, col3 = st.columns([1, 2.5, 1])
    with col2:

        # ----------------------------------------------------------------
        # BASIC INFO — name and current role
        # ----------------------------------------------------------------
        st.markdown("### 👤 Basic Info")
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full name",    value=pref.get("name", ""))
        with c2:
            role = st.text_input("Current role", value=pref.get("role", ""))

        st.markdown("---")

        # ----------------------------------------------------------------
        # DOMAINS — top-level subject areas the user is interested in,
        # with a dynamic subdomain picker rendered per selected domain
        # ----------------------------------------------------------------
        st.markdown("### 🎯 Domains of Interest")
        selected_domains = st.multiselect(
            "Choose domains", options=list(DOMAINS.keys()),
            default=pref.get("domains", []))

        selected_subdomains = pref.get("subdomains", {})
        if selected_domains:
            for domain in selected_domains:
                meta = DOMAINS[domain]
                st.markdown(f"**{meta['icon']} {domain}**")
                # Unique key per domain prevents Streamlit widget-key conflicts
                selected_subdomains[domain] = st.multiselect(
                    f"Subdomains", options=meta["subdomains"],
                    default=selected_subdomains.get(domain, []),
                    key=f"edit_sub_{domain}")

        st.markdown("---")

        # ----------------------------------------------------------------
        # LEARNING STYLE — single-select radio
        # Guard against a stale value that no longer exists in the list
        # ----------------------------------------------------------------
        st.markdown("### 🧠 Learning Style")
        current_style = pref.get("learning_style", LEARNING_STYLES[0])
        if current_style not in LEARNING_STYLES:
            current_style = LEARNING_STYLES[0]  # reset to default if invalid
        learning_style = st.radio("How do you learn best?", options=LEARNING_STYLES,
                                   index=LEARNING_STYLES.index(current_style))

        st.markdown("---")

        # ----------------------------------------------------------------
        # GOAL & PACE — both guarded against stale/invalid saved values
        # ----------------------------------------------------------------
        st.markdown("### 🚀 Goal & Pace")
        cg, cp = st.columns(2)
        with cg:
            current_goal = pref.get("goal", GOALS[0])
            if current_goal not in GOALS:
                current_goal = GOALS[0]  # reset if the goal was removed from the list
            goal = st.selectbox("Primary goal", options=GOALS,
                                index=GOALS.index(current_goal))
        with cp:
            current_pace = pref.get("pace_key", "Steady")
            if current_pace not in PACE:
                current_pace = "Steady"  # reset if the pace key is no longer valid
            pace_key = st.selectbox("Weekly pace", options=list(PACE.keys()),
                                    index=list(PACE.keys()).index(current_pace),
                                    format_func=lambda k: f"{k} · {PACE[k]}")  # show time estimate

        st.markdown("---")

        # ----------------------------------------------------------------
        # PRIOR KNOWLEDGE — level, experience, and topic ratings
        # per subdomain. Uses composite "Domain::Subdomain" keys to
        # match the structure written during onboarding.
        # ----------------------------------------------------------------
        st.markdown("### 🧠 Prior Knowledge")

        # Work on a copy so we only write back to session state on save
        updated_knowledge = knowledge.copy()

        for domain in selected_domains:
            meta = DOMAINS[domain]
            # Fall back to all subdomains if the user deselected them all
            subs = selected_subdomains.get(domain, meta["subdomains"])
            st.markdown(f"**{meta['icon']} {domain}**")

            for sub in subs:
                key         = f"{domain}::{sub}"   # composite key — matches onboarding format
                current_val = updated_knowledge.get(key, {})

                st.markdown(f"*{sub}*")
                cl, ce = st.columns([2, 3])
                with cl:
                    level = st.select_slider(f"Level", options=LEVELS,
                                             value=current_val.get("level", "Beginner"),
                                             key=f"edit_level_{key}")   # prefixed to avoid clashes with onboarding keys
                with ce:
                    months = st.slider(f"Months", 0, 60,
                                       current_val.get("months_exp", 0),
                                       key=f"edit_months_{key}")

                topics = st.text_input("Topics you know",
                                       value=current_val.get("comfortable_topics", ""),
                                       key=f"edit_topics_{key}",
                                       placeholder="e.g. pandas, neural networks")

                # Overwrite the entry for this subdomain with the updated values
                updated_knowledge[key] = {
                    "domain":             domain,
                    "subdomain":          sub,
                    "level":              level,
                    "months_exp":         months,
                    "comfortable_topics": topics,
                }
                st.markdown("---")

        # ----------------------------------------------------------------
        # SAVE BUTTON — validates, persists to DB, then updates session state
        # ----------------------------------------------------------------
        if st.button("💾 Save Changes", use_container_width=True):
            # Client-side validation before hitting the database
            if not name.strip():
                st.error("Please enter your name.")
            elif not selected_domains:
                st.error("Please select at least one domain.")
            else:
                updated_pref = {
                    "name":           name.strip(),
                    "role":           role.strip(),
                    "domains":        selected_domains,
                    "subdomains":     selected_subdomains,
                    "learning_style": learning_style,
                    "goal":           goal,
                    "pace_key":       pace_key,
                    "pace_hours":     PACE[pace_key],   # resolved human-readable string
                }

                user_id = st.session_state.user["id"]
                ok = save_user_profile(user_id, updated_pref, updated_knowledge)

                if ok:
                    # Update session state immediately so the dashboard and
                    # other pages reflect the new values without a re-login
                    st.session_state.pref      = updated_pref
                    st.session_state.knowledge = updated_knowledge
                    st.success("✅ Profile updated successfully!")
                else:
                    st.error("Failed to save. Check your database connection.")