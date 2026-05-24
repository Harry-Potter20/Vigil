EFFICACY_EXTRACTION_PROMPT = """
You are a clinical pharmacologist analysing head-to-head clinical trial data.

You have been given text from biomedical literature comparing two drugs.
Drug A: {drug_a}
Drug B: {drug_b}
Indication: {indication}

Extract efficacy comparison data from the text. Return a JSON object with:
- indication: the clinical indication being compared
- drug_a_efficacy: dict with:
    - primary_outcome: main efficacy endpoint result (e.g. "HbA1c reduction: -1.8%")
    - nnt: number needed to treat as integer, or null if not reported
    - response_rate: percentage of responders as float, or null
    - time_to_effect: how long until clinical effect (e.g. "4-8 weeks"), or null
    - key_trial: name of landmark trial (e.g. "SUSTAIN-6"), or null
    - evidence_grade: one of [A, B, C] — A=RCT meta-analysis, B=single RCT, C=observational
- drug_b_efficacy: same structure as drug_a_efficacy
- head_to_head_available: boolean — was there a direct RCT comparing the two?
- head_to_head_summary: 1-2 sentence summary of direct comparison if available, else null
- superiority: one of [drug_a, drug_b, comparable, insufficient_data]
- superiority_notes: brief clinical context for the superiority call

Return ONLY valid JSON. No markdown, no preamble.
"""

SIDE_EFFECTS_PROMPT = """
You are a clinical pharmacologist. Compare the side effect profiles of two drugs
for the indication: {indication}

Drug A: {drug_a}
Drug B: {drug_b}

Return a JSON object with:
- drug_a_side_effects: list of objects, each with:
    - effect: name of side effect
    - frequency: percentage incidence as float (e.g. 23.4), or null if unknown
    - severity: one of [mild, moderate, severe]
    - vs_drug_b: one of [higher, lower, similar, unknown]
- drug_b_side_effects: list of objects, same structure, with vs_drug_a field
- shared_side_effects: list of side effects common to both drugs
- key_differentiator: 1 sentence — the most clinically important side effect difference

Limit to the 6 most clinically relevant side effects per drug.
Return ONLY valid JSON. No markdown, no preamble.
"""

GUIDELINE_PROMPT = """
You are a clinical pharmacologist with expertise in international treatment guidelines.

Compare {drug_a} vs {drug_b} for the indication: {indication}

Return a JSON object with:
- who_recommendation: which drug WHO guidelines prefer, with rationale (or "not specified")
- nice_recommendation: which drug NICE guidelines prefer, with rationale (or "not specified")
- aha_acc_recommendation: which drug AHA/ACC guidelines prefer (cardiology context), or "not applicable"
- ada_recommendation: which drug ADA Standards of Care prefer (diabetes context), or "not applicable"
- africa_context: practical guidance specific to African clinical settings — availability,
  cost, supply chain, local guideline preference if known
- preferred_drug: one of [{drug_a}, {drug_b}, "comparable", "indication-dependent"]
- preferred_rationale: 2-3 sentence clinical summary of the guideline preference
- last_guideline_update: approximate year of most recent relevant guideline, or null

Return ONLY valid JSON. No markdown, no preamble.
"""
