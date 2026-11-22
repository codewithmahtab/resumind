"""Mock interview engine: questions, answer scoring, communication analysis."""
import random
import re

from core import llm
from core.resume import role_skills

HR = [
    ("Tell me about yourself.", ["background", "skills", "project", "goal"]),
    ("Why should we hire you for this role?", ["skills", "fit", "value", "example"]),
    ("Describe a time you worked in a team and faced a conflict.", ["situation", "action", "result", "team"]),
    ("What is your biggest weakness?", ["weakness", "improve", "example", "learning"]),
    ("Where do you see yourself in five years?", ["growth", "role", "skills", "company"]),
    ("Tell me about a failure and what you learned.", ["situation", "mistake", "learned", "result"]),
]
TECH = ["Explain {s} to someone new to it, and say where you used it.",
        "What problem did {s} solve in one of your projects? What would you do differently?",
        "What are common mistakes people make with {s}?"]
PROJECT = ["Walk me through the project on your resume you are most proud of. What was your exact contribution?",
           "What was the hardest technical problem in your main project, and how did you solve it?"]
FILLERS = ["umm", "um", "uh", "uhh", "hmm", "basically", "actually", "you know", "i mean", "kind of", "sort of",
           "like i said"]


def fallback_questions(role, itype, n):
    sk = role_skills(role) or ["your main skill"]
    tech = [{"q": random.choice(TECH).format(s=s), "key_points": [s, "example", "project", "why"], "type": "Technical"}
            for s in random.sample(sk, min(len(sk), n))]
    hr = [{"q": q, "key_points": k, "type": "HR"} for q, k in random.sample(HR, min(len(HR), n))]
    proj = [{"q": q, "key_points": ["problem", "role", "approach", "result"], "type": "Project"} for q in PROJECT]
    pool = {"Technical": tech, "HR": hr, "Project deep-dive": proj + tech}.get(itype)
    if pool is None:  # Mixed
        pool = [x for trio in zip(tech, hr, proj * 3) for x in trio]
    return (pool * 3)[:n]


def generate_questions(role, itype, difficulty, n, resume_text=""):
    prompt = f"""You are a strict but fair interviewer at an Indian tech company hiring a fresher for: {role}.
Interview type: {itype}. Difficulty: {difficulty}. Write exactly {n} questions.
Ground at least half of them in the candidate's resume below (mention their actual project or skill by name).
Return JSON: {{"questions":[{{"q":"question","key_points":["3-5 short points a strong answer covers"],"type":"Technical|HR|Project"}}]}}
Resume:\n{resume_text[:3500]}"""
    out = llm.json_out(prompt)
    qs = (out or {}).get("questions") if isinstance(out, dict) else None
    if qs and all("q" in q for q in qs):
        return qs[:n], True
    return fallback_questions(role, itype, n), False


def comm_metrics(transcript, seconds=None):
    t = " " + re.sub(r"[^a-z' ]", " ", transcript.lower()) + " "
    words = len(t.split())
    fillers = sum(len(re.findall(r"(?<= )" + re.escape(f) + r"(?= )", t)) for f in FILLERS)
    wpm = round(words / (seconds / 60)) if seconds and seconds > 3 else None
    score = 10.0
    score -= min(4, 40 * fillers / max(words, 1))
    if wpm and not 110 <= wpm <= 165:
        score -= min(2.5, abs(wpm - 138) / 25)
    if words < 40:
        score -= 3 if words < 20 else 1.5
    return {"words": words, "fillers": fillers, "wpm": wpm, "seconds": round(seconds) if seconds else None,
            "score": round(max(0, score), 1)}


def evaluate(q, answer, role):
    prompt = f"""Evaluate this interview answer for a fresher applying as {role}. Be specific and honest.
Question: {q['q']}
Key points a strong answer covers: {q.get('key_points')}
Answer: {answer}
Return JSON: {{"score": 0-10 number, "good": "one sentence on what worked", "missing": "one sentence on what was missing",
"ideal": "a strong 3-4 sentence sample answer"}}"""
    out = llm.json_out(prompt)
    if isinstance(out, dict) and "score" in out:
        out["score"] = float(out["score"])
        out["ai"] = True
        return out
    a = answer.lower()
    words = len(answer.split())
    kp = [k.lower() for k in q.get("key_points", [])]
    hit = [k for k in kp if k in a]
    has_num = bool(re.search(r"\d|percent|%", a))
    reason = any(w in a for w in ("because", "so that", "which", "resulted", "measured", "improved", "reduced", "learned", "chose"))
    star = sum(w in a for w in ("situation", "task", "action", "result", "problem", "approach", "outcome")) >= 2
    score = 2 + min(3, words / 30) + (2 if has_num else 0) + (1.5 if hit else 0) + (1.5 if reason or star else 0)
    tips = []
    if words < 40: tips.append("go deeper (aim for 60-120 words)")
    if not has_num: tips.append("add a number or result")
    if not (reason or star): tips.append("explain why you chose your approach")
    if not hit and kp: tips.append(f"mention {kp[0]}")
    return {"score": round(min(10, score), 1), "ai": False,
            "good": "Clear, specific answer." if score >= 7 else "You answered the question directly." if words >= 15 else "You attempted it.",
            "missing": ("Next time: " + "; ".join(tips) + ".") if tips else "Strong answer. Keep this structure.",
            "ideal": "Use STAR: the Situation, the Task, the Action you took, and the Result with a number."}
