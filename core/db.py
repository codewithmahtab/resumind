"""SQLite storage for ResuMind 2.0 (one file, created on first run)."""
import json
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "resumind.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, name TEXT, pw_hash TEXT, salt TEXT,
  role TEXT DEFAULT 'student', college TEXT, branch TEXT, year TEXT, target_role TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS resumes(id INTEGER PRIMARY KEY, user_id INTEGER, filename TEXT, text TEXT, skills_json TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS analyses(id INTEGER PRIMARY KEY, user_id INTEGER, resume_id INTEGER, ats REAL, subs_json TEXT,
  role_pred TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS matches(id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, match_pct REAL, matched_json TEXT,
  missing_json TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS interviews(id INTEGER PRIMARY KEY, user_id INTEGER, role TEXT, itype TEXT, difficulty TEXT,
  overall REAL, comm REAL, report_json TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS roadmap(id INTEGER PRIMARY KEY, user_id INTEGER, skill TEXT, week INTEGER, status TEXT DEFAULT 'todo',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS feedback(id INTEGER PRIMARY KEY, user_id INTEGER, rating INTEGER, comment TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP);
"""


def conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init():
    with conn() as c:
        c.executescript(SCHEMA)


def q(sql, args=()):
    with conn() as c:
        return [dict(r) for r in c.execute(sql, args).fetchall()]


def one(sql, args=()):
    rows = q(sql, args)
    return rows[0] if rows else None


def x(sql, args=()):
    with conn() as c:
        cur = c.execute(sql, args)
        return cur.lastrowid


def dumps(v):
    return json.dumps(v, ensure_ascii=False)


def loads(v, default=None):
    try:
        return json.loads(v) if v else default
    except Exception:
        return default


# ---- convenience reads used by several pages ----
def latest_resume(uid):
    return one("SELECT * FROM resumes WHERE user_id=? ORDER BY id DESC LIMIT 1", (uid,))


def latest_analysis(uid):
    return one("SELECT * FROM analyses WHERE user_id=? ORDER BY id DESC LIMIT 1", (uid,))


def best_match(uid):
    return one("SELECT * FROM matches WHERE user_id=? ORDER BY match_pct DESC LIMIT 1", (uid,))


def readiness(uid):
    """Career readiness 0-100: resume 35%, job match 25%, interviews 25%, roadmap 15%."""
    a = latest_analysis(uid)
    m = best_match(uid)
    iv = one("SELECT AVG(overall) v, COUNT(*) n FROM interviews WHERE user_id=?", (uid,))
    rm = one("SELECT SUM(status='done') d, COUNT(*) n FROM roadmap WHERE user_id=?", (uid,))
    parts = {
        "Resume": a["ats"] if a else 0,
        "Job match": m["match_pct"] if m else 0,
        "Interviews": (iv["v"] or 0) * 10 if iv and iv["n"] else 0,
        "Roadmap": (100 * (rm["d"] or 0) / rm["n"]) if rm and rm["n"] else 0,
    }
    w = {"Resume": .35, "Job match": .25, "Interviews": .25, "Roadmap": .15}
    return round(sum(parts[k] * w[k] for k in w)), parts
