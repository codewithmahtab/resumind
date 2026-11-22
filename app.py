"""ResuMind 2.0 — run with:  streamlit run app.py"""
import streamlit as st

st.set_page_config(page_title="ResuMind", page_icon=":material/description:", layout="wide")

from core import auth, db, llm, ui  # noqa: E402
from views import admin, analyzer, builder, copilot, dashboard, interview, learning, match  # noqa: E402

db.init()
auth.seed()
ui.inject()

u = auth.user()
if not u:
    auth.login_page()
    st.stop()

pages = {
    "": [st.Page(dashboard.render, title="Dashboard", icon=":material/space_dashboard:", url_path="dashboard", default=True)],
    "Resume": [st.Page(analyzer.render, title="Analyzer", icon=":material/fact_check:", url_path="analyzer"),
               st.Page(match.render, title="Job Match", icon=":material/join_inner:", url_path="job-match"),
               st.Page(builder.render, title="Builder", icon=":material/edit_document:", url_path="builder")],
    "Prepare": [st.Page(interview.render, title="Mock Interview", icon=":material/mic:", url_path="mock-interview"),
                st.Page(learning.render, title="Learning Path", icon=":material/route:", url_path="learning-path"),
                st.Page(copilot.render, title="Copilot", icon=":material/forum:", url_path="copilot")],
}
if u["role"] == "admin":
    pages["Admin"] = [st.Page(admin.render, title="Admin panel", icon=":material/admin_panel_settings:", url_path="admin")]

nav = st.navigation(pages)

with st.sidebar:
    st.divider()
    st.markdown(f"**{ui.e(u['name'])}**  \n<span class='rm-lbl'>{ui.e(u.get('target_role') or '')}</span>", unsafe_allow_html=True)
    if not llm.available():
        st.caption("Offline mode: add GOOGLE_API_KEY to .env for Gemini features.")
    if st.button("Log out", width="stretch"):
        auth.logout()

nav.run()
