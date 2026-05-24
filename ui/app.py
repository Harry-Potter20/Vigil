import sys
import os
import base64
import urllib.parse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from main import run_vigil
from agent.export import generate_brief
from agent.drugs import fuzzy_correct, exact_or_closest
from agent.calculator import calculate_dose, calc_bsa, egfr_category, child_pugh_label
from agent.stars import compute_evidence_stars, stars_html


def load_logo_svg() -> str:
    try:
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "vigil_logo.svg")
        with open(logo_path, "r") as f:
            svg = f.read()
        b64 = base64.b64encode(svg.encode()).decode()
        return f'<img src="data:image/svg+xml;base64,{b64}" width="36" height="36" style="vertical-align:middle;margin-right:10px;">'
    except FileNotFoundError:
        return ""

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Vigil",
    page_icon="🕯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Theme constants ───────────────────────────────────────────────────────────
LIGHT = {
    "bg":          "#faf7f2",
    "bg2":         "#f2ede4",
    "border":      "#e8e0d0",
    "ink":         "#1a1612",
    "ink2":        "#5a5144",
    "ink3":        "#9a8f7e",
    "accent":      "#BA7517",
    "crit":        "#c0392b",
    "mod":         "#BA7517",
    "info":        "#185FA5",
    "safe":        "#3B6D11",
    "tag_crit_bg": "#f85149",
    "tag_mod_bg":  "#BA7517",
    "tag_info_bg": "#185FA5",
}

DARK = {
    "bg":          "#0f0e0c",
    "bg2":         "#1a1814",
    "border":      "#2e2b25",
    "ink":         "#f0ebe2",
    "ink2":        "#b0a898",
    "ink3":        "#6e6558",
    "accent":      "#d4953a",
    "crit":        "#f85149",
    "mod":         "#d4953a",
    "info":        "#58a6ff",
    "safe":        "#7bc47a",
    "tag_crit_bg": "#5c1a1a",
    "tag_mod_bg":  "#4a3008",
    "tag_info_bg": "#0d2e4a",
}

# ── Theme toggle ──────────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

T = DARK if st.session_state.dark_mode else LIGHT

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Source+Serif+4:ital,wght@0,300;0,400;0,600;1,400&family=JetBrains+Mono:wght@400;500&display=swap');

  /* Root overrides */
  .stApp {{ background-color: {T['bg']} !important; }}
  .block-container {{ max-width: 1100px; padding-top: 2rem !important; }}
  section[data-testid="stSidebar"] {{ display: none; }}

  /* Typography */
  html, body, [class*="css"] {{
    font-family: 'Source Serif 4', Georgia, serif !important;
    color: {T['ink']} !important;
  }}

  /* Header */
  .vigil-masthead {{
    border-bottom: 2px solid {T['ink']};
    padding-bottom: 0.6rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: baseline;
    justify-content: space-between;
  }}
  .vigil-logo {{
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: {T['ink']};
    letter-spacing: -0.03em;
    line-height: 1;
  }}
  .vigil-tagline {{
    font-family: 'Source Serif 4', serif;
    font-size: 0.7rem;
    color: {T['ink3']};
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-style: italic;
  }}

  /* Search bar */
  .stTextInput input {{
    background: {T['bg2']} !important;
    border: 1.5px solid {T['ink']} !important;
    border-radius: 0 !important;
    color: {T['ink']} !important;
    font-family: 'Source Serif 4', serif !important;
    font-size: 1rem !important;
    padding: 0.6rem 1rem !important;
  }}
  .stTextInput input:focus {{
    box-shadow: none !important;
    border-color: {T['accent']} !important;
  }}

  /* Buttons */
  .stButton button {{
    background: {T['ink']} !important;
    color: {T['bg']} !important;
    border: none !important;
    border-radius: 0 !important;
    font-family: 'Source Serif 4', serif !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    padding: 0.6rem 1.4rem !important;
  }}
  .stButton button:hover {{
    background: {T['accent']} !important;
  }}

  /* Metric cards */
  [data-testid="stMetric"] {{
    background: {T['bg2']};
    border: 0.5px solid {T['border']};
    padding: 0.9rem 1rem;
  }}
  [data-testid="stMetricLabel"] {{
    font-family: 'Source Serif 4', serif !important;
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: {T['ink3']} !important;
  }}
  [data-testid="stMetricValue"] {{
    font-family: 'Playfair Display', serif !important;
    font-size: 1.6rem !important;
    color: {T['ink']} !important;
  }}

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {{
    border-bottom: 1.5px solid {T['border']};
    gap: 0;
    background: transparent;
  }}
  .stTabs [data-baseweb="tab"] {{
    font-family: 'Source Serif 4', serif !important;
    font-size: 0.8rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: {T['ink3']} !important;
    border-radius: 0 !important;
    padding: 0.5rem 1rem !important;
    border-bottom: 2px solid transparent !important;
    white-space: nowrap !important;
  }}
  .stTabs [aria-selected="true"] {{
    color: {T['ink']} !important;
    border-bottom: 2px solid {T['ink']} !important;
    font-weight: 600 !important;
  }}

  /* Expanders */
  .streamlit-expanderHeader {{
    font-family: 'Source Serif 4', serif !important;
    font-size: 0.9rem !important;
    color: {T['ink']} !important;
    border-bottom: 0.5px solid {T['border']} !important;
    border-radius: 0 !important;
    background: transparent !important;
    padding: 0.6rem 0 !important;
  }}
  .streamlit-expanderContent {{
    border: none !important;
    border-left: 2px solid {T['border']} !important;
    padding-left: 1rem !important;
    margin-left: 0 !important;
  }}

  /* Tags */
  .vig-tag {{
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 2px 7px;
    border-radius: 2px;
    margin-right: 6px;
  }}
  .vig-tag-crit {{ background: {T['tag_crit_bg']}; color: #fff; }}
  .vig-tag-mod  {{ background: {T['tag_mod_bg']};  color: #fff; }}
  .vig-tag-info {{ background: {T['tag_info_bg']}; color: #fff; }}
  .vig-tag-safe {{ background: {T['safe']}; color: #fff; }}
  .vig-tag-contra {{ background: {T['crit']}; color: #fff; }}
  .vig-tag-major  {{ background: {T['mod']};  color: #fff; }}

  /* Signal rows */
  .sig-row {{
    border-bottom: 0.5px solid {T['border']};
    padding: 0.75rem 0;
  }}
  .sig-row:last-child {{ border-bottom: none; }}
  .sig-title {{
    font-family: 'Playfair Display', serif;
    font-size: 0.95rem;
    font-weight: 700;
    color: {T['ink']};
  }}
  .sig-body {{
    font-size: 0.85rem;
    color: {T['ink2']};
    line-height: 1.6;
    margin-top: 0.2rem;
  }}
  .sig-src {{
    font-size: 0.75rem;
    color: {T['ink3']};
    font-style: italic;
    margin-top: 0.25rem;
  }}
  .sig-action {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: {T['safe']};
    margin-top: 0.3rem;
  }}

  /* Rising alert */
  .rising-banner {{
    background: {T['accent']};
    padding: 0.6rem 1rem;
    margin-bottom: 1.2rem;
    font-family: 'Source Serif 4', serif;
    font-size: 0.85rem;
    font-style: italic;
    color: #fff;
  }}

  /* Scorecard bars */
  .score-row {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0.4rem 0;
    border-bottom: 0.5px solid {T['border']};
  }}
  .score-name {{
    font-family: 'Source Serif 4', serif;
    font-size: 0.85rem;
    color: {T['ink']};
    min-width: 160px;
  }}
  .score-bar-bg {{
    flex: 1;
    height: 4px;
    background: {T['border']};
    border-radius: 2px;
  }}
  .score-val {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    font-weight: 500;
    color: {T['ink']};
    min-width: 36px;
    text-align: right;
  }}

  /* Divider */
  .vig-divider {{
    border: none;
    border-top: 1.5px solid {T['ink']};
    margin: 1.5rem 0 1rem;
  }}
  .vig-section-label {{
    font-family: 'Source Serif 4', serif;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: {T['ink3']};
    margin-bottom: 0.75rem;
    border-bottom: 0.5px solid {T['border']};
    padding-bottom: 0.4rem;
  }}

  /* Dosing cards */
  .dose-card {{
    border: 0.5px solid {T['border']};
    padding: 0.9rem 1rem;
    margin-bottom: 0.6rem;
  }}
  .dose-indication {{
    font-family: 'Playfair Display', serif;
    font-size: 0.9rem;
    font-weight: 700;
    color: {T['ink']};
    margin-bottom: 0.4rem;
  }}
  .dose-row {{
    display: flex;
    gap: 8px;
    font-size: 0.82rem;
    color: {T['ink2']};
    margin-bottom: 0.2rem;
  }}
  .dose-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: {T['ink3']};
    min-width: 120px;
  }}
  .dose-val {{ color: {T['ink']}; }}

  /* DDI cards */
  .ddi-card {{
    border-left: 3px solid {T['border']};
    padding: 0.6rem 0.9rem;
    margin-bottom: 0.8rem;
  }}
  .ddi-card.contra {{ border-left-color: {T['crit']}; }}
  .ddi-card.major  {{ border-left-color: {T['mod']};  }}
  .ddi-card.moderate {{ border-left-color: {T['info']}; }}
  .ddi-card.minor  {{ border-left-color: {T['safe']}; }}
  .ddi-drugs {{
    font-family: 'Playfair Display', serif;
    font-size: 0.9rem;
    font-weight: 700;
    color: {T['ink']};
    margin-bottom: 0.3rem;
  }}

  /* Population flags */
  .pop-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.6rem;
  }}
  .pop-card {{
    border: 0.5px solid {T['border']};
    padding: 0.7rem 0.9rem;
  }}
  .pop-label {{
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: {T['ink3']};
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 0.3rem;
  }}
  .pop-val {{
    font-size: 0.85rem;
    color: {T['ink']};
    line-height: 1.5;
  }}

  /* Africa formulary */
  .africa-row {{
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 0.5rem 0;
    border-bottom: 0.5px solid {T['border']};
    font-size: 0.85rem;
  }}
  .africa-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: {T['ink3']};
    min-width: 150px;
  }}
  .africa-val {{ color: {T['ink']}; }}

  /* PGx */
  .pgx-card {{
    border: 0.5px solid {T['border']};
    padding: 0.7rem 0.9rem;
    margin-bottom: 0.5rem;
  }}
  .pgx-gene {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    font-weight: 500;
    color: {T['info']};
    margin-bottom: 0.25rem;
  }}

  /* Footer */
  .vig-footer {{
    border-top: 1px solid {T['border']};
    margin-top: 2rem;
    padding-top: 0.75rem;
    font-size: 0.72rem;
    color: {T['ink3']};
    font-style: italic;
    text-align: center;
  }}

  /* Mobile tab sizing */
  @media (max-width: 768px) {{
    .stTabs [data-baseweb="tab"] {{
      font-size: 0.7rem !important;
      padding: 0.5rem 0.6rem !important;
      letter-spacing: 0.04em !important;
    }}
  }}

  /* Hide Streamlit default elements */
  #MainMenu, footer, header {{ visibility: hidden; }}
  .stDeployButton {{ display: none; }}
</style>
""", unsafe_allow_html=True)

# ── Secrets health-check (shows a clear error instead of cryptic crash) ───────
_missing_keys = [k for k in ["GROQ_API_KEY", "PAPERCLIP_API_KEY"] if not os.getenv(k)]
if _missing_keys:
    st.error(
        f"**Configuration error** — the following API keys are not set: "
        f"`{'`, `'.join(_missing_keys)}`\n\n"
        f"In Streamlit Cloud: go to your app → **Settings → Secrets** and add:\n"
        f"```\nGROQ_API_KEY = \"gsk_...\"\nPAPERCLIP_API_KEY = \"...\"\nSCRAPERAPI_KEY = \"...\"\n```",
        icon="🔑",
    )

# ── Cold start splash ─────────────────────────────────────────────────────────
import time as _time

VIGIL_STATS = [
    "ADRs cause 6.5% of hospital admissions. Most are preventable.",
    "Over 50% of medicines in some African markets are substandard or falsified.",
    "The average clinician checks 4-6 sources to verify a drug interaction.",
    "Only 1 in 10 adverse drug reactions is ever reported to regulators.",
    "Pharmacovigilance data from Africa represents less than 2% of global reports.",
]

if "app_loaded" not in st.session_state:
    splash = st.empty()
    stat = VIGIL_STATS[int(_time.time()) % len(VIGIL_STATS)]
    splash.markdown(f"""
    <div style="
        position:fixed;top:0;left:0;width:100vw;height:100vh;
        background:{T['bg']};
        display:flex;flex-direction:column;
        align-items:center;justify-content:center;
        z-index:9999;
    ">
      <div style="
          font-family:'Playfair Display',Georgia,serif;
          font-size:2.5rem;font-weight:700;
          color:{T['ink']};letter-spacing:-0.03em;
          margin-bottom:0.5rem;
      ">Vigil</div>
      <div style="
          font-family:'Source Serif 4',serif;
          font-size:0.7rem;text-transform:uppercase;
          letter-spacing:0.12em;color:{T['ink3']};
          font-style:italic;margin-bottom:3rem;
      ">Pharmacovigilance Intelligence</div>
      <div style="
          max-width:480px;text-align:center;
          font-family:'Source Serif 4',serif;
          font-size:1.05rem;color:{T['ink2']};
          font-style:italic;line-height:1.7;
          border-top:0.5px solid {T['border']};
          border-bottom:0.5px solid {T['border']};
          padding:1.25rem 2rem;
      ">{stat}</div>
      <div style="
          margin-top:2rem;
          font-family:'JetBrains Mono',monospace;
          font-size:0.7rem;color:{T['ink3']};
          text-transform:uppercase;letter-spacing:0.1em;
      ">Loading...</div>
    </div>
    """, unsafe_allow_html=True)
    _time.sleep(1.5)
    splash.empty()
    st.session_state["app_loaded"] = True

# ── Header ────────────────────────────────────────────────────────────────────
logo_img = load_logo_svg()
top_left, top_right = st.columns([6, 1])
with top_left:
    st.markdown(f"""
    <div class="vigil-masthead">
      <div style="display:flex;align-items:center;">
        {logo_img}
        <div>
          <div class="vigil-logo">Vigil</div>
          <div class="vigil-tagline">Pharmacovigilance Intelligence</div>
        </div>
      </div>
      <div class="vigil-tagline" style="text-align:right;">
        FDA &middot; medRxiv &middot; PMC &middot; ClinicalTrials.gov &middot; WHO &middot; NAFDAC &middot; SAHPRA
      </div>
    </div>
    """, unsafe_allow_html=True)
with top_right:
    mode_label = "☀ Light" if st.session_state.dark_mode else "☾ Dark"
    if st.button(mode_label, key="theme_toggle"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

# ── Read query params on load ─────────────────────────────────────────────────
params = st.query_params
prefilled_drug = params.get("drug", "")
prefilled_comeds = params.get("comeds", "")

# ── Search ────────────────────────────────────────────────────────────────────
# Transfer pending autocomplete value into the widget's session-state key
# BEFORE the widget renders — this is the only reliable way to set a keyed
# text input's value programmatically without triggering the "modified after
# instantiation" error.
if "_drug_pending" in st.session_state:
    st.session_state["drug_search"] = st.session_state.pop("_drug_pending")
elif "drug_search" not in st.session_state and prefilled_drug:
    st.session_state["drug_search"] = prefilled_drug

c1, c2 = st.columns([4, 1])
with c1:
    drug_input = st.text_input(
        "drug",
        key="drug_search",
        placeholder="e.g.  semaglutide,  artemether-lumefantrine,  metformin",
        label_visibility="collapsed",
    )
with c2:
    run = st.button("Scan →", use_container_width=True)

# ── Autocomplete suggestions ──────────────────────────────────────────────────
if drug_input and len(drug_input) >= 2:
    suggestions = fuzzy_correct(drug_input, n=5)
    if suggestions and drug_input.lower().strip() not in suggestions:
        st.markdown(
            f"<div style='font-size:0.75rem;color:{T['ink3']};font-style:italic;"
            f"margin-top:-0.5rem;margin-bottom:0.5rem;font-family:\"Source Serif 4\",serif;'>"
            f"Suggestions: </div>",
            unsafe_allow_html=True,
        )
        sug_cols = st.columns(len(suggestions))
        for col, sug in zip(sug_cols, suggestions):
            with col:
                if st.button(sug, key=f"sug_{sug}"):
                    st.session_state["_drug_pending"] = sug
                    st.rerun()

# ── Fuzzy correction on run ───────────────────────────────────────────────────
drug_name = ""
correction_applied = False

if drug_input:
    corrected = exact_or_closest(drug_input.strip())
    if corrected != drug_input.lower().strip():
        correction_applied = True
    drug_name = corrected

if correction_applied and drug_name:
    st.markdown(
        f"<div style='font-size:0.78rem;color:{T['accent']};font-style:italic;"
        f"margin-bottom:0.5rem;font-family:\"Source Serif 4\",serif;'>"
        f"&#9998; Searching for <b>{drug_name}</b> &mdash; closest match to \"{drug_input}\"</div>",
        unsafe_allow_html=True,
    )

# DDI input
with st.expander("Add co-medications for drug interaction check (optional)"):
    drug_list_raw = st.text_input(
        "co-meds",
        placeholder="e.g.  warfarin, lisinopril, atorvastatin",
        label_visibility="collapsed",
    )
    drug_list = (
        [exact_or_closest(d.strip()) for d in drug_list_raw.split(",") if d.strip()]
        if drug_list_raw else []
    )
    if drug_name:
        drug_list = list({drug_name.lower()} | {d.lower() for d in drug_list})

# ── Run pipeline ──────────────────────────────────────────────────────────────
if run and drug_name:
    if _missing_keys:
        st.error("Cannot run scan — API keys are not configured. See the error above.")
    else:
        try:
            with st.spinner(f"Scanning FDA · medRxiv · PMC · WHO · NAFDAC · SAHPRA for {drug_name}..."):
                result, at_risk_trials, velocity_data, scorecard, clinician_data = run_vigil(
                    drug_name,
                    drug_list=drug_list if len(drug_list) >= 2 else None,
                )
            st.session_state["vigil_result"] = result
            st.session_state["vigil_trials"] = at_risk_trials
            st.session_state["vigil_velocity"] = velocity_data
            st.session_state["vigil_scorecard"] = scorecard
            st.session_state["vigil_clinician"] = clinician_data
        except Exception as _exc:
            st.error(f"Scan failed: {_exc}")
            st.info("Check that GROQ_API_KEY, PAPERCLIP_API_KEY, and SCRAPERAPI_KEY are set in Streamlit Cloud → Settings → Secrets.")

elif run and not drug_name:
    st.warning("Enter a drug name.")

# ── Results ───────────────────────────────────────────────────────────────────
if "vigil_result" in st.session_state:
    result         = st.session_state["vigil_result"]
    at_risk_trials = st.session_state["vigil_trials"]
    velocity_data  = st.session_state["vigil_velocity"]
    scorecard      = st.session_state["vigil_scorecard"]
    clinician_data = st.session_state["vigil_clinician"]

    # ── Metrics ───────────────────────────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)
    safety_score = scorecard[0]["safety_score"] if scorecard else "—"
    m1.metric("Signals", len(result.signals))
    m2.metric("Docs scanned", result.total_documents_scanned)
    m3.metric("At-risk trials", len(at_risk_trials))
    m4.metric("Safety score", f"{safety_score}/100")
    m5.metric("Scan time", f"{result.query_duration_seconds}s")

    # ── Share button ──────────────────────────────────────────────
    base_url = "https://vigil.streamlit.app"
    drug_encoded = urllib.parse.quote(result.drug_name)
    comeds_encoded = urllib.parse.quote(",".join(drug_list)) if drug_list else ""
    share_url = f"{base_url}?drug={drug_encoded}" + (f"&comeds={comeds_encoded}" if comeds_encoded else "")
    st.markdown(
        f"<div style='margin-bottom:0.75rem;'>"
        f"<a href='{share_url}' target='_blank' style='"
        f"font-family:\"JetBrains Mono\",monospace;"
        f"font-size:0.75rem;color:{T['ink3']};text-decoration:none;"
        f"border-bottom:0.5px solid {T['border']};padding-bottom:1px;'>"
        f"Share this report &rarr;</a></div>",
        unsafe_allow_html=True,
    )

    # ── Rising signal banner ──────────────────────────────────────
    if velocity_data.get("any_rising"):
        rising = ", ".join(velocity_data["rising_sources"]).upper()
        st.markdown(
            f'<div class="rising-banner">&#9889; Rising signal detected — '
            f'publication volume accelerating in: {rising}</div>',
            unsafe_allow_html=True,
        )

    # ── Export button ─────────────────────────────────────────────
    exp_col, _ = st.columns([2, 5])
    with exp_col:
        if st.button("Export clinical brief (PDF)"):
            with st.spinner("Generating brief..."):
                comparison = st.session_state.get("vigil_comparison", None)
                pdf_path = generate_brief(
                    result, clinician_data, velocity_data, scorecard,
                    comparison=comparison,
                )
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="Download PDF",
                    data=f.read(),
                    file_name=f"vigil_{result.drug_name.lower().replace(' ','_')}.pdf",
                    mime="application/pdf",
                )

    # ── Clinical summary card ─────────────────────────────────────
    _sev_order = {"critical": 0, "moderate": 1, "informational": 2}
    _sorted_sigs = sorted(result.signals, key=lambda s: _sev_order.get(s.severity, 3))
    _top_sig = _sorted_sigs[0] if _sorted_sigs else None

    _ddi_order = {"contraindicated": 0, "major": 1, "moderate": 2, "minor": 3}
    _sorted_ddi = sorted(
        clinician_data.interactions,
        key=lambda x: _ddi_order.get(x.severity, 4)
    ) if clinician_data.interactions else []
    _top_ddi = _sorted_ddi[0] if _sorted_ddi else None

    _calc_result = st.session_state.get("vigil_calc_result", None)
    _calc_egfr   = st.session_state.get("vigil_calc_egfr", None)
    _has_renal_adjustment = any(
        d.renal_adjustment for d in clinician_data.dosing
    ) if clinician_data.dosing else False

    if _calc_result and _calc_egfr is not None:
        if _calc_egfr < 60:
            dosing_flag_text  = "Renal adjustment required"
            dosing_flag_color = T['mod']
            dosing_flag_sub   = "Check Dosing tab"
        else:
            dosing_flag_text  = "No adjustment needed"
            dosing_flag_color = T['safe']
            dosing_flag_sub   = f"eGFR {int(_calc_egfr)} mL/min — standard dosing"
    elif not _has_renal_adjustment:
        dosing_flag_text  = "No adjustment flag"
        dosing_flag_color = T['safe']
        dosing_flag_sub   = "Standard dosing"
    else:
        dosing_flag_text  = "Enter patient parameters"
        dosing_flag_color = T['ink3']
        dosing_flag_sub   = "Use Dosing tab calculator"

    _af = clinician_data.africa_formulary
    _formulary_status = (
        "NAFDAC registered" if _af and "registered" in _af.nafdac_status.lower()
        else "NAFDAC status unknown" if _af
        else "Formulary not checked"
    )
    _formulary_color = T['safe'] if _af and "registered" in _af.nafdac_status.lower() else T['mod']

    _sig_color = {"critical": T['crit'], "moderate": T['mod'], "informational": T['info']}.get(
        _top_sig.severity if _top_sig else "", T['ink3']
    )
    _ddi_color = {"contraindicated": T['crit'], "major": T['crit'], "moderate": T['mod'], "minor": T['info']}.get(
        _top_ddi.severity if _top_ddi else "", T['ink3']
    )

    st.markdown(f"""
<div style="
    display:grid;grid-template-columns:repeat(4,1fr);
    gap:1px;background:{T['border']};
    border:1.5px solid {T['ink']};margin-bottom:1.25rem;
">
  <div style="background:{T['bg2']};padding:1rem 1.1rem;">
    <div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;
        text-transform:uppercase;letter-spacing:0.1em;color:{T['ink3']};margin-bottom:0.35rem;">Top signal</div>
    <div style="font-family:'Playfair Display',serif;font-size:0.9rem;
        font-weight:700;color:{_sig_color};line-height:1.3;">{
        _top_sig.signal_type.replace('_',' ').title() if _top_sig else 'None detected'
    }</div>
    <div style="font-size:0.75rem;color:{T['ink2']};margin-top:0.2rem;">{
        _top_sig.severity.upper() if _top_sig else ''
    }</div>
  </div>
  <div style="background:{T['bg2']};padding:1rem 1.1rem;">
    <div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;
        text-transform:uppercase;letter-spacing:0.1em;color:{T['ink3']};margin-bottom:0.35rem;">Top interaction</div>
    <div style="font-family:'Playfair Display',serif;font-size:0.9rem;
        font-weight:700;color:{_ddi_color};line-height:1.3;">{
        f"{_top_ddi.drug_a.title()} + {_top_ddi.drug_b.title()}" if _top_ddi else 'None detected'
    }</div>
    <div style="font-size:0.75rem;color:{T['ink2']};margin-top:0.2rem;">{
        _top_ddi.severity.upper() if _top_ddi else ''
    }</div>
  </div>
  <div style="background:{T['bg2']};padding:1rem 1.1rem;">
    <div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;
        text-transform:uppercase;letter-spacing:0.1em;color:{T['ink3']};margin-bottom:0.35rem;">Dosing flag</div>
    <div style="font-family:'Playfair Display',serif;font-size:0.9rem;
        font-weight:700;color:{dosing_flag_color};line-height:1.3;">{dosing_flag_text}</div>
    <div style="font-size:0.75rem;color:{T['ink2']};margin-top:0.2rem;">{dosing_flag_sub}</div>
  </div>
  <div style="background:{T['bg2']};padding:1rem 1.1rem;">
    <div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;
        text-transform:uppercase;letter-spacing:0.1em;color:{T['ink3']};margin-bottom:0.35rem;">Africa formulary</div>
    <div style="font-family:'Playfair Display',serif;font-size:0.9rem;
        font-weight:700;color:{_formulary_color};line-height:1.3;">{_formulary_status}</div>
    <div style="font-size:0.75rem;color:{T['ink2']};margin-top:0.2rem;">{
        'WHO prequalified' if _af and _af.who_prequalified else 'See formulary tab'
    }</div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("<hr class='vig-divider'>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────
    tabs = st.tabs([
        "Signals",
        "Trials",
        "Alternatives",
        "Compare",
        "DDI",
        "Dosing",
        "Populations",
        "PGx",
        "Formulary",
    ])

    # ── TAB 1: Safety Signals ─────────────────────────────────────
    with tabs[0]:
        severity_order = {"critical": 0, "moderate": 1, "informational": 2}
        sorted_signals = sorted(
            result.signals, key=lambda s: severity_order.get(s.severity, 3)
        )

        if not sorted_signals:
            st.info("No signals detected across queried sources.")
        else:
            for sig in sorted_signals:
                tag_cls = {"critical": "crit", "moderate": "mod", "informational": "info"}.get(sig.severity, "info")
                _stars = compute_evidence_stars(sig.credibility, sig.date_detected, sig.signal_type)
                st.markdown(f"""
                <div class="sig-row">
                  <div>
                    <span class="vig-tag vig-tag-{tag_cls}">{sig.severity}</span>
                    <span class="vig-tag" style="background:{T['bg2']};color:{T['ink3']};border:0.5px solid {T['border']};">
                      {sig.signal_type.replace('_',' ')}
                    </span>
                    {stars_html(_stars, T['accent'], T['ink3'])}
                    <span class="sig-title">{sig.summary[:80]}</span>
                  </div>
                  <div class="sig-body">{sig.summary}</div>
                  <div class="sig-body"><b>Population:</b> {sig.population_affected}</div>
                  <div class="sig-action">&rarr; {sig.recommended_action}</div>
                  <div class="sig-src">{sig.source_name}{' &middot; ' + sig.date_detected if sig.date_detected else ''} &middot; {sig.credibility.replace('_',' ')}</div>
                </div>
                """, unsafe_allow_html=True)

        # Velocity detail
        if velocity_data:
            st.markdown("<br><div class='vig-section-label'>Signal velocity — 30 days vs 6 months</div>", unsafe_allow_html=True)
            import pandas as pd
            rows = []
            for source, v in velocity_data.get("sources", {}).items():
                rows.append({
                    "Source": source.upper(),
                    "30-day count": v["count_30d"],
                    "6-month count": v["count_6m"],
                    "Velocity": f"{v['velocity_score']}x",
                    "Rising": "Yes" if v["rising"] else "—",
                })
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ── TAB 2: Trials ─────────────────────────────────────────────
    with tabs[1]:
        urgency_order = {"immediate": 0, "review_at_next_meeting": 1, "monitor": 2}
        sorted_trials = sorted(
            at_risk_trials,
            key=lambda t: urgency_order.get(t.get("urgency", "monitor"), 3)
        )
        if not sorted_trials:
            st.info("No active trials flagged for this drug.")
        else:
            st.caption(
                "Active trials currently recruiting patients on this drug that may require "
                "protocol attention based on detected safety signals."
            )
            for trial in sorted_trials:
                urgency = trial.get("urgency", "monitor")
                with st.expander(
                    f"{trial.get('trial_id','—')} · {urgency.replace('_',' ').title()}"
                ):
                    st.markdown(f"**Trial:** {trial.get('trial_title','—')}")
                    st.markdown(f"**Signal type:** {trial.get('signal_type','—')}")
                    st.markdown(f"**Concern:** {trial.get('concern','—')}")

    # ── TAB 3: Alternatives (Scorecard) ───────────────────────────
    with tabs[2]:
        if not scorecard:
            st.info("No therapeutic alternatives found for this drug.")
        else:
            st.markdown("<div class='vig-section-label'>Safety score — 100 minus weighted signal penalty</div>", unsafe_allow_html=True)
            for entry in scorecard:
                name = entry["drug"].title()
                if entry.get("is_target"):
                    name += " ←"
                score = entry["safety_score"]
                bar_color = T['crit'] if score < 50 else T['mod'] if score < 75 else T['safe']
                st.markdown(f"""
                <div class="score-row">
                  <span class="score-name">{name}</span>
                  <div class="score-bar-bg">
                    <div style="width:{score}%;height:4px;border-radius:2px;background:{bar_color};"></div>
                  </div>
                  <span class="score-val">{score}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown(
                "<br><span style='font-size:0.75rem;font-style:italic;color:"
                + T['ink3'] + ";'>Not a substitute for clinical judgment. "
                "Scores reflect detected signal volume and severity only.</span>",
                unsafe_allow_html=True,
            )

    # ── TAB 4: Compare ───────────────────────────────────────────
    with tabs[3]:
        from agent.comparator_vs import run_full_comparison

        st.markdown(
            f"<div class='vig-section-label'>Head-to-head drug comparison</div>",
            unsafe_allow_html=True,
        )

        auto_drug_b = ""
        if scorecard and len(scorecard) >= 2:
            for entry in scorecard:
                if not entry.get("is_target"):
                    auto_drug_b = entry["drug"]
                    break

        comp_c1, comp_c2, comp_c3 = st.columns([2, 2, 2])
        with comp_c1:
            compare_drug_a = st.text_input(
                "Drug A", value=result.drug_name, key="compare_drug_a",
            )
        with comp_c2:
            compare_drug_b = st.text_input(
                "Drug B", value=auto_drug_b,
                placeholder="e.g. tirzepatide", key="compare_drug_b",
            )
        with comp_c3:
            compare_indication = st.text_input(
                "Indication (optional)",
                placeholder="e.g. type 2 diabetes", key="compare_indication",
            )

        if auto_drug_b and compare_drug_b == auto_drug_b:
            st.markdown(
                f"<div style='font-size:0.75rem;font-style:italic;color:{T['ink3']};'>"
                f"Auto-populated from safety scorecard — {result.drug_name} vs "
                f"{auto_drug_b} (top alternative). Edit above to compare any two drugs."
                f"</div>",
                unsafe_allow_html=True,
            )

        compare_run = st.button("Compare →", key="compare_btn")

        if compare_run and compare_drug_a and compare_drug_b:
            indication = compare_indication.strip() or "general"
            with st.spinner(
                f"Comparing {compare_drug_a} vs {compare_drug_b} for {indication}..."
            ):
                comp = run_full_comparison(
                    compare_drug_a.strip().lower(),
                    compare_drug_b.strip().lower(),
                    indication,
                )
            st.session_state["vigil_comparison"] = comp

        if "vigil_comparison" in st.session_state:
            comp = st.session_state["vigil_comparison"]
            drug_a_label = comp.get("drug_a", "Drug A").title()
            drug_b_label = comp.get("drug_b", "Drug B").title()

            # Efficacy
            st.markdown("<hr class='vig-divider'>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='vig-section-label'>Efficacy — "
                f"{comp.get('indication','').title()}</div>",
                unsafe_allow_html=True,
            )
            eff = comp.get("efficacy", {})
            sup = eff.get("superiority", "insufficient_data")
            sup_color = {
                "drug_a": T['safe'], "drug_b": T['info'],
                "comparable": T['ink3'], "insufficient_data": T['ink3'],
            }.get(sup, T['ink3'])
            sup_label = {
                "drug_a": f"{drug_a_label} superior",
                "drug_b": f"{drug_b_label} superior",
                "comparable": "Comparable efficacy",
                "insufficient_data": "Insufficient data",
            }.get(sup, "Unknown")
            st.markdown(
                f"<div style='font-family:\"Playfair Display\",serif;"
                f"font-size:1.1rem;font-weight:700;color:{sup_color};"
                f"margin-bottom:0.5rem;'>{sup_label}</div>"
                f"<div class='sig-body'>{eff.get('superiority_notes','')}</div>",
                unsafe_allow_html=True,
            )
            if eff.get("head_to_head_available"):
                st.markdown(
                    f"<div style='font-size:0.78rem;color:{T['safe']};"
                    f"font-family:\"JetBrains Mono\",monospace;margin:0.5rem 0;'>"
                    f"Direct RCT available</div>"
                    f"<div class='sig-body'>{eff.get('head_to_head_summary','')}</div>",
                    unsafe_allow_html=True,
                )

            eff_c1, eff_c2 = st.columns(2)

            def _render_eff_card(col, label, eff_data, color):
                with col:
                    rows_html = (
                        f"<div class='dose-row'><span class='dose-label'>Primary outcome</span>"
                        f"<span class='dose-val'>{eff_data.get('primary_outcome','—')}</span></div>"
                        + (f"<div class='dose-row'><span class='dose-label'>NNT</span>"
                           f"<span class='dose-val'>{eff_data.get('nnt','—')}</span></div>"
                           if eff_data.get('nnt') else "")
                        + (f"<div class='dose-row'><span class='dose-label'>Response rate</span>"
                           f"<span class='dose-val'>{eff_data.get('response_rate','—')}%</span></div>"
                           if eff_data.get('response_rate') else "")
                        + (f"<div class='dose-row'><span class='dose-label'>Time to effect</span>"
                           f"<span class='dose-val'>{eff_data.get('time_to_effect','—')}</span></div>"
                           if eff_data.get('time_to_effect') else "")
                        + (f"<div class='sig-src'>Key trial: {eff_data.get('key_trial','—')} · "
                           f"Evidence grade: {eff_data.get('evidence_grade','—')}</div>"
                           if eff_data.get('key_trial') else "")
                    )
                    st.markdown(
                        f"<div class='dose-card'>"
                        f"<div class='dose-indication' style='color:{color};'>{label}</div>"
                        f"{rows_html}</div>",
                        unsafe_allow_html=True,
                    )

            _render_eff_card(eff_c1, drug_a_label, eff.get("drug_a_efficacy", {}), T['safe'])
            _render_eff_card(eff_c2, drug_b_label, eff.get("drug_b_efficacy", {}), T['info'])

            # Side effects
            st.markdown("<hr class='vig-divider'>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='vig-section-label'>Side effect profile</div>",
                unsafe_allow_html=True,
            )
            se = comp.get("side_effects", {})
            if se.get("key_differentiator"):
                st.markdown(
                    f"<div class='rising-banner' style='margin-bottom:0.75rem;'>"
                    f"Key difference: {se['key_differentiator']}</div>",
                    unsafe_allow_html=True,
                )
            se_c1, se_c2 = st.columns(2)

            def _render_se_col(col, label, se_list, vs_key, color):
                with col:
                    st.markdown(
                        f"<div style='font-family:\"Playfair Display\",serif;"
                        f"font-size:0.9rem;font-weight:700;color:{color};"
                        f"margin-bottom:0.5rem;'>{label}</div>",
                        unsafe_allow_html=True,
                    )
                    for item in se_list[:6]:
                        freq = f"{item['frequency']}%" if item.get("frequency") else "freq unknown"
                        vs = item.get(vs_key, "unknown")
                        vs_icon = {"higher": "▲", "lower": "▼", "similar": "=", "unknown": "?"}.get(vs, "?")
                        vs_color = {"higher": T['crit'], "lower": T['safe'], "similar": T['ink3'], "unknown": T['ink3']}.get(vs, T['ink3'])
                        sev_cls = {"severe": "crit", "moderate": "mod", "mild": "info"}.get(item.get("severity", "mild"), "info")
                        st.markdown(
                            f"<div class='sig-row'>"
                            f"<span class='vig-tag vig-tag-{sev_cls}'>{item.get('severity','mild')}</span>"
                            f"<span style='font-size:0.85rem;color:{T['ink']};'>{item.get('effect','—')}</span>"
                            f"<span style='float:right;font-family:\"JetBrains Mono\",monospace;"
                            f"font-size:0.75rem;color:{T['ink3']};'>{freq}</span>"
                            f"<div style='font-size:0.75rem;color:{vs_color};"
                            f"font-family:\"JetBrains Mono\",monospace;margin-top:2px;'>"
                            f"{vs_icon} vs other drug</div></div>",
                            unsafe_allow_html=True,
                        )

            _render_se_col(se_c1, drug_a_label, se.get("drug_a_side_effects", []), "vs_drug_b", T['safe'])
            _render_se_col(se_c2, drug_b_label, se.get("drug_b_side_effects", []), "vs_drug_a", T['info'])
            if se.get("shared_side_effects"):
                st.markdown(
                    f"<div style='font-size:0.78rem;color:{T['ink3']};font-style:italic;margin-top:0.5rem;'>"
                    f"Shared: {', '.join(se['shared_side_effects'])}</div>",
                    unsafe_allow_html=True,
                )

            # Guidelines
            st.markdown("<hr class='vig-divider'>", unsafe_allow_html=True)
            st.markdown(f"""
<div style="display:flex;align-items:baseline;justify-content:space-between;
            border-bottom:0.5px solid {T['border']};padding-bottom:0.4rem;
            margin-bottom:0.75rem;">
  <div class='vig-section-label' style="border:none;margin:0;padding:0;">
    Guideline recommendations
  </div>
  <div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;
      color:{T['crit']};text-transform:uppercase;letter-spacing:0.08em;
      background:{T['tag_crit_bg']};padding:2px 8px;border-radius:2px;">
    &#9888; Verify against current published version
  </div>
</div>
""", unsafe_allow_html=True)
            gl = comp.get("guidelines", {})
            preferred = gl.get("preferred_drug", "").title()
            pref_color = (
                T['safe'] if preferred.lower() == drug_a_label.lower()
                else T['info'] if preferred.lower() == drug_b_label.lower()
                else T['ink3']
            )
            if preferred and preferred.lower() not in ["comparable", "indication-dependent", ""]:
                st.markdown(
                    f"<div style='font-family:\"Playfair Display\",serif;"
                    f"font-size:1.1rem;font-weight:700;color:{pref_color};"
                    f"margin-bottom:0.4rem;'>Guidelines prefer: {preferred}</div>",
                    unsafe_allow_html=True,
                )
            elif preferred:
                st.markdown(
                    f"<div style='font-family:\"Playfair Display\",serif;"
                    f"font-size:1rem;font-weight:700;color:{T['ink3']};"
                    f"margin-bottom:0.4rem;'>{preferred}</div>",
                    unsafe_allow_html=True,
                )
            if gl.get("preferred_rationale"):
                st.markdown(f"<div class='sig-body'>{gl['preferred_rationale']}</div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            for gl_name, gl_text in [
                ("WHO", gl.get("who_recommendation")),
                ("NICE", gl.get("nice_recommendation")),
                ("AHA/ACC", gl.get("aha_acc_recommendation")),
                ("ADA", gl.get("ada_recommendation")),
                ("Africa context", gl.get("africa_context")),
            ]:
                if gl_text and isinstance(gl_text, str) and gl_text.lower() not in ["not specified", "not applicable", ""]:
                    st.markdown(
                        f"<div class='africa-row'>"
                        f"<span class='africa-label'>{gl_name}</span>"
                        f"<span class='africa-val'>{gl_text}</span></div>",
                        unsafe_allow_html=True,
                    )
            gl_year = gl.get("last_guideline_update", "unknown")
            st.markdown(f"""
<div style="font-size:0.75rem;color:{T['ink3']};
    margin-top:1rem;border-top:0.5px solid {T['border']};
    padding-top:0.75rem;line-height:1.6;">
  <b style="color:{T['ink2']};">Data sources:</b>
  Efficacy — Paperclip biomedical corpus (PMC + medRxiv, last 3 years) ·
  Guidelines — Groq/Llama-3.3-70b training knowledge
  (approximate cutoff: early 2024, most recent guideline ~{gl_year}) ·
  <b style="color:{T['crit']};">
  Always verify against the current published guideline before clinical use.
  </b>
</div>
""", unsafe_allow_html=True)

        elif compare_run and (not compare_drug_a or not compare_drug_b):
            st.warning("Enter both Drug A and Drug B to run a comparison.")

    # ── TAB 5: Drug-Drug Interactions ─────────────────────────────
    with tabs[4]:
        if not clinician_data.interactions:
            st.info(
                "No co-medications entered, or no significant interactions found. "
                "Add co-medications in the search bar above and re-run."
            )
        else:
            sev_order = {"contraindicated": 0, "major": 1, "moderate": 2, "minor": 3}
            sorted_ix = sorted(
                clinician_data.interactions,
                key=lambda x: sev_order.get(x.severity, 4)
            )
            for ix in sorted_ix:
                tag_cls = {"contraindicated": "contra", "major": "major", "moderate": "mod", "minor": "info"}.get(ix.severity, "info")
                css_cls = ix.severity if ix.severity in ["contraindicated", "major", "moderate", "minor"] else ""
                st.markdown(f"""
                <div class="ddi-card {css_cls}">
                  <div class="ddi-drugs">
                    <span class="vig-tag vig-tag-{tag_cls}">{ix.severity}</span>
                    {ix.drug_a.title()} + {ix.drug_b.title()}
                  </div>
                  <div class="sig-body"><b>Mechanism:</b> {ix.mechanism}</div>
                  <div class="sig-body"><b>Effect:</b> {ix.clinical_effect}</div>
                  <div class="sig-action">&rarr; {ix.management}</div>
                  <div class="sig-src">Evidence: {ix.evidence_level}</div>
                </div>
                """, unsafe_allow_html=True)

    # ── TAB 6: Dosing ─────────────────────────────────────────────
    with tabs[5]:
        if not clinician_data.dosing:
            st.info("No dosing information retrieved.")
        else:
            # ── Static reference doses ────────────────────────────
            st.markdown(
                "<div class='vig-section-label'>Reference doses</div>",
                unsafe_allow_html=True,
            )
            for d in clinician_data.dosing:
                adj_parts = []
                if d.renal_adjustment:
                    adj_parts.append(f"<b>Renal:</b> {d.renal_adjustment}")
                if d.hepatic_adjustment:
                    adj_parts.append(f"<b>Hepatic:</b> {d.hepatic_adjustment}")
                if d.paediatric_dose:
                    adj_parts.append(f"<b>Paediatric:</b> {d.paediatric_dose}")
                if d.max_dose:
                    adj_parts.append(f"<b>Max dose:</b> {d.max_dose}")
                adj_html = "".join(
                    f'<div class="dose-row"><span class="dose-label"></span>'
                    f'<span class="dose-val">{a}</span></div>'
                    for a in adj_parts
                )
                st.markdown(f"""
                <div class="dose-card">
                  <div class="dose-indication">{d.indication}</div>
                  <div class="dose-row">
                    <span class="dose-label">Standard dose</span>
                    <span class="dose-val">{d.standard_dose} &middot; {d.route} &middot; {d.frequency}</span>
                  </div>
                  {adj_html}
                  {'<div class="sig-src">' + d.notes + '</div>' if d.notes else ''}
                </div>
                """, unsafe_allow_html=True)

            # ── Patient-specific calculator ───────────────────────
            st.markdown("<hr class='vig-divider'>", unsafe_allow_html=True)
            st.markdown(
                "<div class='vig-section-label'>Patient-specific dose calculator</div>",
                unsafe_allow_html=True,
            )

            indications = [d.indication for d in clinician_data.dosing]
            selected_indication = st.selectbox("Indication", indications)
            selected_dose_obj = next(
                (d for d in clinician_data.dosing if d.indication == selected_indication),
                clinician_data.dosing[0],
            )

            pc1, pc2, pc3 = st.columns(3)
            with pc1:
                weight_kg = st.number_input(
                    "Weight (kg)", min_value=1.0, max_value=300.0, value=70.0, step=0.5,
                )
                height_cm = st.number_input(
                    "Height (cm)", min_value=30.0, max_value=250.0, value=170.0, step=0.5,
                )
            with pc2:
                age = st.number_input(
                    "Age (years)", min_value=0, max_value=120, value=45, step=1,
                )
                sex = st.selectbox("Sex", ["Male", "Female"], index=0)
            with pc3:
                egfr = st.number_input(
                    "eGFR (mL/min/1.73m²)", min_value=1.0, max_value=150.0, value=90.0, step=1.0,
                )
                child_pugh_score = st.number_input(
                    "Child-Pugh score (5–15)", min_value=5, max_value=15, value=5, step=1,
                )

            bsa = calc_bsa(weight_kg, height_cm)
            st.markdown(
                f"<div style='font-size:0.75rem;color:{T['ink3']};font-family:"
                f"\"JetBrains Mono\",monospace;margin-bottom:0.75rem;'>"
                f"BSA: {bsa} m² (Mosteller) &nbsp;&middot;&nbsp; "
                f"{egfr_category(egfr)} &nbsp;&middot;&nbsp; "
                f"{child_pugh_label(child_pugh_score)}"
                f"</div>",
                unsafe_allow_html=True,
            )

            calc_run = st.button("Calculate dose →", key="calc_btn")

            if calc_run:
                with st.spinner("Computing patient-specific dose..."):
                    calc_result = calculate_dose(
                        drug_name=result.drug_name,
                        indication=selected_indication,
                        standard_dose=selected_dose_obj.standard_dose,
                        route=selected_dose_obj.route,
                        frequency=selected_dose_obj.frequency,
                        weight_kg=weight_kg,
                        height_cm=height_cm,
                        age=int(age),
                        egfr=egfr,
                        child_pugh_score=int(child_pugh_score),
                        sex=sex,
                    )
                st.session_state["vigil_calc_result"] = calc_result
                st.session_state["vigil_calc_egfr"]   = egfr

                if "error" in calc_result:
                    st.error(f"Calculation failed: {calc_result['error']}")
                else:
                    dose_color = T['crit'] if calc_result.get("max_dose_exceeded") else T['safe']
                    st.markdown(f"""
                    <div style="border:1.5px solid {dose_color};padding:1rem 1.2rem;margin-bottom:1rem;">
                      <div style="font-family:'Playfair Display',serif;font-size:1.3rem;
                                  font-weight:700;color:{dose_color};">
                        {calc_result.get('recommended_dose', '&mdash;')}
                      </div>
                      <div style="font-family:'JetBrains Mono',monospace;font-size:0.75rem;
                                  color:{T['ink3']};margin-top:0.25rem;">
                        {calc_result.get('route','&mdash;')} &middot; {calc_result.get('frequency','&mdash;')}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                    applied = []
                    if calc_result.get("renal_adjustment_applied"):   applied.append("Renal")
                    if calc_result.get("hepatic_adjustment_applied"): applied.append("Hepatic")
                    if calc_result.get("bsa_adjustment_applied"):     applied.append("BSA")
                    if calc_result.get("weight_based"):               applied.append("Weight-based")

                    if applied:
                        st.markdown(
                            f"<div style='font-size:0.78rem;color:{T['accent']};margin-bottom:0.5rem;'>"
                            f"Adjustments applied: {', '.join(applied)}</div>",
                            unsafe_allow_html=True,
                        )

                    if calc_result.get("adjustments_explained"):
                        st.markdown(
                            f"<div class='sig-body'>{calc_result['adjustments_explained']}</div>",
                            unsafe_allow_html=True,
                        )

                    warnings = calc_result.get("warnings", [])
                    for w in warnings:
                        st.markdown(
                            f"<div class='rising-banner' style='margin-bottom:4px;"
                            f"padding:0.4rem 0.8rem;font-size:0.8rem;'>&#9888; {w}</div>",
                            unsafe_allow_html=True,
                        )

                    if calc_result.get("max_dose_exceeded") and calc_result.get("max_dose_note"):
                        st.error(f"Max dose: {calc_result['max_dose_note']}")

                    st.markdown(
                        f"<div style='font-size:0.7rem;font-style:italic;color:{T['ink3']};"
                        f"margin-top:1rem;border-top:0.5px solid {T['border']};padding-top:0.5rem;'>"
                        f"Calculated by Groq / Llama-3.3-70b. Always verify against current BNF, "
                        f"SMPC, or local formulary. Not a substitute for clinical judgment.</div>",
                        unsafe_allow_html=True,
                    )

    # ── TAB 7: Special Populations ────────────────────────────────
    with tabs[6]:
        sp = clinician_data.special_populations
        if not sp:
            st.info("No special population data retrieved.")
        else:
            lac_cls = {"safe": "safe", "caution": "mod", "avoid": "crit", "unknown": "info"}.get(sp.lactation_safety, "info")
            st.markdown(f"""
            <div class="pop-grid">
              <div class="pop-card">
                <div class="pop-label">Pregnancy</div>
                <div class="pop-val"><b>{sp.pregnancy_category}</b><br>{sp.pregnancy_notes}</div>
              </div>
              <div class="pop-card">
                <div class="pop-label">Lactation</div>
                <div class="pop-val">
                  <span class="vig-tag vig-tag-{lac_cls}">{sp.lactation_safety}</span><br>
                  {sp.lactation_notes}
                </div>
              </div>
              <div class="pop-card">
                <div class="pop-label">Geriatric (&gt;65)</div>
                <div class="pop-val">{sp.geriatric_precautions}</div>
              </div>
              <div class="pop-card">
                <div class="pop-label">Paediatric</div>
                <div class="pop-val">{sp.paediatric_restriction}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 8: Pharmacogenomics ───────────────────────────────────
    with tabs[7]:
        if not clinician_data.pharmacogenomics:
            st.info("No known pharmacogenomic interactions for this drug.")
        else:
            for pgx in clinician_data.pharmacogenomics:
                ev_cls = {"high": "crit", "moderate": "mod", "low": "info"}.get(pgx.evidence_level, "info")
                st.markdown(f"""
                <div class="pgx-card">
                  <div class="pgx-gene">
                    {pgx.gene} &middot; {pgx.variant}
                    <span class="vig-tag vig-tag-{ev_cls}" style="margin-left:8px;">{pgx.evidence_level} evidence</span>
                  </div>
                  <div class="sig-body"><b>Clinical impact:</b> {pgx.clinical_impact}</div>
                  <div class="sig-action">&rarr; {pgx.recommendation}</div>
                </div>
                """, unsafe_allow_html=True)

    # ── TAB 9: Africa Formulary ───────────────────────────────────
    with tabs[8]:
        af = clinician_data.africa_formulary
        if not af:
            st.info("No Africa formulary data retrieved.")
        else:
            who_tag = "safe" if af.who_prequalified else "crit"
            who_val = "Yes — WHO prequalified" if af.who_prequalified else "Not WHO prequalified"
            st.markdown(f"""
            <div class="africa-row">
              <span class="africa-label">NAFDAC (Nigeria)</span>
              <span class="africa-val">{af.nafdac_status}</span>
            </div>
            <div class="africa-row">
              <span class="africa-label">SAHPRA (South Africa)</span>
              <span class="africa-val">{af.sahpra_status}</span>
            </div>
            <div class="africa-row">
              <span class="africa-label">WHO Prequalification</span>
              <span class="africa-val">
                <span class="vig-tag vig-tag-{who_tag}">{who_val}</span>
              </span>
            </div>
            <div class="africa-row">
              <span class="africa-label">Availability notes</span>
              <span class="africa-val">{af.availability_notes}</span>
            </div>
            """, unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────
    sources = " &middot; ".join(result.sources_queried)
    st.markdown(
        f'<div class="vig-footer">'
        f'Sources: {sources} &middot; Powered by Paperclip &middot; Bright Data &middot; Gemini &middot; '
        f'Not a substitute for clinical judgment'
        f'</div>',
        unsafe_allow_html=True,
    )
