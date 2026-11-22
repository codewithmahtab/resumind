import streamlit as st

from config.job_roles import JOB_ROLES
from core import db, llm, ml, ui
from core.resume import role_skills
from views.common import me, need_resume


def _sample_jd(role):
    for cat in JOB_ROLES.values():
        if role in cat:
            sk = role_skills(role)
            return (f"We are hiring a {role} (fresher). {cat[role]['description']}. "
                    f"Required: strong {', '.join(sk[:4])}. Good to have: {', '.join(sk[4:])}. "
                    "Must have good communication and teamwork.")
    return ""


def render():
    u = me()
    ui.plate("job match", "Paste any job description. See your match, skill by skill, and send the gaps to your roadmap.", "half")
    txt, _ = need_resume()

    c1, c2 = st.columns([3, 1])
    title = c1.text_input("Job title and company", placeholder="Data Analyst · Infosys · Pune")
    sample = c2.selectbox("Or load a sample JD", ["—"] + [r for cat in JOB_ROLES.values() for r in cat])
    jd = st.text_area("Job description", value=_sample_jd(sample) if sample != "—" else "", height=160,
                      placeholder="Paste the full job description here")
    if st.button("Match my resume", type="primary"):
        if len(jd.split()) < 15:
            st.error("Paste a longer job description (at least a few sentences).")
            st.stop()
        r = ml.match(txt, jd)
        t = title or (sample if sample != "—" else "Pasted job")
        db.x("INSERT INTO matches(user_id,title,match_pct,matched_json,missing_json) VALUES(?,?,?,?,?)",
             (u["id"], t, r["pct"], db.dumps(r["matched"]), db.dumps(r["missing"])))
        st.session_state.jm = {"r": r, "jd": jd, "title": t}

    m = st.session_state.get("jm")
    if m:
        r = m["r"]
        st.write("")
        a, b, c = st.columns([1, 1, 1.4], gap="large")
        with a:
            ui.bignum(r["pct"], "match", "%")
        with b:
            ui.bignum(f"{len(r['matched'])}/{len(r['jd_skills'])}", "job skills you have")
        with c:
            ui.label("how it's computed")
            st.caption(f"40% text similarity (TF-IDF cosine {r['cosine']}) + 60% coverage of the skills this job asks for.")
        ui.label("matched")
        ui.chips(r["matched"], "ok")
        ui.label("missing · red ones are marked must-have in the JD")
        st.markdown("".join(f'<span class="rm-chip {"bad" if s in r["must_missing"] else "warn"}">{ui.e(s)}</span>'
                            for s in r["missing"]) or '<span class="rm-lbl">none</span>', unsafe_allow_html=True)
        b1, b2, b3 = st.columns(3)
        if b1.button("Add gaps to roadmap", type="primary", width="stretch", disabled=not r["missing"]):
            have = {x["skill"] for x in db.q("SELECT skill FROM roadmap WHERE user_id=?", (u["id"],))}
            wk = (db.one("SELECT MAX(week) w FROM roadmap WHERE user_id=?", (u["id"],))["w"] or 0)
            for s in r["missing"]:
                if s not in have:
                    wk += 1
                    db.x("INSERT INTO roadmap(user_id,skill,week) VALUES(?,?,?)", (u["id"], s, wk))
            st.toast("Added to your Learning Path")
        if b2.button("Tailor my resume", width="stretch"):
            st.session_state.jm_out = llm.text(f"Give 5 specific, numbered edits to tailor this resume to the job. "
                                               f"Quote the line to change and the new wording.\nJOB:\n{m['jd']}\nRESUME:\n{txt[:3500]}") \
                or "Offline: add GOOGLE_API_KEY to .env. Meanwhile, add the missing skills you genuinely have to your Skills section."
        if b3.button("Write cover letter", width="stretch"):
            st.session_state.jm_out = llm.text(f"Write a 180-word cover letter for {m['title']} from this fresher, using real details "
                                               f"from the resume only.\nJOB:\n{m['jd']}\nRESUME:\n{txt[:3500]}") \
                or "Offline: add GOOGLE_API_KEY to .env to generate a cover letter."
        if st.session_state.get("jm_out"):
            with st.container(border=True):
                st.markdown(st.session_state.jm_out)

    st.divider()
    st.subheader("roles your resume fits best")
    for rec in ml.recommend_roles(txt):
        st.markdown(f'<div class="rm-row"><span><b>{ui.e(rec["role"])}</b></span><div class="rm-bar {"hi" if rec["pct"] >= 60 else ""}">'
                    f'<b style="width:{rec["pct"]}%"></b></div><span class="v">{rec["pct"]}</span></div>', unsafe_allow_html=True)
        if rec["missing"]:
            st.caption("Learn next: " + ", ".join(rec["missing"]))
