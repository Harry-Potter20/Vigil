import os
try:
    import streamlit as st
    for _key in ["PAPERCLIP_API_KEY", "GROQ_API_KEY", "SCRAPERAPI_KEY"]:
        if _key in st.secrets and _key not in os.environ:
            os.environ[_key] = st.secrets[_key]
except Exception:
    pass

import requests
from dotenv import load_dotenv

load_dotenv()

SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")
SCRAPERAPI_URL = "https://api.scraperapi.com/"

# Confirmed working URLs + per-source render requirements
LIVE_SOURCES = {
    "who_alerts": {
        "url":    "https://www.who.int/teams/regulation-prequalification/incidents-and-SF/full-list-of-who-medical-product-alerts",
        "render": False,
    },
    "nafdac": {
        "url":    "https://nafdac.gov.ng/category/recalls-and-alerts/",
        "render": False,
    },
    "sahpra": {
        "url":    "https://www.sahpra.org.za/product-recalls/",
        "render": True,   # Cloudflare — requires JS rendering
    },
}


def scrape_url(url: str, render: bool = False) -> str:
    """
    Fetch a URL via ScraperAPI.
    render=True for JS-heavy or Cloudflare-protected pages (costs 5 credits vs 1).
    """
    params = {
        "api_key":       SCRAPERAPI_KEY,
        "url":           url,
        "output_format": "markdown",
    }
    if render:
        params["render"] = "true"

    try:
        timeout = 60 if render else 30
        r = requests.get(SCRAPERAPI_URL, params=params, timeout=timeout)
        r.raise_for_status()
        return r.text
    except requests.RequestException as e:
        return f"[Scrape failed for {url}: {e}]"


def scrape_live_sources(drug_name: str) -> dict:
    """
    Scrape WHO, NAFDAC, and SAHPRA in parallel.
    Returns dict of source_name → {url, content, relevant}.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _one(name, config):
        raw = scrape_url(config["url"], render=config["render"])
        relevant = drug_name.lower() in raw.lower()
        print(f"[scraper] {name}: {'relevant' if relevant else 'not mentioned'}", flush=True)
        return name, {
            "url":     config["url"],
            "content": raw[:8000] if relevant else "",
            "relevant": relevant,
        }

    results = {}
    with ThreadPoolExecutor(max_workers=len(LIVE_SOURCES)) as ex:
        futures = {ex.submit(_one, name, cfg): name for name, cfg in LIVE_SOURCES.items()}
        for f in as_completed(futures):
            name, data = f.result()
            results[name] = data
    return results
