import re

import pandas as pd
import streamlit as st

from core import db, llm, ui
from core.resume import analyze
from views.common import me, resume_text, role_select


def _load_builder():
    """Load utils/resume_builder.py directly, skipping utils/__init__ (it imports the old Gemini SDK)."""
    import importlib.util
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "utils", "resume_builder.py")
    spec = importlib.util.spec_from_file_location("resume_builder_v1", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.ResumeBuilder


ResumeBuilder = _load_builder()


def _defaults(u):
    txt, _ = resume_text()
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", txt or "")
    phone = re.search(r"\+?\d[\d \-]{9,}\d", txt or "")
    sk = db.loads((db.latest_resume(u["id"]) or {}).get("skills_json"), []) if txt else []
    return {
        "name": u["name"], "email": email.group(0) if email else "", "phone": phone.group(0) if phone else "",
        "edu": pd.DataFrame([{"degree": "B.Tech", "field": u.get("branch") or "CSE", "school": u.get("college") or "",
                              "year": "2026", "cgpa": ""}]),
        "exp": pd.DataFrame([{"position": "", "company": "", "dates": "", "what you did": ""}]),
        "proj": pd.DataFrame([{"name": "", "tech": "", "what you built and the result": ""}]),
        "skills": ", ".join(s for s in sk if s not in {"communication", "teamwork", "leadership"}),
    }


def _plain(d):
    parts = [d["name"], f"{d['email']} | {d['phone']} | {d['location']} | {d['linkedin']}", "SUMMARY", d["summary"], "EDUCATION"]
    parts += [f"{r['degree']} in {r['field']}, {r['school']}, {r['year']} CGPA {r['cgpa']}" for r in d["edu"]]
    parts += ["PROJECTS"] + [f"{r['name']} ({r['tech']})\n- {r['what you built and the result']}" for r in d["proj"] if r["name"]]
    parts += ["EXPERIENCE"] + [f"{r['position']}, {r['company']} ({r['dates']})\n- {r['what you did']}" for r in d["exp"] if r["position"]]
    parts += ["SKILLS", d["skills"], d["soft"]]
    return "\n".join(str(p) for p in parts)


def _docx(d, template):
    split = lambda s: [x.strip() for x in str(s).split(",") if x.strip()]
    data = {
        "template": template,
        "personal_info": {"full_name": d["name"], "email": d["email"], "phone": d["phone"], "location": d["location"],
                          "linkedin": d["linkedin"], "portfolio": d["portfolio"], "title": d["title"]},
        "summary": d["summary"],
        "education": [{"school": r["school"], "degree": r["degree"], "field": r["field"], "graduation_date": r["year"],
                       "gpa": r["cgpa"], "achievements": []} for r in d["edu"] if r["school"] or r["degree"]],
        "experience": [{"position": r["position"], "company": r["company"], "start_date": r["dates"], "end_date": "",
                        "description": r["what you did"], "responsibilities": [], "achievements": []}
                       for r in d["exp"] if r["position"]],
        "projects": [{"name": r["name"], "technologies": r["tech"], "description": r["what you built and the result"],
                      "responsibilities": [], "achievements": [], "link": ""} for r in d["proj"] if r["name"]],
        "skills": {"technical": split(d["skills"]), "soft": split(d["soft"]), "languages": split(d["languages"]), "tools": []},
    }
    return ResumeBuilder().generate_resume(data)


def render():
    u = me()
    ui.plate("resume builder", "Fill the form on the left. The preview and its ATS score update as you type.", "bar")
    if "bd" not in st.session_state:
        st.session_state.bd = _defaults(u)
    df = st.session_state.bd
    left, right = st.columns([1, 1], gap="large")
    with left:
        role = role_select(key="b_role")
        d = {}
        c1, c2 = st.columns(2)
        d["name"] = c1.text_input("Full name", df["name"])
        d["title"] = c2.text_input("Headline", f"Aspiring {role}")
        d["email"] = c1.text_input("Email", df["email"])
        d["phone"] = c2.text_input("Phone", df["phone"])
        d["location"] = c1.text_input("City", "")
        d["linkedin"] = c2.text_input("LinkedIn URL", "")
        d["portfolio"] = ""
        d["summary"] = st.text_area("Summary", st.session_state.get("b_sum", ""), height=90,
                                    placeholder=f"Final-year student aiming for {role}. 2 lines on your strongest skill and best result.")
        if st.button("Write summary with AI"):
            s = llm.text(f"Write a 2-sentence resume summary for a fresher targeting {role} with skills {df['skills']}. No first person.")
            st.session_state.b_sum = s or "Offline: add GOOGLE_API_KEY to .env to use AI writing."
            st.rerun()
        ui.label("education")
        d["edu"] = st.data_editor(df["edu"], num_rows="dynamic", width="stretch", key="b_edu").to_dict("records")
        ui.label("projects · one row per project")
        d["proj"] = st.data_editor(df["proj"], num_rows="dynamic", width="stretch", key="b_proj").to_dict("records")
        ui.label("experience / internships")
        d["exp"] = st.data_editor(df["exp"], num_rows="dynamic", width="stretch", key="b_exp").to_dict("records")
        d["skills"] = st.text_area("Technical skills (comma separated)", df["skills"], height=70)
        d["soft"] = st.text_input("Soft skills", "Communication, Teamwork, Problem solving")
        d["languages"] = st.text_input("Languages", "English, Hindi")

    with right:
        text = _plain(d)
        res = analyze(text, role)
        a, b = st.columns([1, 2])
        with a:
            ui.bignum(res["ats"], "live ats", "/100")
        with b:
            ui.bars({k: v for k, v in res["subs"].items() if k in ("Keywords", "Impact", "Sections")})
        h = ui.e
        proj = "".join(f"<p><b>{h(r['name'])}</b> · {h(r['tech'])}<br>{h(r['what you built and the result'])}</p>" for r in d["proj"] if r["name"])
        exp = "".join(f"<p><b>{h(r['position'])}</b>, {h(r['company'])} · {h(r['dates'])}<br>{h(r['what you did'])}</p>" for r in d["exp"] if r["position"])
        edu = "".join(f"<p>{h(r['degree'])} in {h(r['field'])}, {h(r['school'])} · {h(r['year'])} {('· CGPA ' + h(r['cgpa'])) if r['cgpa'] else ''}</p>" for r in d["edu"])
        sec = lambda t, body: f'<div class="rm-lbl" style="color:var(--ink);border-bottom:1px solid var(--rule-strong);margin:14px 0 4px">{t}</div>{body}' if body else ""
        st.markdown(f'<div class="rm-doc" style="white-space:normal;color:var(--ink)"><div style="font-weight:800;font-size:1.5rem;letter-spacing:-0.03em">{h(d["name"])}</div>'
                    f'<div style="color:var(--ink-2)">{h(d["title"])} · {h(d["email"])} · {h(d["phone"])} {h(d["location"])}</div>'
                    f'{sec("summary", h(d["summary"]))}{sec("education", edu)}{sec("projects", proj)}{sec("experience", exp)}'
                    f'{sec("skills", h(d["skills"]) + "<br>" + h(d["soft"]))}</div>', unsafe_allow_html=True)
        t = st.radio("Template", ["Modern", "Professional", "Minimal", "Creative"], horizontal=True)
        try:
            st.download_button("Download DOCX", _docx(d, t), f"{d['name'].replace(' ', '_')}_resume.docx", type="primary",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        except Exception as ex:
            st.error(f"Couldn't build the DOCX: {ex}")
