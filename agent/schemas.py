from pydantic import BaseModel
from typing import Literal, Optional


class SafetySignal(BaseModel):
    signal_type: Literal[
        "adverse_event", "contraindication", "drug_interaction", "recall", "warning"
    ]
    severity: Literal["critical", "moderate", "informational"]
    population_affected: str
    summary: str
    source_name: str
    source_url: Optional[str] = None
    credibility: Literal["regulatory", "peer_reviewed", "preprint", "forum"]
    recommended_action: str
    date_detected: Optional[str] = None
    drug_name: str


class DrugWatchResult(BaseModel):
    drug_name: str
    signals: list[SafetySignal]
    sources_queried: list[str]
    total_documents_scanned: int
    query_duration_seconds: float
    velocity: Optional[dict] = None


class DrugInteraction(BaseModel):
    drug_a: str
    drug_b: str
    severity: Literal["contraindicated", "major", "moderate", "minor"]
    mechanism: str
    clinical_effect: str
    management: str
    evidence_level: Literal["established", "probable", "suspected", "theoretical"]


class DosingInfo(BaseModel):
    drug_name: str
    indication: str
    standard_dose: str
    route: str
    frequency: str
    renal_adjustment: Optional[str] = None
    hepatic_adjustment: Optional[str] = None
    paediatric_dose: Optional[str] = None
    max_dose: Optional[str] = None
    notes: Optional[str] = None


class SpecialPopulationFlags(BaseModel):
    drug_name: str
    pregnancy_category: str
    pregnancy_notes: str
    lactation_safety: Literal["safe", "caution", "avoid", "unknown"]
    lactation_notes: str
    geriatric_precautions: str
    paediatric_restriction: str


class PharmacogenomicsFlag(BaseModel):
    drug_name: str
    gene: str
    variant: str
    clinical_impact: str
    recommendation: str
    evidence_level: Literal["high", "moderate", "low"]


class AfricaFormularyStatus(BaseModel):
    drug_name: str
    nafdac_status: str
    sahpra_status: str
    who_prequalified: bool
    availability_notes: str


class ClinicianData(BaseModel):
    interactions: list[DrugInteraction] = []
    dosing: list[DosingInfo] = []
    special_populations: Optional[SpecialPopulationFlags] = None
    pharmacogenomics: list[PharmacogenomicsFlag] = []
    africa_formulary: Optional[AfricaFormularyStatus] = None
