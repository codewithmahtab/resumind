import streamlit as st

from core import db, llm, ml, ui
from core.resume import analyze, extract_skills, extract_text
from views.common import me, resume_text, role_select


def _highlight(text, res):
    out = ui.e(text)
    for g in res["good"]:
        out = out.replace(ui.e(g), f'<mark class="good">{ui.e(g)}</mark>', 1)
    for i in res["issues"]:
        if i["line"]:
            out = out.replace(ui.e(i["line"]), f'<mark class="{i["kind"]}">{ui.e(i["line"])}</mark>', 1)
    return out


def _rewrite(line, role):
    out = llm.text(f"Rewrite this resume bullet for a fresher applying as {role}. Start with a strong action verb, "
                   f"keep it under 25 words, add a placeholder like [X%] where a number is missing. "
                   f"Return only the bullet.\n\nBullet: {line}", temperature=0.4)
    return out.strip() if out else None


def _report(res, preds, role):
    lines = [f"# ResuMind resume report — {role}", f"ATS score: {res['ats']}/100", "",
             "## Sub-scores"] + [f"- {k}: {v}" for k, v in res["subs"].items()] + [
             "", "## Predicted role (ML classifier)"] + [f"- {r}: {p:.0%}" for r, p in preds] + [
             "", "## Skills found", ", ".join(res["found"]) or "-", "", "## Missing skills for the role",
             ", ".join(res["missing"]) or "-", "", "## Fixes"] + [f"- {i['title']}: {i['tip']} {i['line']}" for i in res["issues"]]
    return "\n".join(lines)


def render():
    u = me()
    ui.plate("resume analyzer", "Scores your resume on five areas, predicts the job role it reads as, and marks the lines to fix.", "square")
    txt, saved = resume_text()
    c1, c2 = st.columns([2, 1])
    up = c1.file_uploader("Upload a new version (PDF, DOCX or TXT)", type=["pdf", "docx", "txt"])
    with c2:
        role = role_select()
        go = st.button("Analyze resume", type="primary", width="stretch")
    if saved:
        st.caption(f"Saved resume: {saved['filename']} · uploaded {saved['created_at'][:16]}")

    if go:
        if up:
            txt = extract_text(up)
            if len(txt.split()) < 40:
                st.error("Couldn't read enough text from that file. If it's a scanned PDF, upload a DOCX or text-based PDF.")
                st.stop()
            rid = db.x("INSERT INTO resumes(user_id,filename,text,skills_json) VALUES(?,?,?,?)",
                       (u["id"], up.name, txt, db.dumps(extract_skills(txt))))
        elif saved:
            rid = saved["id"]
        else:
            st.error("Upload a resume first.")
            st.stop()
        res = analyze(txt, role)
        preds = ml.predict_role(txt)
        db.x("INSERT INTO analyses(user_id,resume_id,ats,subs_json,role_pred) VALUES(?,?,?,?,?)",
             (u["id"], rid, res["ats"], db.dumps(res["subs"]), preds[0][0]))
        st.session_state.an = {"text": txt, "res": res, "preds": preds, "role": role}

    a = st.session_state.get("an")
    if not a:
        st.info("Pick your target role and press Analyze resume." if saved else "Upload your resume to begin.")
        return
    res, preds, role = a["res"], a["preds"], a["role"]

    left, right = st.columns([1.05, 1], gap="large")
    with left:
        ui.label("your resume · red = fix · amber = improve · green = strong")
        st.markdown(f'<div class="rm-doc">{_highlight(a["text"], res)}</div>', unsafe_allow_html=True)
    with right:
        n1, n2 = st.columns([1, 1.2])
        with n1:
            ui.bignum(res["ats"], "ats score", "/100")
        with n2:
            ui.label("predicted role · ML classifier")
            for r, p in preds:
                st.markdown(f"**{ui.e(r)}** <span class='mono'>{p:.0%}</span>", unsafe_allow_html=True)
        ui.bars(res["subs"])
        ui.label(f"{role} skills you have")
        ui.chips(res["found"], "ok")
        ui.label("missing for this role")
        ui.chips(res["missing"], "bad")

    st.write("")
    ui.label(f"fixes · {len(res['issues'])}")
    for n, i in enumerate(res["issues"]):
        cols = st.columns([3, 1])
        with cols[0]:
            st.markdown(f'<div class="rm-issue {"warn" if i["kind"] == "warn" else ""}"><b>{ui.e(i["title"])}</b>'
                        f'{ui.e(i["line"])}<i>{ui.e(i["tip"])}</i></div>', unsafe_allow_html=True)
        if i["line"] and cols[1].button("Improve with AI", key=f"rw{n}", width="stretch"):
            new = _rewrite(i["line"], role)
            st.session_state[f"rwo{n}"] = new or "Offline: add GOOGLE_API_KEY to .env to rewrite with Gemini."
        if st.session_state.get(f"rwo{n}"):
            st.success(st.session_state[f"rwo{n}"])
    st.download_button("Download report", _report(res, preds, role), "resumind_report.md", "text/markdown")
