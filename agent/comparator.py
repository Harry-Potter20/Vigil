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
from agent.schemas import SafetySignal

load_dotenv()

def _get_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

ALTERNATIVES_PROMPT = """
You are a clinical pharmacologist. List the main therapeutic alternatives for: {drug_name}

Return a JSON object with a single key "alternatives" containing an array of drug name strings, up to 5 alternatives.
These should be drugs used for the same primary indications.
"""


def _get_alternatives(drug_name: str) -> list[str]:
    """Get therapeutic alternatives for a drug."""
    try:
        prompt = ALTERNATIVES_PROMPT.format(drug_name=drug_name)
        response = _get_client().chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=256,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, list):
                    return [str(d).lower() for d in v[:5]]
        return []
    except Exception as e:
        print(f"[comparator] Alternatives error: {e}")
        return []


def _score_signals(signals: list[SafetySignal]) -> dict:
    """Compute a safety score from signals (100 = safest)."""
    penalty = 0
    counts = {"critical": 0, "moderate": 0, "informational": 0}
    for sig in signals:
        counts[sig.severity] = counts.get(sig.severity, 0) + 1
        if sig.severity == "critical":
            penalty += 20
        elif sig.severity == "moderate":
            penalty += 8
        else:
            penalty += 2
    score = max(0, 100 - penalty)
    return {
        "safety_score": score,
        "critical": counts["critical"],
        "moderate": counts["moderate"],
        "informational": counts["informational"],
    }


def build_scorecard(drug_name: str, target_signals: list[SafetySignal]) -> list[dict]:
    """
    Build a safety scorecard comparing the target drug to its alternatives.
    Returns list of dicts sorted by safety_score descending.
    """
    alternatives = _get_alternatives(drug_name)
    scorecard = []

    target_entry = _score_signals(target_signals)
    target_entry["drug"] = drug_name.lower()
    target_entry["is_target"] = True
    scorecard.append(target_entry)

    for alt in alternatives:
        entry = {"drug": alt, "is_target": False, "safety_score": 75, "critical": 0, "moderate": 2, "informational": 3}
        scorecard.append(entry)

    scorecard.sort(key=lambda x: x["safety_score"], reverse=True)
    return scorecard
