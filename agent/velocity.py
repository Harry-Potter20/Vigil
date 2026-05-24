import os
from dotenv import load_dotenv

load_dotenv()

try:
    from gxl_paperclip import PaperclipClient
    _client = PaperclipClient(api_key=os.getenv("PAPERCLIP_API_KEY"))
    _has_client = True
except Exception:
    _has_client = False


def compute_velocity(drug_name: str) -> dict:
    """
    Compute signal velocity by comparing 30-day vs 6-month publication counts.
    Returns velocity data with rising signal flags per source.
    """
    sources = ["pubmed", "medrxiv", "biorxiv"]
    velocity_sources = {}
    any_rising = False
    rising_sources = []

    for source in sources:
        count_30d, count_6m = _get_counts(drug_name, source)
        if count_6m == 0:
            velocity_score = 1.0
        else:
            monthly_30d = count_30d
            monthly_6m = count_6m / 6
            velocity_score = round(monthly_30d / monthly_6m, 2) if monthly_6m > 0 else 1.0

        rising = velocity_score >= 2.0 and count_30d >= 3
        if rising:
            any_rising = True
            rising_sources.append(source)

        velocity_sources[source] = {
            "count_30d": count_30d,
            "count_6m": count_6m,
            "velocity_score": velocity_score,
            "rising": rising,
        }

    return {
        "sources": velocity_sources,
        "any_rising": any_rising,
        "rising_sources": rising_sources,
    }


def _get_counts(drug_name: str, source: str) -> tuple[int, int]:
    """Get document counts for 30d and 6m windows."""
    if not _has_client:
        return 0, 0
    try:
        query = f"{drug_name} safety adverse"
        r30 = _client.search(query, limit=100, source=source, days=30)
        r6m = _client.search(query, limit=100, source=source, days=180)
        count_30d = len(r30) if isinstance(r30, list) else 0
        count_6m = len(r6m) if isinstance(r6m, list) else 0
        return count_30d, count_6m
    except Exception as e:
        print(f"[velocity] Count error for {source}: {e}")
        return 0, 0
