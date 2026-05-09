from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from .extractor import _suivie
from .state import ConformiteState

load_dotenv()

_INSTRUCTIONS_FILE = Path(__file__).parent.parent / "Instructions pour l'agent d'analyse.txt"


class ExigenceCouverte(BaseModel):
    id: str
    exigence: str
    statut: Literal["conforme", "partiel"]
    evidence: str

class Ecart(BaseModel):
    id: str
    exigence_manquante: str
    description_ecart: str
    impact: Literal["Critique", "Majeur", "Mineur"]
    risque: str
    recommandation: str

class RisqueGlobal(BaseModel):
    categorie: Literal["Opérationnel", "Juridique", "Financier", "Réputation"]
    description: str
    niveau: Literal["Élevé", "Moyen", "Faible"]

class ActionPlan(BaseModel):
    priorite: int = Field(ge=1)
    action: str
    echeance: Literal["Court terme", "Moyen terme", "Long terme"]
    responsable: str

class RapportConformite(BaseModel):
    raisonnement: str
    score_conformite: int = Field(ge=0, le=100)
    niveau: Literal["Conforme", "Partiellement conforme", "Non conforme"]
    resume: str
    exigences_couvertes: list[ExigenceCouverte]
    ecarts: list[Ecart]
    risques_globaux: list[RisqueGlobal]
    plan_action: list[ActionPlan]



_SYSTEM_PROMPT_HEADER = """\
Tu es un expert senior en GRC (Gouvernance, Risque & Conformité), spécialisé dans \
l'audit de procédures internes face à des référentiels normatifs. \
Tu analyses avec rigueur, neutralité et précision.

# OBJECTIFS
1. Identifier les exigences couvertes par la procédure (complètement ou partiellement).
2. Identifier les exigences absentes ou insuffisamment couvertes (écarts).
3. Évaluer le niveau de conformité global sur une échelle de 0 à 100.
4. Proposer un plan d'action priorisé et concret pour combler les écarts.

# PROCESSUS DE RAISONNEMENT (chain-of-thought obligatoire)
Avant de produire ton résultat, tu DOIS raisonner étape par étape dans le champ \
`raisonnement`. Suis impérativement cet ordre :

  Étape 1 — INVENTAIRE DES EXIGENCES
    Liste numérotée de TOUTES les exigences du référentiel avec leur identifiant.
    Ne saute aucune exigence, même si elle semble hors-sujet.

  Étape 2 — ANALYSE EXIGENCE PAR EXIGENCE
    Pour chaque exigence identifiée à l'étape 1 :
    a) Recherche activement dans la procédure un passage qui y répond.
    b) Si trouvé   → cite l'extrait verbatim entre guillemets.
    c) Si absent   → note explicitement « Aucun passage trouvé ».
    d) Si ambigu   → note [AMBIGU] et explique pourquoi.
    e) Statue : conforme / partiel / non-conforme.

  Étape 3 — CALCUL DU SCORE
    Score = (nombre d'exigences conformes + 0.5 × partielles) / total × 100.
    Détaille le calcul : ex. « 3 conformes + 2 × 0.5 partielles = 4/10 = 40 ».

  Étape 4 — ÉVALUATION DES RISQUES
    Pour chaque écart identifié, évalue la conséquence concrète si non corrigé \
(risque légal, opérationnel, financier, réputation).

  Étape 5 — PLAN D'ACTION
    Classe les actions correctives par priorité décroissante. \
Court terme < 3 mois, Moyen terme 3-12 mois, Long terme > 12 mois.

# RÈGLES ABSOLUES
- Ne jamais inventer une exigence absente du référentiel fourni.
- Ne jamais marquer "conforme" si la procédure n'en fait pas mention explicitement.
- Si la procédure ou le référentiel est incomplet → signale [DONNÉES INSUFFISANTES].
- Rester strictement factuel — aucun jugement de valeur sur l'organisation.
- Le score DOIT être cohérent avec le décompte de l'étape 3.
- Niveau : Conforme ≥ 85 | Partiellement conforme 50-84 | Non conforme < 50.

"""


def _load_system_prompt() -> str:
    if _INSTRUCTIONS_FILE.exists():
        instructions = _INSTRUCTIONS_FILE.read_text(encoding="utf-8")
        return _SYSTEM_PROMPT_HEADER + "# RÉFÉRENTIEL DE MÉTHODE D'ANALYSE\n" + instructions + "\n"
    return _SYSTEM_PROMPT_HEADER


_USER_TEMPLATE = """\
Analyse la conformité de la procédure ci-dessous par rapport au référentiel d'exigences.

## RÉFÉRENTIEL D'EXIGENCES
{referentiel}

## PROCÉDURE À ANALYSER
{procedure}
"""


_llm: ChatAnthropic | None = None
_structured_llm = None
_system_prompt: str | None = None


def build_llm() -> ChatAnthropic:
    model    = os.getenv("MODEL_NAME", "claude-sonnet-4-6")
    api_key  = os.getenv("TEMP_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    base_url = os.getenv("TEMP_BASE_URL")
    return ChatAnthropic(model=model, api_key=api_key, base_url=base_url, max_tokens=16384)


def _get_structured_llm():
    global _llm, _structured_llm
    if _structured_llm is None:
        _llm = build_llm()
        _structured_llm = _llm.with_structured_output(RapportConformite)
    return _structured_llm


def _get_system_prompt() -> str:
    global _system_prompt
    if _system_prompt is None:
        _system_prompt = _load_system_prompt()
    return _system_prompt



def analyze_compliance(state: ConformiteState) -> dict:
    print("Analyse LLM en cours...")
    chain = _get_structured_llm()
    rapport: RapportConformite = chain.invoke([
        SystemMessage(content=_get_system_prompt()),
        HumanMessage(content=_USER_TEMPLATE.format(
            referentiel=state["texte_referentiel"][:32000],
            procedure=state["texte_procedure"][:16000],
        )),
    ])
    score  = rapport.score_conformite
    niveau = rapport.niveau
    print(f"[OK] Score : {score}/100 ({niveau})")
    log = list(state.get("suivie_log", [])) + [
        _suivie("compliance_analyzed", {"score": str(score), "niveau": niveau})
    ]
    return {
        "rapport":          rapport.model_dump(),
        "score_conformite": score,
        "niveau":           niveau,
        "suivie_log":       log,
    }
