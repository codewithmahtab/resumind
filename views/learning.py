import urllib.parse

import streamlit as st

from config.courses import get_courses_for_role
from core import db, llm, ui
from views.common import me, need_resume, role_select


def _quiz(skill, key):
    if key not in st.session_state:
        out = llm.json_out(f'Write 3 multiple-choice questions to check a fresher knows "{skill}". '
                           'Return JSON {"qs":[{"q":"","options":["a","b","c","d"],"answer":0}]}')
        st.session_state[key] = (out or {}).get("qs") if isinstance(out, dict) else None
    qs = st.session_state[key]
    if not qs:
        st.caption("Quizzes need a GOOGLE_API_KEY. Mark the topic done when you're confident.")
        return False
    right = 0
    for n, q in enumerate(qs):
        pick = st.radio(q["q"], q["options"], index=None, key=f"{key}{n}")
        right += pick is not None and q["options"].index(pick) == int(q["answer"])
    return right == len(qs)


def render():
    u = me()
    ui.plate("learning path", "Your skill gaps, turned into a week-by-week plan. Finishing topics raises your readiness score.", "bar")
    need_resume()
    a = db.latest_analysis(u["id"])
    rows = db.q("SELECT * FROM roadmap WHERE user_id=? ORDER BY week", (u["id"],))
    c1, c2 = st.columns([2, 1])
    with c1:
        role = role_select("Roadmap for", key="lp_role")
    if c2.button("Build roadmap from my gaps", type="primary", width="stretch"):
        from core.resume import analyze
        txt = db.latest_resume(u["id"])["text"]
        gaps = analyze(txt, role)["missing"]
        m = db.best_match(u["id"])
        gaps += [s for s in db.loads(m["missing_json"], []) if s not in gaps] if m else []
        db.x("DELETE FROM roadmap WHERE user_id=? AND status='todo'", (u["id"],))
        done = {r["skill"] for r in db.q("SELECT skill FROM roadmap WHERE user_id=?", (u["id"],))}
        wk = db.one("SELECT MAX(week) w FROM roadmap WHERE user_id=?", (u["id"],))["w"] or 0
        for s in [g for g in gaps if g not in done][:8]:
            wk += 1
            db.x("INSERT INTO roadmap(user_id,skill,week) VALUES(?,?,?)", (u["id"], s, wk))
        st.rerun()
    if not rows:
        st.info("No roadmap yet. Press the button to build one from your resume gaps" + (" and your best job match." if a else "."))
        return

    done = sum(r["status"] == "done" for r in rows)
    st.progress(done / len(rows), text=f"{done} of {len(rows)} topics done · about 6 hours a week")
    courses = get_courses_for_role(role) or []
    current = next((r["id"] for r in rows if r["status"] != "done"), None)
    for n, r in enumerate(rows):
        cls = "done" if r["status"] == "done" else "now" if r["id"] == current else ""
        res = courses[n % len(courses)] if courses else None
        yt = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(f"learn {r['skill']} for beginners")
        st.markdown(f'<div class="rm-week {cls}"><span class="wk">week {r["week"]}</span><div><b>{ui.e(r["skill"])}</b>'
                    f'<div style="font-size:.88rem;color:var(--ink-2)">'
                    f'{f"<a href={chr(34)}{res[1]}{chr(34)} target=_blank>{ui.e(res[0])}</a> · " if res else ""}'
                    f'<a href="{yt}" target="_blank">free videos on YouTube</a></div></div></div>', unsafe_allow_html=True)
        if r["id"] == current:
            with st.expander(f"Check yourself on {r['skill']}", expanded=False):
                ok = _quiz(r["skill"], f"qz{r['id']}")
                if ok:
                    st.success("All correct.")
                if st.button("Mark as done", key=f"done{r['id']}", type="primary"):
                    db.x("UPDATE roadmap SET status='done' WHERE id=?", (r["id"],))
                    st.rerun()
