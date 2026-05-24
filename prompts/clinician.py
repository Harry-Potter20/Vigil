DDI_PROMPT = """
You are a clinical pharmacist with expertise in drug-drug interactions.

Given the following list of drugs: {drug_list}

Identify all clinically significant drug-drug interactions between any pair.
Return a JSON array. Each object must have:
- drug_a: first drug name
- drug_b: second drug name
- severity: one of [contraindicated, major, moderate, minor]
  - contraindicated = never co-administer
  - major = life-threatening or causing permanent damage
  - moderate = may worsen condition or require close monitoring
  - minor = minimally significant
- mechanism: 1 sentence pharmacokinetic or pharmacodynamic explanation
- clinical_effect: what happens to the patient
- management: what the clinician should do
- evidence_level: one of [established, probable, suspected, theoretical]

Return ONLY valid JSON array. Empty array [] if no interactions found.
"""

DOSING_PROMPT = """
You are a clinical pharmacologist. Provide dosing information for: {drug_name}

Return a JSON array — one object per major indication.
Each object must have:
- drug_name: the drug name
- indication: clinical condition being treated
- standard_dose: dose with units (e.g. "500mg", "0.5-1mg/kg")
- route: one of [oral, IV, IM, subcutaneous, topical, inhaled]
- frequency: dosing frequency (e.g. "twice daily", "every 8 hours", "once weekly")
- renal_adjustment: dose modification for renal impairment, or null
- hepatic_adjustment: dose modification for hepatic impairment, or null
- paediatric_dose: weight-based paediatric dosing, or null
- max_dose: maximum daily dose, or null
- notes: any important clinical notes, or null

Return ONLY valid JSON array.
"""

SPECIAL_POPULATIONS_PROMPT = """
You are a clinical pharmacologist. Provide special population safety data for: {drug_name}

Return a single JSON object with:
- drug_name: the drug name
- pregnancy_category: FDA category (A/B/C/D/X) or "Not rated" — with 1 sentence rationale
- pregnancy_notes: key safety notes for use in pregnancy
- lactation_safety: one of [safe, caution, avoid, unknown]
- lactation_notes: explanation of lactation safety
- geriatric_precautions: specific precautions for patients over 65
- paediatric_restriction: age restrictions or paediatric safety summary

Return ONLY valid JSON object.
"""

PHARMACOGENOMICS_PROMPT = """
You are a clinical pharmacogenomics specialist. Identify known gene-drug interactions for: {drug_name}

Return a JSON array — one object per relevant gene variant.
Each object:
- drug_name: the drug name
- gene: gene name (e.g. CYP2D6, CYP2C19, HLA-B, TPMT, DPYD)
- variant: specific variant or phenotype (e.g. "poor metaboliser", "HLA-B*15:02")
- clinical_impact: what happens to drug metabolism or adverse risk
- recommendation: clinical action based on genotype
- evidence_level: one of [high, moderate, low]

Return ONLY valid JSON array. Empty array [] if no known interactions.
"""

AFRICA_FORMULARY_PROMPT = """
You are a pharmaceutical regulatory specialist with knowledge of African medicines agencies.
Based on your knowledge, provide registration and availability status for: {drug_name}

Return a single JSON object with:
- drug_name: the drug name
- nafdac_status: registration status with Nigeria NAFDAC (registered/not registered/unknown)
- sahpra_status: registration status with South Africa SAHPRA (registered/not registered/unknown)
- who_prequalified: boolean — is this drug WHO prequalified
- availability_notes: practical notes on availability in African markets, generic availability, and supply chain considerations

Return ONLY valid JSON object.
"""
