# Smart AI Resume Analyzer & Builder

An AI and NLP-powered Resume Analysis and Builder application built with **Python**, **Streamlit**, and **Google Gemini Generative AI**.

This project analyzes resumes against industry-specific job profiles, evaluates ATS (Applicant Tracking System) compatibility, highlights skill gaps, recommends targeted courses, and offers an interactive resume builder.

---

## 🌟 Key Features

1. **🏠 Home Page**: Overview of features, interactive hero section, and quick start navigation.
2. **🔍 Resume Analyzer**:
   - **Standard Analyzer**: Rule-based matching against defined job roles, skill extraction, ATS score computation, and course recommendations.
   - **AI Analyzer (Powered by Google Gemini)**: Deep semantic analysis, strengths & weaknesses identification, keyword optimization, and PDF summary reports.
3. **📝 Resume Builder**: Form-driven resume generator supporting modern templates with instant Word (`.docx`) file export.
4. **💬 Feedback**: Interactive user feedback submission form with SQLite persistence and feedback statistics.

---

## 🛠️ Tech Stack & Architecture

- **Frontend & App Framework**: Streamlit (Python)
- **AI / LLM Integration**: Google Gemini API (`google-generativeai`)
- **Document Processing**: `pdfplumber` (PDF parsing), `python-docx` (DOCX parsing & generation), `reportlab` (PDF generation)
- **Data Visualization**: `plotly`, `pandas`
- **Database**: SQLite3 (`resume_data.db`, `feedback.db`)
- **Styling**: Custom CSS (`style/style.css`) & Streamlit UI components

---

## 🚀 How to Run the Project

### 1. Prerequisites
- Python 3.10+ installed.

### 2. Install Required Dependencies
```bash
pip install -r requirements.txt
```

### 3. (Optional) Set up Google Gemini API Key
To use the AI Analysis tab, add your Gemini API key:
- Create a `.env` file in the project folder:
```env
GOOGLE_API_KEY=your_api_key_here
```
*(Note: The Standard Analyzer works offline without any API key!)*

### 4. Start the Application
Run via python:
```bash
python -m streamlit run app.py
```
Or simply double click:
```bash
startup.bat
```
Open your browser at `http://localhost:8501`.
