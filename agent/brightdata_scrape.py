import os
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
    Scrape WHO, NAFDAC, and SAHPRA for drug-specific content.
    Returns dict of source_name → {url, content, relevant}.
    """
    results = {}
    for source_name, config in LIVE_SOURCES.items():
        raw = scrape_url(config["url"], render=config["render"])
        relevant = drug_name.lower() in raw.lower()
        results[source_name] = {
            "url":      config["url"],
            "content":  raw[:8000] if relevant else "",
            "relevant": relevant,
        }
        status = "relevant" if relevant else "not mentioned"
        print(f"[scraper] {source_name}: {status}")
    return results
