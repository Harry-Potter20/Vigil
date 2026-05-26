from difflib import get_close_matches

# Curated list — common drugs across primary care, cardiology,
# endocrinology, infectious disease, and Africa-prevalent conditions.
DRUG_LIST = [
    # Endocrinology / metabolic
    "metformin", "semaglutide", "tirzepatide", "liraglutide", "dulaglutide",
    "exenatide", "insulin glargine", "insulin aspart", "empagliflozin",
    "dapagliflozin", "canagliflozin", "sitagliptin", "glibenclamide",
    "glimepiride", "levothyroxine",
    # Cardiovascular
    "atorvastatin", "rosuvastatin", "simvastatin", "amlodipine", "nifedipine",
    "lisinopril", "ramipril", "enalapril", "losartan", "valsartan",
    "bisoprolol", "carvedilol", "metoprolol", "digoxin", "furosemide",
    "spironolactone", "warfarin", "apixaban", "rivaroxaban", "aspirin",
    "clopidogrel", "ticagrelor", "nitroglycerine",
    # Infectious disease / Africa-prevalent
    "artemether-lumefantrine", "artesunate", "dihydroartemisinin-piperaquine",
    "chloroquine", "doxycycline", "azithromycin", "amoxicillin",
    "amoxicillin-clavulanate", "ciprofloxacin", "metronidazole",
    "fluconazole", "cotrimoxazole", "isoniazid", "rifampicin",
    "pyrazinamide", "ethambutol", "tenofovir", "lamivudine", "efavirenz",
    "dolutegravir", "nevirapine",
    # Pain / CNS
    "paracetamol", "ibuprofen", "diclofenac", "tramadol", "morphine",
    "gabapentin", "pregabalin", "amitriptyline", "fluoxetine", "sertraline",
    "haloperidol", "diazepam",
    # Respiratory / allergy
    "salbutamol", "budesonide", "fluticasone", "montelukast",
    "loratadine", "cetirizine", "fexofenadine", "promethazine",
    "ipratropium", "theophylline",
    # GI
    "omeprazole", "pantoprazole", "ondansetron", "metoclopramide",
    # Other
    "prednisolone", "dexamethasone", "hydrocortisone", "gentamicin",
    "vancomycin", "heparin", "folic acid", "ferrous sulphate",
]

DRUG_LIST_SORTED = sorted(DRUG_LIST)


def fuzzy_correct(input_name: str, n: int = 3, cutoff: float = 0.6) -> list[str]:
    """
    Return up to n close matches for a partial or misspelled drug name.
    cutoff: similarity threshold 0-1. 0.6 is permissive enough for
    common misspellings like "semalgutide" or "metfromin".
    """
    if not input_name or len(input_name) < 2:
        return []

    query = input_name.lower().strip()

    # First pass — prefix match (handles partial typing like "semal")
    prefix_matches = [d for d in DRUG_LIST if d.startswith(query)]
    if prefix_matches:
        return prefix_matches[:n]

    # Second pass — fuzzy match (handles misspellings)
    fuzzy_matches = get_close_matches(query, DRUG_LIST, n=n, cutoff=cutoff)
    return fuzzy_matches


def exact_or_closest(input_name: str) -> str:
    """
    Return the input if it exactly matches a known drug,
    otherwise return the single closest fuzzy match.
    Used to normalise the drug name before passing to the pipeline.
    """
    query = input_name.lower().strip()
    if query in DRUG_LIST:
        return query
    matches = fuzzy_correct(query, n=1, cutoff=0.82)
    return matches[0] if matches else query
