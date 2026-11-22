# ResuMind 2.0 — AI career copilot

Upload your resume once. ResuMind scores it, predicts the job role it reads as, matches it to job descriptions,
builds a week-by-week learning plan from your gaps, and runs voice mock interviews built from your own projects.

## Run

```
startup.bat
```
or `pip install -r requirements.txt` then `streamlit run app.py`. Open http://localhost:8501.

- **Demo:** press "Try the demo account" on the login page.
- **Admin:** username `admin`, password `admin123` (change it before any real use).
- **Gemini (optional):** create `.env` with `GOOGLE_API_KEY=...`. Without it the app runs offline: built-in question bank,
  rule-based answer scoring, no voice transcription, no AI rewriting.

## Modules

| Page | What it does |
|---|---|
| Dashboard | Career readiness score (resume 35%, job match 25%, interviews 25%, roadmap 15%), next steps, progress chart |
| Analyzer | ATS score on 5 areas, ML role prediction (top 3), skill gaps, highlighted lines to fix, AI bullet rewrite, report download |
| Job Match | Match % for any JD (TF-IDF similarity + skill coverage), must-have gaps, tailoring tips, cover letter, best-fit roles |
| Builder | Form + live preview + live ATS score, DOCX export in 4 templates |
| Mock Interview | Resume-based questions, voice or typed answers, content score + communication score (filler words, pace), report, history |
| Learning Path | Roadmap from gaps, courses and videos per week, quiz, progress |
| Copilot | Chat that knows your resume, scores and gaps |
| Admin | Student stats, ML model evaluation, retrain, feedback, CSV export |

## ML

`python -m core.ml` trains and evaluates the job-role classifier (TF-IDF + Naive Bayes / Linear SVM / Logistic Regression)
and writes `ml/models/report.json`. It uses the Kaggle Resume Dataset if `data/Resume.csv` exists (columns `Resume_str`,
`Category`); otherwise it trains on a synthetic dataset generated from `config/job_roles.py` (~87% accuracy).

## Structure

```
app.py             entry point: login gate + navigation
core/              db, auth, llm (Gemini wrapper), resume (parsing + ATS), ml, interview, ui (theme)
views/             one file per page
config/            job roles and courses
tests_smoke.py     loads every page and runs the main flows
```

The original v1 app is kept as `app_v1.py` for reference.
