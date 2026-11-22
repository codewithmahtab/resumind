import streamlit as st

from core import auth, db
from core.resume import all_roles


def me():
    return auth.user()


def resume_text():
    r = db.latest_resume(me()["id"])
    return (r["text"], r) if r else ("", None)


def need_resume():
    txt, r = resume_text()
    if not txt:
        st.info("Upload your resume in the Analyzer first (sidebar → Analyzer). Every other tool reuses it.")
        st.stop()
    return txt, r


def role_select(label="Target role", key=None):
    roles = all_roles()
    cur = me().get("target_role")
    return st.selectbox(label, roles, index=roles.index(cur) if cur in roles else 0, key=key)
