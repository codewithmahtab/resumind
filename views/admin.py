import pandas as pd
import streamlit as st

from core import db, ml, ui


def render():
    ui.plate("admin panel", "How students are doing, what they say, and how the ML model performs.", "square")
    c = st.columns(5)
    c[0].metric("Students", db.one("SELECT COUNT(*) n FROM users WHERE role='student'")["n"])
    c[1].metric("Analyses", db.one("SELECT COUNT(*) n FROM analyses")["n"])
    c[2].metric("Avg ATS", f"{db.one('SELECT AVG(ats) v FROM analyses')['v'] or 0:.0f}")
    c[3].metric("Interviews", db.one("SELECT COUNT(*) n FROM interviews")["n"])
    c[4].metric("Avg interview", f"{db.one('SELECT AVG(overall) v FROM interviews')['v'] or 0:.1f}/10")

    t1, t2, t3 = st.tabs(["students", "ml model", "feedback"])
    with t1:
        df = pd.DataFrame(db.q("""SELECT u.name, u.username, u.college, u.branch, u.target_role,
            (SELECT ats FROM analyses a WHERE a.user_id=u.id ORDER BY id DESC LIMIT 1) ats,
            (SELECT COUNT(*) FROM interviews i WHERE i.user_id=u.id) interviews, u.created_at
            FROM users u WHERE role='student' ORDER BY u.id DESC"""))
        if not df.empty:
            st.dataframe(df, hide_index=True, width="stretch")
            st.download_button("Export CSV", df.to_csv(index=False), "students.csv", "text/csv")
            roles = df["target_role"].value_counts()
            ui.label("target roles")
            st.bar_chart(roles, color="#CF2B2B", height=220)
    with t2:
        rep = ml.report()
        if rep:
            st.markdown(f"**Dataset:** {rep['dataset']} · {rep['samples']} samples · {rep['classes']} roles · "
                        f"test set {rep['test_size']} · deployed: **{rep['deployed']}**")
            st.dataframe(pd.DataFrame(rep["models"]).T.rename_axis("model"), width="stretch")
        if st.button("Retrain model", type="primary"):
            with st.spinner("Training…"):
                ml.train(verbose=False)
                ml._clf = None
            st.rerun()
    with t3:
        fb = db.q("SELECT f.created_at, u.name, f.rating, f.comment FROM feedback f LEFT JOIN users u ON u.id=f.user_id ORDER BY f.id DESC")
        if fb:
            st.metric("Average rating", f"{sum(f['rating'] for f in fb) / len(fb):.1f}/5")
            st.dataframe(pd.DataFrame(fb), hide_index=True, width="stretch")
        else:
            st.info("No feedback yet.")
