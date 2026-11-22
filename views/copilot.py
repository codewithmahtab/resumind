import streamlit as st

from core import db, llm, ui
from views.common import me, resume_text

QUICK = ["How do I answer 'Tell me about yourself' with my resume?", "Which project should I lead with, and why?",
         "What should I learn first for my target role?", "How do I explain a low CGPA honestly?"]


def _context(u):
    txt, _ = resume_text()
    a = db.latest_analysis(u["id"])
    m = db.best_match(u["id"])
    iv = db.one("SELECT AVG(overall) v, COUNT(*) n FROM interviews WHERE user_id=?", (u["id"],))
    gaps = [r["skill"] for r in db.q("SELECT skill FROM roadmap WHERE user_id=? AND status='todo'", (u["id"],))]
    return (f"Student: {u['name']}, {u.get('branch')} {u.get('year')}, target role {u.get('target_role')}.\n"
            f"ATS score: {a['ats'] if a else 'not analyzed'}. Best job match: {m['title'] + ' ' + str(m['match_pct']) + '%' if m else 'none'}.\n"
            f"Mock interviews: {iv['n']} (avg {iv['v'] or 0:.1f}/10). Skills still to learn: {', '.join(gaps) or 'none'}.\n"
            f"Resume:\n{txt[:3000]}")


def render():
    u = me()
    ui.plate("copilot", "Ask anything about your job search. It already knows your resume, scores and gaps.", "half")
    hist = st.session_state.setdefault("chat", [])
    cols = st.columns(len(QUICK))
    pick = next((q for c, q in zip(cols, QUICK) if c.button(q, width="stretch")), None)
    for m in hist:
        st.chat_message(m["role"]).markdown(m["content"])
    ask = st.chat_input("Ask about interviews, your resume or what to learn") or pick
    if ask:
        hist.append({"role": "user", "content": ask})
        st.chat_message("user").markdown(ask)
        convo = "\n".join(f"{m['role']}: {m['content']}" for m in hist[-8:])
        with st.spinner("Thinking…"):
            out = llm.text("You are ResuMind Copilot, a practical career mentor for Indian engineering students. "
                           "Answer in under 150 words, specific to this student, with concrete next steps.\n\n"
                           f"{_context(u)}\n\nConversation:\n{convo}\nassistant:")
        out = out or "I'm offline right now. Add GOOGLE_API_KEY to the .env file to chat with Copilot."
        hist.append({"role": "assistant", "content": out})
        st.chat_message("assistant").markdown(out)
