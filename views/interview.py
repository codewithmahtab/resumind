import time

import pandas as pd
import streamlit as st

from core import db, interview as iv, llm, ui
from views.common import me, need_resume, role_select


def _setup(txt):
    st.subheader("set up your interview")
    c1, c2 = st.columns(2)
    with c1:
        role = role_select(key="iv_role")
        itype = st.radio("Type", ["Mixed", "Technical", "HR", "Project deep-dive"], horizontal=True)
    with c2:
        diff = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"], value="Medium")
        n = st.slider("Questions", 3, 8, 5)
    st.caption("Questions are written from your own resume. Answer by voice (recorded in the browser) or by typing."
               + ("" if llm.available() else " Offline mode: questions come from the built-in bank and scoring is rule-based."))
    if st.button("Start interview", type="primary"):
        with st.spinner("Writing questions from your resume…"):
            qs, ai = iv.generate_questions(role, itype, diff, n, txt)
        st.session_state.iv = {"role": role, "type": itype, "diff": diff, "qs": qs, "i": 0, "ans": [], "t0": time.time(), "ai": ai}
        st.rerun()


def _question(s):
    q = s["qs"][s["i"]]
    st.markdown(f'<div class="rm-lbl">{ui.e(s["type"])} round · {ui.e(s["role"])} · {ui.e(s["diff"])} '
                f'· question {s["i"] + 1} of {len(s["qs"])}</div>', unsafe_allow_html=True)
    st.progress(s["i"] / len(s["qs"]))
    st.markdown(f'<div class="rm-q">{ui.e(q["q"])}</div>', unsafe_allow_html=True)
    st.caption(f"{q.get('type', '')} question" + (" · generated from your resume" if s["ai"] else ""))
    audio = st.audio_input("Record your answer", key=f"aud{s['i']}")
    typed = st.text_area("Or type your answer", key=f"txt{s['i']}", height=110)
    c1, c2, c3 = st.columns([1, 1, 3])
    if c1.button("Submit answer", type="primary", width="stretch"):
        secs, ans = None, typed.strip()
        if audio is not None:
            b = audio.getvalue()
            secs = llm.wav_seconds(b)
            with st.spinner("Transcribing…"):
                tr = llm.transcribe(b)
            if tr:
                ans = tr
            elif not ans:
                st.error("Voice needs a GOOGLE_API_KEY for transcription. Type your answer instead.")
                st.stop()
        if not ans:
            st.error("Record or type an answer first.")
            st.stop()
        with st.spinner("Scoring…"):
            ev = iv.evaluate(q, ans, s["role"])
        s["ans"].append({"q": q["q"], "answer": ans, "eval": ev, "comm": iv.comm_metrics(ans, secs), "voice": audio is not None})
        s["i"] += 1
        st.rerun()
    if c2.button("Skip", width="stretch"):
        s["ans"].append({"q": q["q"], "answer": "(skipped)", "eval": {"score": 0, "good": "", "missing": "Skipped.", "ideal": ""},
                         "comm": iv.comm_metrics("", None), "voice": False})
        s["i"] += 1
        st.rerun()
    if s["ans"]:
        last = s["ans"][-1]
        with st.container(border=True):
            st.markdown(f"**Feedback on the last answer · {last['eval']['score']:.0f}/10**")
            st.write(f"{last['eval'].get('good', '')} {last['eval'].get('missing', '')}")
            m = last["comm"]
            c = st.columns(3)
            c[0].metric("Filler words", m["fillers"])
            c[1].metric("Pace", f"{m['wpm']} wpm" if m["wpm"] else "typed")
            c[2].metric("Words", m["words"])


def _report(s, u):
    ans = s["ans"]
    content = sum(a["eval"]["score"] for a in ans) / len(ans)
    comm = sum(a["comm"]["score"] for a in ans) / len(ans)
    overall = round(0.7 * content + 0.3 * comm, 1)
    if not s.get("saved"):
        db.x("INSERT INTO interviews(user_id,role,itype,difficulty,overall,comm,report_json) VALUES(?,?,?,?,?,?,?)",
             (u["id"], s["role"], s["type"], s["diff"], overall, round(comm, 1), db.dumps(ans)))
        s["saved"] = True
    ui.plate("interview report", f"{s['type']} round · {s['role']} · {s['diff']} · {len(ans)} questions", "circle")
    a, b, c, d = st.columns(4)
    with a:
        ui.bignum(overall, "overall", "/10")
    b.metric("Content (70%)", f"{content:.1f}/10")
    c.metric("Communication (30%)", f"{comm:.1f}/10")
    d.metric("Filler words", sum(x["comm"]["fillers"] for x in ans))
    weak = [x for x in ans if x["eval"]["score"] < 6]
    for n, x in enumerate(ans, 1):
        with st.expander(f"Q{n} · {x['eval']['score']:.0f}/10 · {x['q']}", expanded=x in weak[:1]):
            st.markdown(f"**Your answer** {'(voice)' if x['voice'] else ''}: {x['answer']}")
            st.markdown(f"**What worked:** {x['eval'].get('good', '')}")
            st.markdown(f"**What was missing:** {x['eval'].get('missing', '')}")
            if x["eval"].get("ideal"):
                st.info(f"Sample strong answer: {x['eval']['ideal']}")
    txt = "\n\n".join(f"Q{n}: {x['q']}\nScore: {x['eval']['score']}/10\nAnswer: {x['answer']}\nMissing: {x['eval'].get('missing', '')}\n"
                      f"Ideal: {x['eval'].get('ideal', '')}" for n, x in enumerate(ans, 1))
    c1, c2, c3 = st.columns([1, 1, 2])
    c1.download_button("Download report", f"ResuMind mock interview — {s['role']}\nOverall {overall}/10\n\n{txt}", "interview_report.txt")
    if c2.button("Retry weak questions", disabled=not weak):
        st.session_state.iv = {**s, "qs": [{"q": x["q"], "key_points": []} for x in weak], "i": 0, "ans": [], "saved": False}
        st.rerun()
    if c3.button("New interview", type="primary"):
        del st.session_state.iv
        st.rerun()


def render():
    u = me()
    s = st.session_state.get("iv")
    if s and s["i"] >= len(s["qs"]):
        return _report(s, u)
    ui.plate("mock interview", "Questions built from your resume. Scored on what you said and how you said it.", "circle")
    txt, _ = need_resume()
    if not s:
        _setup(txt)
        hist = db.q("SELECT created_at, role, itype, difficulty, overall, comm FROM interviews WHERE user_id=? ORDER BY id DESC", (u["id"],))
        if hist:
            st.divider()
            st.subheader("past interviews")
            st.dataframe(pd.DataFrame(hist).rename(columns={"created_at": "when", "itype": "type", "overall": "score /10",
                                                             "comm": "communication"}), hide_index=True, width="stretch")
        return
    _question(s)
    if st.button("End interview early") and s["ans"]:
        s["qs"] = s["qs"][:s["i"]]
        st.rerun()
