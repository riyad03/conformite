from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from module_folder.models import RequirementAnalysis

_SYSTEM = """\
Tu es un expert GRC senior. Analyse la conformite d'une procedure interne par rapport a une exigence reglementaire.
Reponds avec un JSON structure contenant obligatoirement les quatre axes suivants :

  1. compliance_level  : niveau de conformite — "Conforme" | "Partiellement conforme" | "Non conforme"
  2. analysis          : synthese analytique de 3-5 phrases sur la situation de conformite,
                         appuyee sur des elements factuels de la procedure — "Conforme sans ecart" si Conforme
  3. recommandation    : action corrective principale, concrete et actionnable — vide si Conforme
  4. actions           : liste de 2-5 actions concretes, priorisees et mesurables pour atteindre la conformite
                         — liste vide si Conforme

CHAMPS COMPLEMENTAIRES :
- criticite        : "Critique" | "Majeur" | "Mineur" | "N/A" (N/A si Conforme)
- priorite (calcule selon la grille) :
    Critique + Non conforme                         → "P1 - Urgente"
    Critique + Partiellement conforme               → "P2 - Haute"
    Majeur   + Non conforme                         → "P2 - Haute"
    Majeur   + Partiellement conforme               → "P3 - Modérée"
    Mineur (tout niveau) ou Conforme avec vigilance → "P3 - Modérée"
    Conforme sans ecart                             → "P4 - Surveiller"
- thematique              : theme reglementaire principal
- processus_impactes      : liste 2-4 processus metier impactes
- directions_proprietaires: liste 1-3 directions/services proprietaires
- ecart_description       : description factuelle et detaillee de l'ecart — vide si Conforme
- preuve_constat          : references de preuves ou constats factuels
- effort_estime           : "Faible" | "Moyen" | "Élevé" | "Très élevé"
- echeance_cible          : date cible realiste ou "Surveillance continue" si Conforme
- responsable_action      : direction ou fonction responsable\
"""

DEFAULT_SYSTEM = _SYSTEM


def analyze_requirement(
    req_id: str,
    req_text: str,
    procedure_text: str,
    extra_context: str = "",
    *,
    llm,
    system_prompt: str | None = None,
) -> RequirementAnalysis:
    """Analyse compliance of a procedure against a single requirement (Agent 4)."""
    ctx = f"\n\nCONTEXTE:\n{extra_context[:6000]}" if extra_context else ""
    user = f"Exigence [ID: {req_id}]:\n{req_text}\n\nProcedure:\n{procedure_text[:14000]}{ctx}"
    result: RequirementAnalysis = llm.with_structured_output(RequirementAnalysis).invoke(
        [SystemMessage(content=system_prompt or _SYSTEM), HumanMessage(content=user)]
    )
    result.requirement_id   = req_id
    result.requirement_text = req_text
    return result
