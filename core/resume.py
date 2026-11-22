"""Resume text extraction, skill extraction and ATS scoring (rule + regex layer)."""
import io
import re

from config.job_roles import JOB_ROLES

EXTRA = """python, java, c++, c#, javascript, typescript, sql, golang, kotlin, swift, php, html, css, react, angular,
vue.js, node.js, express, next.js, redux, tailwind css, jwt, django, flask, fastapi, spring boot, rest api, graphql, mongodb, mysql, postgresql, redis, git, github,
docker, kubernetes, aws, azure, gcp, linux, jenkins, terraform, ci/cd, pandas, numpy, scikit-learn, tensorflow, pytorch,
keras, machine learning, deep learning, nlp, computer vision, opencv, data analysis, data visualization, statistics,
excel, power bi, tableau, matplotlib, seaborn, spark, hadoop, big data, etl, a/b testing, llm, generative ai,
prompt engineering, figma, ui/ux, selenium, testing, agile, scrum, jira, communication, leadership, teamwork,
problem solving, time management, critical thinking"""
_VAGUE = {"frontend tech", "backend tech", "databases", "devops", "system design", "apis"}


def _norm(s):
    return s.strip().lower()


def role_skills(role):
    """Required skills for a role, split into atomic skills ('React/Angular/Vue' -> 3)."""
    for cat in JOB_ROLES.values():
        if role in cat:
            info = cat[role]
            out = []
            for s in info.get("required_skills", []) + info.get("recommended_skills", {}).get("technical", []):
                bits = [b for b in re.split(r"[/,]", s)]
                # split "React/Angular/Vue" but keep "CI/CD", "UI/UX", "A/B testing" whole
                for p in (bits if all(len(b.strip()) >= 4 for b in bits) else [s]):
                    p = _norm(p)
                    if len(p) > 1 and p not in _VAGUE and p not in out:
                        out.append(p)
            return out
    return []


def all_roles():
    return [r for cat in JOB_ROLES.values() for r in cat]


def _vocab():
    v = {_norm(s) for s in EXTRA.split(",")}
    for r in all_roles():
        v.update(role_skills(r))
    return {s for s in v if len(s) > 1}


VOCAB = _vocab()


ALIASES = {"rest api": ["restful api", "rest apis", "restful apis", "restful"], "node.js": ["nodejs", "node"],
           "javascript": ["js"], "machine learning": ["ml"], "postgresql": ["postgres"], "ci/cd": ["cicd"]}


def find_skill(skill, text_lower):
    # digits may follow (html5, css3); letters may not (java != javascript)
    return any(re.search(r"(?<![a-z0-9+#.])" + re.escape(k) + r"(?![a-z+#])", text_lower)
               for k in [skill] + ALIASES.get(skill, []))


def extract_skills(text):
    t = text.lower()
    return sorted(s for s in VOCAB if find_skill(s, t))


def extract_text(uploaded):
    name = uploaded.name.lower()
    data = uploaded.getvalue()
    if name.endswith(".pdf"):
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)
    if name.endswith(".docx"):
        from docx import Document
        return "\n".join(p.text for p in Document(io.BytesIO(data)).paragraphs)
    return data.decode("utf-8", "ignore")


ACTION = {"built", "developed", "designed", "created", "implemented", "led", "improved", "reduced", "increased",
          "automated", "launched", "optimized", "analyzed", "trained", "deployed", "managed", "achieved", "delivered",
          "engineered", "cleaned", "migrated", "won", "organized", "published", "streamlined"}
WEAK = ["responsible for", "worked on", "helped with", "duties included", "various", "etc", "involved in",
        "assisted in", "tasked with"]
SECTIONS = {"Contact": r"@|\+?\d[\d \-]{8,}", "Education": r"education|b\.?tech|degree|university|college|cgpa",
            "Experience": r"experience|internship|intern\b|employment", "Projects": r"project",
            "Skills": r"skills|technologies|tools"}


def _content_lines(text):
    return [l.strip(" •-*\t") for l in text.splitlines() if len(l.split()) >= 6]


def analyze(text, role):
    t = text.lower()
    words = re.findall(r"[A-Za-z]+", text)
    req = role_skills(role)
    found = [s for s in req if find_skill(s, t)]
    missing = [s for s in req if s not in found]
    keywords = 100 * len(found) / len(req) if req else 0

    sec = {k: bool(re.search(p, t)) for k, p in SECTIONS.items()}
    sections = 20 * sum(sec.values())

    lines = _content_lines(text)
    with_num = [l for l in lines if re.search(r"\d", l)]
    with_verb = [l for l in lines if l.split()[0].lower().strip(",.") in ACTION]
    impact = (50 * len(with_num) / len(lines) + 50 * len(with_verb) / len(lines)) if lines else 0
    impact = min(100, impact * 1.4)

    n = len(words)
    fmt = 100
    if n < 250: fmt -= 35
    elif n > 1100: fmt -= 20
    if not re.search(r"^\s*[•\-*▪●]", text, re.M): fmt -= 15
    if not sec["Contact"]: fmt -= 25
    if any(len(l.split()) > 45 for l in text.splitlines()): fmt -= 10
    sents = [s for s in re.split(r"[.\n]", text) if len(s.split()) > 3]
    avg = sum(len(s.split()) for s in sents) / len(sents) if sents else 0
    readability = 100 if 8 <= avg <= 22 else max(30, 100 - 4 * abs(avg - 15))

    subs = {"Keywords": keywords, "Sections": sections, "Impact": impact, "Format": max(0, fmt),
            "Readability": readability}
    w = {"Keywords": .30, "Sections": .20, "Impact": .25, "Format": .15, "Readability": .10}
    ats = round(sum(subs[k] * w[k] for k in w))

    issues = []
    for l in lines:
        low = l.lower()
        weak = next((p for p in WEAK if re.search(r"\b" + re.escape(p) + r"\b", low)), None)
        if weak:
            issues.append({"line": l, "kind": "bad", "title": "Weak phrase",
                           "tip": f'"{weak}" says what you were assigned, not what you did. Start with an action verb.'})
        elif not re.search(r"\d", l) and l.split()[0].lower() in ACTION:
            issues.append({"line": l, "kind": "warn", "title": "No number",
                           "tip": "Good verb. Add a result: a %, a count, time saved or users reached."})
    for k, ok in sec.items():
        if not ok:
            issues.append({"line": "", "kind": "bad", "title": f"Missing {k} section",
                           "tip": f"Recruiters and ATS parsers look for a clear {k} heading."})
    good = [l for l in lines if l in with_num and l in with_verb]
    return {"ats": ats, "subs": {k: round(v) for k, v in subs.items()}, "found": found, "missing": missing,
            "skills": extract_skills(text), "issues": issues[:8], "good": good[:5], "sections": sec, "words": n}
