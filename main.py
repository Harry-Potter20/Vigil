import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    Full Vigil pipeline — parallel where possible.
    Phase 1: paperclip safety + trials + velocity + scraping + clinician all concurrent.
    Phase 2: extract signals (needs phase 1 corpus).
    Phase 3: crossref + scorecard concurrent (needs phase 2 signals).
    Returns: (DrugWatchResult, at_risk_trials, velocity_data, scorecard, ClinicianData)
    """
    start = time.time()
    print(f"[Vigil] Starting pipeline for: {drug_name}", flush=True)

    # Phase 1 — all independent fetches in parallel
    print("[Phase 1] Paperclip + scrapers + velocity + clinician (parallel)...", flush=True)
    with ThreadPoolExecutor(max_workers=6) as ex:
        f_safety    = ex.submit(search_safety_signals, drug_name, 8)
        f_trials    = ex.submit(search_active_trials, drug_name, 15)
        f_velocity  = ex.submit(compute_velocity, drug_name)
        f_scrape    = ex.submit(scrape_live_sources, drug_name)
        f_clinician = ex.submit(get_all_clinician_data, drug_name, drug_list) if run_clinician else None

        paperclip_data  = f_safety.result()
        trials_data     = f_trials.result()
        velocity_data   = f_velocity.result()
        brightdata_data = f_scrape.result()
        doc_count       = get_document_count(paperclip_data)

    # Phase 2 — extraction (needs corpus from phase 1)
    print("[Phase 2] Extracting safety signals...", flush=True)
    signals = extract_signals(drug_name, paperclip_data, brightdata_data)
    print(f"[Phase 2] Extracted {len(signals)} signals", flush=True)

    # Phase 3 — crossref + scorecard in parallel (clinician may already be done)
    print("[Phase 3] Crossref + scorecard (parallel)...", flush=True)
    with ThreadPoolExecutor(max_workers=2) as ex:
        f_crossref  = ex.submit(crossreference_trials, drug_name, signals, trials_data)
        f_scorecard = ex.submit(build_scorecard, drug_name, signals)
        at_risk_trials = f_crossref.result()
        scorecard      = f_scorecard.result()

    clinician_data = f_clinician.result() if f_clinician else ClinicianData()

    duration = round(time.time() - start, 1)
    result = DrugWatchResult(
        drug_name=drug_name,
        signals=signals,
        sources_queried=["FDA", "medRxiv", "PMC", "ClinicalTrials.gov", "WHO", "NAFDAC", "SAHPRA"],
        total_documents_scanned=doc_count,
        query_duration_seconds=duration,
        velocity=velocity_data,
    )

    print(f"[Vigil] Done in {duration}s — {len(signals)} signals, {len(at_risk_trials)} at-risk trials", flush=True)
    return result, at_risk_trials, velocity_data, scorecard, clinician_data


if __name__ == "__main__":
    result, trials, vel, scores, clin = run_vigil("semaglutide")
    for s in result.signals:
        print(f"[{s.severity.upper()}] {s.signal_type} — {s.summary[:80]}")
