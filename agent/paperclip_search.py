import os
try:
    import streamlit as st
    for _key in ["PAPERCLIP_API_KEY", "GROQ_API_KEY", "SCRAPERAPI_KEY", "PAPERCLIP_CREDENTIALS_JSON"]:
        if _key in st.secrets and _key not in os.environ:
            os.environ[_key] = st.secrets[_key]
except Exception:
    pass

import json
import subprocess
import requests
from gxl_paperclip.credentials import Credentials
from gxl_paperclip.config import get_base_url


def _run(query: str) -> str:
    """Call the paperclip CLI via subprocess and return raw stdout."""
    cmd = ["paperclip", "search", query, "--json"]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0 or not result.stdout.strip():
            print(f"[paperclip] cmd: {cmd}")
            print(f"[paperclip] returncode: {result.returncode}")
            print(f"[paperclip] stderr: {result.stderr[:500]}")
        return result.stdout
    except FileNotFoundError:
        print(f"[paperclip] command not found — CLI not on PATH")
        return ""
    except Exception as e:
        print(f"[paperclip] subprocess error: {e}")
        return ""


def _ensure_credentials_file():
    """Write PAPERCLIP_CREDENTIALS_JSON secret to ~/.paperclip/credentials.json if absent."""
    creds_json = os.getenv("PAPERCLIP_CREDENTIALS_JSON")
    if not creds_json:
        return
    creds_file = os.path.expanduser("~/.paperclip/credentials.json")
    if os.path.exists(creds_file):
        return
    os.makedirs(os.path.dirname(creds_file), exist_ok=True)
    with open(creds_file, "w") as f:
        f.write(creds_json)


def _get_headers() -> dict:
    _ensure_credentials_file()
    creds = Credentials.load()
    if not creds:
        raise RuntimeError(
            "Paperclip not authenticated. Add PAPERCLIP_CREDENTIALS_JSON to secrets "
            "(run `cat ~/.paperclip/credentials.json` locally to get the value)."
        )
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


def _parse_run_output(raw: str) -> list[dict]:
    """Try JSON parse first, fall back to CLI text parsing."""
    if not raw or not raw.strip():
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, list):
                    return v
    except (json.JSONDecodeError, ValueError):
        pass
    return _parse_papers(raw)


def search_safety_signals(drug_name: str, n: int = 8) -> list[dict]:
    """Search for safety signals across the biomedical corpus."""
    query = f"{drug_name} adverse event safety signal warning contraindication"
    results = _execute("search", f"{query} -n {n}")
    print(f"[paperclip] safety search: {len(results)} papers", flush=True)
    return results


def search_active_trials(drug_name: str, n: int = 15) -> list[dict]:
    """Search for active clinical trials."""
    query = f"{drug_name} clinical trial recruiting active"
    results = _execute("search", f"{query} -n {n}")
    print(f"[paperclip] trials search: {len(results)} papers", flush=True)
    return results


def get_document_count(results: list) -> int:
    return len(results)
