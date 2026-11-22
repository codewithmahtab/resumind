"""Trained ML layer: job-role classifier (TF-IDF + linear models) and resume-JD matcher.

Train and print the evaluation report:   python -m core.ml
If data/Resume.csv (Kaggle "Resume Dataset", columns Resume_str, Category) exists it is used;
otherwise a synthetic dataset is generated from config/job_roles.py.
"""
import json
import os
import random

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.svm import LinearSVC

from config.job_roles import JOB_ROLES
from core.resume import extract_skills, find_skill, role_skills

ROOT = os.path.dirname(os.path.dirname(__file__))
MODEL = os.path.join(ROOT, "ml", "models", "role_clf.joblib")
REPORT = os.path.join(ROOT, "ml", "models", "report.json")

_FILLER = ("college university project team internship worked student b.tech engineering final year "
           "certificate hackathon club event course training intern company client report").split()


def _role_info():
    for cat in JOB_ROLES.values():
        for role, info in cat.items():
            yield role, info


def synthetic_dataset(per_role=80, seed=7):
    rnd = random.Random(seed)
    roles = list(_role_info())
    all_sk = [s for r, _ in roles for s in role_skills(r)]
    X, y = [], []
    for role, info in roles:
        own = role_skills(role) + [s.lower() for s in info.get("recommended_skills", {}).get("soft", [])]
        desc = info.get("description", "").lower().split()
        for _ in range(per_role):
            k = rnd.randint(2, min(4, len(own)))
            parts = rnd.sample(own, k) + rnd.sample(all_sk, rnd.randint(3, 6))  # overlap with other roles
            parts += rnd.sample(desc, min(len(desc), rnd.randint(0, 2))) + rnd.sample(_FILLER, 6)
            rnd.shuffle(parts)
            X.append(" ".join(parts))
            y.append(role)
    return X, y, "synthetic (generated from config/job_roles.py)"


def load_dataset():
    path = os.path.join(ROOT, "data", "Resume.csv")
    if os.path.exists(path):
        import pandas as pd
        df = pd.read_csv(path).dropna(subset=["Resume_str", "Category"])
        return df["Resume_str"].tolist(), df["Category"].tolist(), "Kaggle Resume Dataset (data/Resume.csv)"
    return synthetic_dataset()


def train(verbose=True):
    X, y, source = load_dataset()
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    vec = lambda: TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1)
    candidates = {
        "Naive Bayes (baseline)": make_pipeline(vec(), MultinomialNB()),
        "Linear SVM": make_pipeline(vec(), LinearSVC()),
        "Logistic Regression": make_pipeline(vec(), LogisticRegression(max_iter=3000, C=5)),
    }
    results = {}
    for name, pipe in candidates.items():
        pipe.fit(Xtr, ytr)
        p = pipe.predict(Xte)
        results[name] = {"accuracy": round(accuracy_score(yte, p), 4),
                         "macro_f1": round(f1_score(yte, p, average="macro"), 4)}
        if verbose:
            print(f"{name:26s} acc={results[name]['accuracy']:.3f}  macroF1={results[name]['macro_f1']:.3f}")
    best = candidates["Logistic Regression"]  # needs predict_proba for top-3 confidence
    os.makedirs(os.path.dirname(MODEL), exist_ok=True)
    joblib.dump(best, MODEL)
    report = {"dataset": source, "samples": len(X), "classes": len(set(y)), "test_size": len(Xte),
              "models": results, "deployed": "Logistic Regression"}
    with open(REPORT, "w") as f:
        json.dump(report, f, indent=2)
    return report


_clf = None


def predict_role(text, k=3):
    global _clf
    if _clf is None:
        if not os.path.exists(MODEL):
            train(verbose=False)
        _clf = joblib.load(MODEL)
    proba = _clf.predict_proba([text.lower()])[0]
    idx = np.argsort(proba)[::-1][:k]
    return [(_clf.classes_[i], float(proba[i])) for i in idx]


def report():
    try:
        with open(REPORT) as f:
            return json.load(f)
    except Exception:
        return None


def match(resume_text, jd_text):
    """Match % = 40% TF-IDF cosine similarity + 60% skill coverage of the JD's skills."""
    tf = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit([resume_text, jd_text])
    cos = float(cosine_similarity(tf.transform([resume_text]), tf.transform([jd_text]))[0, 0])
    jd_sk = extract_skills(jd_text)
    r = resume_text.lower()
    matched = [s for s in jd_sk if find_skill(s, r)]
    missing = [s for s in jd_sk if s not in matched]
    must = set()
    for sent in jd_text.lower().replace("\n", ". ").split("."):
        if any(w in sent for w in ("must", "required", "strong", "proficien", "mandatory", "expert")):
            must.update(s for s in jd_sk if find_skill(s, sent))
    cover = len(matched) / len(jd_sk) if jd_sk else 0
    pct = round(100 * (0.4 * min(1.0, cos * 2.2) + 0.6 * cover))
    return {"pct": pct, "cosine": round(cos, 3), "matched": matched, "missing": missing,
            "must_missing": [s for s in missing if s in must], "jd_skills": jd_sk}


def recommend_roles(resume_text, k=5):
    out = []
    r = resume_text.lower()
    for role, info in _role_info():
        req = role_skills(role)
        have = [s for s in req if find_skill(s, r)]
        out.append({"role": role, "pct": round(100 * len(have) / len(req)) if req else 0,
                    "missing": [s for s in req if s not in have][:4], "desc": info.get("description", "")})
    return sorted(out, key=lambda d: -d["pct"])[:k]


if __name__ == "__main__":
    print(json.dumps(train(), indent=2))
