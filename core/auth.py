"""Login, sign-up and guest demo (passwords hashed with PBKDF2-SHA256)."""
import hashlib
import os
import secrets

import streamlit as st

from core import db
from core.resume import all_roles

SAMPLE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "sample_resume.txt")


def _hash(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 120_000).hex()


def create_user(username, pw, name, role="student", **profile):
    salt = secrets.token_hex(16)
    return db.x("INSERT INTO users(username,name,pw_hash,salt,role,college,branch,year,target_role) VALUES(?,?,?,?,?,?,?,?,?)",
                (username.lower(), name, _hash(pw, salt), salt, role, profile.get("college"), profile.get("branch"),
                 profile.get("year"), profile.get("target_role")))


def check(username, pw):
    u = db.one("SELECT * FROM users WHERE username=?", (username.lower().strip(),))
    return u if u and secrets.compare_digest(u["pw_hash"], _hash(pw, u["salt"])) else None


def seed():
    if not db.one("SELECT id FROM users WHERE username='admin'"):
        create_user("admin", "admin123", "Placement Cell", role="admin", target_role="Data Scientist")
    if not db.one("SELECT id FROM users WHERE username='demo'"):
        uid = create_user("demo", secrets.token_hex(8), "Aarav Sharma", college="Demo Institute of Technology",
                          branch="CSE", year="Final year", target_role="Data Scientist")
        if os.path.exists(SAMPLE):
            from core.resume import extract_skills
            txt = open(SAMPLE, encoding="utf-8").read()
            db.x("INSERT INTO resumes(user_id,filename,text,skills_json) VALUES(?,?,?,?)",
                 (uid, "sample_resume.txt", txt, db.dumps(extract_skills(txt))))


def user():
    return st.session_state.get("user")


def refresh():
    u = user()
    if u:
        st.session_state.user = db.one("SELECT * FROM users WHERE id=?", (u["id"],))


def logout():
    st.session_state.clear()
    st.rerun()


def login_page():
    left, right = st.columns([1.25, 1], gap="large")
    with left:
        st.markdown('<div class="rm-hero-login"><h1>resume.<br>match.<br>practice.<br><span style="color:var(--signal)">get hired.</span></h1></div>',
                    unsafe_allow_html=True)
        st.markdown("ResuMind reads your resume once, then scores it, matches it to jobs, plans what to learn next "
                    "and runs voice mock interviews built from your own projects.")
        if st.button("Try the demo account", type="primary"):
            st.session_state.user = db.one("SELECT * FROM users WHERE username='demo'")
            st.rerun()
    with right:
        t1, t2 = st.tabs(["log in", "create account"])
        with t1, st.form("login"):
            un = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("Log in", width="stretch"):
                u = check(un, pw)
                if u:
                    st.session_state.user = u
                    st.rerun()
                st.error("That username and password don't match. Try again or create an account.")
        with t2, st.form("signup"):
            name = st.text_input("Full name")
            un2 = st.text_input("Username", key="su_un")
            pw2 = st.text_input("Password (6+ characters)", type="password", key="su_pw")
            c1, c2 = st.columns(2)
            college = c1.text_input("College")
            branch = c2.text_input("Branch", placeholder="CSE")
            year = c1.selectbox("Year", ["Final year", "3rd year", "2nd year", "Graduate"])
            role = c2.selectbox("Target role", all_roles(), index=all_roles().index("Data Scientist") if "Data Scientist" in all_roles() else 0)
            if st.form_submit_button("Create account", type="primary", width="stretch"):
                if not (name and un2 and len(pw2) >= 6):
                    st.error("Fill name and username, and use a password of at least 6 characters.")
                elif db.one("SELECT id FROM users WHERE username=?", (un2.lower(),)):
                    st.error("That username is taken. Pick another.")
                else:
                    uid = create_user(un2, pw2, name, college=college, branch=branch, year=year, target_role=role)
                    st.session_state.user = db.one("SELECT * FROM users WHERE id=?", (uid,))
                    st.rerun()
