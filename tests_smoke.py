from streamlit.testing.v1 import AppTest
from core import db, auth
db.init(); auth.seed()
demo = db.one("SELECT * FROM users WHERE username='demo'")
adm = db.one("SELECT * FROM users WHERE username='admin'")
def page(mod):
    import importlib, streamlit as st
    importlib.import_module(f"views.{mod}").render()
for mod, u in [("dashboard",demo),("analyzer",demo),("match",demo),("builder",demo),("interview",demo),("learning",demo),("copilot",demo),("admin",adm)]:
    at = AppTest.from_function(page, args=(mod,), default_timeout=60)
    at.session_state["user"] = u
    at.run()
    errs = [e.value for e in at.exception]
    print(f"{mod:10s}", "OK" if not errs else errs[0][:300])
# interactive flows
at = AppTest.from_function(page, args=("match",), default_timeout=60); at.session_state["user"]=demo; at.run()
at.selectbox[0].select("Data Scientist").run(); at.button[0].click().run()
print("match flow", [e.value[:200] for e in at.exception] or "OK", at.session_state["jm"]["r"]["pct"] if "jm" in at.session_state else None)
at = AppTest.from_function(page, args=("interview",), default_timeout=60); at.session_state["user"]=demo; at.run()
at.button[0].click().run()
for i in range(5):
    at.text_area[0].input("Umm basically I built a sales forecasting model with XGBoost and pandas, I used a time based split to validate and the error dropped by 18 percent which helped the team plan stock.").run()
    at.button[0].click().run()
print("interview flow", [e.value[:200] for e in at.exception] or "OK", db.one("SELECT overall, comm FROM interviews ORDER BY id DESC LIMIT 1"))
at = AppTest.from_function(page, args=("learning",), default_timeout=60); at.session_state["user"]=demo; at.run()
at.button[0].click().run()
print("learning flow", [e.value[:200] for e in at.exception] or "OK", db.one("SELECT COUNT(*) n FROM roadmap WHERE user_id=?", (demo['id'],)))
