import os
import time

try:
    import streamlit as st
    for _key in ["PAPERCLIP_API_KEY", "GROQ_API_KEY", "SCRAPERAPI_KEY"]:
        if _key in st.secrets and _key not in os.environ:
            os.environ[_key] = st.secrets[_key]
except Exception:
    pass

from dotenv import load_dotenv
from agent.paperclip_search import (
    search_safety_signals, search_active_trials, get_document_count,
)
from agent.brightdata_scrape import scrape_live_sources
from agent.extractor import extract_signals, crossreference_trials
from agent.velocity import compute_velocity
from agent.comparator import build_scorecard
from agent.clinician import get_all_clinician_data
from agent.schemas import DrugWatchResult, ClinicianData

load_dotenv()


def run_vigil(
    drug_name: str,
    drug_list: list[str] = None,
    run_clinician: bool = True,
):
    """
    Full Vigil pipeline.
    drug_list: optional list of co-medications for DDI checking.
    Returns: (DrugWatchResult, at_risk_trials, velocity_data, scorecard, ClinicianData)
    """
    start = time.time()
    print(f"[Vigil] Starting pipeline for: {drug_name}")

    # 1. Paperclip — biomedical corpus
    print("[1/6] Querying Paperclip...")
    paperclip_data = search_safety_signals(drug_name, n=8)
    trials_data = search_active_trials(drug_name, n=15)
    doc_count = get_document_count(paperclip_data)

    # 1b. Signal velocity
    print("[1b/6] Computing signal velocity...")
    velocity_data = compute_velocity(drug_name)

    # 2. Bright Data — live web
    print("[2/6] Scraping live sources (WHO, NAFDAC, SAHPRA)...")
    brightdata_data = scrape_live_sources(drug_name)

    # 3. Gemini — extract signals
    print("[3/6] Extracting safety signals...")
    signals = extract_signals(drug_name, paperclip_data, brightdata_data)

    # 4. Gemini — trial cross-reference
    print("[4/6] Cross-referencing trials...")
    at_risk_trials = crossreference_trials(drug_name, signals, trials_data)

    # 5. Scorecard — competing drugs
    print("[5/6] Building safety scorecard...")
    scorecard = build_scorecard(drug_name, signals)

    # 6. Clinician tools
    clinician_data = ClinicianData()
    if run_clinician:
        print("[6/6] Fetching clinician data (DDI, dosing, populations, PGx, Africa)...")
        clinician_data = get_all_clinician_data(drug_name, drug_list)

    duration = round(time.time() - start, 1)

    result = DrugWatchResult(
        drug_name=drug_name,
        signals=signals,
        sources_queried=["FDA", "medRxiv", "PMC", "ClinicalTrials.gov", "WHO", "NAFDAC", "SAHPRA"],
        total_documents_scanned=doc_count,
        query_duration_seconds=duration,
        velocity=velocity_data,
    )

    print(f"[Vigil] Done in {duration}s — {len(signals)} signals, {len(at_risk_trials)} at-risk trials")
    return result, at_risk_trials, velocity_data, scorecard, clinician_data


if __name__ == "__main__":
    result, trials, vel, scores, clin = run_vigil("semaglutide")
    for s in result.signals:
        print(f"[{s.severity.upper()}] {s.signal_type} — {s.summary[:80]}")
