EXTRACTION_PROMPT = """
You are a pharmacovigilance expert. Extract all drug safety signals from the provided documents.

Drug: {drug_name}

For each safety signal found, return a JSON object with a single key "signals" containing an array.
Each signal object must have:
- signal_type: one of [adverse_event, contraindication, drug_interaction, recall, warning]
- severity: one of [critical, moderate, informational]
- population_affected: description of affected population
- summary: concise summary of the signal (1-2 sentences)
- source_name: name of the source document or database
- source_url: URL if available, or null
- credibility: one of [regulatory, peer_reviewed, preprint, forum]
- recommended_action: what clinicians should do
- date_detected: date of the signal if mentioned, or null
- drug_name: the drug name

Return ONLY valid JSON. Use empty array if no signals found.
"""

TRIAL_CROSSREF_PROMPT = """
You are a clinical trial safety expert. Given safety signals for {drug_name} and a list of active trials,
identify which trials may require immediate protocol attention.

Return a JSON object with a single key "trials" containing an array of at-risk trials. Each object:
- trial_id: NCT ID or identifier
- trial_title: trial title
- signal_type: the signal type that triggered this flag
- concern: specific safety concern
- urgency: one of [immediate, review_at_next_meeting, monitor]

Return ONLY valid JSON. Use empty array if no trials at risk.
"""
