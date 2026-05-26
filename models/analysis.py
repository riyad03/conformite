from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


def _to_str(item) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return (
            item.get("text") or item.get("action")
            or item.get("description") or item.get("value") or str(item)
        )
    return str(item)


class SingleValidationResult(BaseModel):
    is_relevant: bool
    reason: str = ""


class RequirementAnalysis(BaseModel):
    requirement_id: str
    requirement_text: str = ""
    thematique: str = ""
    procedure_name: str = ""
    compliance_level: Literal["Conforme", "Partiellement conforme", "Non conforme"]
    criticite: Literal["Critique", "Majeur", "Mineur", "N/A"] = "N/A"
    priorite: Literal["P1 - Urgente", "P2 - Haute", "P3 - Modérée", "P4 - Surveiller"] = "P3 - Modérée"
    processus_impactes: list[str] = []
    directions_proprietaires: list[str] = []
    ecart_description: str = ""
    preuve_constat: str = ""
    analysis: str = ""
    actions: list[str] = []
    recommandation: str = ""
    effort_estime: Literal["Faible", "Moyen", "Élevé", "Très élevé"] = "Moyen"
    echeance_cible: str = ""
    responsable_action: str = ""

    @model_validator(mode="before")
    @classmethod
    def coerce_list_fields(cls, data):
        import json
        if not isinstance(data, dict):
            return data
        for field in ("actions", "processus_impactes", "directions_proprietaires"):
            val = data.get(field)
            if isinstance(val, list):
                data[field] = [_to_str(item) for item in val]
            elif isinstance(val, str):
                try:
                    parsed = json.loads(val)
                    data[field] = [_to_str(item) for item in parsed] if isinstance(parsed, list) else [val]
                except (json.JSONDecodeError, ValueError):
                    data[field] = [val] if val.strip() else []
        return data


class SingleRequirementFeedback(BaseModel):
    satisfait: bool
    score_qualite: int = Field(ge=0, le=100)
    critique: str = ""
    should_reanalyse: bool = False


class RapportFinal(BaseModel):
    procedure_name: str
    selected_processes: list[str]
    score_global: int
    niveau_global: Literal["Conforme", "Partiellement conforme", "Non conforme"]
    resume_executif: str
    nb_total: int
    nb_concernes: int
    nb_conformes: int
    nb_partiels: int
    nb_non_conformes: int
    nb_iterations_evaluateur: int
    analyses: list[RequirementAnalysis]
    client: str = ""
    autorite_emettrice: str = ""
    reference: str = ""
    intitule: str = ""
    entree_en_vigueur: str = ""
    echeance_conformite: str = ""
    date_publication: str = ""
