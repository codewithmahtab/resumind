import datetime as dt

import pandas as pd
import streamlit as st

from core import db, ui
from views.common import me


def _steps(uid, parts):
    a = db.latest_analysis(uid)
    steps = []
    if not db.latest_resume(uid):
        steps.append(("Upload your resume in the Analyzer", "+35"))
    elif not a:
        steps.append(("Run your first resume analysis", "+35"))
    else:
        subs = db.loads(a["subs_json"], {})
        weakest = min(subs, key=subs.get) if subs else None
        if weakest and subs[weakest] < 75:
            steps.append((f"Raise your {weakest.lower()} score (now {subs[weakest]})", "+4"))
    if parts["Job match"] == 0:
        steps.append(("Paste a job description in Job Match", "+25"))
    if parts["Interviews"] == 0:
        steps.append(("Do your first mock interview", "+25"))
    elif parts["Interviews"] < 70:
        steps.append(("Practice another interview round", "+5"))
    todo = db.one("SELECT skill FROM roadmap WHERE user_id=? AND status='todo' ORDER BY week LIMIT 1", (uid,))
    if todo:
        steps.append((f"Finish this week's topic: {todo['skill']}", "+3"))
    elif parts["Roadmap"] == 0:
        steps.append(("Generate your learning roadmap", "+15"))
    return steps[:4]


def render():
    u = me()
    hour = dt.datetime.now().hour
    hello = "good morning" if hour < 12 else "good afternoon" if hour < 17 else "good evening"
    ui.plate(f"{hello}, {u['name'].split()[0]}",
             f"Target role: {u.get('target_role') or '—'}  ·  {u.get('branch') or ''} {u.get('year') or ''}".strip(), "circle")
    score, parts = db.readiness(u["id"])

    c1, c2, c3 = st.columns([1, 1.3, 1.3], gap="large")
    with c1:
        ui.bignum(score, "career readiness", "/100")
        st.caption("Resume 35% · job match 25% · interviews 25% · roadmap 15%")
    with c2:
        ui.label("where the score comes from")
        ui.bars(parts)
    with c3:
        ui.label("next steps")
        steps = _steps(u["id"], parts)
        if steps:
            for s, gain in steps:
                st.markdown(f'<div class="rm-issue warn"><b>{ui.e(s)}</b><i>up to {gain} readiness</i></div>', unsafe_allow_html=True)
        else:
            st.success("Everything is in motion. Keep practising interviews.")

    st.write("")
    iv = db.q("SELECT created_at, overall FROM interviews WHERE user_id=? ORDER BY id", (u["id"],))
    an = db.q("SELECT created_at, ats FROM analyses WHERE user_id=? ORDER BY id", (u["id"],))
    best = db.best_match(u["id"])
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Latest ATS score", f"{round(an[-1]['ats'])}" if an else "—",
              delta=f"{round(an[-1]['ats'] - an[0]['ats'])} since first" if len(an) > 1 else None)
    m2.metric("Mock interviews", len(iv), delta=f"avg {sum(i['overall'] for i in iv) / len(iv):.1f}/10" if iv else None,
              delta_color="off")
    rm = db.one("SELECT SUM(status='done') d, COUNT(*) n FROM roadmap WHERE user_id=?", (u["id"],))
    m3.metric("Roadmap topics done", f"{rm['d'] or 0}/{rm['n']}" if rm["n"] else "—")
    m4.metric("Best job match", f"{round(best['match_pct'])}%" if best else "—", delta=best["title"] if best else None,
              delta_color="off")

    if len(an) + len(iv) > 1:
        ui.label("progress over time")
        rows = [{"when": r["created_at"], "series": "ATS score", "value": r["ats"]} for r in an] + \
               [{"when": r["created_at"], "series": "Interview ×10", "value": r["overall"] * 10} for r in iv]
        df = pd.DataFrame(rows).sort_values("when")
        df["when"] = pd.to_datetime(df["when"])
        st.line_chart(df, x="when", y="value", color="series", height=240)

    with st.expander("Send feedback about ResuMind"):
        with st.form("fb", clear_on_submit=True):
            rating = st.slider("Rating", 1, 5, 4)
            comment = st.text_area("What should we improve?")
            if st.form_submit_button("Send feedback"):
                db.x("INSERT INTO feedback(user_id,rating,comment) VALUES(?,?,?)", (u["id"], rating, comment))
                st.toast("Feedback sent")
