import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from groq import Groq
from dotenv import load_dotenv
from agent.paperclip_search import _execute
from prompts.comparison import (
    EFFICACY_EXTRACTION_PROMPT,
    SIDE_EFFECTS_PROMPT,
    GUIDELINE_PROMPT,
)

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

PAPERCLIP_API_KEY = os.getenv("PAPERCLIP_API_KEY")


def _groq(prompt: str, max_tokens: int = 2048) -> dict | list:
    """Call Groq and parse JSON response."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content
    return json.loads(raw)


def _paperclip_trial_text(drug_a: str, drug_b: str, indication: str) -> str:
    """
    Search Paperclip for head-to-head trial data between two drugs.
    Returns combined raw text for Groq to extract from.
    """
    queries = [
        f'"{drug_a}" versus "{drug_b}" {indication} randomised trial --n 5 --source pmc,medrxiv',
        f'"{drug_a}" "{drug_b}" efficacy comparison {indication} --n 5',
        f'"{drug_a}" "{drug_b}" head-to-head --n 5',
    ]
    blocks = []
    for q in queries:
        try:
            results = _execute("search", q)
            if isinstance(results, list):
                for item in results[:3]:
                    title = item.get("title", "")
                    abstract = item.get("abstract", item.get("content", ""))[:800]
                    if drug_a.lower() in abstract.lower() or drug_b.lower() in abstract.lower():
                        blocks.append(f"TITLE: {title}\n{abstract}")
        except Exception:
            pass

    return "\n\n".join(blocks[:6]) if blocks else ""


def get_efficacy_comparison(drug_a: str, drug_b: str, indication: str) -> dict:
    """Fetch trial data from Paperclip, extract efficacy comparison via Groq."""
    trial_text = _paperclip_trial_text(drug_a, drug_b, indication)

    prompt = EFFICACY_EXTRACTION_PROMPT.format(
        drug_a=drug_a, drug_b=drug_b, indication=indication,
    )

    if trial_text:
        prompt += f"\n\n--- LITERATURE ---\n{trial_text}"
    else:
        prompt += (
            "\n\nNo literature text was retrieved. Use your training knowledge "
            "to provide the best available efficacy comparison. Mark "
            "evidence_grade as B or C accordingly."
        )

    try:
        return _groq(prompt)
    except Exception as e:
        print(f"[comparator_vs] efficacy error: {e}")
        return {}


def get_side_effects_comparison(drug_a: str, drug_b: str, indication: str) -> dict:
    """Compare side effect profiles via Groq knowledge."""
    prompt = SIDE_EFFECTS_PROMPT.format(drug_a=drug_a, drug_b=drug_b, indication=indication)
    try:
        return _groq(prompt)
    except Exception as e:
        print(f"[comparator_vs] side effects error: {e}")
        return {}


def get_guideline_comparison(drug_a: str, drug_b: str, indication: str) -> dict:
    """Get guideline recommendations via Groq knowledge."""
    prompt = GUIDELINE_PROMPT.format(drug_a=drug_a, drug_b=drug_b, indication=indication)
    try:
        return _groq(prompt, max_tokens=1500)
    except Exception as e:
        print(f"[comparator_vs] guideline error: {e}")
        return {}


def run_full_comparison(drug_a: str, drug_b: str, indication: str = "general") -> dict:
    """Run all three comparisons in parallel. Returns combined comparison dict."""
    results = {}

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(get_efficacy_comparison, drug_a, drug_b, indication): "efficacy",
            executor.submit(get_side_effects_comparison, drug_a, drug_b, indication): "side_effects",
            executor.submit(get_guideline_comparison, drug_a, drug_b, indication): "guidelines",
        }
        for future in as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as e:
                print(f"[comparator_vs] {key} failed: {e}")
                results[key] = {}

    results["drug_a"] = drug_a
    results["drug_b"] = drug_b
    results["indication"] = indication
    return results
