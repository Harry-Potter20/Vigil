import os
try:
    import streamlit as st
    for _key in ["PAPERCLIP_API_KEY", "GROQ_API_KEY", "SCRAPERAPI_KEY"]:
        if _key in st.secrets and _key not in os.environ:
            os.environ[_key] = st.secrets[_key]
except Exception:
    pass

import json
from typing import Optional
from groq import Groq
from dotenv import load_dotenv
from prompts.clinician import (
    DDI_PROMPT, DOSING_PROMPT, SPECIAL_POPULATIONS_PROMPT,
    PHARMACOGENOMICS_PROMPT, AFRICA_FORMULARY_PROMPT,
)
from agent.schemas import (
    DrugInteraction, DosingInfo, SpecialPopulationFlags,
    PharmacogenomicsFlag, AfricaFormularyStatus, ClinicianData,
)

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


def _call(prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=2048,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


def _unwrap_list(raw: str) -> list:
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        for v in data.values():
            if isinstance(v, list):
                return v
    except Exception:
        pass
    return []


def _unwrap_dict(raw: str) -> dict:
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def get_drug_interactions(drug_list: list[str]) -> list[DrugInteraction]:
    if len(drug_list) < 2:
        return []
    prompt = DDI_PROMPT.format(drug_list=", ".join(drug_list))
    try:
        items = _unwrap_list(_call(prompt))
        return [DrugInteraction(**item) for item in items if isinstance(item, dict)]
    except Exception as e:
        print(f"[clinician] DDI error: {e}")
        return []


def get_dosing(drug_name: str) -> list[DosingInfo]:
    prompt = DOSING_PROMPT.format(drug_name=drug_name)
    try:
        items = _unwrap_list(_call(prompt))
        return [DosingInfo(**item) for item in items if isinstance(item, dict)]
    except Exception as e:
        print(f"[clinician] dosing error: {e}")
        return []


def get_special_populations(drug_name: str) -> Optional[SpecialPopulationFlags]:
    prompt = SPECIAL_POPULATIONS_PROMPT.format(drug_name=drug_name)
    try:
        data = _unwrap_dict(_call(prompt))
        return SpecialPopulationFlags(**{**data, "drug_name": drug_name})
    except Exception as e:
        print(f"[clinician] special pop error: {e}")
        return None


def get_pharmacogenomics(drug_name: str) -> list[PharmacogenomicsFlag]:
    prompt = PHARMACOGENOMICS_PROMPT.format(drug_name=drug_name)
    try:
        items = _unwrap_list(_call(prompt))
        return [
            PharmacogenomicsFlag(**{**item, "drug_name": drug_name})
            for item in items if isinstance(item, dict)
        ]
    except Exception as e:
        print(f"[clinician] PGx error: {e}")
        return []


def get_africa_formulary(drug_name: str) -> Optional[AfricaFormularyStatus]:
    prompt = AFRICA_FORMULARY_PROMPT.format(drug_name=drug_name)
    try:
        data = _unwrap_dict(_call(prompt))
        return AfricaFormularyStatus(**{**data, "drug_name": drug_name})
    except Exception as e:
        print(f"[clinician] Africa formulary error: {e}")
        return None


def get_all_clinician_data(
    drug_name: str,
    drug_list: list[str] = None,
) -> ClinicianData:
    return ClinicianData(
        interactions=get_drug_interactions(drug_list) if drug_list and len(drug_list) >= 2 else [],
        dosing=get_dosing(drug_name),
        special_populations=get_special_populations(drug_name),
        pharmacogenomics=get_pharmacogenomics(drug_name),
        africa_formulary=get_africa_formulary(drug_name),
    )
