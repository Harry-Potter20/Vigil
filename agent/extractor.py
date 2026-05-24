import os
try:
    import streamlit as st
    for _key in ["PAPERCLIP_API_KEY", "GROQ_API_KEY", "SCRAPERAPI_KEY"]:
        if _key in st.secrets and _key not in os.environ:
            os.environ[_key] = st.secrets[_key]
except Exception:
    pass

import json
from groq import Groq
from dotenv import load_dotenv
from prompts.extraction import EXTRACTION_PROMPT, TRIAL_CROSSREF_PROMPT
from agent.schemas import SafetySignal

load_dotenv()

def _get_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.1-8b-instant"


def _call(prompt: str) -> str:
    """Call Groq and return raw response text."""
    response = _get_client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=2048,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


def _parse_list(raw: str) -> list:
    """Parse JSON response, unwrapping to a list."""
    data = json.loads(raw)
    if isinstance(data, list):
        return data
    for v in data.values():
        if isinstance(v, list):
            return v
    return []


def extract_signals(
    drug_name: str,
    paperclip_data: dict,
    brightdata_data: dict,
) -> list[SafetySignal]:
    """Extract and classify safety signals from all sources."""
    context_blocks = []

    # paperclip_data is a list of result dicts
    if isinstance(paperclip_data, list):
        for item in paperclip_data[:5]:
            if isinstance(item, dict):
                title = item.get("title", "")
                abstract = item.get("abstract", item.get("content", ""))[:400]
                source = item.get("source", "paperclip")
                context_blocks.append(f"SOURCE: {source} | {title}\n{abstract}")
    elif isinstance(paperclip_data, dict):
        for source, data in paperclip_data.items():
            if isinstance(data, dict) and "raw_text" in data:
                context_blocks.append(f"=== {source.upper()} ===\n{data['raw_text'][:1500]}")
            elif isinstance(data, list):
                for item in data[:3]:
                    title = item.get("title", "")
                    abstract = item.get("abstract", item.get("content", ""))[:400]
                    context_blocks.append(f"SOURCE: {source} | {title}\n{abstract}")

    for source_name, data in brightdata_data.items():
        if data.get("relevant") and data.get("content"):
            context_blocks.append(
                f"=== LIVE: {source_name.upper()} ===\n{data['content'][:1200]}"
            )

    if not context_blocks:
        prompt = (
            EXTRACTION_PROMPT.format(drug_name=drug_name)
            + "\n\nNo real-time corpus data was retrieved. Use your clinical "
            "pharmacology training knowledge to identify the most important known "
            "safety signals for this drug — key adverse events, contraindications, "
            "drug interactions, and warnings. Set source_name to 'Training knowledge' "
            "and credibility to 'peer_reviewed' for well-established signals, "
            "'regulatory' only for documented FDA/EMA actions."
        )
    else:
        combined = "\n\n".join(context_blocks)
        prompt = (
            EXTRACTION_PROMPT.format(drug_name=drug_name)
            + f"\n\n--- DOCUMENTS ---\n{combined}"
        )

    try:
        raw = _call(prompt)
        signals_data = _parse_list(raw)
        return [
            SafetySignal(**{**s, "drug_name": drug_name})
            for s in signals_data
            if isinstance(s, dict)
        ]
    except Exception as e:
        print(f"[extractor] error: {e}")
        return []


def crossreference_trials(
    drug_name: str,
    signals: list[SafetySignal],
    trials_data: dict,
) -> list[dict]:
    """Cross-reference signals against active clinical trials."""
    if not signals or not trials_data:
        return []

    signals_text = json.dumps([s.model_dump() for s in signals], indent=2)
    raw_trials = (
        trials_data if isinstance(trials_data, list)
        else trials_data.get("results", [])
    )
    trial_list = [
        {
            "id": t.get("id", t.get("nct_id", "unknown")),
            "title": t.get("title", "")[:200],
            "status": t.get("status", ""),
            "conditions": t.get("conditions", ""),
        }
        for t in raw_trials[:20]
    ]

    if not trial_list:
        return []

    prompt = (
        TRIAL_CROSSREF_PROMPT.format(drug_name=drug_name)
        + f"\n\nSAFETY SIGNALS:\n{signals_text}"
        + f"\n\nACTIVE TRIALS:\n{json.dumps(trial_list, indent=2)}"
    )

    try:
        raw = _call(prompt)
        result = _parse_list(raw)
        return result if isinstance(result, list) else []
    except Exception as e:
        print(f"[crossref] error: {e}")
        return []
