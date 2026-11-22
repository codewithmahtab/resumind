"""Visual system + small HTML components."""
import html

import streamlit as st

CSS = """
/* Hallmark · macrostructure: Workbench (app) · theme: Grid · ink: signal red · tone: utilitarian
 * audience: final-year students + examiners · display: Archivo 800 lowercase · body: Archivo · data: JetBrains Mono */
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;800&family=JetBrains+Mono:wght@400;500&display=swap');
:root{
  --paper: oklch(99% 0.003 255); --paper-2: oklch(97.2% 0.003 255); --paper-3: oklch(94.5% 0.004 255);
  --ink: oklch(16% 0.010 255); --ink-2: oklch(43% 0.012 255); --ink-3: oklch(62% 0.010 255);
  --rule: oklch(90% 0.005 255); --rule-strong: oklch(80% 0.006 255);
  --signal: oklch(55% 0.21 28); --signal-soft: oklch(95% 0.03 28);
  --ok: oklch(50% 0.12 150); --ok-soft: oklch(95% 0.035 150); --warn: oklch(58% 0.13 70); --warn-soft: oklch(95.5% 0.04 80);
  --font-display: 'Archivo', 'Helvetica Neue', Arial, sans-serif; --font-mono: 'JetBrains Mono', Consolas, monospace;
  --radius: 2px;
}
html, body, .stApp, .stApp p, .stApp label, .stApp input, .stApp textarea, .stApp button, .stApp li { font-family: var(--font-display); }
[data-testid="stIconMaterial"], .material-symbols-rounded, span[translate="no"] { font-family: 'Material Symbols Rounded' !important; }
[data-testid="stSidebarNav"]::before { content: "resumind"; display: block; font-family: var(--font-display); font-weight: 800;
  font-size: 1.7rem; letter-spacing: -0.05em; line-height: 1; padding: 0 0 14px 12px; margin: 0 1rem 10px;
  border-left: 10px solid var(--signal); }
html, body { overflow-x: clip; }
.stApp { background: var(--paper); color: var(--ink); }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"], .block-container {
  max-width: 1180px; padding-top: 2.2rem;
}
h1, h2, h3, h4 { font-family: var(--font-display) !important; font-weight: 800 !important; text-transform: lowercase;
  letter-spacing: -0.045em; color: var(--ink) !important; font-style: normal; }
h1 { font-size: clamp(2.4rem, 5vw, 4.2rem) !important; line-height: .95 !important; }
h2 { font-size: 1.9rem !important; } h3 { font-size: 1.35rem !important; letter-spacing: -0.03em; }
p, li, label, .stMarkdown { color: var(--ink); }
button p, button span { color: inherit !important; }
code, .mono { font-family: var(--font-mono) !important; }

/* sidebar */
[data-testid="stSidebar"] { background: var(--paper-2); border-right: 1px solid var(--rule-strong); }
[data-testid="stSidebarNav"] a, [data-testid="stSidebarNavLink"] { border-radius: var(--radius); }
[data-testid="stSidebarNav"] a[aria-current="page"] { background: var(--paper) !important; box-shadow: inset 4px 0 0 var(--signal), inset 0 0 0 1px var(--rule-strong); }
[data-testid="stSidebarNav"] a[aria-current="page"] span { color: var(--ink) !important; font-weight: 700; }
[data-testid="stSidebarNavSeparator"] { border-color: var(--rule-strong); }

/* controls */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button, [data-testid="stBaseButton-secondary"] {
  border-radius: var(--radius); border: 1.5px solid var(--ink); background: var(--paper); color: var(--ink);
  font-weight: 600; transition: background .12s cubic-bezier(.2,.7,.2,1), color .12s; white-space: nowrap; }
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
  background: var(--ink); color: var(--paper); border-color: var(--ink); }
button[kind="primary"], button[kind="primaryFormSubmit"], [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {
  background: var(--signal) !important; border-color: var(--signal) !important; color: #fff !important; }
button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover { background: var(--ink) !important; border-color: var(--ink) !important; }
button:focus-visible { outline: 2px solid var(--signal) !important; outline-offset: 2px; }
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div { border-radius: var(--radius) !important; }
[data-testid="stFileUploaderDropzone"] { border-radius: var(--radius); border: 1.5px dashed var(--rule-strong); background: var(--paper-2); }
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: var(--radius) !important; }
div[data-testid="stExpander"] details { border-radius: var(--radius); }
.stTabs [data-baseweb="tab-list"] { gap: 0; border-bottom: 1.5px solid var(--ink); }
.stTabs [data-baseweb="tab"] { font-weight: 600; text-transform: lowercase; padding: 8px 16px; }
.stTabs [aria-selected="true"] { color: var(--signal) !important; }
.stTabs [data-baseweb="tab-highlight"] { background: var(--signal); height: 3px; }
[data-testid="stMetric"] { border-top: 1.5px solid var(--ink); padding-top: 8px; }
[data-testid="stMetricLabel"] p { font-family: var(--font-mono) !important; font-size: .72rem !important;
  letter-spacing: .06em; text-transform: uppercase; color: var(--ink-2) !important; }
[data-testid="stMetricValue"] { font-weight: 800; letter-spacing: -0.04em; font-variant-numeric: tabular-nums; }
.stProgress > div > div > div > div { background: var(--signal); }
[data-testid="stChatMessage"] { border-radius: var(--radius); }

/* components */
.rm-plate { display: grid; grid-template-columns: minmax(0,1fr) auto; gap: 24px; align-items: end;
  border-bottom: 1.5px solid var(--ink); padding-bottom: 18px; margin-bottom: 22px; }
.rm-plate h1 { margin: 0 !important; padding: 0 !important; overflow-wrap: anywhere; min-width: 0; }
.rm-plate p { color: var(--ink-2); margin: 10px 0 0; max-width: 60ch; font-size: 1.02rem; }
.rm-mark { width: 74px; height: 74px; background: var(--signal); flex: none; }
.rm-mark.circle { border-radius: 50%; } .rm-mark.half { border-radius: 74px 74px 0 0; height: 37px; }
.rm-mark.bar { width: 18px; height: 96px; }
.rm-num { font-family: var(--font-display); font-weight: 800; font-size: clamp(3rem, 5.2vw, 5.6rem); line-height: .85; white-space: nowrap; letter-spacing: -0.06em;
  font-variant-numeric: tabular-nums; color: var(--ink); }
.rm-num small { font-size: 1.1rem; letter-spacing: 0; color: var(--ink-3); font-weight: 500; }
.rm-lbl { font-family: var(--font-mono); font-size: .72rem; letter-spacing: .06em; text-transform: uppercase; color: var(--ink-2); }
.rm-chip { display: inline-block; font-size: .8rem; padding: 2px 9px; margin: 0 4px 6px 0; border: 1px solid var(--rule-strong);
  border-radius: var(--radius); background: var(--paper); white-space: nowrap; font-weight: 500; }
.rm-chip.ok { background: var(--ok-soft); border-color: transparent; color: var(--ok); }
.rm-chip.bad { background: var(--signal-soft); border-color: transparent; color: var(--signal); }
.rm-chip.warn { background: var(--warn-soft); border-color: transparent; color: var(--warn); }
.rm-row { display: grid; grid-template-columns: minmax(4.5rem, 7.5rem) minmax(3rem,1fr) 2.4rem; gap: 12px; align-items: center; margin: 7px 0; font-size: .9rem; }
.rm-bar { height: 8px; background: var(--paper-3); }
.rm-bar > b { display: block; height: 100%; background: var(--ink); }
.rm-bar.hi > b { background: var(--ok); } .rm-bar.lo > b { background: var(--signal); }
.rm-row .v { font-family: var(--font-mono); text-align: right; font-variant-numeric: tabular-nums; }
.rm-doc { background: var(--paper); border: 1px solid var(--rule-strong); padding: 22px 24px; font-size: .86rem; line-height: 1.6;
  max-height: 560px; overflow-y: auto; white-space: pre-wrap; color: var(--ink-2); }
.rm-doc mark.bad { background: var(--signal-soft); color: var(--signal); padding: 0 2px; }
.rm-doc mark.warn { background: var(--warn-soft); color: var(--warn); padding: 0 2px; }
.rm-doc mark.good { background: var(--ok-soft); color: var(--ok); padding: 0 2px; }
.rm-issue { border-left: 4px solid var(--signal); padding: 8px 12px; background: var(--paper-2); margin-bottom: 8px; font-size: .9rem; }
.rm-issue.warn { border-left-color: var(--warn); }
.rm-issue b { display: block; }
.rm-issue i { font-style: normal; color: var(--ink-2); display: block; font-size: .82rem; margin-top: 2px; }
.rm-q { font-size: 1.55rem; font-weight: 600; letter-spacing: -0.02em; line-height: 1.25; margin: 6px 0 4px; }
.rm-week { display: grid; grid-template-columns: 4.5rem minmax(0,1fr); gap: 14px; padding: 12px 0; border-top: 1px solid var(--rule-strong); }
.rm-week .wk { font-family: var(--font-mono); font-size: .8rem; color: var(--ink-3); padding-top: 3px; }
.rm-week.now .wk { color: var(--signal); font-weight: 500; }
.rm-week.done b { text-decoration: line-through; color: var(--ink-3); }
.rm-hero-login h1 { font-size: clamp(3rem, 8vw, 6.4rem) !important; }
@media (max-width: 640px) { .rm-plate { grid-template-columns: 1fr; } .rm-mark { display: none; } .rm-num { font-size: 4rem; }
  .rm-row { grid-template-columns: 7rem minmax(0,1fr) 2.4rem; } }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
"""


def inject():
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def e(s):
    return html.escape(str(s))


def plate(title, sub="", mark="square"):
    st.markdown(f'<div class="rm-plate"><div><h1>{e(title)}</h1>{f"<p>{e(sub)}</p>" if sub else ""}</div>'
                f'<div class="rm-mark {mark}"></div></div>', unsafe_allow_html=True)


def chips(items, kind=""):
    if not items:
        return st.markdown('<span class="rm-lbl">none</span>', unsafe_allow_html=True)
    st.markdown("".join(f'<span class="rm-chip {kind}">{e(i)}</span>' for i in items), unsafe_allow_html=True)


def bars(d):
    rows = []
    for k, v in d.items():
        cls = "hi" if v >= 75 else "lo" if v < 50 else ""
        rows.append(f'<div class="rm-row"><span>{e(k)}</span><div class="rm-bar {cls}"><b style="width:{max(0, min(100, v))}%"></b></div>'
                    f'<span class="v">{round(v)}</span></div>')
    st.markdown("".join(rows), unsafe_allow_html=True)


def bignum(value, label, unit=""):
    st.markdown(f'<div class="rm-lbl">{e(label)}</div><div class="rm-num">{e(value)}<small>{e(unit)}</small></div>',
                unsafe_allow_html=True)


def label(text):
    st.markdown(f'<div class="rm-lbl" style="margin:14px 0 6px">{e(text)}</div>', unsafe_allow_html=True)
