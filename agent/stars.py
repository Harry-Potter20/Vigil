from datetime import datetime, date
from typing import Optional


def compute_evidence_stars(
    credibility: str,
    date_detected: Optional[str],
    signal_type: str,
) -> int:
    """
    Rules-based evidence quality score. Fully deterministic — no LLM involved.

    Scoring matrix:
    ┌─────────────────┬────────┬──────────┬─────────┬────────┐
    │ Credibility     │ <3mo   │ 3–12mo   │ >12mo   │ None   │
    ├─────────────────┼────────┼──────────┼─────────┼────────┤
    │ regulatory      │  5     │  4       │  4      │  4     │
    │ peer_reviewed   │  4     │  3       │  3      │  3     │
    │ preprint        │  3     │  2       │  2      │  2     │
    │ forum           │  1     │  1       │  1      │  1     │
    └─────────────────┴────────┴──────────┴─────────┴────────┘

    Bonus: +1 if signal_type is recall (regulatory action = highest confidence)
    Cap at 5.
    """
    base = {
        "regulatory":    4,
        "peer_reviewed": 3,
        "preprint":      2,
        "forum":         1,
    }.get(credibility, 2)

    recency_bonus = 0
    if date_detected:
        try:
            detected = datetime.strptime(date_detected, "%Y-%m-%d").date()
            days_old = (date.today() - detected).days
            if days_old <= 90:
                recency_bonus = 1
        except ValueError:
            pass

    recall_bonus = 1 if signal_type == "recall" else 0

    return min(5, base + recency_bonus + recall_bonus)


def stars_html(n: int, accent_color: str, ink3_color: str) -> str:
    """Return HTML star string for rendering in Streamlit."""
    filled = "★" * n
    empty  = "☆" * (5 - n)
    return (
        f"<span style='font-family:\"JetBrains Mono\",monospace;"
        f"font-size:0.75rem;color:{accent_color};'>{filled}</span>"
        f"<span style='font-family:\"JetBrains Mono\",monospace;"
        f"font-size:0.75rem;color:{ink3_color};'>{empty}</span>"
    )
