import streamlit as st
from utils.db import save_user_profile

DOMAINS = {
    "Artificial Intelligence": {
        "icon": "🤖",
        "subdomains": ["Machine Learning", "Natural Language Processing", "Computer Vision"],
    },
    "Data Science": {
        "icon": "📊",
        "subdomains": ["Statistical Analysis", "Data Visualisation", "Big Data Engineering"],
    },
    "Web Development": {
        "icon": "🌐",
        "subdomains": ["Frontend Development", "Backend Development", "DevOps & Deployment"],
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
GOALS = ["Get a job / switch careers", "Upskill for my current role",
         "Build a personal project", "Academic research", "General curiosity & exploration"]
PACE = {"Casual": "~1–2 hrs / week", "Steady": "~3–5 hrs / week",
        "Intensive": "~6–10 hrs / week", "Full-time": "10+ hrs / week"}

def render():
    st.markdown("# ✏️ Edit Profile")
    st.markdown("Update your learning preferences. Changes are saved to the database.")
    st.markdown("---")

    pref = st.session_state.get("pref", {})
    knowledge = st.session_state.get("knowledge", {})

    col1, col2, col3 = st.columns([1, 2.5, 1])
    with col2:
        # ── Basic Info ────────────────────────────────────────────────────
        st.markdown("### 👤 Basic Info")
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full name", value=pref.get("name", ""))
        with c2:
            role = st.text_input("Current role", value=pref.get("role", ""))

        st.markdown("---")

        # ── Domains ───────────────────────────────────────────────────────
        st.markdown("### 🎯 Domains of Interest")
        selected_domains = st.multiselect(
            "Choose domains", options=list(DOMAINS.keys()),
            default=pref.get("domains", []))

        selected_subdomains = pref.get("subdomains", {})
        if selected_domains:
            for domain in selected_domains:
                meta = DOMAINS[domain]
                st.markdown(f"**{meta['icon']} {domain}**")
                selected_subdomains[domain] = st.multiselect(
                    f"Subdomains", options=meta["subdomains"],
                    default=selected_subdomains.get(domain, []),
                    key=f"edit_sub_{domain}")

        st.markdown("---")

        # ── Learning Style ────────────────────────────────────────────────
        st.markdown("### 🧠 Learning Style")
        current_style = pref.get("learning_style", LEARNING_STYLES[0])
        if current_style not in LEARNING_STYLES:
            current_style = LEARNING_STYLES[0]
        learning_style = st.radio("How do you learn best?", options=LEARNING_STYLES,
                                   index=LEARNING_STYLES.index(current_style))

        st.markdown("---")

        # ── Goal & Pace ───────────────────────────────────────────────────
        st.markdown("### 🚀 Goal & Pace")
        cg, cp = st.columns(2)
        with cg:
            current_goal = pref.get("goal", GOALS[0])
            if current_goal not in GOALS:
                current_goal = GOALS[0]
            goal = st.selectbox("Primary goal", options=GOALS,
                                index=GOALS.index(current_goal))
        with cp:
            current_pace = pref.get("pace_key", "Steady")
            if current_pace not in PACE:
                current_pace = "Steady"
            pace_key = st.selectbox("Weekly pace", options=list(PACE.keys()),
                                    index=list(PACE.keys()).index(current_pace),
                                    format_func=lambda k: f"{k} · {PACE[k]}")

        st.markdown("---")

        # ── Prior Knowledge ───────────────────────────────────────────────
        st.markdown("### 🧠 Prior Knowledge")
        updated_knowledge = knowledge.copy()
        for domain in selected_domains:
            meta = DOMAINS[domain]
            subs = selected_subdomains.get(domain, meta["subdomains"])
            st.markdown(f"**{meta['icon']} {domain}**")
            for sub in subs:
                key = f"{domain}::{sub}"
                current_val = updated_knowledge.get(key, {})
                st.markdown(f"*{sub}*")
                cl, ce = st.columns([2, 3])
                with cl:
                    level = st.select_slider(f"Level", options=LEVELS,
                                             value=current_val.get("level", "Beginner"),
                                             key=f"edit_level_{key}")
                with ce:
                    months = st.slider(f"Months", 0, 60,
                                       current_val.get("months_exp", 0),
                                       key=f"edit_months_{key}")
                topics = st.text_input("Topics you know",
                                       value=current_val.get("comfortable_topics", ""),
                                       key=f"edit_topics_{key}",
                                       placeholder="e.g. pandas, neural networks")
                updated_knowledge[key] = {
                    "domain": domain, "subdomain": sub,
                    "level": level, "months_exp": months,
                    "comfortable_topics": topics
                }
                st.markdown("---")

        # ── Save Button ───────────────────────────────────────────────────
        if st.button("💾 Save Changes", use_container_width=True):
            if not name.strip():
                st.error("Please enter your name.")
            elif not selected_domains:
                st.error("Please select at least one domain.")
            else:
                updated_pref = {
                    "name": name.strip(),
                    "role": role.strip(),
                    "domains": selected_domains,
                    "subdomains": selected_subdomains,
                    "learning_style": learning_style,
                    "goal": goal,
                    "pace_key": pace_key,
                    "pace_hours": PACE[pace_key],
                }
                user_id = st.session_state.user["id"]
                ok = save_user_profile(user_id, updated_pref, updated_knowledge)
                if ok:
                    st.session_state.pref = updated_pref
                    st.session_state.knowledge = updated_knowledge
                    st.success("✅ Profile updated successfully!")
                else:
                    st.error("Failed to save. Check your database connection.")