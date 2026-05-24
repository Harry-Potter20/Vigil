import os
try:
    import streamlit as st
    for _key in ["PAPERCLIP_API_KEY", "GROQ_API_KEY", "SCRAPERAPI_KEY"]:
        if _key in st.secrets and _key not in os.environ:
            os.environ[_key] = st.secrets[_key]
except Exception:
    pass

import json
import requests
from gxl_paperclip.credentials import Credentials
from gxl_paperclip.config import get_base_url


def _get_headers() -> dict:
    creds = Credentials.load()
    if not creds:
        raise RuntimeError("Not logged in to Paperclip. Run: paperclip login")
    token = creds.get_id_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "paperclip/0.1.4",
    }


def _execute(command: str, raw: str = "") -> list[dict]:
    """Call the Paperclip /api/cli/execute endpoint and parse paper results."""
    base = get_base_url()
    url = f"{base}/api/cli/execute"
    try:
        resp = requests.post(
            url,
            json={"command": command, "raw": raw},
            headers=_get_headers(),
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        output = data.get("output", "")
        return _parse_papers(output)
    except Exception as e:
        print(f"[paperclip] API error: {e}")
        return []


def _parse_papers(output: str) -> list[dict]:
    """Parse Paperclip CLI formatted output into structured dicts."""
    import re

    ansi_escape = re.compile(r"\033\[[0-9;]*m")
    text = ansi_escape.sub("", output)

    papers = []
    entries = re.split(r"\n(?=\s*\d+\.\s)", text)
    for entry in entries:
        lines = entry.strip().split("\n")
        if not lines:
            continue
        m = re.match(r"\s*\d+\.\s+(.+)", lines[0])
        if not m:
            continue

        paper: dict = {"title": m.group(1).strip()}
        remaining = [l.strip() for l in lines[1:] if l.strip()]
        for line in remaining:
            if line.startswith("https://") or line.startswith("http://"):
                paper.setdefault("source_url", line)
            elif line.startswith('"') and line.endswith('"'):
                paper["abstract"] = line.strip('"')
            elif "·" in line or "·" in line:
                sep = "·" if "·" in line else "·"
                parts = [p.strip() for p in line.split(sep)]
                if parts:
                    paper["id"] = parts[0]
                if len(parts) >= 2:
                    paper["source"] = parts[1]
                if len(parts) >= 3:
                    paper["date"] = parts[2]
            elif "authors" not in paper:
                paper["authors"] = line
        papers.append(paper)
    return papers


def search_safety_signals(drug_name: str, n: int = 8) -> list[dict]:
    """Search for safety signals across the biomedical corpus."""
    query = f"{drug_name} adverse event safety signal warning contraindication --n {n}"
    results = _execute("search", query)
    print(f"[paperclip] safety search: {len(results)} papers")
    return results


def search_active_trials(drug_name: str, n: int = 15) -> list[dict]:
    """Search for active clinical trials."""
    query = f"{drug_name} clinical trial recruiting active --n {n} --source clinicaltrials"
    results = _execute("search", query)
    print(f"[paperclip] trials search: {len(results)} papers")
    return results


def get_document_count(results: list) -> int:
    return len(results)
