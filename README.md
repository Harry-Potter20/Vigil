# Vigil

**Know before you prescribe.**

Pharmacovigilance intelligence for clinicians — drug safety signals, interactions,
dosing, and Africa formulary status. Any drug. Any patient. Under 60 seconds.

---

## What it does

Type a drug name. Vigil scans 11M+ biomedical papers and live regulatory sources,
then returns:

- **Safety signals** — severity-classified, evidence-rated, source-cited
- **Rising signal detection** — publication velocity tracking (30-day vs 6-month)
- **Trial cross-reference** — active ClinicalTrials.gov studies flagged against signals
- **Safety scorecard** — therapeutic alternatives scored /100
- **Drug-drug interactions** — severity-ranked with mechanism and management
- **Dosage calculator** — patient-specific dose with renal, hepatic, BSA, weight adjustments
- **Special populations** — pregnancy, lactation, geriatric, paediatric flags
- **Pharmacogenomics** — CYP2D6, CYP2C19, HLA-B, TPMT gene-drug interactions
- **Africa formulary** — NAFDAC, SAHPRA, WHO prequalification status
- **PDF clinical brief** — one-click export of all findings

---

## Architecture

```
Paperclip     →  11M+ papers, 225K+ FDA docs, 580K+ trials (semantic search)
ScraperAPI    →  Live: WHO alerts, NAFDAC, SAHPRA
Groq / Llama  →  Signal extraction, DDI, dosing, PGx, Africa formulary
Streamlit     →  Editorial UI — dark/light mode, 8-tab dashboard
fpdf2         →  PDF clinical brief export
```

---

## Quickstart

```bash
git clone https://github.com/Harry-Potter20/vigil
cd vigil
pip install -r requirements.txt
cp .env.example .env
# Add your keys: PAPERCLIP_API_KEY, GROQ_API_KEY, SCRAPERAPI_KEY
streamlit run ui/app.py
```

---

## Demo

**Try it live:** [vigil.streamlit.app](https://vigil.streamlit.app)

**Demo search:** `semaglutide` + co-medication `warfarin`

- 3 critical signals including thyroid C-cell tumour (rising signal — medRxiv x3.5)
- 12 active trials flagged, 3 marked immediate review
- Tirzepatide 70/100 vs semaglutide 55/100
- DDI: delayed absorption, monitor INR
- Renal-adjusted dose for eGFR 22 patient
- NAFDAC registered, WHO prequalified

---

## Built for

- DevNetwork AI/ML Hackathon 2026 (May 28)
- Bright Data Web Data UNLOCKED Hackathon (May 31)

---

## Disclaimer

Vigil is a research and awareness tool. Output does not replace clinical judgment,
formulary guidelines, or consultation with a qualified pharmacist or physician.

---

*Built by TIBA Health · Lagos, Nigeria*
