import os
try:
    import streamlit as st
    for _key in ["PAPERCLIP_API_KEY", "GROQ_API_KEY", "SCRAPERAPI_KEY"]:
        if _key in st.secrets and _key not in os.environ:
            os.environ[_key] = st.secrets[_key]
except Exception:
    pass

import json
import math
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def _get_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


# ── Patient parameter calculations ───────────────────────────────────────────

def calc_bsa(weight_kg: float, height_cm: float) -> float:
    """Mosteller formula: BSA (m2) = sqrt(height_cm x weight_kg / 3600)"""
    return round(math.sqrt((height_cm * weight_kg) / 3600), 2)


def egfr_category(egfr: float) -> str:
    """CKD staging from eGFR (mL/min/1.73m2)"""
    if egfr >= 90:  return "G1 - Normal (>=90)"
    if egfr >= 60:  return "G2 - Mildly reduced (60-89)"
    if egfr >= 45:  return "G3a - Mildly-moderately reduced (45-59)"
    if egfr >= 30:  return "G3b - Moderately-severely reduced (30-44)"
    if egfr >= 15:  return "G4 - Severely reduced (15-29)"
    return          "G5 - Kidney failure (<15)"


def child_pugh_label(score: int) -> str:
    if score <= 6:  return f"Class A (score {score}) - Well-compensated"
    if score <= 9:  return f"Class B (score {score}) - Significant dysfunction"
    return          f"Class C (score {score}) - Decompensated"


# ── Groq dynamic dose calculation ─────────────────────────────────────────────

CALCULATOR_PROMPT = """
You are a clinical pharmacologist computing a patient-specific drug dose.

Drug: {drug_name}
Indication: {indication}
Standard dose from literature: {standard_dose} {route} {frequency}

Patient parameters:
- Weight: {weight_kg} kg
- Age: {age} years
- Height: {height_cm} cm
- BSA: {bsa} m2 (Mosteller)
- eGFR: {egfr} mL/min/1.73m2 ({egfr_category})
- Hepatic function: Child-Pugh {child_pugh_label}
- Sex: {sex}

Compute the adjusted dose for this specific patient. Return a JSON object with:
- recommended_dose: the computed dose with units (e.g. "850mg", "0.5mg/kg = 37.5mg")
- route: route of administration
- frequency: dosing frequency
- renal_adjustment_applied: boolean
- hepatic_adjustment_applied: boolean
- bsa_adjustment_applied: boolean
- weight_based: boolean — true if dose was computed per kg or per m2
- adjustments_explained: plain-English explanation of any adjustments made
- warnings: list of strings — any patient-specific warnings (e.g. age >75, low eGFR, obesity)
- max_dose_exceeded: boolean — true if computed dose hits or approaches max daily dose
- max_dose_note: string or null — note if max dose applies

Return ONLY valid JSON. No markdown, no preamble.
"""


def calculate_dose(
    drug_name: str,
    indication: str,
    standard_dose: str,
    route: str,
    frequency: str,
    weight_kg: float,
    height_cm: float,
    age: int,
    egfr: float,
    child_pugh_score: int,
    sex: str,
) -> dict:
    """
    Call Groq to compute a patient-specific adjusted dose.
    Returns structured calculation result dict.
    """
    bsa = calc_bsa(weight_kg, height_cm)

    prompt = CALCULATOR_PROMPT.format(
        drug_name=drug_name,
        indication=indication,
        standard_dose=standard_dose,
        route=route,
        frequency=frequency,
        weight_kg=weight_kg,
        height_cm=height_cm,
        age=age,
        bsa=bsa,
        egfr_category=egfr_category(egfr),
        egfr=egfr,
        child_pugh_label=child_pugh_label(child_pugh_score),
        sex=sex,
    )

    try:
        response = _get_client().chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.05,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        result = json.loads(raw)
        result["bsa"] = bsa
        result["egfr_category"] = egfr_category(egfr)
        result["child_pugh_label"] = child_pugh_label(child_pugh_score)
        return result
    except Exception as e:
        return {"error": str(e)}
